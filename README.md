# Fedora Icons

1,234 icons in Regular, Filled, Duocolor, and Duotone styles: **4,936 SVGs**,
drawn on a 24 x 24 grid. Line styles default to 1.25px strokes. Negative space and
modifier clearances are transparent.

Fedora's goal is to help people find the right icon quickly and ship it
consistently, from design to code. Icon count is not the success metric.

## Product principles

These are research-informed product priorities, not a customer-survey ranking
or a claim that every planned capability has shipped.

- **Recognizable meaning.** Prefer familiar actions and concepts; consider
  cultural differences rather than assuming every metaphor is universal.
- **One visual family.** Keep stroke weight, proportions, spacing, and optical
  balance coherent across icons and matching styles.
- **Useful coverage.** Prioritize real product actions, objects, statuses, and
  domain needs over adding icons solely to increase the count.
- **Fast discovery.** Use predictable names, categories, synonyms, and useful
  previews so finding an icon does not require knowing its exact name.
- **Design-to-code parity.** Keep canonical names and source geometry aligned
  across Figma, SVGs, and generated packages. Handoff should not require redrawing.
- **Native-size clarity.** Judge detail at actual UI sizes, not only enlarged.
  The current artwork targets 24px; other optical sizes need their own validation.
- **Controlled flexibility.** Support color, size, style, and reusable modifiers
  without manual path edits. New weights or optical sizes must be designed and
  validated, not implied by arbitrary stroke overrides.
- **Accessible usage.** Explain labels, accessible names, contrast, and
  interactive targets. An icon library alone cannot make an interface accessible.
- **Production confidence.** Keep licensing and provenance explicit, delivery
  lightweight, and distribution dependable.

## Planned workflow

A React package and a searchable website are planned. The core SVG package
contains all four styles, with reusable modifiers and a Python composition tool.
The versioned core source release is `v0.1.0`.

The duo styles default to blue, with 12 editable Figma color presets:
Slate, Blue, Sky, Cyan, Teal, Green, Lime, Yellow, Amber, Orange, Red, and Rose.
Each preset has Light/Dark primary and secondary variables in **Fedora / Theme**.
Alias `color/duo-primary` and `color/duo-secondary` to a matching
`color/palette/{name}` pair to change the library's duo colors. For arbitrary
colors, edit `color/custom/primary` and `color/custom/secondary` and alias the
duo variables to that pair. Individual vector fills and strokes can also use
the palette variables. Duotone retains its 16% interior fill.

Optional full warm-neutral themes are available in Figma: **Ivory, Sand, and
Stone**, with backgrounds, surfaces, borders, text, and matching icon colors.
Select **Warm Light** or **Warm Dark** in **Fedora / Theme**, then choose the
palette in **Fedora / Warm palette**. Original Light/Dark values and blue
defaults are unchanged. `metadata/warm-themes.json` records the editable
variables, native mode IDs, colors, and contrast verification. These are Figma
theme presets; SVG defaults remain blue. For warm inline SVGs, use the matching
primary/secondary values with `--fedora-primary` and `--fedora-secondary`.

Duocolor accents separate details. Single-contour icons without a separate
detail stay primary-only; continuous outlines are not split just to force
two colors.

The expansion preserves 30 approved duo masters and derives the remaining
variants from native Regular geometry. Contour length distinguishes dominant
structure from smaller details, without arbitrarily recoloring equal repeated
strokes. Duotone tints explicitly closed contours at 16% with NORMAL isolation;
open-only symbols do not get invented interior regions.

AI editing includes `image-user-sparkles` (portrait/reference),
`image-hd-sparkles` (resolution enhancement), `layers-rename-sparkles`,
`content-replace-sparkles`, `scissors-sparkles`, and `wand-sparkles`.
These six additions and the existing `image-sparkles`, `edit-sparkles`, and
`translate-sparkles` use solid AI sparkle accents in all four styles.
Standalone `sparkle`/`sparkles` style choices remain unchanged.
`metadata/ai-editing.json` records native sources, action meanings, and
Light/Dark proof verification.

Modifiers compose a base icon with a reusable glyph rather than requiring a
separate drawing for every combination. The chooser will group actions
(Add, Delete, Remove, Block, Edit, and four directional arrows), statuses
(Warning, Check), access/identity (Key, Lock, User, Clip), and file-type labels.
All nineteen are reusable Figma components and SVG assets.
Glyphs remain solid independently of the base style: Key, Lock, User, and Clip
have no colored backplate.

Add (`+`) defaults to the top-left corner; Delete (a cross) defaults to the
bottom-right. An explicit corner can override the default. The Add/Delete Figma
proof uses squircle backgrounds and a matching 1.25px transparent clearance
gap so the badge never touches the underlying icon. Warning and Check also use
squircles. The six extended glyphs have explicit corner variants; no automatic
defaults have been assigned to them.

