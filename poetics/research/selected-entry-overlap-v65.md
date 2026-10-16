# V65 — keep the selected entry clear of map controls

16 October 2026. User supplied a screenshot showing the selected-person card covering the top-city shortcuts and reaching toward the map source credits.

Opened the current Sites source with the supported helper at `a6f7c513f268119c4bfcf76b3a99723ea8348199` (V64). Starting GitHub main: `b9aa87bebfbd1c72e9433b0f487db2718af623f9`. Read the current canonical Drive ledger, including coordinator contributions through EV099. No research/data/database or migration changes in this pass.

The cause was the legacy `.map-floating-profile` positioning: absolute, bottom80px against the entire growing map stage. The map stage now also contains city controls and attribution, so the card covered those controls. The selected entry is now an aside with a scoped `.map-selection-preview` layout in normal document flow. It reserves its own row before the city shortcuts, has no absolute offsets, wraps long names, and is visible within the flow at narrow widths. Source links and profile information remain available. Existing Vic’Adex colours, typography, map layers, nameplate and consolidated credits are retained.

Passed the existing map-attribution/clutter, UI-uplift, Atlas-navigation, syntax and delivery checks. Full composed data remains 453 entries and667 connections. Current index and immutable V65 entry use fingerprinted assets.

Verification limits: the uploaded screenshot was directly inspected. Fresh connected-browser initialization returned `UNAVAILABLE: Sheep MCP session closed: RPC INTERNAL`. The managed preview supervisor failed before health with `bwrap: Can't mount proc on /newroot/proc: Operation not permitted`; status was checked. No replacement server/browser was installed or used. The source change removes the overlapping positioning, but a new rendered desktop/mobile confirmation is pending. P013 remains PARTIAL. No fresh touch, screen-reader, overflow or contrast claim. Native saved/deployed identifiers and readback results are recorded in the canonical ledger after publication. Restricted audience retained; no live WordPress, database, permissions, hosting/domain or schedule changes.
