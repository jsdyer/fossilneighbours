import gzip
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from refresh import neighbours


class SourceTests(unittest.TestCase):
    def test_overlap_is_positive_and_same_environment_must_be_known(self):
        focus = dict(id=1, formation="Focal", old=10, young=9, env="")
        peers = [dict(focus, id=2, old=11, young=10, formation="other"),
                 dict(focus, id=3, old=10.5, young=9.5, formation="other")]
        self.assertEqual(neighbours(focus, peers), {"age": [3], "environment": []})

    def test_snapshot_links_and_counts(self):
        with gzip.open(ROOT / "web/data/records.json.gz") as fp:
            data = json.load(fp)
        summary = json.loads((ROOT / "web/data/index.json").read_text())
        self.assertEqual(summary["count"], len({r["id"] for r in data["occurrences"]}))
        collections = {c["id"]: c for c in data["collections"]}
        self.assertEqual(len(collections), summary["collections"])
        for c in collections.values():
            self.assertGreaterEqual(c["old"], c["young"])
            self.assertIn(str(c["ref"]), data["references"])
            for peers in c.get("peers", {}).values():
                self.assertTrue(set(peers) <= collections.keys())
        for record in data["occurrences"]:
            self.assertIn(record["col"], collections)
            self.assertIn(str(record["ref"]), data["references"])