The file-type proof uses reusable PDF, SVG, EPS, and PSD labels, defaulting to
bottom-left, on a rounded document base with a softened fold. Existing named
action and file-type icons remain compatible; the rounded base is currently
a separate Figma prototype, not a replacement of the published file-type geometry.
Remove uses a minus, Delete uses a cross, and Block uses a prohibition mark.
Structural details remain part of the base icon.
Automatic semantic/geometric conflict handling is deferred.

The website's primary action will be **Download SVG**, with **Download PNG**,
**Download XAML**, **Copy SVG**, **Copy image**, and **Copy name** also available.
Users choose the base icon, style, and optional glyph before exporting. Every
export should reflect the selected style, colors, modifier, and position. The
supported XAML dialect still needs to be established.

## Use

### Figma

The **Get Started** page contains an original Figma quick-start with linked
instances, style-page navigation, live warm-theme samples, and editable stroke
examples. It covers styles, instances, themes, modifiers, and native exports.
The supplied reference guide remains alongside it.

**Fedora / Stroke** exposes the FLOAT variable `icon/stroke-width` for Regular,
Duocolor, and Duotone. Select a frame or instance and apply a collection mode:

| Stroke preset | Default value |
| --- | --- |
| 16 px | 1px |
| 24 px (default) | 1.25px |
| 32 px | 1.5px |

Edit a mode's value in local variables to customize its weight. All 10,094 live
core outline strokes are bound; Solid silhouettes, filled accents, and legacy
brands are excluded. The default 24px appearance is preserved.

Modes change stroke weight, **not icon dimensions**. Current masters are
authored at 24px; the other presets are not separately authored optical sizes.
Resize separately and check at the final size. SVG exports resolve the current
appearance rather than retaining Figma variable bindings; the checked-in SVGs
keep their default strokes. `metadata/stroke-variables.json` records native
bindings and verification, and `metadata/get-started.json` identifies the guide.

Component descriptions contain the icon name and relevant metaphors/synonyms,
without pixel-grid or drawing-specification boilerplate.

### SVG

Copy SVGs from `icons/regular/`, `icons/filled/`, `icons/duocolor/`, or
`icons/duotone/`. There is no runtime
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

Duo SVGs use `--fedora-primary` and `--fedora-secondary` with blue defaults.
Set these CSS custom properties on an inline SVG or its ancestor; a CSS
`color` rule can also override the root's primary default. Named duo presets
add `--fedora-modifier` for their solid glyph. `metadata/colors.json` records
the twelve Light/Dark Figma palette pairs. Standalone SVGs default to Light;
use the composer with `--theme dark` for dark-theme exports.

## Compose an SVG with a modifier

The dependency-free Python tool uses the canonical core asset and modifier
geometry exported from Figma. It does not create or alter named core icons:

```sh
python3 scripts/compose_svg.py user --modifier add --output user-add.svg
python3 scripts/compose_svg.py file --style filled --modifier pdf --output file-pdf.svg
python3 scripts/compose_svg.py user --style duocolor --modifier add --theme dark \
  --color '#93C5FD' --secondary-color '#60A5FA' --cutout --output user-add-duo.svg
python3 scripts/compose_svg.py home-smile --modifier key --position bottom-right \
  --color '#212121' --modifier-color '#245B9E' --output home-key.svg
```

Available modifiers: `add`, `delete`, `warning`, `check`, `key`, `lock`, `user`,
`clip`, `pdf`, `svg`, `eps`, `psd`, `remove`, `block`, `edit`, `arrow-up`,
`arrow-down`, `arrow-left`, and `arrow-right`. `auto` uses the approved Add/Delete and
file-type defaults. Other modifiers require an explicit `--position`:
`top-left`, `top-right`, `bottom-left`, or `bottom-right`.

Use `--theme dark` for dark-theme modifier and duo colors. `--color` controls the base;
`--secondary-color` controls Duocolor details;
`--modifier-color` and `--glyph-color` override the modifier's primary and stencil
colors. Colors accept `#RGB`, `#RRGGBB`, `#RRGGBBAA`, or `currentColor`.
Theme selection never paints a background. Regular/Filled retain inherited
`currentColor`; duo styles receive the selected theme's blue defaults.
Use `--cutout` for transparent stencil marks rather than a theme-colored glyph.

The exported SVG uses a contour-matched clip path, not a background-colored halo,
and unique internal IDs for safe inline reuse. Each composition verifies source
SHA-256 digests before using the assets. The raw files in `modifiers/` use
`currentColor` and `--fedora-glyph-color` (white fallback); the composer resolves
the selected theme or custom colors into the output.

