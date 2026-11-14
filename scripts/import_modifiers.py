"""Import a live Figma modifier snapshot without changing the core icon manifest."""

import argparse
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from import_figma import SVG

ROOT = Path(__file__).resolve().parents[1]
POSITIONS = ("top-left", "top-right", "bottom-left", "bottom-right")
GLYPH_PAINT = "var(--fos-glyph-color, #FFFFFF)"
ET.register_namespace("", SVG)


def allowed_positions(record):
    positions = record.get("allowedPositions", POSITIONS)
    if not isinstance(positions, (list, tuple)) or not positions or any(
        position not in POSITIONS for position in positions
    ) or len(set(positions)) != len(positions):
        raise ValueError(f"Invalid allowed positions: {record['name']}")
    return tuple(positions)


def namespace_ids(root, prefix):
    mapping = {
        node.get("id"): f"{prefix}-{index}"
        for index, node in enumerate(node for node in root.iter() if node.get("id"))
    }
    for node in root.iter():
        if node.get("id") in mapping:
            node.set("id", mapping[node.get("id")])
        for attr, value in list(node.attrib.items()):
            value = re.sub(
                r"url\(#([^)]+)\)",
                lambda match: f"url(#{mapping.get(match[1], match[1])})",
                value,
            )
            if attr.rsplit("}", 1)[-1] == "href" and value.startswith("#"):
                value = "#" + mapping.get(value[1:], value[1:])
            node.set(attr, value)


def normalize_modifier(record):
    root = ET.fromstring(record["svg"])
    size = f"0 0 {record['width']} {record['height']}"
    if root.tag != f"{{{SVG}}}svg" or root.get("viewBox") != size:
        raise ValueError(f"Incorrect modifier dimensions: {record['name']}")
    roles = record.get("paintRoles", record["colors"]["light"])
    primary = roles["primary"].lower()
    glyph = roles["glyph"].lower()
    for node in root.iter():
        for attr in ("fill", "stroke"):
            color = node.get(attr, "").lower()
            if color == primary:
                node.set(attr, "currentColor")
            elif color == glyph or (color == "white" and glyph == "#ffffff"):
                node.set(attr, GLYPH_PAINT)
            elif color not in ("", "none"):
                raise ValueError(f"Unmapped modifier paint: {color}")
    namespace_ids(root, f"fos-modifier-{record['name']}")
    return ET.tostring(root, encoding="unicode") + "\n"


def import_modifiers(payload, output):
    while isinstance(payload, dict) and "result" in payload:
        payload = payload["result"]
        if isinstance(payload, str):
            payload = json.loads(payload)
    if payload.get("schemaVersion") != 1 or not payload.get("records"):
        raise ValueError("Expected a Figma modifier snapshot")
    manifest = {
        "schemaVersion": 1,
        "grid": 24,
        "license": "MIT",
        "source": payload["source"],
        "modifiers": [],
    }
    prepared = []
    names = set()
    for row in payload["records"]:
        name = row["name"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or name in names:
            raise ValueError(f"Invalid or duplicate modifier name: {name}")
        names.add(name)
        allowed = allowed_positions(row)
        if set(row["positions"]) != set(allowed):
            raise ValueError(f"Missing explicit corner: {name}")
        if row["defaultPosition"] not in (None, *allowed):
            raise ValueError(f"Invalid automatic position: {name}")
        for position in row["positions"].values():
            if not position["clearance"] or any(
                path["windingRule"] not in ("EVENODD", "NONZERO")
                or not path["data"] or re.search(r"\b(?:nan|inf)\b", path["data"], re.I)
                for path in position["clearance"]
            ):
                raise ValueError(f"Invalid clearance geometry: {name}")
        svg = normalize_modifier(row)
        record = copy.deepcopy({
            key: value for key, value in row.items() if key not in ("svg", "paintRoles")
        })
        record["file"] = f"modifiers/{name}.svg"
        record["sha256"] = hashlib.sha256(svg.encode()).hexdigest()
        manifest["modifiers"].append(record)
        prepared.append((output / record["file"], svg))
    for path, svg in prepared:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8")
    (output / "metadata").mkdir(parents=True, exist_ok=True)
    (output / "metadata/modifiers.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    imported = import_modifiers(
        json.loads(args.snapshot.read_text(encoding="utf-8")), args.output,
    )
    print(f"Imported {len(imported['modifiers'])} reusable modifiers")
