"""Independent invented-metadata probes; no corpus, model or output fixtures."""
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path('C:/GitHub/FDEmailClassifier-review-D002-R002')
for area in ('training/scripts', 'training/labels', 'training/splits', 'training/augmentation'):
    sys.path.insert(0, str(ROOT / area))
import augment
import ingest_dataset as ingestion
import sinabis_source as sinabis
import split_data as splits
import training_boundary as boundary

def refused(exception, operation):
    try:
        operation()
    except exception as error:
        return str(error)
    raise AssertionError('Expected refusal')

checks = {}
for pack in sorted(boundary.FIXTURE_PACKS):
    for purpose in boundary.PURPOSES:
        checks[pack + '/' + purpose] = refused(augment.AugmentationError, lambda: augment.load_pack(pack, purpose))
profile = boundary.assert_training_source(sinabis.IDENTITY, purpose='commercial_training')
assert profile['requires_origin_projection'] and profile['requires_independent_labels'] and profile['requires_split_and_consent'] and not profile['release_approved']
checks['sinabis_legacy_guard'] = refused(ingestion.IngestionError, lambda: ingestion.inclusion(sinabis.IDENTITY['dataset_id'], sinabis.IDENTITY['revision'], sinabis.IDENTITY['artifact'], 'commercial_training', 'specialized-email-classifier'))
checks['single_source_split'] = refused(splits.SplitError, lambda: splits.assign([[{'record_id': 'a' * 64}]], 1, dict(train=80, validation=10, test=10)))

# Compare complete source/thread/content/family/lexical transitive closure with
# a separate deliberately quadratic graph on deterministic generated metadata.
rng = random.Random(14002)
comparisons = 0
for run in range(35):
    records = []
    for index in range(35):
        values = set(rng.sample(range(70), rng.randint(5, 25)))
        if index and index % 4 == 0:
            values = set(records[-1]['shingles']) | {rng.randrange(70)}
        records.append(dict(record_id=f'{index:064x}', source=dict(dataset_id=f'token/{rng.randrange(24)}'), content_sha256=f'{rng.randrange(30):064x}', thread_id=None if index % 3 else f'{rng.randrange(8):064x}', family_ids=[] if index % 5 else [f'{rng.randrange(6):064x}'], shingles=sorted(values)))
    edges = [set() for _ in records]
    for right, row in enumerate(records):
        for left in range(right):
            prior = records[left]
            a, b = set(row['shingles']), set(prior['shingles'])
            linked = row['source']['dataset_id'] == prior['source']['dataset_id'] or row['content_sha256'] == prior['content_sha256']
            linked |= row['thread_id'] is not None and row['thread_id'] == prior['thread_id']
            linked |= bool(set(row['family_ids']) & set(prior['family_ids']))
            linked |= len(a & b) * 100 >= len(a | b) * 80
            comparisons += 1
            if linked:
                edges[left].add(right)
                edges[right].add(left)
    unseen = set(range(len(records)))
    expected = set()
    while unseen:
        pending = [unseen.pop()]
        component = set(pending)
        while pending:
            for adjacent in edges[pending.pop()] - component:
                component.add(adjacent)
                unseen.discard(adjacent)
                pending.append(adjacent)
        expected.add(frozenset(records[index]['record_id'] for index in component))
    actual = {frozenset(row['record_id'] for row in group) for group in splits.components(records)}
    assert actual == expected, run
checks['grouping_exhaustive_comparison'] = dict(seed=14002, inventories=35, records_per_inventory=35, pair_comparisons=comparisons, agrees=True)
amendment = json.loads((ROOT / 'Tasks/epics/FDEC-EPIC-D002/evidence/effective-outcome-v1.json').read_text(encoding='utf-8-sig'))
assert not amendment['actual_training_data_admitted'] and amendment['full_project_objective_preserved']
assert amendment['authority_kind'] == 'recorded_application_of_existing_owner_instructions'
report = json.loads((ROOT / 'Tasks/items/ai/FDEC-011-multilingual-synthetic-augmentation/evidence/sinabis-final-preparation-report-v12.json').read_text(encoding='utf-8-sig'))
assert not report['training_ready'] and report['summary']['supervised_records'] == 0 and report['summary']['independent_source_cohorts'] == 1
checks['explicit_completion_boundary'] = dict(actual_training_data_admitted=False, sinabis_training_ready=False, supervised_records=0, independent_source_cohorts=1, authority_kind=amendment['authority_kind'])
print(json.dumps(dict(result='PASS', checks=checks), indent=2))
