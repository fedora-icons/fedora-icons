import copy
import hashlib
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compose_svg import color_value, compose_svg
from import_figma import SVG, references
from import_modifiers import GLYPH_PAINT, POSITIONS, import_modifiers

NS = {"s": SVG}


def snapshot():
    return {
        "schemaVersion": 1,
        "source": {"type": "figma", "fileKey": "fixture"},
        "records": [{
            "name": "add", "label": "Add", "source": "1:2",
            "width": 10, "height": 10, "defaultPosition": "top-left",
            "colors": {
                "light": {"primary": "#0F7B0F", "glyph": "#FFFFFF"},
                "dark": {"primary": "#6CCB5F", "glyph": "#141414"},
            },
            "positions": {
                corner: {
                    "x": 1.25, "y": 1.25,
                    "clearance": [{
                        "windingRule": "EVENODD",
                        "data": "M0 0H24V24H0Z M0 0H12V12H0Z",
                    }],
                } for corner in POSITIONS
            },
            "svg": (
                f'<svg xmlns="{SVG}" width="10" height="10" viewBox="0 0 10 10">'
                '<defs><clipPath id="c"><rect width="10" height="10"/>'
                '</clipPath></defs><g clip-path="url(#c)">'
                '<rect width="10" height="10" fill="#0F7B0F"/>'
                '<path d="M4 2H6V8H4Z" fill="white"/></g></svg>'
            ),
        }],
    }


