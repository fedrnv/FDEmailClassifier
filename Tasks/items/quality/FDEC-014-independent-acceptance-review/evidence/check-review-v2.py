"""Read-only executor reconciliation; never substitutes for semantic review."""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
ROUND = ROOT / "Tasks/epics/FDEC-EPIC-D002/reviews/R002"
EXPECTED = {
    "review_id": "R002",
    "review_task_id": "FDEC-014",
    "epic_id": "FDEC-EPIC-D002",
    "candidate_sha": "94f9669920b1ff105f6d29f1e5e98064f10ca583",
    "candidate_tree": "6b7af50ea1fdbb1a6ad12cdad5dd445cf491560c",
    "ledger_sha": "b1a99b5613b60146ead9e0fac122fd936ab2d48f",
    "policy_sha256": "ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403",
    "gate_result_sha256": "b296cd4acf6267a82f829d1e37c09992640435485ccdd993e12112ee3bb0988b",
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


def git_bytes(revision, path):
    return subprocess.check_output(["git", "-C", str(ROOT), "show", revision + ":" + path])


def canonical(raw):
    return raw.replace(b"\r\n", b"\n")


def ledger_binding(path, expected):
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT) or not resolved.is_file():
        raise ValueError("missing or escaping ledger artifact")
    stored = canonical(git_bytes(EXPECTED["ledger_sha"], path))
    if hashlib.sha256(stored).hexdigest() != expected or canonical(resolved.read_bytes()) != stored:
        raise ValueError("changed bound ledger artifact")
    return stored


def gate_closure(gate, gate_path):
    prefix = "Tasks/items/quality/FDEC-013-targeted-integration-gate/"
    events = git("ls-tree", "-r", "--name-only", EXPECTED["ledger_sha"], "--", prefix + "events").splitlines()
    done = []
    for path in events:
        raw = git_bytes(EXPECTED["ledger_sha"], path).decode("utf-8-sig")
        front = envelope(raw)
        if front.get("event_type") == "status-changed" and re.search(r"\bInProgress -> Done\b", raw):
            done.append((front["created_at"], path, front))
    done.sort()
    if not done or len([row for row in done if row[0] == done[-1][0]]) != 1:
        raise ValueError("missing or ambiguous latest gate Done")
    _, _, front = done[-1]
    proof_path = prefix + front["closure_proof"]
    if not proof_path.startswith(prefix + "evidence/") or ".." in Path(proof_path).parts:
        raise ValueError("invalid gate proof path")
    proof = json.loads(ledger_binding(proof_path, front["closure_proof_sha256"]).decode("utf-8-sig"))
    task_bytes = canonical(git_bytes(EXPECTED["ledger_sha"], prefix + "TASK.md"))
    if (proof.get("source_sha") != EXPECTED["candidate_sha"]
            or proof.get("task_sha256") != hashlib.sha256(task_bytes).hexdigest()
            or proof.get("source_state_sha256") != gate.get("source_state_sha256")):
        raise ValueError("latest gate closure source mismatch")
    verification = proof.get("verification", [])
    if len([entry for entry in verification if entry["path"] == gate_path and entry["sha256"] == EXPECTED["gate_result_sha256"]]) != 1:
        raise ValueError("current gate is not latest Done evidence")
    for entry in verification:
        if not entry["path"].startswith(prefix + "evidence/"):
            raise ValueError("escaping gate verification")
        ledger_binding(entry["path"], entry["sha256"])
    if len(gate.get("stages", [])) != 9 or len(gate.get("component_gate_result", {}).get("stages", [])) != 8:
        raise ValueError("incomplete current/component gate")
    for binding in gate.get("runner_bindings", []):
        ledger_binding(binding["path"], binding["sha256"])
    request = "Tasks/version-requests/FDEC-013.json"
    if canonical(git_bytes(EXPECTED["candidate_sha"], request)) != canonical(git_bytes(EXPECTED["ledger_sha"], request)):
        raise ValueError("original gate request changed")


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
        envelope(request_text.replace("review_id: R002", "review_id: R002\nreview_id: R999"))
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
    gate_path = "Tasks/items/quality/FDEC-013-targeted-integration-gate/evidence/result-v2.json"
    raw = (ROOT / gate_path).read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(raw).hexdigest() != EXPECTED["gate_result_sha256"]:
        raise ValueError("gate identity mismatch")
    gate = json.loads(raw.decode("utf-8-sig"))
    if any(gate.get(k) != EXPECTED[k] for k in ("candidate_sha", "candidate_tree", "epic_id", "policy_sha256")):
        raise ValueError("gate source mismatch")
    if gate.get("result") != "PASS" or gate.get("exit_code") != 0:
        raise ValueError("gate failed")
    gate_closure(gate, gate_path)
    delta = git("diff", "--no-renames", "--name-status", EXPECTED["candidate_sha"], EXPECTED["ledger_sha"]).splitlines()
    prefix = "Tasks/items/quality/FDEC-013-targeted-integration-gate/"
    for line in delta:
        kind, path = line.split("\t")
        if kind != "A" or not (path.startswith(prefix + "events/") or path.startswith(prefix + "evidence/") or path == "Tasks/version-requests/FDEC-013.json"):
            raise ValueError("gate ledger changed implementation")
    print(json.dumps({"schema": "fdec-review-binding-check/v1", "decision": decision,
                      "negative_checks": checks, "gate_ledger_added_paths": len(delta),
                      "latest_gate_done_verified": True, "gate_stages": 9,
                      "original_gate_request_unchanged": True,
                      "semantic_acceptance_automated": False, "mutations": False}, indent=2))


if __name__ == "__main__":
    main()
