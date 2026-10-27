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

## Anchor evidence and confidence (rechecked 27 October 2026)

| Anchor | Evidence currently verified | Confidence and rendering decision |
| --- | --- | --- |
| LAUTECH Main Gate | The university's Contact page identifies the first gate on Old Ogbomoso–Ilorin Road. | High confidence in name/access relationship; exact gate coordinates are unverified. Use a schematic marker only. |
| Under-G Gate | The same university page identifies the second entrance as Under G gate. | High confidence in name and identity; no surveyed marker or routing claim. |
| Kuye | The university names Kuye among the areas reached through the second gate. | High confidence in the named access relationship; its boundary and point location remain unverified. Diagram placement is illustrative. |
| Sifax Hall | The current Open Mic Ogbomoso archive says the 2015 event moved from the advertised 250LT to Sifax Hall, LAUTECH. | First-party historical account; precise address and current operation are unverified. Retain the venue record without plotting it. |

The university's published campus coordinate is campus-level context and is not assigned to any of these four anchors. The Stadium Road name and residential classification were rechecked on the OSM-derived Streets of Nigeria page; this does not verify the alignment of the original diagram stroke. No OSM geometry extract is redistributed by this change. Visible contributor credit and the linked ODbL notice remain beside the schematic and separate OSM reference view.

## Historic photo research and reuse ledger

| Candidate | What is established | Reuse decision |
| --- | --- | --- |
| Words on Rampage album linked from the Open Mic Ogbomoso archive | The current archive links an album as historical event evidence. Individual photographs, photographer ownership, dates and reuse grants have not been verified. | Excluded from game assets pending confirmed rights for each selected image. |
| Independent announcement dated 19 May 2015 on MyFernandez | Its link is retained by the archive; the announcement could not be fetched during the 27 October recheck. No image licence or reuse permission is established. | Excluded. Do not infer image rights from an accessible article or event invitation. |

The map and buildings use original vector/procedural art. No historical photograph is included in this release.

## Verification status

## City-map coverage pass (26 October 2026)

- The bundled Atlas snapshot contains 34 `Place`, `Venue`, `Event`, and `Event series` records across ten offline cities: Abuja, Calabar, Enugu, Gombe, Jos, Kano, Lagos, Maiduguri, Ogbomoso, and Zaria. The simulation renders all of these city-associated records rather than drawing old unsourced venue coordinates for non-Ogbomoso cities.
- Non-Ogbomoso city maps use an original place diagram grouped by the database city. Diagram positions do not represent addresses or directions. The OSM link opens a city-level reference using the existing city-centre locator; no Google Maps content or coordinates are copied into the diagrams.
- Ogbomoso keeps its source-backed gate and road-name schematic. Database places and event records without a source-backed position appear in an explicitly unplotted list, including Sifax Hall, 250LT, Lion’s Lounge, Nurudeen, and the university venue record. They are not assigned invented pins.
- Exact street names and venue positions outside that Ogbomoso evidence remain research items. Google Maps can be consulted visually, but its terms prohibit copying map content and using it to create or augment another mapping dataset; do not persist Google-derived coordinates into these independent diagrams. Use official records or a deliberately selected reusable data source for future precise points.
- Focused checks: `test-ogbomoso-map.cjs`, `test-living-sim.cjs`, and `test-sim-polish.cjs` pass. These are code/data checks, not mobile browser visual QA.

The focused regression test checks record IDs, omission of unsupported venue coordinates, Sifax's unplotted state, source/licence labels, escaped Atlas names, Ogbomoso-origin transit rendering, preservation of the Lagos renderer, the full simulation API after all lazy game modules load, and accessible map-view switching. Its UI assertions use a DOM stub.

On 26 October 2026, the local branch was loaded in the in-app browser. That rendered check exposed a real integration fault: `gamemap.js` replaced the full `PoeticsLivingSim` API with its older helper copy, so `enhanceScene` threw before the map button was wired. The map module now keeps its helper API under `PoeticsMapSimulation`; a browser rerun opened the map and switched between the game scene, named-place schematic, and live OSM reference. Visual inspection led to an additional layout correction so the schematic scrolls with the dialog rather than creating a nested map-card scrollbar, and the OSM caption sits outside the iframe. The live OSM embed loaded with its contributor credit. This is desktop preview evidence; mobile browser QA remains outstanding.

After those code and test changes, all 48 `test-*.cjs` files passed on the branch, including the focused Ogbomoso regression test. The fast-startup and delivery checks measured 676,335 raw startup bytes, 221 bytes under the strict 676,556-byte ceiling. The changed game modules remain lazy assets; their content-addressed files and game asset list were fingerprinted.

## Review and staging state

