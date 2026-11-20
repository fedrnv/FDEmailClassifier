"""Versioned multilingual multi-label metrics with explicit unresolved decisions."""
from collections import defaultdict

from baseline_metrics import EvaluationError, TOPICS, field, score as baseline_score
from map_annotations import PRIORITIES, ACTIONS

UNRESOLVED = ("__invalid__", "__unknown__", "__abstained__")


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def decision(prediction, head):
    if prediction is None:
        return "__invalid__"
    if prediction["status"] != "classified":
        return "__abstained__" if prediction["status"] == "abstained" else "__unknown__"
    value = field(prediction, head)
    return "__unknown__" if value == "unknown" else value


def measure(gold, predictions):
    """Validated aligned records, not an attestation of model/data provenance.

    Topic FN includes missed positives on invalid/abstained outputs. Binary FPR
    is conditional on decided reviewed negatives; unresolved bounds separately
    show the full-negative denominator. Unsupported/no-eligible scores are null.
    """
    if not isinstance(predictions, list):
        raise EvaluationError("invalid_measurement_alignment")
    result = baseline_score(gold, predictions)
    languages = defaultdict(list)
    for index, row in enumerate(gold):
        languages[row["language"]].append(index)

    def enhance(section, indexes):
        topics = section["topics"]
        for count in topics["counts"].values():
            count["precision"] = ratio(count["tp"], count["tp"] + count["fp"])
            count["recall"] = ratio(count["tp"], count["support"])
            count["f1"] = ratio(2 * count["tp"], 2 * count["tp"] + count["fp"] + count["fn"])
        eligible_topics = section["heads"]["topics"]["eligible"]
        topics["macro_f1"] = sum(item["f1"] or 0 for item in topics["counts"].values()) / len(TOPICS) if eligible_topics else None
        topics["macro_all_labels_denominator"] = len(TOPICS) if eligible_topics else 0
        topics["eligible_rows"] = eligible_topics
        topics["decided_rows"] = sum(gold[i]["mask"]["topics"] and predictions[i] is not None and predictions[i]["status"] == "classified" for i in indexes)
        topics["decision_coverage"] = ratio(topics["decided_rows"], eligible_topics)
        for head, values in (("priority", PRIORITIES), ("action", ACTIONS), ("spam", ("clear", "flagged")), ("phishing", ("clear", "flagged")), ("malware", ("clear", "flagged"))):
            matrix = {truth: dict.fromkeys((*values, *UNRESOLVED), 0) for truth in values}
            for index in indexes:
                if gold[index]["mask"][head]:
                    matrix[field(gold[index]["classification"], head)][decision(predictions[index], head)] += 1
            metric = section["heads"][head]
            decided = sum(matrix[truth][predicted] for truth in values for predicted in values)
            metric.update(confusion=matrix, decided=decided, decision_coverage=ratio(decided, metric["eligible"]), unresolved=metric["eligible"] - decided)
            if head in ("spam", "phishing", "malware"):
                tp, fp, tn, fn = matrix["flagged"]["flagged"], matrix["clear"]["flagged"], matrix["clear"]["clear"], matrix["flagged"]["clear"]
                clear = sum(matrix["clear"].values())
                flagged = sum(matrix["flagged"].values())
                unresolved_clear, unresolved_flagged = clear - fp - tn, flagged - tp - fn
                metric.update(tp=tp, fp=fp, tn=tn, fn_decided=fn, clear_support=clear, flagged_support=flagged,
                              unresolved_clear=unresolved_clear, unresolved_flagged=unresolved_flagged,
                              false_positive_rate=ratio(fp, fp + tn), false_positive_rate_denominator=fp + tn,
                              unresolved_fpr_bounds={"lower": ratio(fp, clear), "upper": ratio(fp + unresolved_clear, clear), "denominator": clear},
                              recall_with_unresolved_as_misses=ratio(tp, flagged))
    enhance(result["overall"], list(range(len(gold))))
    for language, indexes in languages.items():
        enhance(result["by_language"][language], indexes)
    result["schema"] = "fdec-multilabel-metrics/v1"
    result["definitions"] = {"macro_f1": "all-12-topics; zero undefined class F1 only when topic-eligible rows exist", "macro_supported_f1": "gold-supported-topics-only",
                             "invalid_outputs": "retained as failures in eligible correctness and topic-recall denominators",
                             "false_positive_rate": "FP/(FP+TN) on decided reviewed clear examples; inspect coverage and unresolved_fpr_bounds",
                             "unresolved_fpr_bounds": "possible full-negative FPR range if unresolved predictions become clear/flagged, not a confidence interval"}
    return result
