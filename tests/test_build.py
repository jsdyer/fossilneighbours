import gzip
import json
from xml.etree import ElementTree as ET
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build import ROOT, build, metadata


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "web", self.root / "web")
        shutil.copyfile(ROOT / "tool.json", self.root / "tool.json")
        shutil.copyfile(ROOT / "README.md", self.root / "README.md")

    def edit(self, **changes):
        tool = json.loads((self.root / "tool.json").read_text())
        tool.update(changes)
        (self.root / "tool.json").write_text(json.dumps(tool))

    def test_build_is_scoped_to_web_and_escapes_metadata(self):
        (self.root / "private.txt").write_text("must not publish")
        self.edit(title='<img src=x onerror="bad()">')
        build(self.root)
        page = (self.root / "dist/index.html").read_text()
        self.assertIn('&lt;img', page)
        self.assertNotIn('<img', page)
        self.assertNotIn('{{', page)
        self.assertIn('href="./style.css"', page)
        self.assertFalse((self.root / "dist/private.txt").exists())
        self.assertTrue((self.root / "dist/.nojekyll").exists())

    def test_sitemap_and_profiles_track_the_edition_and_escape_new_records(self):
        data_dir = self.root / "web/data"
        with gzip.open(data_dir / "records.json.gz") as fp:
            data = json.load(fp)
        focal = data["presets"]["Joggins"][0]
        parent = next(c for c in data["collections"] if c["id"] == focal)
        added = dict(parent, id=999999, name="Test fossil <&>", formation="Other")
        added.pop("peers")
        data["collections"].append(added)
        parent["peers"]["age"].append(added["id"])
        (data_dir / "records.json.gz").write_bytes(gzip.compress(json.dumps(data).encode()))
        index = json.loads((data_dir / "index.json").read_text())
        index["collections"] += 1
        (data_dir / "index.json").write_text(json.dumps(index))
        build(self.root)
        out = self.root / "dist"
        sitemap = ET.parse(out / "sitemap.xml")
        paths = [row.text.removeprefix("https://coolcode.ca/fossilneighbours/") for row in sitemap.findall(".//{*}loc")]
        self.assertEqual(len(paths), len(data["collections"]) + len(data["presets"]) + 1)
        self.assertEqual(set(paths), {p.parent.relative_to(out).as_posix()+"/" for p in (out/"records").rglob("index.html")})
        for path in paths:
            content = (out / path / "index.html").read_text()
            self.assertIn(f'<link rel="canonical" href="https://coolcode.ca/fossilneighbours/{path}">',content)
            self.assertIn('<meta name="description"',content)
        profile = (out/"records/collections/999999/index.html").read_text()
        self.assertIn("Test fossil &lt;&amp;&gt;",profile)
        self.assertIn("No occurrence records were returned",profile)
        self.assertIn(f"collection={focal}&amp;peer=999999",profile)
        self.assertIn("Overlap ",profile)
        self.assertIn("PBDB collection record",profile)

    def test_url_matches_tool_id(self):
        self.edit(url="/different/")
        with self.assertRaises(ValueError): metadata(self.root)

    def test_requires_a_source_sentence_and_a_guide_note(self):
        (self.root / "README.md").write_text("# A tool")
        with self.assertRaisesRegex(ValueError, "README note"):
            metadata(self.root)
        self.edit(data_info={"mode": "local", "detail": ""})
        with self.assertRaisesRegex(ValueError, "homepage card"):
            metadata(self.root)

    def test_browser_access_is_explicit(self):
        self.edit(access="install")
        with self.assertRaisesRegex(ValueError, "immediately usable"):
            metadata(self.root)

    def test_failed_build_keeps_existing_output(self):
        build(self.root)
        existing = (self.root / "dist/index.html").read_bytes()
        self.edit(source="javascript:bad()")
        with self.assertRaises(ValueError): build(self.root)
        self.assertEqual((self.root / "dist/index.html").read_bytes(), existing)


if __name__ == "__main__": unittest.main()
