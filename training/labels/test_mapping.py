"""Synthetic annotation metadata only; no mail contents or corpus access."""

from copy import deepcopy
import io
from contextlib import redirect_stdout, redirect_stderr
import json
from pathlib import Path
import sys
import unittest

import map_annotations as mapping

LOCAL = dict(dataset_id="fdec/canonical-annotations", revision="1", artifact="annotations.jsonl", sha256="b" * 64)
SEED = dict(dataset_id=mapping.SEED_ID, revision=mapping.SEED_REVISION, artifact="data/train.parquet", sha256=mapping.SEED_HASH)


def annotation(row=0, **labels):
    return dict(source_row=row, labels=labels)


def mapped(*annotations, source=LOCAL):
    return mapping.map_annotations(content_id="a" * 64, source=source, annotations=list(annotations))


def schema_fixtures():
    for category in mapping.TOPICS:
        yield mapped(annotation(category=category, priority="normal", action="review", security="normal"))
    for category in ("finance", "travel", "newsletter", "promotion", "personal", "meeting_request", "customer_support", "system_update", "spam", "phishing", "unknown", "new_value"):
        yield mapped(annotation(category=category, priority="medium", action="forward"), source=SEED)
    yield mapped(annotation(labels=["work", "finance"], priority="urgent", security="phishing", action="reply"))
    yield mapped(annotation(category="finance"), annotation(1, category="travel"))
    yield mapped(annotation(category="other", status="abstained", security="phishing"))
    yield mapped(annotation())


