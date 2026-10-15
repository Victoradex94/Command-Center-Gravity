# V63 — category icons and map delivery

15 October 2026. User authorised category clarity and a quicker Atlas. This is a UI/delivery change, with no research imports or semantic record edits.

## Source basis

- GitHub `Victoradex94/Command-Center-Gravity`, `main`, `poetics/`, starting commit `c671810c68315942e39bfe98eb0d0c001e969069`.
- Sites project `appgprj_6acce9493e8c81919635a9e7438b820c`, V62 source `5ff6bf48cbbb722ff5a9b4c3c6bcbb720173f69d`, opened through the supported source helper.
- Fresh canonical Drive ledger through `UI-20261015-V62-UPLIFT-HISTORY-AUDIT`, including DB136's production database boundary. No database access or writes in this pass.
- Restricted/custom preview audience retained. GitHub remains primary source; Sites publication is explicit, not automatic.

## Changes

The same person, location pin, microphone, trophy and book symbols now accompany People, Places, Platforms, Prizes and Publications in filters, the map legend and state/city category-count buttons. The Platforms symbol replaces its less specific four-square grid. Existing entry/profile icons use the same definitions. Written labels remain visible and decorative SVGs are hidden from assistive technology. Approved category colours remain secondary cues. The neutral slate-purple national total circles still mean all selected categories.

The browser now receives a generated `canonical-research-runtime.js` containing the People & Platforms table and the same metadata, supplemental profiles and deep research used by the directory. The full original `canonical-research.js`, its other five research tables, research logs and historical assets remain intact. This display derivative is regenerated automatically by `scripts/fingerprint-assets.py` using `scripts/prepare-browser-data.py`; it is not another task ledger or research authority.

Five Games modules are content-addressed but requested only on the Games route. Atlas startup no longer creates a fictional game or reads its saved journey. The loader shares pending/completed requests, preserves dependency order, handles navigation away during loading, and retries only failed assets. The existing game save is restored once after successful loading.

State/urban map paths and label projections now use a bounded eight-viewport LRU cache. Counts, enabled/disabled city buttons, selection, percentage fill and accessible labels remain freshly rendered. Loading a replacement state payload invalidates its cached projections. Projection bounds use a streaming pass instead of flattened point arrays. Geographic source bytes, qualification, clipping and all 37 payload hashes are unchanged. State geometry remains fetched only on demand; national Atlas loading requests none of the 37 state payloads.

## Verification

- Full composed JSON equality against immutable V62: **453 records and 667 connections**, including all sources, status/uncertainty fields and edges; not just count equality.
- Initial index-selected CSS/JS: **990,093 → 817,400 bytes**, a **172,693-byte / 17.44%** reduction. This is uncompressed local payload size, not measured network transfer or browser load time. Historical files in the deployment archive are not initial page requests.
- All original research snapshot tables remain; browser derivative matches its explicitly selected subset exactly.
- Icons present alongside labels in filters/legend/state counts. No external icon library, font or image request added.
- Geometry paths match V62 exactly for Kaduna, Lagos, Niger and Borno, both state and available city views. A warm filter redraw makes no new Mercator log/projection calls; changing counts and zero-city availability remains correct; priming a new payload invalidates the cache.
- Node/VM sample of 20 warm redraw preparations per state: Kaduna 296.68 → 1.31 ms; Lagos 761.26 → 0.88 ms; Niger 76.87 → 0.45 ms; Borno 141.65 → 0.62 ms. These are a local CPU sample, excluding DOM insertion, layout, paint, network and device differences; no browser-speed percentage is asserted.
- Passed `test-category-performance.cjs`, `test-game-lazy-route.cjs`, `test-delivery.cjs`, `test-ui-uplift.cjs`, `test-populated-zoom.cjs`, `test-state-urban-rollout.cjs`, `test-map-nameplate.cjs`, `test-atlas-navigation.cjs`, `test-engine.cjs` and changed-module syntax checks. The new route test initially had a missing harness brace, corrected before it passed; no app workaround.
- The lazy-route test covers no Games fetch/save read on Atlas, pending route cancellation, warm return, load failure and narrow retry. Original game engine checks still pass.

## Limits and next work

Supported control-browser capability is unavailable in this managed Sites environment. Per the Sites skill, no improvised browser, preview server or installation was used. No new rendered desktop/mobile/screen-reader/touch/pen/overflow check, contrast measurement, network timing, FCP or LCP claim. P013 remains partial. A fresh supported browser check of icon sizing and actual load/interaction timing is the next verification step.

This pass does not change the four unresolved urban associations, ADM2 availability, entry evidence, WordPress, sharing, hosting/domain settings, Supabase access, or schedules. Native saved/deployed identifiers and exact archive verification are recorded in the canonical shared ledger after publication.