Victor subsequently approved a staging-only sync of `codex/ogbomoso-map-mvp`. The guarded sync completed at 22:23:15 Africa/Lagos on 26 October 2026 after its 22 required checks passed: 331 files verified, 15 files changed, and overwritten files backed up in `poetics-sync-backups/20261026T212315201996Z` beside the worktree. The authoritative sync record is `poetics-sync-status-codex-ogbomoso-map-mvp.json` beside the worktree. It records base commit `c90751f41f30129ae0bae15a7c4d4eaf151eb341`; the map changes are still uncommitted working-tree changes, so that commit alone does not identify the staged build.

Those fingerprints describe the older branch, not the current release candidate. On 27 October, a fresh comparison found nine staging files differed from that branch. The staging game asset list matched refreshed GitHub main `a1302411015a4ef30461a2bb13ef72fd2854a532`, including the lazy pronunciation dictionary from PR #30. The older branch must not be copied wholesale over this newer build.

## Current release candidate and completion audit (27 October 2026)

The review checkout `ogbomoso-current-main` starts at `a1302411015a4ef30461a2bb13ef72fd2854a532`. It carries only the map additions, source/evidence notes, regenerated delivery references, and relevant regression updates. Current-main app, dictionary, loader, Near Me, and other released fixes are retained. At review completion this candidate was unpublished. Victor subsequently explicitly authorized pushing it to main and syncing LocalWP staging on 27 October 2026; the guarded sync receipt records the resulting deployed commit and backup.

Visual QA used a loopback-only local HTTP preview in Chrome after the in-app staging webview failed to attach. It exercised the actual generated game modules through the portal, Ogbomoso journey, full district map, Places schematic, online OSM reference, and Game scene. Desktop (943 × 834) and mobile (390 × 844) views were inspected. A mobile readability defect led to larger anchor/road labels and a relationship note that wraps below the SVG. The final online OSM embed loaded with its contributor credit. Direct OSM-area and copyright/ODbL links remain outside the iframe so the provenance survives a failed embed. Escape closed the map and returned focus to the opener. A Maiduguri journey rendered its three Atlas records; no console errors or warnings were observed during that run.

Evidence screenshots are saved beside the checkout in `ogbomoso-map-review-evidence/`: `desktop-places.jpg`, `mobile-places.jpg`, `mobile-osm.jpg`, and `mobile-maiduguri.jpg`. These prove local candidate rendering, not staging deployment or physical-device touch behaviour. Some CDP mouse/selector operations timed out while the 3D scene was visible; keyboard/native controls and fresh state checks completed the map switches. An existing `Switch Poet / Log In` control was unresponsive, and current-main `app.js` contains its button markup without a corresponding handler. This app file is unchanged by the map candidate; reloading and entering through the portal restored the QA save.

After the final visual fixes, all 48 `test-*.cjs` suites passed. Startup is 671,345 raw bytes, 5,211 bytes below the strict 676,556-byte limit. `git diff --check` passed. The generated delivery manifest records `living-sim.25a7618d03dc.js`, `gamemap.98c94cae83a8.js`, `world.6c630917e916.js`, and `game-assets.1494cbce307f.js`; `dist/index.html` SHA-256 is `fd38fc599bdb8bc73689cd62785ef14565964c85d92ff2e6f0144a889f228011`. Superseded untracked hashes from this review were removed; existing tracked assets were preserved.

| Goal requirement | Authoritative evidence and disposition |
| --- | --- |
| Verify four named anchors; qualify uncertain positions | Anchor table above, fresh university/archive reads, `cityLayouts.Ogbomoso`, and the rendered schematic. Three approximate markers; Sifax explicitly unplotted. |
| Correct unsupported coordinates/street claims | No latitude/longitude on schematic anchors; campus coordinate remains context only; original strokes explicitly lack geographic alignment. Stadium Road's name is supported by the cited OSM-derived tag listing. |
| Provenance, confidence and OSM licence | Per-anchor evidence table, linked road sources, visible OSM contributor/ODbL links in both schematic and map dialog, plus loaded reference-map credit. |
| Original map/building art | Changed source renders original SVG/procedural shapes; no map tiles are packaged as game art. The online OSM iframe remains a separately attributed reference. |
| Historic venue-photo research | Separate rights ledger above. No confirmed grant was found and no historic image is included. |
| Rendered map and regression verification | Saved desktop/mobile screenshots, observed map switching/keyboard focus, and 48 passing suites against the final candidate. |
| Preserve unrelated behaviour | Candidate is based on current main; `app.js`, rhyme game, pronunciation index, loaders and Atlas data are unchanged. Existing baseline issues are distinguished above. |
| Reviewable release with publication held | Checkout diff, generated manifest, source notes and evidence bundle completed before release. Explicit authorization for main and LocalWP staging was received on 27 October 2026. |
