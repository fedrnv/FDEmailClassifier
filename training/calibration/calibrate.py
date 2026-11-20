"""Empirical raw-margin thresholds, not probability estimates or safety guarantees."""
from collections import defaultdict, Counter
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/labels"))
from map_annotations import TOPICS, PRIORITIES, ACTIONS

LABELS = tuple("topic:" + value for value in TOPICS) + tuple("priority:" + value for value in PRIORITIES) + ("security:spam", "security:phishing", "security:malware") + tuple("action:" + value for value in ACTIONS)
SCORE_KIND = "binary-logit-margin/v1"


class CalibrationError(ValueError):
    """Static diagnostics only."""


def number(value):
    return type(value) in (float, int) and math.isfinite(value) and abs(value) <= 1_000_000


def validate(bundle):
    import re
    if not isinstance(bundle, dict) or set(bundle) != {"schema", "score_kind", "model", "rows"} or bundle["schema"] != "fdec-calibration-observations/v1" or bundle["score_kind"] != SCORE_KIND:
        raise CalibrationError("unsupported_score_measurements")
    model = bundle["model"]
    if not isinstance(model, dict) or set(model) != {"id", "revision", "sha256"} or any(not isinstance(value, str) for value in model.values()) or not re.fullmatch(r"[A-Za-z0-9_./-]{1,128}", model["id"]) or not re.fullmatch("[a-f0-9]{40}", model["revision"]) or not re.fullmatch("[a-f0-9]{64}", model["sha256"]):
        raise CalibrationError("invalid_score_model_identity")
    rows = bundle["rows"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= 100_000:
        raise CalibrationError("invalid_calibration_rows")
    seen, identities, groups = set(), {}, {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"record_id", "group_id", "role", "language", "label", "score", "gold"}:
            raise CalibrationError("invalid_calibration_row")
        if any(not isinstance(row[name], str) or not re.fullmatch("[a-f0-9]{64}", row[name]) for name in ("record_id", "group_id")) or row["role"] not in ("validation", "test") or row["label"] not in LABELS or not isinstance(row["language"], str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", row["language"]):
            raise CalibrationError("invalid_calibration_identity")
        if row["score"] is not None and not number(row["score"]) or row["gold"] is not None and (type(row["gold"]) is not int or row["gold"] not in (0, 1)):
            raise CalibrationError("invalid_calibration_measurement")
        key = row["record_id"], row["label"]
        if key in seen:
            raise CalibrationError("duplicate_calibration_observation")
        seen.add(key)
        identity = row["group_id"], row["role"], row["language"]
        if row["record_id"] in identities and identities[row["record_id"]] != identity or row["group_id"] in groups and groups[row["group_id"]] != row["role"]:
            raise CalibrationError("calibration_holdout_leakage")
        identities[row["record_id"]], groups[row["group_id"]] = identity, row["role"]
    if {row["role"] for row in rows} != {"validation", "test"}:
        raise CalibrationError("independent_validation_and_test_required")


def fit(bundle, *, min_class_support=20, min_tail_support=20):
    validate(bundle)
    if any(type(value) is not int or not 2 <= value <= 100_000 for value in (min_class_support, min_tail_support)):
        raise CalibrationError("invalid_support_policy")
    buckets = defaultdict(list)
    languages = sorted({row["language"] for row in bundle["rows"] if row["role"] == "validation"})
    for row in bundle["rows"]:
        if row["role"] == "validation":
            buckets[row["language"], row["label"]].append(row)
    policies = {}
    for language in languages:
        policies[language] = {}
        for label in LABELS:
            observed = buckets[language, label]
            known = [row for row in observed if row["score"] is not None and row["gold"] is not None]
            positive = sorted(row["score"] for row in known if row["gold"] == 1)
            negative = sorted(row["score"] for row in known if row["gold"] == 0)
            policy = dict(status="unsupported", reason="insufficient_validation_support", positive_support=len(positive), negative_support=len(negative), unmeasured_validation_rows=len(observed)-len(known),
                          threshold=None, minimum=None, maximum=None, negative_cut=None, positive_cut=None)
            if min(len(positive), len(negative)) >= min_class_support:
                # Exact integer ratios determine F1 ties; larger thresholds win.
                candidates = sorted({row["score"] for row in known})
                best = None
                positives, negatives = Counter(positive), Counter(negative)
                tp, fp = len(positive), len(negative)
                for threshold in candidates:
                    denominator = 2 * tp + fp + len(positive) - tp
                    if best is None or 2 * tp * best[2] >= best[1] * denominator:
                        best = (threshold, 2 * tp, denominator)
                    tp -= positives[threshold]
                    fp -= negatives[threshold]
                clear_tail = [value for value in negative if value < min(positive)]
                flagged_tail = [value for value in positive if value > max(negative)]
                low = max(clear_tail) if len(clear_tail) >= min_tail_support else None
                high = min(flagged_tail) if len(flagged_tail) >= min_tail_support else None
                policy.update(status="supported" if low is not None or high is not None else "unsupported", reason="empirical_tails" if low is not None or high is not None else "overlapping_validation_scores",
                              threshold=best[0], minimum=min(candidates), maximum=max(candidates), negative_cut=low, positive_cut=high)
            policies[language][label] = policy
    return dict(schema="fdec-margin-calibration/v1", score_kind=SCORE_KIND, model=bundle["model"].copy(), min_class_support=min_class_support, min_tail_support=min_tail_support,
                probabilities_estimated=False, fit_role="validation-only", policies=policies)


def decide(policy, score):
    if policy is None or policy.get("status") != "supported":
        return "abstained:unsupported"
    if score is None or not number(score):
        return "abstained:unmeasured"
    if not all(number(policy.get(name)) for name in ("minimum", "maximum")) or policy["minimum"] > policy["maximum"]:
        raise CalibrationError("invalid_calibration_band")
    low, high = policy.get("negative_cut"), policy.get("positive_cut")
    if low is None and high is None or any(value is not None and (not number(value) or not policy["minimum"] <= value <= policy["maximum"]) for value in (low, high)) or low is not None and high is not None and low >= high:
        raise CalibrationError("invalid_calibration_band")
    if not policy["minimum"] <= score <= policy["maximum"]:
        return "abstained:outside_validation_range"
    if policy["negative_cut"] is not None and score <= policy["negative_cut"]:
        return "clear"
    if policy["positive_cut"] is not None and score >= policy["positive_cut"]:
        return "flagged"
    return "abstained:uncertain_band"


def evaluate(artifact, bundle):
    validate(bundle)
    if artifact.get("schema") != "fdec-margin-calibration/v1" or artifact.get("model") != bundle["model"] or artifact.get("score_kind") != bundle["score_kind"] or artifact.get("probabilities_estimated") is not False:
        raise CalibrationError("calibration_model_or_score_kind_changed")
    counts = defaultdict(lambda: dict(eligible=0, decided=0, correct=0, fp=0, fn=0, abstained=0))
    for row in bundle["rows"]:
        if row["role"] != "test" or row["gold"] is None:
            continue
        decision = decide(artifact["policies"].get(row["language"], {}).get(row["label"]), row["score"])
        count = counts[row["language"] + "/" + row["label"]]
        count["eligible"] += 1
        if decision.startswith("abstained:"):
            count["abstained"] += 1
        else:
            predicted = int(decision == "flagged")
            count["decided"] += 1
            count["correct"] += predicted == row["gold"]
            count["fp"] += predicted == 1 and row["gold"] == 0
            count["fn"] += predicted == 0 and row["gold"] == 1
    for value in counts.values():
        value["coverage"] = value["decided"] / value["eligible"]
        value["correct_fraction_all_eligible"] = value["correct"] / value["eligible"]
    return dict(schema="fdec-margin-holdout-report/v1", evaluated_role="test-only", probabilities_estimated=False, counts=dict(sorted(counts.items())))
