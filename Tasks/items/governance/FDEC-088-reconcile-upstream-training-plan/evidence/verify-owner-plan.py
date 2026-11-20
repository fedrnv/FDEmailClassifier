"""Verify actual Git source identities and complete, exact plan continuation."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
UPSTREAM = "0ea1e407e32eb2671226ab9f8430e54e4207d6b7"
BASE = "6ecce79"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    identities = json.loads((Path(__file__).parent / "import-inventory-v1.json").read_text())["identities"]
    manifests = [json.loads((ROOT / entry["migration"]["path"]).read_text()) for entry in identities]
    if len(manifests) != 10 or len({m["retired"]["path"] for m in manifests}) != 10:
        raise ValueError("incomplete_collision_inventory")
    preserved = 0
    paths = git("diff", "--name-only", f"{BASE}...{UPSTREAM}", "--", "Tasks").decode().splitlines()
    for path in paths:
        expected = git("show", f"{UPSTREAM}:{path}")
        actual = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        if actual != expected.replace(b"\r\n", b"\n"):
            raise ValueError("owner_source_record_modified")
        preserved += 1
    accepted_changes = git("diff", "--name-status", BASE, "--", "Tasks").decode().splitlines()
    if any(not row.startswith("A\t") for row in accepted_changes):
        raise ValueError("accepted_local_task_history_modified")
    retained_count = 0
    for entry, migration in zip(identities, manifests, strict=True):
        path = entry["retained"]["path"]
        expected = git("show", f"{BASE}:{path}")
        if (ROOT / path).read_bytes().replace(b"\r\n", b"\n") != expected.replace(b"\r\n", b"\n"):
            raise ValueError("retained_local_spec_changed")
        for binding in (migration["retired"], migration["replacement"], *[p["original"] for p in migration["planning_history"]], *[p["replay"] for p in migration["planning_history"]]):
            actual = hashlib.sha256((ROOT / binding["path"]).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            if actual != binding["sha256"]:
                raise ValueError("migration_binding_changed")
        retained_count += 1
    print(f"PASS: {preserved} exact upstream task/Epic/event records preserved; {retained_count} local collision specs unchanged; task ledger changes append-only")


if __name__ == "__main__":
    main()
