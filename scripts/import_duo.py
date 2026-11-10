"""Import a complete native duo expansion without rewriting monochrome assets."""

import argparse
import hashlib
import json
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from build_presets import build_presets
from duo import DUO_STYLES
from import_figma import ROOT, extract_icon, unwrap
from validate import ALL_STYLES, validate_library, validate_svg


def import_duo(payload, root=ROOT):
    root = Path(root)
    original = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    records = payload["records"]
    rows = {r["name"]: r for r in records}
    icons = {r["name"]: r for r in original["icons"]}
    if len(rows) != len(records) or rows.keys() != icons.keys():
        raise ValueError("Duo expansion must include every canonical name exactly once")
    presets_path = root / "metadata/presets.json"
    presets = json.loads(presets_path.read_text())["presets"] if presets_path.exists() else []
    preset_names = {p["name"] for p in presets}
    sheet = ET.fromstring(payload["svg"])
    prepared = {}
    for name, row in rows.items():
        icon = icons[name]
        if row["componentSet"] != icon["componentSet"] or any(
            row["source"][s] != icon["source"][s] for s in ("regular", "filled")
        ):
            raise ValueError(f"Canonical Figma identity changed: {name}")
        if set(row["source"]) != set(ALL_STYLES):
            raise ValueError(f"Missing four-style source identities: {name}")
        for style in DUO_STYLES:
            if name in preset_names:
                continue
            text = extract_icon(
                sheet, row["positions"][style], f"{name}-{style}",
                style=style, paint_roles=payload["paintRoles"],
            )
            errors = validate_svg(text, style)
            if errors:
                raise ValueError(f"{name}/{style}: {errors}")
            prepared[f"icons/{style}/{name}.svg"] = text.encode("utf-8")
    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory)
        for name in ("icons", "metadata", "modifiers"):
            if (root / name).exists():
                shutil.copytree(root / name, stage / name)
        if "palette" in payload:
            colors = {
                "schemaVersion": 1, "defaultPalette": "Blue",
                "primaryVariable": "VariableID:48:36636",
                "secondaryVariable": "VariableID:48:36637",
                "palettes": payload["palette"], "custom": payload.get("custom"),
            }
            if len(colors["palettes"]) != 12 or len({p["name"] for p in colors["palettes"]}) != 12:
                raise ValueError("Expected twelve distinct Figma palettes")
            (stage / "metadata").mkdir(exist_ok=True)
            (stage / "metadata/colors.json").write_text(json.dumps(colors, indent=2) + "\n")
        original["styles"] = list(ALL_STYLES)
        original["source"]["duoExportedOn"] = payload["exportedOn"]
        for name, icon in icons.items():
            for style in DUO_STYLES:
                relative = f"icons/{style}/{name}.svg"
                icon["source"][style] = rows[name]["source"][style]
                icon["files"][style] = relative
                icon["sha256"][style] = hashlib.sha256(prepared.get(relative, b"")).hexdigest()
            icon["duoAuthoring"] = rows[name].get("duoAuthoring", {})
        for relative, data in prepared.items():
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (stage / "manifest.json").write_text(json.dumps(original, indent=2, ensure_ascii=False) + "\n")
        if presets:
            for style in DUO_STYLES:
                (stage / "icons" / style).mkdir(parents=True, exist_ok=True)
            build_presets(stage)
        errors = validate_library(stage)
        if errors:
            raise ValueError("\n".join(errors))
        for icon in icons.values():
            for style in ("regular", "filled"):
                relative = icon["files"][style]
                if (stage / relative).read_bytes() != (root / relative).read_bytes():
                    raise ValueError(f"Duo import would rewrite monochrome artwork: {relative}")
        for style in DUO_STYLES:
            destination = root / "icons" / style
            destination.mkdir(parents=True, exist_ok=True)
            for source in (stage / "icons" / style).glob("*.svg"):
                shutil.copy2(source, destination / source.name)
        shutil.copy2(stage / "manifest.json", root / "manifest.json")
        if (stage / "metadata/colors.json").exists():
            (root / "metadata").mkdir(exist_ok=True)
            shutil.copy2(stage / "metadata/colors.json", root / "metadata/colors.json")
    return original["iconCount"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(f"Imported duo styles for {import_duo(unwrap(json.loads(args.snapshot.read_text())), args.root)} icons")