`metadata/modifiers.json` is the shared source contract for downstream generators:
native dimensions, glyph provenance, theme colors, approved defaults, four corner
origins, and actual 1.25px clearance contours. The Python composer supports all
four styles. React and website integration, additional file types, and modifier
conflict rules have not shipped.

### Compatible named presets

Twenty-one existing icons now use reusable compositions: `briefcase-lock`,
the eleven `user` action/status variants, and the nine `users` action variants.
Their names, paths, and original Regular/Filled component IDs are unchanged.
`user-circle`, `user-square`, `user-focus`, `user-identity`, and `user-badge`
retain their structural artwork.

`metadata/presets.json` records each base, modifier, explicit corner, and any
deliberate optical fit. Add is top-left; these presets explicitly place the other
actions bottom-right without inventing new automatic defaults. The two Add
presets fit their base around the badge without cutting through a head, while
retaining the 1.25px Regular stroke. This is authored placement, not automatic
conflict detection. The composer also uses that fit when the selected base,
modifier, and corner exactly match a declared preset.

Regular/Filled presets remain monochrome `currentColor`; duo presets retain
their base color roles and solid semantic modifier color. All use genuinely
transparent stencil marks and clearance gaps in SVG. The same presets are native
four-style Figma components. Regenerate the named
SVGs after changing their shared base or modifier:

```sh
python3 scripts/build_presets.py
```

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

The core library in the Fedora Icons design file (`5zcUV9E4Bu8FSssDfhyOWw`)
contains 1,239 native component sets. The 1,234 core sets have
`Style=Regular/Filled/Duocolor/Duotone` and `Size=24`, with original
Regular/Filled component IDs preserved. Five excluded brand sets retain their
original two styles. Source catalogs and native/4x validation tiles remain
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

Validation checks four files per name, XML, 24px dimensions, explicit color roles,
line-style stroke widths, internal references, unique source IDs, searchable
metadata, SHA-256 digests, and unmanifested SVGs.

For updates, run `scripts/export_figma.js` in a Figma plugin context and call
`exportFedoraIcons(manifest)` with the current manifest object. Save the returned
snapshot JSON (including `styles` and `paintRoles`) outside the repository, then run:

```sh
python3 scripts/import_figma.py /path/to/figma-export.json
python3 scripts/validate.py
```

The exporter clones sources into a temporary sheet, exports current live
geometry with stable group IDs, and removes its temporary section. The importer
splits the sheet into standalone 24px SVGs, restores each tile's coordinate
origin, converts visible primary paints to `currentColor`, maps secondary duo
paints explicitly, retains referenced definitions, and regenerates the manifest.
An old two-style snapshot cannot downgrade an existing four-style library.
Add or remove icons in the manifest
deliberately before exporting; unmanifested files are not silently deleted.

For a duo-only refresh, run `scripts/export_duo_figma.js` and call
`exportFedoraDuo()`, then import its snapshot with
`python3 scripts/import_duo.py /path/to/duo-export.json`. This stages and validates
the complete expansion, refreshes the twelve live palette pairs, and refuses
to rewrite Regular/Filled files or their original source IDs.

For modifier updates, run `scripts/export_modifiers_figma.js` in the same live
plugin context and call `exportFedoraModifiers()`. Save its returned snapshot
outside the repository, then run:

```sh
python3 scripts/import_modifiers.py /path/to/modifier-export.json
python3 scripts/build_presets.py
python3 -m unittest discover -s tests
```

The modifier importer preserves the core; the preset builder updates only the
21 declared named compositions. `exportFedoraPresets()` in the same JavaScript
file exports the live preset definitions after checking their nested sources.
Import an updated preset snapshot with
`python3 scripts/build_presets.py --snapshot /path/to/preset-export.json`.
Core sheet imports automatically rebuild declared presets so monochrome
normalization cannot collapse stencil marks into solid badges.

Modifier tests verify all 76 corner compositions in both monochrome styles, source
digests, transparent-clearance paths, ID isolation, theme/custom colors, and
rejection of unapproved automatic defaults. Preset tests cover transparent
stencils, optical fits, deterministic regeneration, shared-glyph updates,
preserved names/IDs, and core re-imports. Duo tests cover explicit paint roles,
theme/custom colors, palette persistence, transparent composition, original
asset preservation, and rejection without partial writes.

The November 10, 2026 source audit is recorded in
[metadata/figma-audit.json](metadata/figma-audit.json).

## License

Fedora's core artwork and repository tooling are available under the
[MIT License](LICENSE). Third-party brand artwork is **not included** in this
grant or SVG package. Product names and trademarks belong to their respective
owners; this project does not imply affiliation or endorsement.
