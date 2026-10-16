# V66 — one aligned filter row

16 October2026. User screenshot directly inspected: Format had wrapped onto a full-width second row, while Categories sat above the other control baselines. User requested all filters on one line.

Opened latest Sites source `51931260ad40ce6925d88ddf4ef8bd3158de7b88` (V65) through the supported helper. GitHub main starting checkpoint `25deab606b46ddec18bbab65e373163b43aadff0`. Fresh canonical Drive ledger read through the coordinator's EV099 material and the V65 run; no conflicting app edits observed.

Placed Categories, Zone, State, City/location, Documented year and Format in one six-column grid row below the existing Filters/Clear all heading. Labels use the same baseline, spacing and control height. Each column keeps at least96px; when the map panel is narrower, this row alone scrolls horizontally. The heading stays stationary. Categories remains a multi-select disclosure, with choices below its own selector when opened; it no longer expands its selector to the full row. Filter collapse, parent/child selection logic, clear/reset, URLs, source notes and the V65 non-overlapping selection card remain intact. Existing Vic’Adex colours and fonts retained.

Passed existing syntax, UI-uplift, zone/category, map-attribution/clutter, Atlas-navigation and delivery checks. Composed453entries/667connections unchanged. No new tests added for the small reversible layout edit. Fingerprinted assets and immutable V66 entry updated.

Limits: uploaded screenshot inspected, source/package checks only. The preceding V65 browser attempt failed UNAVAILABLE and the managed preview failed its proc mount before health. No infrastructure recovery observed; no repeated initialization or alternate server/browser workaround attempted in this pass. Fresh rendered wide/narrow layout, actual swipe/touch, keyboard horizontal scrolling and screen-reader checks remain pending. P013 stays PARTIAL. Restricted audience retained; no live WordPress, database, access, domain/hosting policy or schedule changes. Deployment/source identifiers and exact canonical append readback recorded after publication.

## V67 alignment follow-up

User asked to check All categories relative to the other fields. Source audit found global `label select{margin-top:6px}` still applied to the five native selects; the Categories summary value had margin0. The six-column wrapper alone did not reset that inherited rule. Added margin0 to the scoped filter-select rule, aligning label-to-control spacing with Categories. Existing42px heights retained. This corrects the missed cascade in V66. Same checks and visual-verification limits apply; no data, behaviour or permission changes. V67 source/deployment/ledger readback recorded in the canonical run.
