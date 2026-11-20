"""One-shot, append-only replay of a pinned owner's planned task namespace."""
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[5]
UPSTREAM = "0ea1e407e32eb2671226ab9f8430e54e4207d6b7"
BASE = "6ecce79"
TASK = "Tasks/items/governance/FDEC-088-reconcile-upstream-training-plan"
MAPPING = {f"FDEC-{number:03}": f"FDEC-{number + 15:03}" for number in range(74, 84)}


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def original(revision, path):
    return git("show", f"{revision}:{path}").decode("utf-8")


def mapped(text):
    return re.sub(r"\bFDEC-\d{3}\b", lambda m: MAPPING.get(m[0], m[0]), text)


def put(relative, text):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def bind(path):
    return dict(path=path, sha256=hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest())


def event(directory, task_id, kind, payload, **fields):
    uid = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    # Owner planning events use 17:32 UTC. Never retire before their timestamp.
    now = max(now, datetime(2026, 11, 20, 17, 32, 3, tzinfo=timezone.utc))
    timestamp = now.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    relative = f"{directory}/events/{now.strftime('%Y%m%dT%H%M%S%fZ')}-codex-{kind}-{uid[:8]}.md"
    front = dict(schema="fdtasks-event/v3", event_id=uid, task_id=task_id,
                 event_type=kind, created_at=timestamp, actor="codex",
                 base_revision=git("rev-parse", "HEAD").decode().strip(), server_revision=None, **fields)
    put(relative, "---\n" + "".join(f"{key}: {json.dumps(value) if value is not None else 'null'}\n" if key in ("base_revision",) else f"{key}: {value if value is not None else 'null'}\n" for key, value in front.items()) + "---\n\n## Payload\n" + payload + "\n")
    return relative


