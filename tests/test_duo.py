import copy
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from compose_svg import compose_svg
from import_duo import import_duo
from import_figma import SVG, extract_icon, import_sheet
from test_svg_package import payload
from validate import validate_library, validate_svg


def duo_payload():
    data = payload()
    row = data["records"][0]
    row["source"].update(duocolor="1:4", duotone="1:5")
    row["positions"] = {}
    sheet = ET.Element(f"{{{SVG}}}svg")
    for style in ("duocolor", "duotone"):
        row["positions"][style] = {"id": style, "x": 0, "y": 0}
        group = ET.SubElement(sheet, f"{{{SVG}}}g", id=style)
        ET.SubElement(group, f"{{{SVG}}}path", {
            "d": "M2 2H22V22H2Z", "stroke": "#123456", "stroke-width": "1.25",
        })
        if style == "duotone":
            group = ET.SubElement(group, f"{{{SVG}}}g", opacity="0.16")
        ET.SubElement(group, f"{{{SVG}}}path", {
            "d": "M8 8H16V16H8Z", "fill": "#654321",
        })
    data["svg"] = ET.tostring(sheet, encoding="unicode")
    data["paintRoles"] = {"primary": "#123456", "secondary": "#654321"}
    data["palette"] = [
        {"name": name, "light": {"primary": "#245B9E", "secondary": "#5B87B7"},
         "dark": {"primary": "#93C5FD", "secondary": "#60A5FA"}}
        for name in ("Slate", "Blue", "Sky", "Cyan", "Teal", "Green", "Lime",
                     "Yellow", "Amber", "Orange", "Red", "Rose")
    ]
    data["exportedOn"] = "2026-11-10"
    return data


class DuoTests(unittest.TestCase):
    def test_role_import_preserves_tint_and_definition_paints(self):
        data = duo_payload()
        svg = data["svg"].replace("</svg>", '<defs><clipPath id="c">'
                                 '<rect fill="white" width="24" height="24"/>'
                                 '</clipPath></defs></svg>')
        svg = svg.replace('id="duotone"', 'id="duotone" clip-path="url(#c)"')
        result = extract_icon(
            ET.fromstring(svg), data["records"][0]["positions"]["duotone"],
            "fixture", style="duotone", paint_roles=data["paintRoles"],
        )
        self.assertIn('fill="white"', result)
        self.assertIn("var(--fos-secondary, #5B87B7)", result)
        self.assertIn('opacity="0.16"', result)
        self.assertEqual(validate_svg(result, "duotone"), [])
        for roles in (None, {"primary": "#123456", "secondary": "#123456"}):
            with self.assertRaises(ValueError):
                extract_icon(ET.fromstring(svg), {"id": "duotone", "x": 0, "y": 0},
                             "fixture", style="duotone", paint_roles=roles)

    def test_expansion_preserves_both_original_assets_and_all_source_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = import_sheet(payload(), root)
            assets = {s: (root / f"icons/{s}/sample.svg").read_bytes()
                      for s in ("regular", "filled")}
            import_duo(duo_payload(), root)
            self.assertEqual(validate_library(root), [])
            result = json.loads((root / "manifest.json").read_text())
            colors = json.loads((root / "metadata/colors.json").read_text())
            self.assertEqual(colors["palettes"], duo_payload()["palette"])
            expanded = (root / "manifest.json").read_bytes()
            with self.assertRaisesRegex(ValueError, "two-style"):
                import_sheet(payload(), root)
            self.assertEqual(expanded, (root / "manifest.json").read_bytes())
            for style, data in assets.items():
                self.assertEqual(data, (root / f"icons/{style}/sample.svg").read_bytes())
                self.assertEqual(before["icons"][0]["source"][style],
                                 result["icons"][0]["source"][style])

    def test_invalid_expansion_does_not_write_partial_artwork(self):
        for mutation in ("color", "identity", "missing", "palette"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                import_sheet(payload(), root)
                before = (root / "manifest.json").read_bytes()
                data = copy.deepcopy(duo_payload())
                if mutation == "color":
                    data["svg"] = data["svg"].replace("#654321", "#ABCDEF")
                elif mutation == "identity":
                    data["records"][0]["source"]["regular"] = "changed"
                elif mutation == "missing":
                    data["records"] = []
                else:
                    data["palette"][0]["name"] = "Blue"
                with self.assertRaises(ValueError):
                    import_duo(data, root)
                self.assertEqual(before, (root / "manifest.json").read_bytes())
                self.assertFalse((root / "icons/duocolor").exists())
                self.assertFalse((root / "metadata/colors.json").exists())

    def test_duo_composition_supports_theme_custom_colors_and_transparent_stencils(self):
        for style in ("duocolor", "duotone"):
            light = compose_svg("user", "add", style=style, cutout=True, id_prefix="duo")
            dark = compose_svg("user", "add", style=style, theme="dark", cutout=True, id_prefix="duo")
            self.assertIn("#245B9E", light)
            self.assertIn("#93C5FD", dark)
            self.assertIn("<mask", light)
            self.assertEqual(validate_svg(light, style), [])
            custom = compose_svg("home-smile", "add", style=style, cutout=True,
                                 color="#123456", secondary_color="#ABCDEF")
            self.assertIn('color="#123456"', custom)
            self.assertNotIn("--fos-secondary", custom)
            if style == "duocolor":
                self.assertIn("#ABCDEF", custom)
        with self.assertRaises(ValueError):
            compose_svg("user", "add", style="duocolor", secondary_color="url(#bad)")


if __name__ == "__main__":
    unittest.main()
