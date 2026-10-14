# Kaduna / Zaria uploaded OSM export review

Received 14 October 2026. Original export retained unchanged as `kaduna-zaria-osm-export.geojson`.
184716 bytes; SHA256 `b99ab84a9e53e11bd94ce47854423664364aade90104afaf444edf69c3faa151`.
Overpass Turbo export timestamp: 2026-10-14T20:35:21Z. OSM data, ODbL; © OpenStreetMap contributors.

| Object | Geometry | Tags / classification | Use |
| --- | --- | --- | --- |
| relation/3709353 | Polygon | NG-KD; administrative level 4; source:ehealthafrica.org; source:date 2013 | Kaduna state outline |
| relation/3709376 | Polygon | Zaria; administrative level 6 | Excluded: does not establish requested city/urban extent |
| node/27565091 | Point | Kaduna; place=city | City-centre locator |
| node/501388581 | Point | Zaria; place=city; GNS source, legacy population fixme | City-centre locator; no population or history claim |
| node/2163706705 | Point | Kaduna; place=state; state relation label | Excluded |

No city-area polygons are present in this supplied export. It is not evidence of absence elsewhere in OSM. City areas remain pending. Do not rename the Zaria administrative polygon as an urban footprint or infer legal/current boundary accuracy from the export date.

The retained state polygon has one closed ring with 1930 positions. Both city points lie within it under a longitude/latitude point-in-ring test. All coordinates are finite and within geographic ranges. This is bounded structural/containment checking, not a full topology or legal-boundary audit.

For Kaduna's selected-state overview, the state polygon and city points use the same Web Mercator projection and fitted SVG viewport. The national MapSVG geometry is retained; no approximate affine overlay onto that unrelated SVG projection was attempted. The switch between the source state outline and the national map is explicit. Existing evidence/category/city counts are calculated from the original directory; no new poetry records, relationships, residence, venue or attendance claims.

City markers expose their existing city filters and retain state context; the separate street-map option remains accessible. City-area outlines remain OPEN. External data retrieval blockers are not claimed resolved: the upload supplied readable bytes.
