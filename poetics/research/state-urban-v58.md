# Geographic state views and urban footprints — V58

User-uploaded geoBoundaries-NGA-ADM1_simplified.geojson is827817bytes and
SHA256edd28050c7f1ae40471424605f74e4d2df83502e4f301089761ae18f8ae2fbbf,
exactly matching the previously read Git LFS pointer. Original Library file
libfile_9b5efc75e93c81918b7e83699d691d5b. All37unique ADM1 units validated;
source FCT name normalized explicitly to Atlas Federal Capital Territory.
Official metadata: GRID3 via geoBoundaries, represented2022, CCBY4;
https://www.geoboundaries.org/api/current/gbOpen/NGA/ADM1/ .

Preparation pairs these coordinates with the original1714-feature Africapolis
upload, restricting candidates to NGA and the prior complete39-city audit.
30normalized names qualify using source centroid in expected state or existing
city centre contained in both expected state and urban footprint. Five other
qualified source areas are retained with source names: Ile-Ife/Ife1,
Ilesa/Ilesha,Ogbomoso/Ogbomosho,Lafia/Lafia1,Yola/Jimeta. Yola is explicitly
a containing-area association, not a Jimeta rename. Lagos footprint centroid
lies outside Lagos state; the existing sourced Lagos centre is inside both
Lagos state and the footprint, supporting cross-state interpretation. All
displayed footprints are clipped to the selected state's geometry. This is
not an exhaustive audit of every cross-state urban border.

35selectable footprint associations, four unresolved: Awka,IkotEkpene,Karu,
Owerri. Unresolved cities remain selectable in the city filter; no made-up
polygon or newly inferred centre. No new poetry profiles/relationships.
All37state views use geographic state geometry; national map remains the
existing approved Nigeria-onlySVG. State and urban shapes share Mercator
coordinates, not a guessed SVG-to-lonlat transform.

37content-addressed lazy JSON payloads total5036614bytes; largest585214bytes.
No state payload fetch at national level. State selection fetches only that
state and caches the validated response; pending requests deduplicated,
stale state request cannot redraw a different state, failure visible with
refresh instruction. Urban outlines and labels support click/Enter/Space,
filter connections, source names/vintages/CCBY4 attribution. No street embed.

Rendering derivative uses RDP .0001degree (~11m maximum planar deviation
before six-decimal rounding), every ring retained, winding and1%area guard
per ring, fallback to original ring on guard failure. Existing city-centre
containment is checked after simplification and full original feature used
on membership change. Original full uploads remain available; derivatives
are for overview rendering, not legal/current-boundary or precise topology
analysis. No full polygon topology audit claimed. Geometry files contain no
poetry records. Reproduction script: scripts/prepare-state-urban-layers.py;
manifest/review output: research/geography/state-urban-rollout.json.

Tests cover37statefile hashes/byte sizes/ring validity/projection bounds,
35paths/fourunresolved cases, category controls, cross-state and Jimeta labels,
lazy cache/request deduplication, actual index-selected modules/async filter
integration and unchanged453entries/667connections. Existing navigation,
top-five city filters and legacy pilot checks pass. DOM/VM checks are not
fresh browser/mobile/touch/screen-reader QA; those remain open.
