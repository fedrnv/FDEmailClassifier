import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
for area in ("training/finetune", "training/splits", "training/augmentation"):
    sys.path.insert(0, str(ROOT / area))

from disk_inventory import DiskInventory
from gemma_source import IDENTITY as GEMMA
from mlx_return_training import source_provenance
from sinabis_source import IDENTITY as SINABIS
from trainer_config import TrainerError


class MLXReturnProvenanceTests(unittest.TestCase):
    def test_exact_sources_keep_their_notices_and_audit(self):
        triage = {
            "dataset_id": "weijianzhg/email-triage-action-seed",
            "revision": "8c98baa8b10a1dddd676c860d9e1b86c89141c38",
            "artifact": "data/train.parquet",
            "sha256": "9ea7c656d016012f7e800a9612d399114ca081bfcbdce4101d1999cb6c293854",
        }
        records = [{"source": source} for source in (SINABIS, GEMMA, triage, SINABIS)]
        result = source_provenance({"records": records})
        compact = DiskInventory(ROOT, {}, tuple(records), ())
        self.assertEqual(source_provenance(compact), result)
        by_source = {row["identity"]["dataset_id"]: row for row in result}
        self.assertEqual(set(by_source), {source["dataset_id"] for source in (SINABIS, GEMMA, triage)})
        oil = by_source[SINABIS["dataset_id"]]
        self.assertEqual(oil["inventory_records"], 2)
        self.assertEqual(oil["attribution"]["creator"], "Sinabis GmbH")
        self.assertTrue(all(row["attribution"] and len(row["source_audit_sha256"]) == 64 for row in result))
        self.assertEqual({row["public_weight_rights"] for row in result}, {"separate-review-required"})

    def test_missing_bound_notice_rejects(self):
        with patch("training_boundary.assert_training_source", return_value={"descriptor": {"license": "MIT"}}):
            with self.assertRaisesRegex(TrainerError, "mlx_return_source_provenance_incomplete"):
                source_provenance({"records": [{"source": GEMMA}]})


if __name__ == "__main__":
    unittest.main()
