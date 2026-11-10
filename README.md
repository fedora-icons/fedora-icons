# Fedora Icons

1,228 monochrome icons in Regular and Filled styles: **2,456 SVGs**, drawn on a
24 x 24 grid. Regular uses 1.25px strokes. Both styles use `currentColor` and
transparent negative space.

## Use

Copy SVGs directly from `icons/regular/` or `icons/filled/`. There is no runtime
dependency, framework wrapper, or icon font.

```html
<img src="./icons/regular/text-align-left.svg" width="24" height="24"
     alt="Align text left">
```

For CSS theming, inline the SVG markup instead of using an `<img>`: the SVG's
`currentColor` follows the containing element's `color`. Use `aria-hidden="true"`
on decorative inline SVGs and give icon-only controls an accessible name. For
meaningful standalone inline SVGs, use `role="img"` and an accessible label.
Do not globally override path fills: Filled icons use real transparent cutouts.

## Find an icon

`manifest.json` contains canonical kebab-case names, categories, semantic tags,
legacy search aliases, paths, SHA-256 digests, keylines, and Figma source IDs.
Aliases are search terms, not additional files or guaranteed one-to-one names.

```python
import json

icons = json.load(open("manifest.json", encoding="utf-8"))["icons"]
query = "weather"
matches = [
    icon["name"] for icon in icons
    if query in " ".join(
        [icon["name"], icon["category"], *icon["tags"], *icon["aliases"]]
    ).lower()
]
print(matches)
```

## Figma source

The Fedora Icons design file (`5zcUV9E4Bu8FSssDfhyOWw`) contains 1,233 native
component sets. Each has `Style=Regular/Filled` and `Size=24`, with original
component IDs preserved. Source catalogs and native/4x validation tiles remain
linked. Select a catalog or verification board and change its **Fedora / Theme**
mode to switch Light/Dark.

The SVG core excludes five third-party brand drawings still present in the
design file. See [BRANDS.md](BRANDS.md) for exclusions and the unfinished
official-logo import. The Figma source is not included as a `.fig` archive.

## Validate and re-export

Python 3.10+ is sufficient; no third-party Python packages are needed.

```sh
python3 -m unittest discover -s tests
python3 scripts/validate.py
```

Validation checks both files per name, XML, 24px dimensions, `currentColor`,
Regular stroke widths, internal references, unique source IDs, searchable
metadata, SHA-256 digests, and unmanifested SVGs.

For updates, run `scripts/export_figma.js` in a Figma plugin context and call
`exportFedoraIcons(manifest)` with the current manifest object. Save the returned
`{records, svg}` JSON outside the repository, then run:

```sh
python3 scripts/import_figma.py /path/to/figma-export.json
python3 scripts/validate.py
```

The exporter clones sources into a temporary sheet, exports current live
geometry with stable group IDs, and removes its temporary section. The importer
splits the sheet into standalone 24px SVGs, restores each tile's coordinate
origin, converts visible monochrome paints to `currentColor`, retains referenced
definitions, and regenerates the manifest. Add or remove icons in the manifest
deliberately before exporting; unmanifested files are not silently deleted.

The November 10, 2026 source audit is recorded in
[metadata/figma-audit.json](metadata/figma-audit.json).

## License

Fedora's core artwork and repository tooling are available under the
[MIT License](LICENSE). Third-party brand artwork is **not included** in this
grant or SVG package. Product names and trademarks belong to their respective
owners; this project does not imply affiliation or endorsement.
