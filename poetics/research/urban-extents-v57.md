# Africapolis urban-extent pilot — Preview 57

The user downloaded the WFS response using the capabilities-confirmed layer
`africapolis:Africapolis_2020` and uploaded `nigeria-urban-extents-2020.geojson.json`.
The full original remains Library file `libfile_ce185536a008819194fdbf82381e52cc`.
Its SHA-256, byte size, extraction timestamp and country counts are recorded in
`geography/africapolis-pilot-manifest.json`. It contains 1714 MultiPolygons, of
which 1465 have ISO3 NGA. Other countries must not be treated as Nigerian nodes.

This release integrates only Kaduna (`Africapolis_2020.4291`) and Zaria
(`Africapolis_2020.9129`) with the previously sourced Kaduna state geometry.
Exact selected source features are retained in
`geography/africapolis-kaduna-zaria-2020-source.geojson`; the reproducible
preparation script accepts the original upload as input. Runtime coordinates
round to six decimal degrees, without simplification or dropped rings. All
26474 positions and 48 holes are retained. Both source city-centre locators
fall inside their respective urban footprints. All layers share the same
geographic projection; urban paths are visually clipped to the state outline.
No alignment to hand-drawn SVG state coordinates is fabricated.

UI: teal urban footprints, orange selected/focused footprint, keyboard Enter
or Space/click city selection, original city-centre labels/counts, explicit
2020 vintage and CC BY4 attribution to OECD/SWAC and e-Geopolis, downloadable
Kaduna/Zaria GeoJSON with provenance. These are settlement footprints, not
legal city limits or current2026 boundaries. State source tag remains2013;
export date2026 does not imply current state-boundary verification.

Documentation read: https://docs.digitalearthafrica.org/en/latest/data_specs/Africapolis_urban_specs.html
Capabilities uploaded separately: `Pasted text(4).txt`, Library
`libfile_557c699b5e1081918698f83de85449e0`, confirms qualified case-sensitive
layer name and JSON support. Prior unqualified/lowercase request returned
unknown feature type; it is not evidence that the dataset is absent.

Checks: source IDs/country/ring and coordinate integrity, centre containment,
projection bounds, registry metadata, state clipping, downloadable GeoJSON,
keyboard event binding and unchanged453/667 graph. No legal-boundary audit,
full polygon topology audit, browser rendering, mobile/touch or screen-reader
verification is claimed. Other states need georeferenced state outlines and
reviewed spatial/name mapping before rollout. Full urban catalogue not added
to Atlas counts; geometry is a background layer, not new poetry evidence.
