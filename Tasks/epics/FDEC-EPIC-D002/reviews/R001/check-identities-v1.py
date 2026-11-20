"""Read-only independent identity/binding verification; emits no corpus data."""
import hashlib
import json
from pathlib import Path
import subprocess

MAIN = Path('C:/GitHub/FDEmailClassifier')
CANDIDATE = Path('C:/GitHub/FDEmailClassifier-review-D002-R001')
SHA = '0bcd4c4f377af86ee8b83d1d0bf770f0eb448ad8'
LEDGER = '7868e944c7a9c5e721b0a435acd0ae572055789d'
TREE = '558697de3b18fd1bea8358a144bae90a90231c76'
POLICY = 'ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403'
GATE = '0702e6c97126247f79ab5184b1c4b1e74d453877346fac3b776800ea882b9f10'

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])

def sha(data):
    return hashlib.sha256(data).hexdigest()

def canonical(data):
    return sha(data.replace(b'\r\n', b'\n'))

def document(path):
    return json.loads(git(MAIN, 'show', LEDGER + ':' + path).decode('utf-8-sig'))

assert git(CANDIDATE, 'rev-parse', 'HEAD').decode().strip() == SHA
assert git(CANDIDATE, 'rev-parse', 'HEAD^{tree}').decode().strip() == TREE
assert not git(CANDIDATE, 'status', '--porcelain').strip()
assert canonical(git(CANDIDATE, 'show', SHA + ':Tasks/policy/upstream-5.6.md')) == POLICY
base = 'Tasks/items/quality/FDEC-013-targeted-integration-gate/'
assert canonical(git(MAIN, 'show', LEDGER + ':' + base + 'evidence/result-v1.json')) == GATE
gate = document(base + 'evidence/result-v1.json')
assert (gate['candidate_sha'], gate['candidate_tree'], gate['policy_sha256']) == (SHA, TREE, POLICY)
assert gate['result'] == 'PASS' and gate['exit_code'] == 0
assert len(gate['stages']) == 8 and all(s['result'] == 'PASS' for s in gate['stages'])
changes = git(MAIN, 'diff', '--name-status', SHA, LEDGER).decode().splitlines()
assert len(changes) == 9
assert all(line.startswith('A\t') and (line[2:].startswith(base + 'evidence/') or line[2:].startswith(base + 'events/') or line[2:] == 'Tasks/version-requests/FDEC-013.json') for line in changes)
closure = document(base + 'evidence/closure-readiness-v3.json')
assert closure['source_sha'] == SHA and closure['policy_sha256'] == POLICY
assert closure['source_state_sha256'] == gate['source_state_sha256']
catalog = document('Tasks/policy/checkout-identities-076.json')['bindings']
checked = 0

def walk(value):
    global checked
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256'}:
            data = git(MAIN, 'show', LEDGER + ':' + value['path'])
            actual = canonical(data)
            valid = value['sha256'] in (sha(data), actual)
            valid |= any(b['path'] == value['path'] and b['legacy_sha256'] == value['sha256'] and b['canonical_sha256'] == actual for b in catalog)
            assert valid, value['path']
            checked += 1
        else:
            for child in value.values():
                walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)

walk(closure)
event = git(MAIN, 'show', LEDGER + ':' + base + 'events/20261120T191552998Z-codex-status-changed-41d76a56.md').decode()
assert 'InProgress -> Done' in event and 'closure_proof: evidence/closure-readiness-v3.json' in event
assert 'closure_proof_sha256: ' + canonical(git(MAIN, 'show', LEDGER + ':' + base + 'evidence/closure-readiness-v3.json')) in event
transcript = git(MAIN, 'show', LEDGER + ':' + base + 'evidence/test-output-v1.txt').decode('utf-8-sig')
assert transcript.count('STAGE: ') == 8 and 'GATE_RESULT_BEGIN' in transcript and 'GATE_RESULT_END' in transcript
assert canonical(git(MAIN, 'show', LEDGER + ':' + base + 'evidence/test-output-v1.txt')) == gate['raw_monitor_log_sha256']
print(json.dumps(dict(result='PASS', candidate_sha=SHA, candidate_tree=TREE, ledger_sha=LEDGER, policy_sha256=POLICY, gate_result_sha256=GATE, closure_bindings_verified=checked, ledger_additions=len(changes), gate_stages=8, candidate_clean=True), indent=2))
