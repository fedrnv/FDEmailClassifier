"""Independent read-only frozen identities, ledger and actual transcript checks."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

MAIN = Path('C:/GitHub/FDEmailClassifier')
SOURCE = Path('C:/GitHub/FDEmailClassifier-review-D002-R002')
SHA = '94f9669920b1ff105f6d29f1e5e98064f10ca583'
TREE = '6b7af50ea1fdbb1a6ad12cdad5dd445cf491560c'
LEDGER = 'b1a99b5613b60146ead9e0fac122fd936ab2d48f'
POLICY = 'ddb4f644496956b9fd2ba45752a62e3fd6800412ef477aeb882f4214c46a8403'
GATE = 'b296cd4acf6267a82f829d1e37c09992640435485ccdd993e12112ee3bb0988b'
BASE = 'Tasks/items/quality/FDEC-013-targeted-integration-gate/'

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])

def data(path, revision=LEDGER):
    return git(MAIN, 'show', revision + ':' + path)

def canonical(value):
    return hashlib.sha256(value.replace(b'\r\n', b'\n')).hexdigest()

def doc(path, revision=LEDGER):
    return json.loads(data(path, revision).decode('utf-8-sig'))

assert git(SOURCE, 'rev-parse', 'HEAD').decode().strip() == SHA
assert git(SOURCE, 'rev-parse', 'HEAD^{tree}').decode().strip() == TREE
assert not git(SOURCE, 'status', '--porcelain').strip()
assert canonical(data('Tasks/policy/upstream-5.6.md', SHA)) == POLICY
assert canonical(data(BASE + 'evidence/result-v2.json')) == GATE
gate = doc(BASE + 'evidence/result-v2.json')
assert (gate['candidate_sha'], gate['candidate_tree'], gate['policy_sha256']) == (SHA, TREE, POLICY)
assert gate['result'] == 'PASS' and gate['exit_code'] == 0
assert len(gate['stages']) == 9 and all(stage['result'] == 'PASS' for stage in gate['stages'])
assert gate['component_gate_result']['stages'] == gate['stages'][1:]
for key in ('candidate_sha', 'candidate_tree', 'policy_sha256', 'source_state_sha256'):
    assert gate[key] == gate['component_gate_result'][key]
for entry in gate['runner_bindings']:
    assert canonical(data(entry['path'], SHA)) == entry['sha256']
changes = git(MAIN, 'diff', '--name-status', SHA, LEDGER).decode().splitlines()
assert len(changes) == 12
assert all(line.startswith('A\t') and any(line[2:].startswith(BASE + area) for area in ('evidence/', 'events/')) for line in changes)
closure_path = BASE + 'evidence/closure-readiness-v6.json'
closure = doc(closure_path)
assert closure['source_sha'] == SHA and closure['policy_sha256'] == POLICY
assert closure['source_state_sha256'] == gate['source_state_sha256']
catalog = doc('Tasks/policy/checkout-identities-076.json')['bindings']
count = 0

def walk(value):
    global count
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256'}:
            raw = data(value['path'])
            actual = canonical(raw)
            valid = value['sha256'] in (actual, hashlib.sha256(raw).hexdigest())
            valid |= any(b['path'] == value['path'] and b['legacy_sha256'] == value['sha256'] and b['canonical_sha256'] == actual for b in catalog)
            assert valid, value['path']
            count += 1
        else:
            for child in value.values():
                walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)

walk(closure)
event = data(BASE + 'events/20261120T204941952Z-codex-status-changed-79d91231.md').decode()
assert 'InProgress -> Done' in event
assert 'closure_proof: evidence/closure-readiness-v6.json' in event
assert 'closure_proof_sha256: ' + canonical(data(closure_path)) in event
transcript = data(BASE + 'evidence/test-output-v2.txt').decode('utf-8-sig')
assert transcript.count('STAGE: ') == 9
outer = re.findall(r'(?ms)^GATE_RESULT_BEGIN\r?\n(.*?)^GATE_RESULT_END\r?$', transcript)
inner = re.findall(r'(?ms)^COMPONENT_GATE_RESULT_BEGIN\r?\n(.*?)^COMPONENT_GATE_RESULT_END\r?$', transcript)
assert len(outer) == len(inner) == 1
actual = json.loads(outer[0])
assert all(gate[key] == value for key, value in actual.items())
assert json.loads(inner[0]) == actual['component_gate_result']
counts = [int(n) for n in re.findall(r'Ran (\d+) tests? in ', transcript)]
assert counts == gate['python_test_groups'] and sum(counts) == 139
assert '4 passed; 0 failed' in transcript
walk(gate['preflight_evidence'])
assert doc(BASE + 'evidence/preflight-v2.json')['result'] == 'PASS'
print(json.dumps(dict(result='PASS', candidate_sha=SHA, candidate_tree=TREE, ledger_sha=LEDGER, policy_sha256=POLICY, gate_result_sha256=GATE, closure_and_preflight_bindings_verified=count, ledger_additions=len(changes), gate_stages=9, transcript_matches_outer_and_component=True, python_tests=sum(counts), rust_tests=4, candidate_clean=True), indent=2))
