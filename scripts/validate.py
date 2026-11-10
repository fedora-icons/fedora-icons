"""Validate the paired SVG library and its searchable manifest (no dependencies)."""

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG = "http://www.w3.org/2000/svg"
STYLES = ("regular", "filled")
ALLOWED = {
    "svg", "g", "path", "circle", "ellipse", "rect", "line",
    "polyline", "polygon", "defs", "clipPath", "mask", "use",
}


def validate_svg(text, style):
    errors = []
    if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        return ["XML declarations/entities are not allowed"]
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        return [f"Invalid XML: {error}"]
    if root.tag != f"{{{SVG}}}svg":
        errors.append("Expected an SVG namespace root")
    if root.get("viewBox") != "0 0 24 24":
        errors.append("Expected viewBox 0 0 24 24")
    if root.get("width") != "24" or root.get("height") != "24":
        errors.append("Expected 24px dimensions")
    identifiers = [node.get("id") for node in root.iter() if node.get("id")]
    if len(identifiers) != len(set(identifiers)):
        errors.append("Duplicate SVG IDs")
    references = set()
    visible_paints = 0
    geometry = 0

    def visit(node, definition=False):
        nonlocal visible_paints, geometry
        tag = node.tag.rsplit("}", 1)[-1]
        definition = definition or tag in {"defs", "mask", "clipPath"}
        if tag not in ALLOWED or not node.tag.startswith(f"{{{SVG}}}"):
            errors.append(f"Unsupported SVG element: {tag}")
        if not definition and tag in {"path", "circle", "ellipse", "rect", "line", "polyline", "polygon"}:
            geometry += 1
        for key, value in node.attrib.items():
            attr = key.rsplit("}", 1)[-1]
            if attr.startswith("on") or attr == "style":
                errors.append(f"Unexpected active/style attribute: {attr}")
            if re.search(r"NaN|Infinity", value):
                errors.append(f"Non-finite {attr}")
            references.update(re.findall(r"url\(#([^)]+)\)", value))
            if "url(" in value and not re.fullmatch(r"url\(#[^)]+\)", value):
                errors.append(f"External or unsupported reference: {value}")
            if attr == "href":
                if value.startswith("#"):
                    references.add(value[1:])
                else:
                    errors.append("External href")
            if attr in {"fill", "stroke"} and not definition:
                if value not in {"none", "currentColor"}:
                    errors.append(f"Non-themable {attr}: {value}")
                visible_paints += value == "currentColor"
            if attr == "stroke-width" and style == "regular" and not definition:
                try:
                    if abs(float(value) - 1.25) > 0.001:
                        errors.append(f"Regular stroke is not 1.25px: {value}")
                except ValueError:
                    errors.append(f"Invalid stroke width: {value}")
        for child in node:
            visit(child, definition)

    visit(root)
    if not geometry or not visible_paints:
        errors.append("Empty or unpainted icon")
    if references - set(identifiers):
        errors.append(f"Broken references: {sorted(references - set(identifiers))}")
    return errors


def validate_library(root):
    errors = []
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"Cannot read manifest: {error}"]
    icons = manifest.get("icons", [])
    if manifest.get("schemaVersion") != 1 or manifest.get("grid") != 24:
        errors.append("Unsupported manifest schema/grid")
    if manifest.get("styles") != list(STYLES) or manifest.get("license") != "MIT":
        errors.append("Unexpected styles/license")
    if manifest.get("iconCount") != len(icons):
        errors.append("Icon count does not match manifest")
    names = [row.get("name", "") for row in icons]
    if names != sorted(set(names)):
        errors.append("Canonical names must be unique and sorted")
    exclusions = set(manifest.get("source", {}).get("excludedBrands", []))
    expected = set()
    source_ids = []
    for row in icons:
        name = row.get("name", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
            errors.append(f"Invalid canonical name: {name}")
            continue
        if name in exclusions:
            errors.append(f"Excluded brand in core: {name}")
        if not row.get("category") or not row.get("componentSet"):
            errors.append(f"Missing category/component set: {name}")
        if not isinstance(row.get("tags"), list) or not isinstance(row.get("aliases"), list):
            errors.append(f"Invalid search metadata: {name}")
        for style in STYLES:
            relative = f"icons/{style}/{name}.svg"
            expected.add(relative)
            if row.get("files", {}).get(style) != relative:
                errors.append(f"Invalid manifest path: {name}/{style}")
            source = row.get("source", {}).get(style)
            if not source:
                errors.append(f"Missing Figma source: {name}/{style}")
            source_ids.append(source)
            path = root / relative
            try:
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() != row.get("sha256", {}).get(style):
                    errors.append(f"Digest mismatch: {relative}")
                for error in validate_svg(data.decode("utf-8"), style):
                    errors.append(f"{relative}: {error}")
            except (OSError, UnicodeError) as error:
                errors.append(f"{relative}: {error}")
    if len(source_ids) != len(set(source_ids)):
        errors.append("Figma source IDs must be unique")
    actual = {str(path.relative_to(root)) for path in (root / "icons").rglob("*.svg")}
    if actual != expected:
        errors.append(f"Unmanifested/missing SVGs: {sorted(actual ^ expected)}")
    if not icons:
        errors.append("Library is empty")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=ROOT)
    args = parser.parse_args()
    failures = validate_library(args.root)
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    count = len(json.loads((args.root / "manifest.json").read_text())["icons"])
    print(f"PASS: {count} pairs / {count * 2} SVGs; XML, themes, links, metadata and SHA-256")
