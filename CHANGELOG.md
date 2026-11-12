# Changelog

Changes are recorded under Unreleased until a release is tagged.

## Unreleased

### Added

- Eighteen icons in all four styles, bringing the library to 1,252 icons and
  5,008 SVGs:
  - `dataflow-vertical`, `fuel-pump`, and `pause`.
  - `image-4k`, `image-4k-sparkles`, and `image-hd`.
  - Franc, lira, won, and yuan currency symbols and their circle variants.
  - `music-clef-treble`, `music-note-half`, `music-note-single`, and `music-sharp`.
- Expanded reusable modifier assets and style-safe compositions, with 92 named
  presets and preserved source metadata.
- Added the first-party Fedora Icons mark to a separate Figma Brands page in
  Regular and Filled only; it is not part of the four-style core exports.

### Changed

- Redrew `thermometer`, `thermometer-cold`, `thermometer-warm`, and
  `tool-crossed` across all four styles.
- Curved battery-family terminals to follow their casings and rounded the
  receipt family's upper corners and torn edges across all four styles.
- Redrew `podcast` with balanced broadcast arcs, `coins-hand` with a cupped
  palm and two coins, and `chart-pie` with matching circular sectors.
- Moved the five existing third-party brand sets and their catalog instances,
  including Figma and Framer, to the Brands page with an ownership disclaimer.
- Matched the Brands catalog to the main Regular catalog's header, margins,
  category spacing, and compact 24px icon grid.
- Reduced the `layers-offset` foreground panel's corner radius across all four
  styles, preserving the two offset lines.
- Redrew `torso` with curved shoulders, a tapered waist, and separated chest
  details; rebuilt `wheelchair` with a connected seated figure and rounded
  footrest; replaced `spine`'s pill-like shapes with articulated vertebrae and
  a tapered lower end, optically balancing Filled vertebral weight.
- Rebuilt `test-tube` with straight parallel walls, a rounded bottom, a distinct
  rim, graduation marks, and a horizontal liquid level.
- Redrew `hot-dog` with separate bun lobes and flowing mustard, `tea` with curved
  steam and a hanging tea tag, and `noodles` with wavy strands.
- Slimmed `bandage` with a central dressing pad and ventilation holes; rebuilt
  `arm` as a recognizable flexed arm with fist, wrist, and bicep details.
- Redrew `cake` with connected candles, flame details, rounded corners, and
  scalloped icing; Filled uses a transparent icing cutout.
- Rebuilt `arrows-triangle` as three evenly rotated arrows with consistent turns,
  arrowheads, spacing, and softer main bends.
- Matched exposed L-shaped bends to surrounding corner radii across offset
  stacks, document folds, crop/focus marks, chart axes, and related artwork,
  retaining rounded line caps and style-safe modifier colors.
- Rounded `navigation-pointer` and `navigation-pointer-off`, preserving the
  direction, off-state slash, and transparent gaps.
- Rounded play triangles, the image family's hills, and home-family corners,
  preserving structural details and linked modifiers.
- Refined commerce, document, instrument, currency, and music artwork across
  matching styles.

### Fixed

- Connected the image family's rounded hills to both frame borders in all four
  styles, including transparent Filled cutouts and the lower-left silhouette.
- Removed the opaque fill from `head-profile` Duocolor and made the ear its
  secondary-color accent, preserving the original profile geometry.
- Restored Filled details and transparent negative space.
- Preserved solid AI sparkle accents, themed modifier clearances, and modifier
  controls when changing a host icon's Style.
- Corrected `scissors-dashed` stroke scaling across Figma's 16px, 24px, and 32px
  stroke modes.

### Tooling

- Added pinned, conservative SVGO optimization for canonical and modifier SVGs.
  Geometry, numeric precision, paints, IDs, viewBoxes, and dimensions are not
  rewritten.
- Added Light, Dark, and custom-color pixel-parity checks at 24px and 48px before
  optimized assets are written, plus idempotence and manifest-hash checks.
- Added optimizer regression tests and CI validation; documented synchronization
  with the separate React package.
