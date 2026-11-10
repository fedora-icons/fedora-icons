"""Split an ID-preserving Figma SVG sheet into paired 24px SVGs."""

import argparse
import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ROOT = Path(__file__).resolve().parents[1]
BRANDS = ["chrome-cast", "figma", "framer", "google-chrome", "youtube"]


def unwrap(value):
    if isinstance(value, dict) and "records" in value and "svg" in value:
        return value
    if isinstance(value, dict) and "result" in value:
        result = value["result"]
        return unwrap(json.loads(result) if isinstance(result, str) else result)
    if isinstance(value, dict) and "content" in value:
        return unwrap(value["content"])
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict) and item.get("type") == "text":
                try:
                    return unwrap(json.loads(item["text"]))
                except (ValueError, KeyError):
                    continue
    raise ValueError("Expected a Figma bulk export containing records and svg")


def references(element):
    result = set()
    for node in element.iter():
        for key, value in node.attrib.items():
            result.update(re.findall(r"url\(#([^)]+)\)", value))
            if key.rsplit("}", 1)[-1] == "href" and value.startswith("#"):
                result.add(value[1:])
    return result


def extract_icon(sheet, position, prefix):
    matches = [
        node for node in sheet.iter() if node.get("id") == position["id"]
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one group for {position['id']}")
    group = copy.deepcopy(matches[0])
    definitions = {}
    for defs in sheet.findall(f"{{{SVG}}}defs"):
        for node in defs:
            if node.get("id"):
                definitions[node.get("id")] = node
    required = references(group)
    selected = {}
    while required:
        key = required.pop()
        if key in selected:
            continue
        if key not in definitions:
            raise ValueError(f"Missing SVG definition: {key}")
        selected[key] = copy.deepcopy(definitions[key])
        required.update(references(selected[key]) - selected.keys())
    icon = ET.Element(
        f"{{{SVG}}}svg",
        width="24",
        height="24",
        viewBox="0 0 24 24",
        fill="none",
    )
    if selected:
        defs = ET.SubElement(icon, f"{{{SVG}}}defs")
        for key in sorted(selected):
            defs.append(selected[key])
    wrapper = ET.SubElement(
        icon,
        f"{{{SVG}}}g",
        transform=f"translate({-position['x']} {-position['y']})",
    )
    wrapper.append(group)
    used = references(icon)
    mapping = {key: f"{prefix}-{index}" for index, key in enumerate(sorted(used))}
    for node in icon.iter():
        identifier = node.attrib.pop("id", None)
        if identifier in mapping:
            node.set("id", mapping[identifier])
        for attr, value in list(node.attrib.items()):
            for old, new in mapping.items():
                value = value.replace(f"url(#{old})", f"url(#{new})")
                if attr.rsplit("}", 1)[-1] == "href" and value == f"#{old}":
                    value = f"#{new}"
            node.set(attr, value)
    for node in wrapper.iter():
        for attr in ("fill", "stroke"):
            value = node.get(attr)
            if value and re.fullmatch(r"#[0-9a-fA-F]{3,8}", value):
                node.set(attr, "currentColor")
    return ET.tostring(icon, encoding="unicode") + "\n"


def import_sheet(payload, output):
    records = payload["records"]
    names = [row["name"] for row in records]
    if len(names) != len(set(names)) or set(names) & set(BRANDS):
        raise ValueError("Duplicate names or excluded brand artwork")
    sheet = ET.fromstring(payload["svg"])
    manifest = {
        "schemaVersion": 1,
        "name": "fedora-icons",
        "license": "MIT",
        "grid": 24,
        "regularStrokeWidth": 1.25,
        "styles": ["regular", "filled"],
        "iconCount": len(records),
        "source": {
            "type": "figma",
            "fileKey": "5zcUV9E4Bu8FSssDfhyOWw",
            "exportedOn": payload.get("exportedOn", date.today().isoformat()),
            "componentPairs": payload.get("componentPairs", len(records) + len(BRANDS)),
            "excludedBrands": BRANDS,
        },
        "icons": [],
    }
    for row in sorted(records, key=lambda row: row["name"]):
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", row["name"]):
            raise ValueError(f"Invalid canonical name: {row['name']}")
        record = {key: value for key, value in row.items() if key != "positions"}
        record["files"], record["sha256"] = {}, {}
        for style in manifest["styles"]:
            relative = f"icons/{style}/{row['name']}.svg"
            svg = extract_icon(
                sheet, row["positions"][style], f"{row['name']}-{style}"
            )
            data = svg.encode("utf-8")
            path = output / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            record["files"][style] = relative
            record["sha256"][style] = hashlib.sha256(data).hexdigest()
        manifest["icons"].append(record)
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT)
    args = parser.parse_args()
    payload = unwrap(json.loads(args.snapshot.read_text(encoding="utf-8")))
    manifest = import_sheet(payload, args.output)
    print(f"Imported {manifest['iconCount']} Regular/Filled pairs")