class MappingTests(unittest.TestCase):
    def test_twelve_topics_and_multilabel(self):
        for topic in mapping.TOPICS:
            with self.subTest(topic=topic):
                result = mapped(annotation(category=topic))
                self.assertEqual(result["classification"]["topics"], [topic])
                self.assertTrue(result["training_mask"]["topics"])
        result = mapped(annotation(labels=["finance", "work", "finance"]))
        self.assertEqual(result["classification"]["topics"], ["work", "finance"])

    def test_all_priorities_and_actions(self):
        for priority in mapping.PRIORITIES:
            for action in mapping.ACTIONS:
                result = mapped(annotation(category="work", priority=priority, action=action))
                self.assertEqual(result["classification"]["priority"], priority)
                self.assertEqual(result["classification"]["suggested_action"], action)
                self.assertTrue(result["training_mask"]["priority"])
                self.assertTrue(result["training_mask"]["action"])

    def test_seed_card_vocabulary(self):
        for category, topic in dict(finance="finance", travel="travel", newsletter="newsletters", promotion="marketing", personal="personal").items():
            result = mapped(annotation(category=category, priority="medium", action="flag"), source=SEED)
            self.assertEqual(result["classification"]["topics"], [topic])
            self.assertEqual(result["classification"]["priority"], "normal")
            self.assertEqual(result["classification"]["suggested_action"], "review")
        for priority, target in dict(low="low", medium="normal", high="high", urgent="urgent").items():
            self.assertEqual(mapped(annotation(priority=priority), source=SEED)["dimensions"]["priority"]["values"], [target])
        for action, target in dict(reply="reply", archive="archive", flag="review", ignore="none").items():
            self.assertEqual(mapped(annotation(action=action), source=SEED)["dimensions"]["action"]["values"], [target])

    def test_seed_ambiguous_topics_are_candidates_not_multilabel_targets(self):
        for category, candidates in dict(meeting_request=["social", "work"], customer_support=["shopping", "work"]).items():
            result = mapped(annotation(category=category), source=SEED)
            self.assertEqual(result["dimensions"]["topics"]["state"], "ambiguous")
            self.assertEqual(result["dimensions"]["topics"]["values"], candidates)
            self.assertFalse(result["training_mask"]["topics"])
            self.assertEqual(result["classification"]["status"], "abstained")

    def test_unsupported_actions_are_not_silently_relabelled(self):
        for action in ("forward", "mark_read", "delete", "execute", "new_value"):
            result = mapped(annotation(category="finance", action=action), source=SEED)
            self.assertEqual(result["dimensions"]["action"]["state"], "unmapped")
            self.assertEqual(result["classification"]["suggested_action"], "review")
            self.assertFalse(result["training_mask"]["action"])
            self.assertEqual(result["annotations"][0]["source_annotation"]["labels"]["action"], action)

    def test_security_normal_spam_phishing_independent_of_topics(self):
        for label in ("normal", "spam", "phishing"):
            result = mapped(annotation(category="marketing", security=label))
            security = result["classification"]["security"]
            self.assertEqual(security["malware"], "unknown")
            if label == "normal":
                self.assertEqual((security["spam"], security["phishing"]), ("clear", "clear"))
            else:
                self.assertEqual(security[label], "flagged")
                self.assertEqual(security["phishing" if label == "spam" else "spam"], "unknown")
        result = mapped(annotation(category="promotion"), source=SEED)
        self.assertEqual(set(result["classification"]["security"].values()), {"unknown"})
        for security in ("spam", "phishing"):
            result = mapped(annotation(category=security), source=SEED)
            self.assertEqual(result["classification"]["security"][security], "flagged")
            self.assertFalse(result["training_mask"]["topics"])
            self.assertEqual(result["classification"]["topics"], [])

    def test_unknown_never_becomes_other(self):
        for category in ("unknown", "", "new_label", "system_update", "Finance"):
            result = mapped(annotation(category=category), source=SEED)
            self.assertEqual(result["classification"]["topics"], [])
            self.assertFalse(result["training_mask"]["topics"])
        self.assertEqual(mapped(annotation(category="other"))["classification"]["topics"], ["other"])

    def test_missing_unknown_and_abstain_remain_distinct(self):
        for labels, state in (({}, "missing"), ({"category": "unknown"}, "unknown"), ({"category": "abstain"}, "abstained"), ({"category": "new_value"}, "unmapped")):
            result = mapped(annotation(**labels))
            self.assertEqual(result["dimensions"]["topics"]["state"], state)
            self.assertFalse(result["training_mask"]["topics"])

    def test_explicit_withholding_disables_targets_but_retains_security(self):
        for status in ("unknown", "abstained"):
            result = mapped(annotation(category="work", priority="high", action="reply", security="phishing", status=status))
            self.assertEqual(result["classification"]["status"], status)
            self.assertEqual(result["classification"]["topics"], [])
            self.assertEqual(result["classification"]["priority"], "unknown")
            self.assertEqual(result["classification"]["suggested_action"], "review")
            self.assertEqual(result["classification"]["security"]["phishing"], "flagged")
            self.assertTrue(result["training_mask"]["phishing"])
            self.assertFalse(any(result["training_mask"][key] for key in ("topics", "priority", "action")))

    def test_conflicting_duplicate_annotations_no_majority_vote_or_union(self):
        result = mapped(annotation(category="work", priority="low", action="reply"), annotation(1, category="finance", priority="high", action="archive"), annotation(2, category="work", priority="low", action="reply"))
        self.assertEqual(len(result["annotations"]), 3)
        for key in ("topics", "priority", "action"):
            self.assertEqual(result["dimensions"][key]["state"], "ambiguous")
            self.assertFalse(result["training_mask"][key])
        self.assertEqual(result["classification"]["status"], "abstained")

    def test_conflicting_security_is_unknown_not_clear_or_flagged(self):
        result = mapped(annotation(security="normal"), annotation(1, security="phishing"))
        self.assertEqual(result["dimensions"]["phishing"]["state"], "ambiguous")
        self.assertEqual(result["classification"]["security"]["phishing"], "unknown")
        self.assertFalse(result["training_mask"]["phishing"])

    def test_missing_duplicate_not_contradiction_but_explicit_unknown_is(self):
        self.assertTrue(mapped(annotation(category="work"), annotation(1))["training_mask"]["topics"])
        self.assertFalse(mapped(annotation(category="work"), annotation(1, category="unknown"))["training_mask"]["topics"])

    def test_round_order_and_duplicate_identical_labels_are_deterministic(self):
        first = dict(annotation(1, category="work"), source_round="r1")
        second = dict(annotation(0, category="work"), source_round="r2")
        self.assertEqual(mapped(first, second), mapped(second, first))
        self.assertTrue(mapped(first, second)["training_mask"]["topics"])

    def test_normalized_bridge_does_not_copy_or_read_message_fields(self):
        record = dict(schema="fdec-normalized-email/v1", content_id="a" * 64, source=SEED, annotations=[annotation(category="finance")], subject=object(), body=object(), annotation_conflict=False)
        result = mapping.map_normalized_record(record)
        self.assertNotIn("subject", result)
        self.assertNotIn("body", result)
        self.assertEqual(result["classification"]["topics"], ["finance"])

    def test_no_input_mutation_and_output_does_not_alias_input(self):
        source, annotations = deepcopy(SEED), [annotation(category="finance", action="forward")]
        before = deepcopy((source, annotations))
        result = mapping.map_annotations(content_id="a" * 64, source=source, annotations=annotations)
        self.assertEqual((source, annotations), before)
        result["annotations"][0]["source_annotation"]["labels"]["category"] = "changed"
        result["source"]["dataset_id"] = "changed"
        self.assertEqual((source, annotations), before)

    def test_invalid_input_static_errors_and_original_state_preserved(self):
        invalid = [None, [], {}, {"source_row": True, "labels": {}}, annotation(-1), annotation(100000), annotation(category=42), annotation(labels="work"), annotation(labels=["work"] * 33), annotation(category="private\\nbody"), annotation(category="\ud800"), annotation(status="invalid"), dict(annotation(), extra="private"), annotation(secret="private")]
        for value in invalid:
            with self.subTest(value_type=type(value).__name__):
                before = deepcopy(value)
                output = io.StringIO()
                with redirect_stdout(output), redirect_stderr(output), self.assertRaises(mapping.MappingError) as error:
                    mapped(value)
                self.assertRegex(str(error.exception), r"^[a-z_]+$")
                self.assertEqual(output.getvalue(), "")
                self.assertEqual(value, before)

    def test_reject_duplicate_rows_and_empty_metadata(self):
        for annotations in ([], None, [annotation(), annotation()]):
            with self.assertRaises(mapping.MappingError):
                mapping.map_annotations(content_id="a" * 64, source=LOCAL, annotations=annotations)

    def test_unsupported_sources_revisions_artifacts_and_hashes(self):
        for source in (None, {}, dict(SEED, dataset_id="talby/spamassassin"), dict(SEED, dataset_id="imnim/multiclass-email-classification"), dict(SEED, revision="main"), dict(SEED, artifact="messages.jsonl"), dict(SEED, sha256="0" * 64), dict(LOCAL, revision="2"), dict(LOCAL, sha256=True)):
            with self.subTest(source=source), self.assertRaises(mapping.MappingError):
                mapped(annotation(), source=source)
        with self.assertRaises(mapping.MappingError):
            mapping.map_annotations(content_id="private", source=LOCAL, annotations=[annotation()])
        with self.assertRaises(mapping.MappingError):
            mapping.map_normalized_record({"schema": "future"})

    def test_seed_does_not_accept_invented_source_columns(self):
        for labels in (dict(security="normal"), dict(labels=["work"]), dict(status="abstained")):
            with self.assertRaises(mapping.MappingError):
                mapped(annotation(**labels), source=SEED)

    def test_no_missing_action_or_unknown_topic_is_supervision_fallback(self):
        result = mapped(annotation(category="finance"))
        self.assertEqual(result["classification"]["suggested_action"], "review")
        self.assertFalse(result["training_mask"]["action"])
        # A topic-only abstention does not discard independent priority evidence.
        result = mapped(annotation(category="unknown", priority="urgent", action="reply"))
        self.assertTrue(result["training_mask"]["priority"])
        self.assertEqual(result["dimensions"]["priority"]["values"], ["urgent"])
        self.assertEqual(result["classification"]["priority"], "unknown")

    def test_canonical_contract_enumerations_unchanged(self):
        schema = json.loads((mapping.ROOT / "schemas/classification-v1.schema.json").read_text())
        self.assertEqual(list(mapping.TOPICS), schema["properties"]["topics"]["items"]["enum"])
        self.assertEqual(["unknown", *mapping.PRIORITIES], schema["properties"]["priority"]["enum"])
        self.assertEqual(list(mapping.ACTIONS), schema["properties"]["suggested_action"]["enum"])
        for result in schema_fixtures():
            mapping.validate_projection(result["classification"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--fixtures":
        output = Path(sys.argv[2]).resolve()
        if not output.is_relative_to(mapping.ROOT / "training/outputs") or output.exists():
            raise SystemExit("invalid_fixture_output")
        output.mkdir(parents=True)
        for index, result in enumerate(schema_fixtures()):
            (output / f"mapping-{index}.json").write_text(mapping.canonical(result), encoding="utf-8")
            (output / f"classification-{index}.json").write_text(mapping.canonical(result["classification"]), encoding="utf-8")
        # The same generic schema must reject unsafe structural claims.
        for index, change in enumerate((lambda v: v.update(schema="future"), lambda v: v["dimensions"]["topics"].update(supervise=False), lambda v: v["classification"].update(suggested_action="delete"), lambda v: v["dimensions"]["priority"].update(values=["medium"]), lambda v: v.update(extra=True))):
            result = next(schema_fixtures())
            change(result)
            (output / f"invalid-{index}.json").write_text(mapping.canonical(result), encoding="utf-8")
    else:
        unittest.main()
