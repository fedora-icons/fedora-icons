# Brand icons

The Figma **Brands** page keeps brand artwork separate from the core icon
catalogs and components. It uses Regular and, where applicable, Filled (Solid)
styles only, without Duocolor or Duotone variants.

The page displays: "All brand icons belong to their respective owners."

Its catalog follows the main Regular catalog (`29:4984`): a 1440px frame,
96px outer margins, the shared header and category styling, and 24px icons on
a 60px-column, 56px-row grid without individual captions.

The first-party `fedora-icons` mark is adapted from the supplied F Symbol,
preserving its interlocking contours and proportions. Its native component set
is `71:151203`, with Regular `71:151173` and Filled `71:151178`. It is a separate
Figma companion, not a four-style core SVG or React export.

The supplied Social icon set (`71:151402`) is a reference for recognizable
silhouettes and proportions. Its color and hover variants are not imported into
the Fedora collection.

## Third-party brands

No third-party brand SVGs are included in this package.

The Brands page contains five existing third-party drawings, including Figma
and Framer. Their original masters and linked catalog instances were moved
without changing their source IDs or artwork. They are
excluded from the MIT core, not presented as official artwork, and have not been
replaced or redistributed here:

| Canonical name | Figma Regular source |
| --- | --- |
| `chrome-cast` | `33:21822` |
| `figma` | `33:26832` |
| `framer` | `33:26858` |
| `google-chrome` | `33:19672` |
| `youtube` | `33:25429` |

The requested unmodified social and Microsoft logo collection, including Teams,
Edge, Windows, and an official replacement for Chrome, is **not yet imported**.
Its exact brand list, authoritative source assets, and applicable redistribution
terms remain to be established. Do not copy these older drawings into the core
or assume that the repository's MIT license covers a logo.

Future brand assets should remain separate from `icons/`, retain their original
artwork and colours, and record their owner, official source, retrieval date,
asset digest, terms, and any required attribution. An ownership disclaimer is
not a substitute for the applicable permissions.

Official resources:

- [Microsoft Trademark and Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks)
- [Google Brand Resource Center: products and services](https://about.google/brand-resource-center/products-and-services/)

All third-party names and marks are the property of their respective owners.
No affiliation or endorsement is implied.
