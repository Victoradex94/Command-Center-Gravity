# Administrative layer audit and populated zoom — V59

Direct official API reads15Oct2026 (web tool, no keyword queries):
https://www.geoboundaries.org/api/current/gbOpen/NGA/ADM0/
https://www.geoboundaries.org/api/current/gbOpen/NGA/ADM2/
https://www.geoboundaries.org/api/current/gbOpen/NGA/ADM3/
https://www.geoboundaries.org/api/current/gbOpen/NGA/ALL/
Lowercase /all/ failed; official uppercase /ALL/ succeeded and lists only
ADM0/ADM1/ADM2. ADM3 direct open inaccessible; no ADM3 layer advertised in
that current gbOpen Nigeria listing. This is not worldwide ward-data absence.

ADM0: NGA-ADM0-39225661, country boundary,1unit,GRID3,represented2022,CCBY4.
ADM1: already uploaded37states/FCT. ADM2: NGA-ADM2-59680162,774LGAs,
GRID3,represented2022,CCBY4. LGAs are not city footprints; ward/ADM3 geometry
and unit conventions require another qualified source. No administrative
level is inferred from the urban footprints. No new record-to-LGA attribution
from city association alone.

Advertised direct simplified GeoJSON downloads:
https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/NGA/ADM0/geoBoundaries-NGA-ADM0_simplified.geojson
https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/NGA/ADM2/geoBoundaries-NGA-ADM2_simplified.geojson
Connected GitHub file reads at9469f09 returned GitLFS pointer bytes, not
geometries. Country/LGA overlays are not imported. User download/upload
remains needed through current supported access. No workaround attempted.

Implemented available second zoom: positive-entry state→positive-entry urban
footprint. Selected footprint provides projection bounds, state context is
clipped toviewport; Back to[state] returns to state overview. This is urban
focus, not an implemented ADM2/LGA layer. All state geographic SVG canvases
explicitly retain dark#171717 surround, light page and existing fills.

Zero matching entries: national state shapes have no activation data/tabstop;
state/city dropdown choices disabled; navigation skips zero-entry states;
state/city selection handlers recheck current nongeographic filters. Existing
selection filtering tozero falls back to national map without fetching/zoom.
Urban zero-count footprint/label stays context-only,aria-disabled,noactivation
or tabstop. Source urban geometry without a matching entry is not a zoom target.
Counts still reflect directory associations, not population/event frequency.

Tests cover direct handlers, URL/filter outcomes, state→urban→state projections,
nozero-state fetch,zero-city inertness,filter-tozero fallback,and unchanged
453/667. Existing state navigation assertion updated: wrap fromAbia nowYobe
because Zamfara haszeroentries. Native/package/VM checks do not establish
fresh rendered/mobile/touch/screen-reader behavior.
