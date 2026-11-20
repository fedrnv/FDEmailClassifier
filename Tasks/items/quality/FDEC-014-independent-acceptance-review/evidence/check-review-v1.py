"""Read-only executor reconciliation; never substitutes for semantic review."""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
ROUND = ROOT / "Tasks/epics/FDEC-EPIC-D002/reviews/R001"
EXPECTED = {
    "review_id": "R001",
    "review_task_id": "FDEC-014",
    "epic_id": "FDEC-EPIC-D002",
    "candidate_sha": "0bcd4c4f377af86ee8b83d1d0bf770f0eb448ad8",
    "candidate_tree": "558697de3b18fd1bea8358a144bae90a90231c76",
    "ledger_sha": "7868e944c7a9c5e721b0a435acd0ae572055789d",
    "policy_sha256": "ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403",
    "gate_result_sha256": "0702e6c97126247f79ab5184b1c4b1e74d453877346fac3b776800ea882b9f10",
}


def envelope(text):
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip("\ufeff\r\n "):
        raise ValueError("missing envelope")
    fields = {}
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([a-z_][a-z_0-9]*): (.+)", line)
        if not match or match[1] in fields:
            raise ValueError("invalid or duplicate field")
        fields[match[1]] = match[2].strip().strip('"')
    return fields


def validate(request, result):
    for fields, schema in ((request, "fdec-independent-review-request/v1"),
                           (result, "fdec-independent-review-result/v1")):
        if fields.get("schema") != schema:
            raise ValueError("invalid schema")
        for key, value in EXPECTED.items():
            if fields.get(key) != value:
                raise ValueError("mismatched " + key)
    if not result.get("reviewer", "").strip():
        raise ValueError("missing reviewer")
    if result.get("result") not in {"Accepted", "ChangesRequired"}:
        raise ValueError("invalid decision")
    return result["result"]


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def main():
    request_text = (ROUND / "REQUEST.md").read_text(encoding="utf-8-sig")
    request = envelope(request_text)
    # Isolated, explicitly counterfactual envelopes test fail-closed behavior.
    # They are never written as reviewer evidence or accepted as a real review.
    technical = dict(EXPECTED, schema="fdec-independent-review-result/v1",
                     reviewer="technical-parser-fixture", result="Accepted")
    assert validate(request, technical) == "Accepted"
    checks = 0
    for field in [*EXPECTED, "schema", "reviewer", "result"]:
        bad = copy.deepcopy(technical)
        bad.pop(field)
        try:
            validate(request, bad)
        except ValueError:
            checks += 1
        else:
            raise AssertionError("accepted missing " + field)
    for field in EXPECTED:
        bad = dict(technical, **{field: "wrong"})
        try:
            validate(request, bad)
        except ValueError:
            checks += 1
        else:
            raise AssertionError("accepted mismatched " + field)
    try:
        envelope(request_text.replace("review_id: R001", "review_id: R001\nreview_id: R999"))
    except ValueError:
        checks += 1
    else:
        raise AssertionError("accepted duplicate identity")
    assert validate(request, dict(technical, result="ChangesRequired")) == "ChangesRequired"
    result_file = ROUND / "RESULT.md"
    if not result_file.is_file():
        raise ValueError("independent RESULT.md missing; closure prohibited")
    decision = validate(request, envelope(result_file.read_text(encoding="utf-8-sig")))
    if git("rev-parse", EXPECTED["candidate_sha"] + "^{tree}") != EXPECTED["candidate_tree"]:
        raise ValueError("candidate tree mismatch")
    gate_path = "Tasks/items/quality/FDEC-013-targeted-integration-gate/evidence/result-v1.json"
    raw = (ROOT / gate_path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != EXPECTED["gate_result_sha256"]:
        raise ValueError("gate identity mismatch")
    gate = json.loads(raw.decode("utf-8-sig"))
    if any(gate.get(k) != EXPECTED[k] for k in ("candidate_sha", "candidate_tree", "epic_id", "policy_sha256")):
        raise ValueError("gate source mismatch")
    if gate.get("result") != "PASS" or gate.get("exit_code") != 0:
        raise ValueError("gate failed")
    delta = git("diff", "--no-renames", "--name-status", EXPECTED["candidate_sha"], EXPECTED["ledger_sha"]).splitlines()
    prefix = "Tasks/items/quality/FDEC-013-targeted-integration-gate/"
    for line in delta:
        kind, path = line.split("\t")
        if kind != "A" or not (path.startswith(prefix + "events/") or path.startswith(prefix + "evidence/") or path == "Tasks/version-requests/FDEC-013.json"):
            raise ValueError("gate ledger changed implementation")
    print(json.dumps({"schema": "fdec-review-binding-check/v1", "decision": decision,
                      "negative_checks": checks, "gate_ledger_added_paths": len(delta),
                      "semantic_acceptance_automated": False, "mutations": False}, indent=2))


if __name__ == "__main__":
    main()
