# V64 — consolidated map credits and less repetition

16 October 2026. User authorised combining the map source footnote and checking clutter/repeated tags. No research imports or database edits.

## Current source and coordination

Read the canonical Drive ledger before work and again on resumption through EV092. Preserve the coordinator's EV086–EV092 research/source/database findings and the production-labelled Supabase boundary. GitHub main remains the primary app source at `Victoradex94/Command-Center-Gravity/poetics/`; starting head `6e708e45e6bd1cc9663fe9d2f2e95fd13e22f6a3`. Sites V63 source `4f4eeffae95f939a1ae3ac0a8006c5f6f3a08419` was opened through the supported helper. Fresh GitHub and Sites checks on resumption found those same versions. Research migration work is separate from this UI pass.

## Map sources

- One `Map sources` area beneath the map/city shortcuts. Credits and licence links remain visible; a single `Notes & downloads` disclosure holds layer dates, geometry qualifications and downloads.
- The national map credits MapSVG / Michael Chukwu / @svg-maps/nigeria from existing metadata and links its CC BY 4.0 licence and national JSON.
- Current state/city geometry credits GRID3 / geoBoundaries. Africapolis / OECD-SWAC & e-Geopolis appears when that state has matched urban extents. State vintage2022 and urban vintage2020, clipped/cross-state qualification, Jimeta association, unresolved city lists and no-legal/current-boundary claim remain in the notes.
- State downloads use that state's existing fingerprinted payload. No geographic bytes changed. In a zero-result national fallback the attribution returns to the national source.
- Legacy Kaduna fallback, if used without the current state renderer, supplies its own OpenStreetMap/ODbL and applicable Africapolis credits to the same area. No attribution is relabelled to a different dataset.
- Removed per-renderer footnotes and the sidebar's repeated national-source link, which was inappropriate for the current geographic state layer. The full metadata and source URLs remain available through the layer attribution API.

## Clutter changes

- Removed the extra Atlas footer repeating creator branding, About and map attribution. The introductory creator tag and ordinary site footer remain.
- Removed duplicated About/Submit links from the introduction; both destinations remain in main navigation.
- Use one removable location chip for the deepest selected location. The geographic path retains all parents and navigation; no geography state is discarded.
- State/city category-count buttons already provide icons and labels, so their duplicate floating category legend is omitted. National view retains its movable legend.
- Entry cards show at most two unique status tags. Event evidence, publication status and critical planned/cancelled/proposal phase labels receive priority; activity and verification remain available. Profiles retain the full deduplicated status set and detailed source/verification explanations. The Orerokpe card still explicitly says `Proposal; not completed` with inferred-year wording.
- The heat-scale methodology explanation moved into map notes; the scale and percentage bands remain visible.

## Checks and limits

Passed new `test-map-attribution-clutter.cjs`: one attribution area, correct national/state/urban source transitions, one visible shared licence, downloads, disclosure-open state, unresolved Owerri and Jimeta/cross-state notes, no duplicate footer/navigation/legend, one location chip, all453 cards limited to two unique tags, explicit proposal warning and complete profile evidence. The first new assertion looked for the proposal wording in `eventEvidence`; inspection showed it is a `phase.label`. The test now uses stable ID `ccpc-orerokpe-proposal`, without changing its data.

Passed UI-uplift, state-urban integration, all37 state payload hash/geometry checks, Atlas navigation, populated/zero-entry zoom, category/data performance, delivery and syntax checks. Full composed JSON is identical to V63: **453 records / 667 connections**. The rollout test now checks qualifications through `attribution()` because footnotes deliberately moved out of the geometry renderer.

Initial CSS/JS is820218 uncompressed local bytes, versus817400 inV63 and990093 inV62. The small attribution/UI code increase retains the earlier lazy Games loading and cached geometry. No network-speed claim.

This is a source/DOM-stub review, not a visual review. Supported control-browser remains unavailable; no improvised browser path/server was used. Fresh desktop/mobile screenshots, overflow, touch, screen-reader, icon sizing and measured contrast remain unverified. P013 stays partial. Colours, typography, dark outside-Nigeria/state map, light page and geographic nameplate are retained. No WordPress, Supabase, sharing, domain/hosting policy or schedule changes. Deployment identifiers and ledger readback are appended to the current canonical ledger after publication.
