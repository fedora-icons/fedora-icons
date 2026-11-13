# Brand icons

The Figma **Brands** page keeps brand artwork separate from the core icon
catalogs and components. It uses Regular and, where applicable, Filled (Solid)
styles only, without Duocolor or Duotone variants.

The page displays: "All brand icons belong to their respective owners."

Its catalog follows the main Regular catalog (`29:4984`): a 1440px frame,
96px outer margins, the shared header and category styling, and 24px icons on
a 60px-column, 56px-row grid without individual captions. The Brands page now
contains 37 Regular icons and five Solid icons. Third-party marks appear only
in the Regular row; Solid is limited to marks that already have a Solid source.

The first-party `fedora-icons` mark is adapted from the supplied F Symbol,
preserving its interlocking contours and proportions. Its native component set
is `71:151203`, with Regular `71:151173` and Filled `71:151178`. It is a separate
Figma companion, not a four-style core SVG or React export.

## Brand collection

The 28 social marks use the `Style=Brand, State=Default` variants in the
Figma Social icon set (`71:151402`). The selected canonical identities are
Facebook, X, Instagram, LinkedIn, Google, WhatsApp, Apple, Snapchat, Pinterest,
Dribbble, Reddit, Discord, TikTok, Tumblr, Telegram, Clubhouse, Signal, GitHub,
AngelList, Layers, Twitch, Slack, Spotify, Stripe, PayPal, Wise, Notion, and
Webflow. X is used instead of Twitter; one Discord identity is retained.
Existing Figma, Framer, YouTube, Chromecast, and Fedora icons remain in the
catalog without duplicating those identities.

Google Chrome, Microsoft Edge, Teams, and Windows are separate brand-only
components. The new Chrome component is `74:164000`; it replaces only the
Brands-page Regular instance. The existing shared Chrome masters
(`33:19672` and `33:38771`) and their uses elsewhere remain unchanged. The old
Solid Chrome instance was removed because no approved Solid brand source was
provided.

Third-party assets are stored under `brand-assets/`, outside `icons/` and the
core package. `brand-assets/manifest.json` records each asset's owner, source,
and SHA-256 digest, with a collection retrieval date and shared rights and
attribution notes that apply to every entry. The collection contains 32 SVGs:
28 social marks and four Google/Microsoft product marks.

## Rights and attribution

The user explicitly confirmed authorization to redistribute the social and
Microsoft marks. This records that confirmation; it is not an independent
verification or a license from the owners. The repository's MIT license does
not cover third-party marks. Copyright and trademark rights remain with their
respective owners; follow each owner's current terms and brand guidelines.
No affiliation or endorsement is implied.

Official guidance:

- [Microsoft Trademark and Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks)
- [Google Brand Resource Center: products and services](https://about.google/brand-resource-center/products-and-services/)

All third-party names and marks are the property of their respective owners.