class ModifierTests(unittest.TestCase):
    def test_import_preserves_clearance_and_normalizes_paints_and_references(self):
        data = snapshot()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = import_modifiers({"result": data}, root)
            record = manifest["modifiers"][0]
            asset = (root / record["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(asset).hexdigest(), record["sha256"])
            self.assertEqual(record["positions"], data["records"][0]["positions"])
            self.assertIn(b'fill="currentColor"', asset)
            self.assertIn(GLYPH_PAINT.encode(), asset)
            self.assertNotIn(b'url(#c)', asset)
            self.assertFalse((root / "manifest.json").exists())

    def test_import_rejects_bad_names_missing_corners_and_unmapped_colors(self):
        for mutation in ("duplicate", "name", "corner", "color"):
            data = snapshot()
            if mutation == "duplicate":
                data["records"].append(copy.deepcopy(data["records"][0]))
            elif mutation == "name":
                data["records"][0]["name"] = "../escape"
            elif mutation == "corner":
                del data["records"][0]["positions"]["top-right"]
            else:
                data["records"][0]["svg"] = data["records"][0]["svg"].replace(
                    "#0F7B0F", "#FF0000",
                )
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.assertRaises(ValueError):
                    import_modifiers(data, root)
                self.assertEqual(list(root.iterdir()), [])

    def test_import_keeps_color_roles_when_figma_theme_values_are_identical(self):
        data = snapshot()
        row = data["records"][0]
        row["paintRoles"] = {"primary": "#123456", "glyph": "#FEDCBA"}
        row["colors"]["light"] = {"primary": "#FFFFFF", "glyph": "#FFFFFF"}
        row["svg"] = row["svg"].replace("#0F7B0F", "#123456").replace("white", "#FEDCBA")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = import_modifiers(data, root)
            svg = (root / manifest["modifiers"][0]["file"]).read_text()
            self.assertIn('fill="currentColor"', svg)
            self.assertIn(GLYPH_PAINT, svg)

    def test_composition_matches_all_exported_corners_without_an_opaque_halo(self):
        manifest = json.loads((ROOT / "metadata/modifiers.json").read_text())
        for glyph in manifest["modifiers"]:
            for position in glyph.get("allowedPositions", POSITIONS):
                for style in ("regular", "filled"):
                    with self.subTest(glyph=glyph["name"], position=position, style=style):
                        result = ET.fromstring(compose_svg(
                            "file", glyph["name"], style=style, position=position,
                        ))
                        clip = result.find("s:defs/s:clipPath", NS)
                        self.assertEqual(
                            [path.get("d") for path in clip],
                            [path["data"] for path in glyph["positions"][position]["clearance"]],
                        )
                        base = result.find("s:g", NS)
                        self.assertEqual(base.get("clip-path"), f"url(#{clip.get('id')})")
                        self.assertEqual(list(base)[0].tag, f"{{{SVG}}}svg")
                        badge = list(result)[-1]
                        self.assertEqual(float(badge.get("x")), glyph["positions"][position]["x"])
                        self.assertEqual(float(badge.get("y")), glyph["positions"][position]["y"])
                        self.assertEqual([node.tag.rsplit("}", 1)[-1] for node in result],
                                         ["defs", "g", "svg"])
                        ids = {node.get("id") for node in result.iter() if node.get("id")}
                        self.assertFalse(references(result) - ids)

    def test_import_enforces_explicit_position_restrictions(self):
        data = snapshot()
        row = data["records"][0]
        row["allowedPositions"] = ["bottom-left"]
        row["defaultPosition"] = "bottom-left"
        row["positions"] = {"bottom-left": row["positions"]["bottom-left"]}
        with tempfile.TemporaryDirectory() as directory:
            imported = import_modifiers(data, Path(directory))
            self.assertEqual(imported["modifiers"][0]["allowedPositions"], ["bottom-left"])
        for mutation in ("extra-corner", "default", "unknown", "empty", "duplicate"):
            bad = copy.deepcopy(data)
            row = bad["records"][0]
            if mutation == "extra-corner":
                row["positions"]["top-right"] = row["positions"]["bottom-left"]
            elif mutation == "default":
                row["defaultPosition"] = "top-right"
            elif mutation == "unknown":
                row["allowedPositions"] = ["center"]
            elif mutation == "empty":
                row["allowedPositions"] = []
            else:
                row["allowedPositions"] *= 2
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    import_modifiers(bad, Path(directory))

    def test_file_type_modifiers_cannot_move_from_bottom_left(self):
        metadata = json.loads((ROOT / "metadata/modifiers.json").read_text())
        for glyph in metadata["modifiers"]:
            if glyph["group"] != "file-types":
                continue
            with self.subTest(modifier=glyph["name"]):
                self.assertEqual(glyph["allowedPositions"], ["bottom-left"])
                self.assertEqual(
                    compose_svg("file", glyph["name"], id_prefix="fixed"),
                    compose_svg(
                        "file", glyph["name"], position="bottom-left", id_prefix="fixed",
                    ),
                )
                for position in ("top-left", "top-right", "bottom-right"):
                    with self.assertRaisesRegex(ValueError, "only supports bottom-left"):
                        compose_svg("file", glyph["name"], position=position)

    def test_auto_uses_only_approved_defaults_and_manual_position_overrides(self):
        for glyph, position in (("add", "top-left"), ("delete", "bottom-right"),
                                ("pdf", "bottom-left")):
            auto = compose_svg("user", glyph, id_prefix="test")
            explicit = compose_svg("user", glyph, position=position, id_prefix="test")
            self.assertEqual(auto, explicit)
        for glyph in ("warning", "check", "key", "lock", "user", "clip"):
            with self.assertRaisesRegex(ValueError, "explicit corner"):
                compose_svg("user", glyph)

    def test_sparkle_is_a_solid_modifier_independent_of_base_style(self):
        for style in ("regular", "filled", "duocolor", "duotone"):
            with self.subTest(style=style):
                root = ET.fromstring(compose_svg(
                    "mail", "sparkle", style=style, position="top-right",
                ))
                badge = list(root)[-1]
                paths = badge.findall(".//s:path", NS)
                self.assertTrue(paths)
                self.assertTrue(all(path.get("fill") == "currentColor" for path in paths))
                self.assertTrue(all(path.get("stroke") in (None, "none") for path in paths))
                self.assertNotEqual(badge.get("opacity"), "0.16")

    def test_theme_and_custom_colors_apply_to_glyph_without_changing_base_paths(self):
        light = ET.fromstring(compose_svg("user", "add", id_prefix="test"))
        dark = ET.fromstring(compose_svg("user", "add", theme="dark", id_prefix="test"))
        self.assertEqual(ET.tostring(light.find("s:g", NS)), ET.tostring(dark.find("s:g", NS)))
        self.assertNotEqual(list(light)[-1].get("color"), list(dark)[-1].get("color"))
        custom = ET.fromstring(compose_svg(
            "user", "add", color="#123456", modifier_color="#abcdef",
            glyph_color="#f0f",
        ))
        self.assertEqual(custom.get("color"), "#123456")
        self.assertEqual(list(custom)[-1].get("color"), "#abcdef")
        self.assertIn('stroke="#f0f"', ET.tostring(custom, encoding="unicode"))
        self.assertNotIn("--fedora-glyph-color", ET.tostring(custom, encoding="unicode"))

    def test_inline_compositions_have_disjoint_ids(self):
        first = ET.fromstring(compose_svg("file", "pdf"))
        second = ET.fromstring(compose_svg("file", "pdf"))
        ids = lambda root: {node.get("id") for node in root.iter() if node.get("id")}
        self.assertFalse(ids(first) & ids(second))
        for root in (first, second):
            self.assertFalse(references(root) - ids(root))

    def test_invalid_inputs_and_tampered_asset_fail(self):
        for value in ("#12345", "#1234567", "url(https://example.com)", "red;fill:none"):
            with self.subTest(color=value), self.assertRaises(ValueError):
                color_value(value)
        for options in ({"style": "unsupported"}, {"theme": "other"}, {"position": "center"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                compose_svg("user", "add", **options)
        with self.assertRaises(ValueError):
            compose_svg("../user", "add")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            import_modifiers(snapshot(), root)
            (root / "manifest.json").write_text(json.dumps({
                "styles": ["regular"], "icons": [{
                    "name": "sample", "files": {"regular": "sample.svg"},
                    "sha256": {"regular": "0" * 64},
                }],
            }))
            (root / "sample.svg").write_text("<svg/>")
            with self.assertRaisesRegex(ValueError, "Digest mismatch"):
                compose_svg("sample", "add", root=root)


if __name__ == "__main__":
    unittest.main()
