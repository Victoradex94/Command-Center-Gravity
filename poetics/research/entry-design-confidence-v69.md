# Entry presentation and confidence — V69

Date: 16 October 2026 (Africa/Lagos)

## Scope

Improve the Atlas entry cards and About page using the existing 453-entry, 667-connection graph. This is a presentation and explanation change; it adds no historical claims, sources, nodes, or edges. The raw canonical graph and its composed browser JSON remain unchanged.

## Entry confidence

The interface now shows one explicit grade and explanation:

- **Unconfirmed:** no recorded direct review of the core entry.
- **Weak:** reviewed support is limited to an index/listing or its basis is unclear.
- **Strong:** a directly reviewed primary source or credible report supports the entry as worded, including its qualifications.
- **Very strong:** a directly reviewed primary source and a distinct independent source family support the same claim, with no unresolved core conflict.

The existing review metadata maps 176 entries to Unconfirmed, 2 to Weak and 275 to Strong; zero entries are marked Very strong. This is a conservative display mapping, not a new review of 453 records. A source URL alone cannot raise confidence. Very strong requires an explicit entry-specific assessment with claim, review date, no unresolved conflict, and directly read source URLs from different source families. Repeated or copied reports do not qualify as independent corroboration. Announcement confidence does not mean event completion; current activity remains separately labelled.

## Dates and claim-linked references

Where records contain explicit, dated activity evidence, cards use **Years active** based only on those activities. Else they show **Recorded span**, the earliest and latest dated references. Neither label claims continuous activity, founding, lifespan, residence or attendance. Exact dates, original date meanings and date qualifications remain available in each record's evidence panel.

Card summaries now attach numbered superscript links to the sources supporting each displayed claim. Matching numbered source links appear below the card. Profile details use the same numbering and retain the complete source records, original notes, attribution, evidence limits, rights notes and unresolved questions. Summary text is factual and role-specific where the existing graph supports a typed, sourced connection. Proposed and announced venues retain their status; an event's year is not substituted for an exact event date. Unmapped/ambiguous records retain their qualified original descriptions.

## Controls, cards and icons

Categories now uses the same native dropdown pattern as the other filters. “Choose multiple…” opens an explicit multi-select panel; selecting categories updates map/results together. The single-category and all-category paths remain available, including URL state.

Cards now share a stable order: project-authored category icon tile, name, factual summary, location and date label, entry-confidence control, connections and numbered sources. Confidence and source links are visible without opening profile details; the profile retains deeper evidence.

Official icon-reference and licensing pages were reviewed: [Flaticon Uicons](https://www.flaticon.com/uicons/interface-icons), [Noun Project microphone collection](https://thenounproject.com/browse/icons/term/microphone/), [Noun Project licensing](https://help.thenounproject.com/hc/en-us/articles/200509798-What-licenses-do-you-offer-for-icons), [Noun Project creator credit](https://help.thenounproject.com/hc/en-us/articles/200509928-How-do-I-give-creators-credit-in-my-work), and [Flaticon license](https://www.flaticon.com/media/license/license.pdf). No third-party artwork, font or license-dependent asset was downloaded. The existing project-authored inline SVG set was retained and made more consistent in size, tile shape and category-color treatment. Thus no new icon attribution was required or implied.

## Validation and limits

- Presentation policy tests cover evidence-review gating, independent-source-family requirements, date-range conservatism and exclusion of future/undated activity.
- Card tests compare every superscript claim URL/number with the matching numbered source below the card, check for nested links inside the main card button, and verify factual venue/event qualifications and retained proposal metadata.
- Native category control tests cover single selection, opening/closing the multi-select panel, multiple categories, all-category reset and URL state.
- Contribution/About tests verify the displayed confidence definitions and date/citation guidance.
- Navigation, attribution/clutter, geometry preparation and delivery checks pass. All 453 entries and 667 connections remain equal to the V68 canonical composed data.
- These are source, VM/DOM-stub and package checks. A fresh rendered visual, mobile, keyboard, touch, screen-reader, contrast or overflow review is not claimed here; the connected browser and managed preview were previously unavailable. Existing bounded mobile/keyboard work remains partial.

## Source-search note

Icon reference searches on 16 October 2026 used these exact queries: `site.flaticon.com license free icons attribution website`; `site.thenounproject.com help icons attribution creative commons download license`; and `site.flaticon.com/uicons "user" "map-marker" "microphone"`. Official licensing/reference pages were inspected; the asset-oriented results did not establish a suitable licensed external set for this build. This was a design-asset check, not research about Atlas people, events or places.
