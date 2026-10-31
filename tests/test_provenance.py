import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from provenance import sha256, validate_ranking_metrics, validate_splits, write_json  # noqa: E402


class EvidenceChecks(unittest.TestCase):
    def test_detects_cross_split_leakage(self):
        with self.assertRaises(ValueError):
            validate_splits({"train": [(1, 2)], "test": [(1, 2)]})

    def test_detects_duplicate_interactions(self):
        with self.assertRaises(ValueError):
            validate_splits({"train": [(1, 2), (1, 2)]})

    def test_valid_split(self):
        validate_splits({"train": [(1, 2)], "test": [(1, 3)]})

    def test_metrics_reject_invalid_results(self):
        for value in (float("nan"), float("inf"), -0.1, 1.01):
            with self.assertRaises(ValueError):
                validate_ranking_metrics({"ndcg@10": value})
        with self.assertRaises(ValueError):
            validate_ranking_metrics({})

    def test_hash_changes_when_data_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.json"
            write_json(path, {"value": 1})
            before = sha256(path)
            write_json(path, {"value": 2})
            self.assertNotEqual(before, sha256(path))


if __name__ == "__main__":
    unittest.main()
