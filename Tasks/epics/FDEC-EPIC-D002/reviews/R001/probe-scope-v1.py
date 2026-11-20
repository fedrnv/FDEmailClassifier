"""Focused reviewer probes on frozen code, public metadata and invented tokens."""
import json
from pathlib import Path
import random
import sys

ROOT = Path('C:/GitHub/FDEmailClassifier-review-D002-R001')
for area in ('training/scripts', 'training/labels', 'training/splits', 'training/augmentation'):
    sys.path.insert(0, str(ROOT / area))
import augment
import ingest_dataset as ingestion
import map_annotations as labels
import sinabis_source as sinabis
import split_data as splits
import training_boundary as boundary

def rejected(exception, function):
    try:
        function()
    except exception as error:
        return str(error)
    raise AssertionError('Expected rejection')

checks = {}
for pack in sorted(boundary.FIXTURE_PACKS):
    for purpose in boundary.PURPOSES:
        checks[pack + '/' + purpose] = rejected(augment.AugmentationError, lambda: augment.load_pack(pack, purpose))
admission = boundary.assert_training_source(sinabis.IDENTITY, purpose='commercial_training')
assert admission['requires_origin_projection'] and admission['requires_independent_labels'] and admission['requires_split_and_consent'] and not admission['release_approved']
checks['sinabis_legacy_guard'] = rejected(ingestion.IngestionError, lambda: ingestion.inclusion(sinabis.IDENTITY['dataset_id'], sinabis.IDENTITY['revision'], sinabis.IDENTITY['artifact'], 'commercial_training', 'specialized-email-classifier'))
checks['single_source_split'] = rejected(splits.SplitError, lambda: splits.assign([[{'record_id': 'a' * 64}]], 1, dict(train=80, validation=10, test=10)))
source = dict(dataset_id='fdec/canonical-annotations', revision='1', artifact='annotations.jsonl', sha256='a' * 64)
mapped = labels.map_annotations(content_id='b' * 64, source=source, annotations=[dict(source_row=0, labels=dict(category='work', priority='high')), dict(source_row=1, labels=dict(category='finance', priority='high'))])
assert mapped['classification']['status'] == 'abstained' and not mapped['training_mask']['topics'] and mapped['training_mask']['priority'] and not mapped['training_mask']['action']
checks['annotation_conflict'] = 'abstained; topic mask false; independent assessed priority retained'
rng = random.Random(14001)
sets = []
for index in range(80):
    values = set(rng.sample(range(120), rng.randint(10, 50)))
    sets.extend((values, values | set(rng.sample(range(120), 2))))
expected = {(left, right) for right in range(len(sets)) for left in range(right) if len(sets[left] & sets[right]) * 100 >= len(sets[left] | sets[right]) * 80}
actual = set(sinabis.near_pairs(sets))
assert actual == expected
checks['sinabis_near_pair_probe'] = dict(seed=14001, sets=len(sets), pairs_checked=len(sets) * (len(sets) - 1) // 2, matches=len(actual), agrees_with_exhaustive=True)
epic = (ROOT / 'Tasks/epics/FDEC-EPIC-D002/EPIC.md').read_text(encoding='utf-8-sig')
assert 'Produce provenance-tracked, lawful, reproducible training/evaluation data' in epic
events = sorted((ROOT / 'Tasks/epics/FDEC-EPIC-D002/events').glob('*.md'))
assert len(events) == 1 and 'Planned -> Active' in events[0].read_text(encoding='utf-8-sig')
report = json.loads((ROOT / 'Tasks/items/ai/FDEC-011-multilingual-synthetic-augmentation/evidence/sinabis-final-preparation-report-v12.json').read_text(encoding='utf-8-sig'))
assert report['training_ready'] is False and report['summary']['supervised_records'] == 0 and report['summary']['independent_source_cohorts'] == 1
checks['epic_contract_gap'] = dict(epic_events=len(events), epic_outcome_refinement_recorded=False, sinabis_training_ready=report['training_ready'], supervised_records=report['summary']['supervised_records'], independent_source_cohorts=report['summary']['independent_source_cohorts'], remaining_gates=report['remaining_gates'])
print(json.dumps(dict(result='PASS: probes reproduced; Epic contract gap remains', checks=checks), indent=2))
