# Preview 61 — map nameplate

15 October 2026. User requested a visible top-left nameplate inside the map boundary, changing with the current country, geopolitical zone, state or city view.

Replaced the old absolute caption with one reserved first row within the map-stage boundary. Explicit light text on the existing dark background, wrapping long names, full available width and normal flow keep it out of the geographic drawing and controls. Mobile flex order keeps it first; filters follow. Name uses city, then populated state, then zone, then Nigeria; the separate layer label distinguishes Lagos city from Lagos state. Filter-to-zero national fallback reads Nigeria. aria-live polite/atomic announces changes. Source CSS rules implement this layout; no fresh visual screenshot claim.

Fresh basis GitHub main159d5a7ba7cc14e315e82a066650510eac66d200, Sites60 source89e51a88bbf360f14fa638e3e66956fe0e3f0802; current canonical ledger read through DB121 and preserved. No research/database edits. Tests: nameplate country/zone/state/city/fallback/reset/placement/uniqueness, populated zoom, state navigation and URL navigation;453entries/667connections unchanged. Deferred loading and compressed generated data retained. Supported control-browser remains unavailable, so desktop/mobile rendered visibility/overflow not independently verified. No WordPress or audience changes.