def main():
    source_paths = git("ls-tree", "-r", "--name-only", UPSTREAM, "--", "Tasks/items").decode().splitlines()
    base_paths = git("ls-tree", "-r", "--name-only", BASE, "--", "Tasks/items").decode().splitlines()
    inventory = []
    for old_id, new_id in MAPPING.items():
        old_path, = [p for p in source_paths if p.endswith("/TASK.md") and f"/{old_id}-" in p]
        retained_path, = [p for p in base_paths if p.endswith("/TASK.md") and f"/{old_id}-" in p]
        old_text = original(UPSTREAM, old_path)
        if (ROOT / old_path).read_text(encoding="utf-8").replace("\r\n", "\n") != old_text:
            raise ValueError("imported source spec differs from pinned upstream")
        new_path = old_path.replace(f"/{old_id}-", f"/{new_id}-")
        put(new_path, mapped(old_text))
        parent = re.search(r"(?m)^epic_id: (.+)$", old_text)[1]
        history = []
        event_prefix = str(Path(old_path).parent).replace("\\", "/") + "/events/"
        for path in [p for p in source_paths if p.startswith(event_prefix) and p.endswith(".md")]:
            text = original(UPSTREAM, path)
            if (ROOT / path).read_text(encoding="utf-8").replace("\r\n", "\n") != text:
                raise ValueError("imported source event differs from pinned upstream")
            replay = mapped(text)
            replay = re.sub(r"(?m)^event_id: (.+)$", lambda m: m[0] + "-reidentified-" + new_id, replay)
            replay_path = path.replace(f"/{old_id}-", f"/{new_id}-")
            put(replay_path, replay)
            history.append(dict(original=bind(path), replay=bind(replay_path)))
        retirement = event(str(Path(old_path).parent).replace("\\", "/"), old_id, "superseded",
                           f"The imported, unexecuted owner plan identity collides with retained local {old_id}. Preserve this specification and all planning events as immutable source history. Its exact ID-substituted continuation is {new_id}, governed by FDEC-088. No requirement or execution result is discarded.",
                           replacement_id=new_id, correction_id="FDEC-088")
        resolution = dict(schema="fdec-identity-resolution/v2", correction_id="FDEC-088", retired=bind(old_path),
                          retained=bind(retained_path), replacement=bind(new_path), retirement_event=bind(retirement),
                          source_revision=UPSTREAM, id_map=[dict(old_id=k, new_id=v) for k, v in MAPPING.items()], planning_history=history)
        manifest = f"Tasks/migrations/FDEC-088-{old_id}.json"
        put(manifest, json.dumps(resolution, indent=2) + "\n")
        inventory.append(dict(old_id=old_id, new_id=new_id, source=bind(old_path), retained=bind(retained_path), replacement=bind(new_path), migration=bind(manifest)))
        event(f"Tasks/epics/{parent}", parent, "membership-replaced", f"Replace the imported planning membership {old_id} with its exact continuation {new_id}; retain the established local identity and the original owner specification.", old_task_id=old_id, new_task_id=new_id)
    for old_id in ("FDEC-080", "FDEC-081", "FDEC-082", "FDEC-083"):
        event("Tasks/items/quality/FDEC-085-targeted-integration-gate", "FDEC-085", "dependency-replaced",
              f"Resolve the imported benchmark dependency {old_id} to {MAPPING[old_id]} under its exact FDEC-088 identity migration. The independent benchmark gate keeps the same source requirements.", old_task_id=old_id, new_task_id=MAPPING[old_id])
    # Resolve the only content conflict using the verified local capabilities and
    # the owner's explicit free/commercial integration and Mac training direction.
    readme = original(BASE, "README.md")
    readme = readme.replace("**Local-first email classification, built around a shared Rust engine.**", "**Free, open-source email classification with local inference, designed for commercial integrations including paid FDFiles.**")
    addition = """## Free software, commercial integration and training

The standalone project is intended to be available at no charge. Original code
uses Apache-2.0, which permits commercial and proprietary integration, including
paid FDFiles, subject to its terms. FDEmailClassifier stays independent of FDFiles
internals and does not require a paid external inference API. The project's free
distribution policy adds no noncommercial or no-resale restriction.

Weights and LoRA adapters need separate base-model and dataset rights audits,
including commercial inference and public redistribution. Until approved, they
remain private or are omitted from releases. Missing optional data rights do not
stop independent software and benchmark development. See the
[commercial-use policy](docs/legal/COMMERCIAL_USE_POLICY.md) and
[product descriptions](docs/PRODUCT_DESCRIPTION.md).

Training is planned for Qwen3-0.6B with LoRA/QLoRA. The owner's MacBook Air M4
with 32 GB memory is the preferred temporary MLX host when a dependency-ready
training step requires it. The [Mac handoff](docs/training/MACBOOK_M4_HANDOFF.md)
requires operator confirmation and verified private artifact transfer before
returning to the original development workstation. No training run is claimed.
Independent benchmark tooling and measured public reports are planned; source
licenses, cohort independence and per-language evidence remain mandatory.

## Branding

The selected logo is a red rounded-square E; see [branding assets](assets/branding/).
The planned website follows the visual language of files.fedrv.de with neutral
backgrounds and red accents.

"""
    readme = readme.replace("## License and artifact rights\n", addition + "## License and artifact rights\n")
    (ROOT / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    # These are mutable product docs, not immutable accepted TASK/EPIC specs.
    for path in ("docs/legal/COMMERCIAL_USE_POLICY.md", "docs/PRODUCT_DESCRIPTION.md", "docs/benchmark/ROADMAP.md"):
        file = ROOT / path
        file.write_text(mapped(file.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    put(f"{TASK}/evidence/import-inventory-v1.json", json.dumps(dict(schema="fdec-owner-plan-import/v1", upstream=UPSTREAM, local_base=git("rev-parse", BASE).decode().strip(), identities=inventory), indent=2) + "\n")


if __name__ == "__main__":
    main()
