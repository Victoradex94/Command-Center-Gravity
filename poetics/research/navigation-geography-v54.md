# Preview 54: navigation reliability and geography registry

Implemented from the 15 October comparison-study priorities. The Atlas visual system and original records are retained.

- Atlas view URLs carry record, map/list/connections view, region/city, categories, documented year, format, search, panel and street/outline choice. Unknown IDs and invalid filters are normalized. City-only links synchronize parent geography.
- Selecting records and discrete filters creates browser-history entries. Search typing replaces the current entry. The application handles `popstate` as well as hash navigation; initial hydration replaces/canonicalizes its URL and does not create a new history entry.
- Copy link uses the Clipboard API when available, with a visible selectable-URL fallback. It copies the current restricted-site URL; sharing the link does not grant access.
- Surprise me uses the full active predicate, including selected state/city. Empty selections do nothing. A compact context line displays active scope.
- Geography registry records native SVG coordinate space separately from geographic WGS84 layers. Existing GeoNames centres and uploaded OSM Kaduna state/centres retain provenance, licence, vintage/unknown values and review qualifications. The Kaduna renderer consumes the registry geometry. No new geometry, geocoding, poetry entries or urban boundaries are inferred.
- This is a foundation for a shared geography pipeline, not a nationwide mapping-engine migration. National MapSVG and existing street embeds remain. Kaduna urban extents are still unavailable. Native-SVG layers must not be interpreted as longitude/latitude.

Verification: URL/history/restore and malformed-link harness; repeated filtered random selection; geometry validation; prior map/state/zone/UI-guard checks. Dataset remains 453 records / 667 relationships. Browser history tests are a simulated window/history harness, not actual rendered browser or mobile QA. Actual Back/Forward, clipboard permissions, focus/scroll behavior, screen readers and mobile layout require an independent fresh preview check.

No Supabase writes, editorial-intake backend, permissions changes, automatic GitHub/Sites synchronization or live WordPress changes. Drive remains the canonical working ledger; existing database reconciliation work is separate.
