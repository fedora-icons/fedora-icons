import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_presets import build_presets
from compose_svg import compose_svg
from import_figma import SVG, import_sheet, references
from import_modifiers import GLYPH_PAINT
from validate import validate_library, validate_svg

NS = {"s": SVG}


def fixture(root):
    manifest = json.loads((ROOT / "manifest.json").read_text())
    manifest["icons"] = [
        row for row in manifest["icons"] if row["name"] in ("user", "user-add")
    ]
    manifest["iconCount"] = 2
    for row in manifest["icons"]:
        row.pop("composition", None)
        for path in row["files"].values():
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)
    (root / "manifest.json").write_text(json.dumps(manifest))
    modifiers = json.loads((ROOT / "metadata/modifiers.json").read_text())
    modifiers["modifiers"] = [
        row for row in modifiers["modifiers"] if row["name"] == "add"
    ]
    (root / "metadata").mkdir()
    (root / "metadata/modifiers.json").write_text(json.dumps(modifiers))
    (root / "modifiers").mkdir()
    shutil.copyfile(ROOT / "modifiers/add.svg", root / "modifiers/add.svg")
    icon = next(row for row in manifest["icons"] if row["name"] == "user-add")
    return {
        "schemaVersion": 1,
        "presets": [{
            "name": "user-add", "base": "user", "modifier": "add",
            "position": "top-left", "fit": {"scale": 5 / 6, "x": 5.75, "y": 2.5},
            "componentSet": icon["componentSet"], "source": icon["source"],
        }],
    }


class PresetTests(unittest.TestCase):
    def test_cutout_is_transparent_not_a_theme_colored_stencil(self):
        svg = compose_svg("user", "add", cutout=True, modifier_color="currentColor")
        root = ET.fromstring(svg)
        self.assertNotIn(GLYPH_PAINT, svg)
        mask = root.find(".//s:mask", NS)
        self.assertIsNotNone(mask)
        self.assertEqual(mask.find("s:rect", NS).get("fill"), "white")
        self.assertTrue(any(
            node.get(attr) == "black"
            for node in mask.iter() for attr in ("fill", "stroke")
        ))
        self.assertEqual(validate_svg(svg, "regular"), [])
        ids = {node.get("id") for node in root.iter() if node.get("id")}
        self.assertFalse(references(root) - ids)

    def test_optical_fit_preserves_stroke_weight_and_rejects_bad_transforms(self):
        options = {"scale": 5 / 6, "x": 5.75, "y": 2.5}
        root = ET.fromstring(compose_svg(
            "user", "add", base_fit=options, cutout=True, modifier_color="currentColor",
        ))
        base = root.find("s:g/s:svg", NS)
        self.assertEqual(float(base.get("width")), 20)
        self.assertEqual(float(base.get("x")), 5.75)
        stroked = [node for node in base.iter() if node.get("stroke") == "currentColor"]
        self.assertTrue(stroked)
        self.assertTrue(all(
            node.get("vector-effect") is None
            and float(node.get("stroke-width")) * options["scale"] == 1.25
            for node in stroked
        ))
        self.assertEqual(validate_svg(ET.tostring(root, encoding="unicode"), "regular"), [])
        for fit in ({}, {**options, "scale": 0}, {**options, "x": float("nan")}):
            with self.subTest(fit=fit), self.assertRaises(ValueError):
                compose_svg("user", "add", base_fit=fit)

    def test_rebuild_keeps_names_and_ids_and_propagates_shared_glyph_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = fixture(root)
            build_presets(root, data)
            self.assertEqual(validate_library(root), [])
            composed = ET.fromstring(compose_svg("user", "add", root=root))
            self.assertEqual(float(composed.find("s:g/s:svg", NS).get("width")), 20)
            first = (root / "icons/regular/user-add.svg").read_bytes()
            build_presets(root)
            self.assertEqual(first, (root / "icons/regular/user-add.svg").read_bytes())
            metadata = json.loads((root / "metadata/modifiers.json").read_text())
            asset = root / "modifiers/add.svg"
            tree = ET.fromstring(asset.read_text())
            tree.find(".//s:path", NS).set("d", "M0 0H10V10H0Z")
            changed = ET.tostring(tree, encoding="utf-8")
            asset.write_bytes(changed)
            metadata["modifiers"][0]["sha256"] = hashlib.sha256(changed).hexdigest()
            (root / "metadata/modifiers.json").write_text(json.dumps(metadata))
            build_presets(root)
            self.assertNotEqual(first, (root / "icons/regular/user-add.svg").read_bytes())
            self.assertEqual(validate_library(root), [])

    def test_invalid_or_recursive_presets_do_not_partially_rewrite_the_core(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = fixture(root)
            before = (root / "icons/regular/user-add.svg").read_bytes()
            for mutation in ("recursive", "source", "duplicate"):
                bad = copy.deepcopy(data)
                if mutation == "recursive":
                    bad["presets"][0]["base"] = "user-add"
                elif mutation == "source":
                    bad["presets"][0]["source"]["regular"] = "unexpected"
                else:
                    bad["presets"].append(copy.deepcopy(bad["presets"][0]))
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    build_presets(root, bad)
                self.assertEqual(before, (root / "icons/regular/user-add.svg").read_bytes())
                self.assertFalse((root / "metadata/presets.json").exists())

    def test_core_reimport_restores_composition_instead_of_losing_the_stencil(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            build_presets(root, fixture(root))
            manifest = json.loads((root / "manifest.json").read_text())
            sheet = ET.Element(f"{{{SVG}}}svg")
            records = []
            for icon in manifest["icons"]:
                row = {key: icon[key] for key in
                       ("name", "category", "tags", "aliases", "source", "componentSet")}
                row["positions"] = {}
                for style in manifest["styles"]:
                    identifier = f"{icon['name']}-{style}"
                    group = ET.SubElement(sheet, f"{{{SVG}}}g", id=identifier)
                    ET.SubElement(group, f"{{{SVG}}}path", {
                        "d": "M2 2H22V22H2Z",
                        "fill": "#123456" if style in ("duocolor", "duotone") else "#212121",
                    })
                    row["positions"][style] = {"id": identifier, "x": 0, "y": 0}
                records.append(row)
            imported = import_sheet({
                "svg": ET.tostring(sheet, encoding="unicode"), "records": records,
                "styles": manifest["styles"],
                "paintRoles": {"primary": "#123456", "secondary": "#654321"},
            }, root)
            self.assertEqual(validate_library(root), [])
            preset = next(row for row in imported["icons"] if row["name"] == "user-add")
            self.assertEqual(preset["composition"]["modifier"], "add")
            self.assertIn("<mask", (root / preset["files"]["regular"]).read_text())


if __name__ == "__main__":
    unittest.main()
