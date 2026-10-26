# Ogbomoso minimum viable map

## Map decisions

- Use an original, not-to-scale diagram for named Ogbomoso places. Do not present diagram positions as latitude/longitude, surveyed coordinates, walking directions, or a complete street map.
- Show the LAUTECH Main Gate, Under-G Gate, and Kuye as approximate campus-area groupings. The university describes the first entrance on Old Ogbomoso–Ilorin Road and identifies the second gate and nearby areas; it does not establish the diagram's distances or exact marker positions.
- Keep Sifax Hall in the Atlas/game venue list as a documented 2015 Words on Rampage venue, but do not plot it. The reviewed event source does not establish its exact location or current operation.
- Keep the named road shapes as original schematic strokes. The Old Ogbomoso–Ilorin Road label is supported by LAUTECH's campus directions. A Streets of Nigeria directory reports `name=Stadium Road` and `highway=residential` from OSM tags. Its page is linked as a data index, not treated as proof of the SVG stroke's alignment. OSM way endpoints were inaccessible to the research browser during this verification, so unverified way IDs and the unsupported unnamed connector were removed.
- The separate OpenStreetMap view is for area context, with no venue marker. Its wider bounding box is intended to include both LAUTECH's published campus locator (8.133333, 4.266667) and the northern campus/Stadium area represented in secondary locality sources; no gate is placed at either point. The schematic displays © OpenStreetMap contributors and links the ODbL notice. It is an adaptation, not a traced street geometry.
- Use original vector shapes only. No Google/Waze/OSM map tiles, historic photos, building imagery, or textures are copied into the game. Historic venue photos remain research references unless reuse rights are confirmed.

## Source cross-check (26 October 2026)

- LAUTECH's current campus directions page gives the campus locator as 8° 8′ 0″ N, 4° 16′ 0″ E (8.133333, 4.266667), says the first gate is on Old Ogbomosho–Ilorin Road, and says the second/Under G gate leads toward Under-G, Nurudeen, Stadium, and Kuye. The coordinate is campus-level context, not a coordinate for either gate or for Kuye; the diagram therefore keeps all place markers schematic.
- The Stadium Road directory page explicitly identifies its data as © OpenStreetMap contributors and lists the OSM tags `highway=residential` and `name=Stadium Road`. It supports the name only; the original schematic stroke is not an OSM alignment.
- OSM's copyright page states the data is ODbL, requires visible credit to OpenStreetMap contributors and a clear ODbL notice, and explains that adaptations of OSM data must be shared under the same license. The interface links that page next to its attribution. The schematic uses only the cited road-name fact from OSM-derived data; it does not copy OSM geometry or tiles.

## Sources

- LAUTECH, campus directions: <https://www.lautech.edu.ng/de/node/115>
- LAUTECH, published campus locator and gate relationships: <https://lautech.edu.ng/index.php/contact-us>
- Streets of Nigeria, Stadium Road page and OSM tags: <https://nigeria-streets.openalfa.com/streets/stadium-rd-ogbomosho-north-oyo>
- OSM-derived Ogbomoso street-name index: <https://osm2cdr.com/en/map/town/ogbomosho-27565054/>
- OpenStreetMap copyright and ODbL: <https://www.openstreetmap.org/copyright>
- Vic'Adex, historical Words on Rampage / Sifax Hall account: <https://vicadex.com/portfolio/open-mic-ogbomoso/>
- Independent 2015 event announcement, which documents an advertised campus venue but does not grant image reuse rights: <https://myfernandez.com/2015/05/19/lautech-poets-presents-words-on-rampage-a-laupoetic-open-mic-event-taking-place-in-nigeria-dont-miss-it/>

## Verification status

The focused regression test checks record IDs, omission of unsupported venue coordinates, Sifax's unplotted state, source/licence labels, escaped Atlas names, Ogbomoso-origin transit rendering, preservation of the Lagos renderer, the full simulation API after all lazy game modules load, and accessible map-view switching. Its UI assertions use a DOM stub.

On 26 October 2026, the local branch was loaded in the in-app browser. That rendered check exposed a real integration fault: `gamemap.js` replaced the full `PoeticsLivingSim` API with its older helper copy, so `enhanceScene` threw before the map button was wired. The map module now keeps its helper API under `PoeticsMapSimulation`; a browser rerun opened the map and switched between the game scene, named-place schematic, and live OSM reference. Visual inspection led to an additional layout correction so the schematic scrolls with the dialog rather than creating a nested map-card scrollbar, and the OSM caption sits outside the iframe. The live OSM embed loaded with its contributor credit. This is desktop preview evidence; mobile browser QA remains outstanding.

After those code and test changes, all 48 `test-*.cjs` files passed on the branch, including the focused Ogbomoso regression test. The fast-startup and delivery checks measured 676,335 raw startup bytes, 221 bytes under the strict 676,556-byte ceiling. The changed game modules remain lazy assets; their content-addressed files and game asset list were fingerprinted.

An approved guarded sync subsequently copied the branch build to LocalWP staging and retained backups of overwritten files. The final sync verification checked 325 files, changed 10, and passed all 22 release checks; startup remained 676,335 bytes. Browser review on staging confirmed the Near Me location-fallback dialog and typed Ogbomoso lookup. This remains LocalWP staging evidence, not a public deployment. Mobile browser QA of the map remains outstanding.
