"""Rebuild compatible named icons from reusable base icons and modifiers."""

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from compose_svg import ROOT, compose_svg
from validate import validate_svg
from duo import DUO_STYLES


def build_presets(root=ROOT, snapshot=None):
    root = Path(root)
    data = snapshot or json.loads(
        (root / "metadata/presets.json").read_text(encoding="utf-8"),
    )
    while isinstance(data, dict) and "result" in data:
        data = data["result"]
        if isinstance(data, str):
            data = json.loads(data)
    if data.get("schemaVersion") != 1 or not data.get("presets"):
        raise ValueError("Expected a named preset snapshot")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    icons = {row["name"]: row for row in manifest["icons"]}
    names = [row["name"] for row in data["presets"]]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate preset names")
    prepared = []
    for preset in data["presets"]:
        name, base = preset["name"], preset["base"]
        if name not in icons or base not in icons or base in names:
            raise ValueError(f"Unknown, recursive, or nested preset: {name}")
        if icons[name]["componentSet"] != preset["componentSet"]:
            raise ValueError(f"Figma component set changed: {name}")
        for style in manifest["styles"]:
            if icons[name]["source"][style] != preset["source"][style]:
                raise ValueError(f"Figma component ID changed: {name}/{style}")
            svg = compose_svg(
                base, preset["modifier"], style=style,
                position=preset["position"], base_fit=preset.get("fit"),
                cutout=True, modifier_color=None if style in DUO_STYLES else "currentColor", root=root,
                id_prefix=f"fedora-{name}-{style}",
            )
            if style in DUO_STYLES:
                document = ET.fromstring(svg)
                badge = list(document)[-1]
                badge.set("color", f"var(--fedora-modifier, {badge.get('color')})")
                svg = ET.tostring(document, encoding="unicode") + "\n"
            failures = validate_svg(svg, style)
            if failures:
                raise ValueError(f"{name}/{style}: {failures}")
            relative = icons[name]["files"][style]
            if relative != f"icons/{style}/{name}.svg":
                raise ValueError(f"Invalid canonical preset path: {relative}")
            icons[name]["sha256"][style] = hashlib.sha256(svg.encode()).hexdigest()
            prepared.append((root / relative, svg))
        icons[name]["composition"] = {
            key: preset[key] for key in ("base", "modifier", "position", "fit")
        }
    for path, svg in prepared:
        path.write_text(svg, encoding="utf-8")
    (root / "metadata/presets.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8",
    )
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    return len(data["presets"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text()) if args.snapshot else None
    print(f"Built {build_presets(args.root, snapshot)} compatible named presets")
