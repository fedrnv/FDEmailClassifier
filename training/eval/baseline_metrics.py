"""Masked baseline measurements. This module never generates gold annotations."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/labels"))
from map_annotations import TOPICS, DIMENSIONS, validate_projection


class EvaluationError(ValueError):
    """Static diagnostics only."""


def projection(value):
    try:
        if not isinstance(value, dict):
            raise ValueError()
        validate_projection(value)
        return value
    except Exception:
        raise EvaluationError("invalid_classification") from None


def field(value, head):
    if head in ("spam", "phishing", "malware"):
        return value["security"][head]
    return value["suggested_action" if head == "action" else head]


def validate_gold(row):
    from re import fullmatch
    if not isinstance(row, dict) or set(row) != {"record_id", "language", "classification", "mask"}:
        raise EvaluationError("invalid_gold_row")
    if not isinstance(row["record_id"], str) or not fullmatch("[a-f0-9]{64}", row["record_id"]):
        raise EvaluationError("invalid_gold_identity")
    if not isinstance(row["language"], str) or not fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", row["language"]):
        raise EvaluationError("invalid_gold_language")
    value, mask = projection(row["classification"]), row["mask"]
    if not isinstance(mask, dict) or set(mask) != set(DIMENSIONS) or any(type(v) is not bool for v in mask.values()) or not any(mask.values()):
        raise EvaluationError("invalid_gold_mask")
    for head in DIMENSIONS:
        if mask[head] and (value["status"] != "classified" or field(value, head) == "unknown" or head == "topics" and not value["topics"]):
            raise EvaluationError("uncertain_gold_is_not_supervision")
    return row


def score(gold, predictions):
    """None means invalid output and counts as a failure for every eligible head.

    Unknown/abstained predictions also count as incorrect. Unknown gold is never
    promoted to a negative. Topic micro F1 includes a false negative for each
    missed positive; valid extra topics add false positives. Macro F1 uses only
    topics having gold support. Scalar accuracy denominators include failures.
    """
    if not isinstance(gold, list) or not gold or len(gold) != len(predictions):
        raise EvaluationError("invalid_measurement_alignment")
    for row in gold:
        validate_gold(row)
    if len({row["record_id"] for row in gold}) != len(gold):
        raise EvaluationError("duplicate_gold_identity")
    for value in predictions:
        if value is not None:
            projection(value)

    def aggregate(indexes):
        heads = {name: {"eligible": 0, "correct": 0} for name in DIMENSIONS}
        counts = {topic: dict(tp=0, fp=0, fn=0, support=0) for topic in TOPICS}
        invalid = abstained = unknown = 0
        for index in indexes:
            row, predicted = gold[index], predictions[index]
            invalid += predicted is None
            abstained += predicted is not None and predicted["status"] == "abstained"
            unknown += predicted is not None and predicted["status"] == "unknown"
            usable = predicted is not None and predicted["status"] == "classified"
            for head in DIMENSIONS:
                if not row["mask"][head]:
                    continue
                heads[head]["eligible"] += 1
                target = field(row["classification"], head)
                actual = field(predicted, head) if usable else None
                heads[head]["correct"] += actual == target if head != "topics" else usable and set(actual) == set(target)
                if head == "topics":
                    expected, observed = set(target), set(actual or ())
                    for topic, count in counts.items():
                        count["tp"] += topic in expected & observed
                        count["fp"] += topic in observed - expected
                        count["fn"] += topic in expected - observed
                        count["support"] += topic in expected
        for head in heads.values():
            head["accuracy"] = head["correct"] / head["eligible"] if head["eligible"] else None
        def f1(count):
            denominator = 2 * count["tp"] + count["fp"] + count["fn"]
            return 2 * count["tp"] / denominator if denominator else None
        total = {name: sum(count[name] for count in counts.values()) for name in ("tp", "fp", "fn")}
        supported = [f1(count) for count in counts.values() if count["support"]]
        return {"rows": len(indexes), "invalid_outputs": invalid, "abstained_outputs": abstained, "unknown_outputs": unknown,
                "heads": heads, "topics": {"micro_f1": f1(total), "macro_supported_f1": sum(supported) / len(supported) if supported else None,
                "macro_denominator": len(supported), "counts": counts}}
    return {"schema": "fdec-baseline-metrics/v1", "overall": aggregate(list(range(len(gold)))),
            "by_language": {language: aggregate([i for i, row in enumerate(gold) if row["language"] == language]) for language in sorted({row["language"] for row in gold})}}
