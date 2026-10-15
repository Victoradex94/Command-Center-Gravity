# Atlas UI uplift and conversation audit — Preview 62

15 October 2026. This is a supporting implementation/audit artifact. The same-ID Drive Markdown ledger remains the working task authority.

## Source and scope

Fresh sources: GitHub main `9685091ad3730f02c9482beece334b157e4e3f7b`; Sites61 source `57cbda58090ea37b1a74784872c8b7b29e36e53d`; canonical Drive read through DB136 and UI-V61. Reviewed the supplied conversation history and actual composed UI/data, rather than treating earlier reports as fresh visual proof. No active app edits found at opening; coordinator database work left separate. No new web research or record imports in this UI batch.

## Earlier decisions and execution gaps

| Request / decision | Audit finding and disposition |
|---|---|
| Minimal, specifically Vic'Adex / 60 Seconds Poetry | Existing cream, dark map, teal/peach/orange, Comfortaa/Afacad retained. V62 reduces intro height and repeated control rows. Visual alignment is a code-level refinement, not a fresh rendered approval. |
| One connected category/zone/state/city filter | V61 had year/format outside the geographic card and no individual clearing. V62 places all filters in one collapsible card, adds active removable chips, retains dependent geographic choices and zero-entry destination guards. |
| Keep the map useful while browsing | Confirmed defect: V61 close/hide-results handler cleared city, state and search. V62 separates panel visibility from geography; `panel=0` retains a closed filtered view on reload. Opening a profile now preserves the search, so returning to results restores context. |
| Current-layer nameplate, top-left unobstructed | V61 reserved top-left row retained, with current-layer label. V62 confines legend movement to the map viewport's vertical bounds so it cannot be dragged onto that row or filters. Actual layout/occlusion remains untested in a browser. |
| Easy parent navigation | Added selectable Nigeria / zone / state parents. Parent selection retains non-geographic filters. City-to-state keeps the state, state-to-zone keeps the zone. The user-approved previous/next state arrows remain; obsolete zoom/reset controls remain absent. |
| One total circle per state; disaggregate when selected | National slate-purple totals retained and enlarged modestly. Current state/city category counts moved from small SVG glyphs to real HTML circle buttons with category labels and 44–46 CSS-pixel circles. City counts now agree with filtered results and the displayed state's relative count. Dense national markers and actual touch behavior still need rendered/device QA. |
| Five distinct P columns and standard records | People, Places, Platforms, Prizes, Publications preserved. Cards consistently show name/category/location/date/summary/status plus direct source and connection count. Full source/uncertainty/activity details remain in profiles; announced Delta proposal remains explicitly labelled. No evidence upgrade. |
| Less noisy cards and useful links | V62 creates one bounded card with separately usable source and profile/connection controls; missing-photo placeholder reduced. Current verification labels can still be long; they are retained rather than compressed into falsely stronger claims. |
| Top cities rather than an endless city bar | V55 top-five ranking already implemented; retained current-filter ranking, counts and Surprise me. Old '5+ entries' threshold is superseded. Bar wraps; lighter background makes the previously low-contrast heading readable in source styles. |
| Dark outside Nigeria, light page, subtle boundaries | Preserved. V62 gives geographic SVGs their own proportional height, so category buttons and source text are not forced inside an unrelated fixed-height viewport. No measured overflow pass. |
| Nigeria-only and actual state/urban geometry | 37 geographic state/FCT payloads and 35 qualified urban associations already exist; lazy loading retained. Awka, Ikot Ekpene, Karu and Owerri extents remain unresolved. City filters remain useful there; no invented polygon. Urban areas are 2020 settlement extents, not legal/current city boundaries. |
| Administrative 0/2/3 layers | V59 established official ADM0 and ADM2 availability, but actual geometry bytes remain pending. ADM2 has 774 LGAs and is not a city layer. ADM3 was not advertised by that source, not a worldwide absence claim. No ADM2 overlay delivered in this batch. |
| Fast loading | V60 data compaction, ordered defer scripts and geographic association cache retained; selected-state geometry remains on demand. V62 adds small UI assets. File size is checked; no actual loading-time/FCP/LCP measurement. Games scripts still load in the common shell and remain a future route-loading opportunity. |
| Research verification and connected evidence | 453 entries/667 connections unchanged. Search matrices/history and uncertainty preserved. Outstanding source/imprint/edition questions remain open; UI work does not resolve them. |
| Submit an entry | Source confirms browser-local draft plus download only. No live ingestion/moderation backend. Reviewed durable submission workflow remains open. |
| GitHub editing outside ChatGPT | GitHub main is primary app source; `poetics-staging` is older. GPT Sites publication remains explicit. External Vercel/Codespaces instructions are not proof of deployment/configuration; no external host was connected here. |
| Database / SQL linkage | Preview still uses packaged source data. DB136 warns the Supabase project's active branch is marked PRODUCTION. No database writes, access changes, imports or assumed live sync. Reconciliation and a confirmed staging environment remain open. |
| Games and real opportunities | Separate fictional game modules retained, not materially audited in this Atlas UI batch. In-game fictional alerts must not be described as verified real-world opportunity notifications. |
| Visual QA and accessibility | Earlier attributed 390px/keyboard checks are historical and scoped. Current supported control-browser is absent; Sites skill requires skipping browser QA. P013 stays PARTIAL: no fresh desktop/mobile screenshot, touch/pen, screen-reader, overlap or overflow pass. Focus styles and semantic controls are source improvements only. |

## Validation and remaining work

`test-ui-uplift.cjs` executes actual index-selected modules and exercises filter collapse, unique filters, hierarchical parent navigation, removable chips, panel close/reopen/reload, preserving a profile's search context, city category totals, Delta proposal label and 453/667. Existing nameplate, zero-entry zoom, URL history, top-five cities, state navigation, urban integration/37-file rollout and delivery checks run as regression gates. Full composed rows/edges are compared to the immutable V61 modules. These VM/DOM-stub tests do not measure layout or browser performance.

Next: fresh supported desktop/mobile visual pass; assess dense national marker legibility and touch targets, long filters/names, card scanning and map/legend overflow. Then qualified ADM2 bytes and four urban gaps; separate reviewed submission backend and database reconciliation. Retained canonical research files, source links, data counts, audience, WordPress and hosting settings.
