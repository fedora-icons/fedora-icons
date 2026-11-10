import copy
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from import_figma import extract_icon, import_sheet
from validate import validate_library, validate_svg


SHEET = """<svg xmlns="http://www.w3.org/2000/svg" fill="none">
<g id="Export"><g id="export--regular--sample">
<path d="M34 34H54V54H34Z" stroke="#212121" stroke-width="1.25"
clip-path="url(#clip1)"/></g><g id="export--filled--sample">
<path d="M66 34H86V54H66Z" fill="#212121"/></g></g>
<defs><clipPath id="clip1"><rect x="32" y="32" width="24" height="24"
fill="white"/></clipPath><clipPath id="unused"><rect width="1" height="1"/>
</clipPath></defs></svg>"""


def payload():
    return {
        "svg": SHEET,
        "records": [{
            "name": "sample", "category": "Shapes", "tags": ["square"],
            "aliases": [], "componentSet": "1:3",
            "source": {"regular": "1:1", "filled": "1:2"},
            "keyline": {"width": 20, "height": 20},
            "positions": {
                "regular": {"x": 32, "y": 32, "id": "export--regular--sample"},
                "filled": {"x": 64, "y": 32, "id": "export--filled--sample"},
            },
        }],
    }


class SvgPackageTests(unittest.TestCase):
    def test_extract_restores_coordinates_and_rewrites_referenced_definitions(self):
        row = payload()["records"][0]
        svg = extract_icon(ET.fromstring(SHEET), row["positions"]["regular"], "sample-regular")
        self.assertIn('translate(-32 -32)', svg)
        self.assertIn('stroke="currentColor"', svg)
        self.assertIn('fill="white"', svg)
        self.assertNotIn("unused", svg)
        self.assertNotIn("clip1", svg)
        self.assertEqual(validate_svg(svg, "regular"), [])

    def test_missing_group_and_definition_fail(self):
        row = payload()["records"][0]
        with self.assertRaises(ValueError):
            extract_icon(ET.fromstring(SHEET), {"id": "missing"}, "sample")
        with self.assertRaises(ValueError):
            extract_icon(ET.fromstring(SHEET.replace('id="clip1"', 'id="other"')),
                         row["positions"]["regular"], "sample")

    def test_import_rejects_duplicate_and_excluded_names(self):
        for name in ("sample", "google-chrome"):
            data = payload()
            data["records"].append(copy.deepcopy(data["records"][0]))
            data["records"][-1]["name"] = name
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    import_sheet(data, Path(directory))

    def test_round_trip_detects_tampering_and_unmanifested_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            import_sheet(payload(), root)
            self.assertEqual(validate_library(root), [])
            path = root / "icons/regular/sample.svg"
            path.write_text(path.read_text().replace("currentColor", "#212121"))
            (root / "icons/filled/orphan.svg").write_text("<svg/>")
            errors = validate_library(root)
            self.assertTrue(any("Digest mismatch" in error for error in errors))
            self.assertTrue(any("Non-themable" in error for error in errors))
            self.assertTrue(any("Unmanifested" in error for error in errors))

    def test_validator_rejects_active_external_and_nonfinite_svg(self):
        for content in (
            '<script/>',
            '<path fill="currentColor" d="MNaN 2"/>',
            '<use href="https://example.com/icon.svg"/>',
            '<path fill="currentColor" onclick="alert(1)" d="M2 2H22"/>',
            '<path fill="currentColor" clip-path="url(#missing)" d="M2 2H22"/>',
        ):
            svg = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">' + content + '</svg>'
            self.assertTrue(validate_svg(svg, "regular"))


if __name__ == "__main__":
    unittest.main()
