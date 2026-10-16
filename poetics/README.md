# Poetics Atlas & Games

**Current handoff: Version 76 · 16 October 2026**

Poetics is a static, browser-run Nigerian poetry Atlas and a separate fictional poetry-life simulation. This folder is the working application snapshot in the private GitHub repository `Victoradex94/Command-Center-Gravity`, under `poetics/` on `main`.

Version 76 is the latest source mirrored here. Its Sites source checkpoint is `e22287464f447cfec4f664c3b9ddf7be7b870b2e`; the matching source and build instructions are in current GitHub main. The Atlas test suite verifies **453 records and 667 source-linked relationships**.

**The dated notes below the current handoff are a historical change log. If an older note conflicts with this section, use this section as current.**

## Run it locally

Requirements: Git (or download the repository ZIP), Python 3, and a modern browser. Node.js is needed only to run the checks. There is no `npm install` step.

### Windows PowerShell

    git clone https://github.com/Victoradex94/Command-Center-Gravity.git
    cd Command-Center-Gravity/poetics
    py -3 -m http.server 4173 --directory dist

Open `http://localhost:4173/#/atlas` in your browser. Leave the terminal open while using the preview; stop the server with Ctrl+C.

### macOS or Linux

    git clone https://github.com/Victoradex94/Command-Center-Gravity.git
    cd Command-Center-Gravity/poetics
    python3 -m http.server 4173 --directory dist

Open `http://localhost:4173/#/atlas`. Serve `dist/` over HTTP; opening `index.html` as a `file://` URL will break data fetches.

To use GitHub without cloning, sign in, open the `poetics/` folder, and use GitHub’s web editor. For local previews or tests, download the repository ZIP and follow the same server step.

## What is in the app

- `dist/index.html` is the entrypoint. Hash routes are `#/atlas`, `#/games`, `#/about`, and `#/submit`.
- `dist/*.js`, `*.css`, and JSON files contain the Atlas, map, game, evidence and presentation assets. Edit the readable, non-fingerprinted files (for example `directory.js`); the entrypoint loads fingerprinted copies.
- `research/` contains supporting query logs, matrices and claim reviews. The shared Drive Markdown ledger remains the canonical task ledger; read its latest copy before research or data edits: https://drive.google.com/file/d/13qDg2XVdUM5ZAbplLoeNT5X6hB89cnSq/view
- `wordpress/poetics-preview/` is packaged source only. It is not a live WordPress deployment.

The Atlas keeps historical records and their source links separate from the fictional game. Its state map uses Nigerian state boundaries. Detailed urban layers are available only where data has been prepared; where a detailed layer is missing or fails to load, the app falls back to the state outline. Africapolis urban extents describe built-up areas, not legal city boundaries.

The game’s save data stays in that browser’s localStorage and can be exported/imported as JSON. There is no account, cloud save, multiplayer server, or live submission backend. The Submit form makes a local draft; it does not publish an entry.

## Edit, check, and save your work

Start from the current `main`. The old `poetics-staging` branch is a Version 45 snapshot; do not use it as the base for new work.

Create a separate working branch before editing:

    git switch -c poetics-work

Edit the original non-fingerprinted sources. From the `poetics/` folder, regenerate entrypoint fingerprints and run the relevant checks:

    python scripts/fingerprint-assets.py
    node test-atlas-navigation.cjs
    node test-state-urban-integration.cjs
    node test-directory.cjs
    node test-delivery.cjs
    node test-engine.cjs
    node test-contribute.cjs
    node test-nigeria-gis.cjs

Commit your work and push the branch:

    git status
    git add .
    git commit -m "Describe the Poetics change"
    git push -u origin poetics-work

Keep source claims tied to evidence. Do not turn an announcement into a completed event, infer a residence or venue from an association, or collapse distinct name/venue variants without documentation. Do not represent fictional game events as history.

## Hosting and preview

The private GitHub repository is an editable source copy. It is **not connected to automatic hosting**. A GitHub commit does not update the restricted ChatGPT Sites preview, and the preview does not push changes back to GitHub.

Current restricted preview: https://poetics-vicadex-lab.vicadexconcepts.chatgpt.site/#/atlas

The preview is hosted separately through Sites and remains custom-access. This repository has no GitHub Pages deployment or independent production host configured. To keep working locally, the ChatGPT subscription is not needed once you can access the private GitHub repository. To host the app independently, choose and configure a static host for the `dist/` directory; that hosting migration has not been done.

Do not change live WordPress, domain, hosting, or visitor-access settings as part of local editing. Updating the Sites preview is a separate, deliberate publish step; reconcile the newest GitHub and Sites sources first and preserve the restricted audience.

## Version 76 performance update

Startup local asset references are reduced from 26 to 17 and raw bytes from 845,695 to 630,506. The new data bundle is a generated lossless derivative; all 453 records and 667 relationships match Version 75. Regeneration still uses only Python's standard library. Phone exploration actions now remain visible below the city rail. See [performance report](research/performance-v76.md), [measurements](research/performance-v76-verification.json), and [rendered QA](research/visual-qa-v76.md). No automatic GitHub-to-Sites deployment has been configured.

## Verification limits

Version 76’s navigation, data, map-fallback, contribution, game and delivery checks pass in the source checkout. Automated checks are not a full visual or accessibility review. Recheck rendered layout, mobile, touch, keyboard and screen-reader behavior on the host and devices you intend to support.

## Historical change log

## Dynamic revision — 12 October 2026

Animated fictional room, day/activity transitions, incoming wall posts, changing statistics and a skippable open-mic/slam performance dialog. Reduced-motion preferences suppress animations. Automated clock tests cover single timer, day/save updates, editor selection preservation, busy-state gating and hidden-page pause; map tests check real embed URLs and correct lat/lon ordering for both source-backed cities. Browser rendering and actual map-tile availability remain unverified.

## Visual life-sim & phone revision

Original low-poly WebGL neighbourhood with an avatar, moving fictional NPCs/bus, orbit camera, zoom, WASD/arrows and touch movement controls. Place buttons move the avatar and expose the existing writing/rest/work/performance actions. This is a visual prototype: collision/pathfinding, enterable interiors and full 3D multiplayer are not implemented. An illustrated fallback remains if WebGL is unavailable. No Lagos Life assets are copied.

The in-game phone opens a live poetry-wall feed with a touch-friendly original-poem composer. Direct phone entry: `#/games?phone`. The phone dialog fills a real phone viewport and uses safe-area insets; drafts and fictional posts are device-local. The existing owner-only preview can be opened from a phone signed into the owning ChatGPT account. No public sharing or cloud synchronization was enabled.

`node test-city3d.cjs` checks generated geometry/matrices, renderer draw wiring, a 390px canvas configuration, cleanup and phone route/feed/post wiring using stubs. This is not a real rendered WebGL/browser test. Phone touch usability, actual WebGL visuals and target-game resemblance remain review items.

## Ogbomoso regionalisation & expanded research

12 October 2026: the game district now specifically adapts the LAUTECH-area campus/gate/Under-G context, with an inland low-rise setting, campus greens, compounds and a neutral minibus. The generic waterfront/skyscraper/danfo template is removed. LadoTech, Under-Verse Court, Lion’s Lines and VerseMart are fictional game names. The district minimap is compressed gameplay geography; road bearings, distances and building placement are not measured or verified as a reconstruction of 2010. Other travel destinations do not reuse this district and display a local-research hold instead.

Google Maps was explicitly attempted through web retrieval and direct interactive browser navigation. Retrieval gave JavaScript-only content; the cloud browser returned ERR_BLOCKED_BY_CLIENT. Exact Google Maps inspection and street-level matching remain blocked. LAUTECH’s official contact page confirms the first-gate/Old Ogbomoso–Ilorin Road and second-gate/Under-G relationships. A Google Maps reference link is provided in the game, with the limitation disclosed.

Bauhaus-inspired art direction uses original geometric architecture/sculpture, red/blue/yellow accents, clear sans-serif typography and restrained composition; no museum artworks or third-party game assets are copied.

Atlas: 80 source-linked metadata records, 69 relationships and 12 claim sources, with 11 activity locations (10 cities plus Online). Geographic city-centre locators use GeoNames and do not identify private residences. Dates describe documented activity/source evidence, not inferred birth/founding dates. Announcements and programme billing remain labelled unconfirmed as attendance/occurrence. A discovery index retains 87 relevant leads from 117 initially found URLs; leads are not accepted claims. These exports are a prototype ingestion package, not replacement canonical research trackers.

Known evidence conflicts: the official LIPFest archive repeats incorrect edition dates for 2016–2018; use the contemporaneous 2018 programme for that edition. SLANG’s 2026 page gives two different start times; no exact time is imported. The old Port Harcourt poetry festival domain is parked; it is not offered as a functioning official resource. Contemporary venue references inspire fictional 2010 gameplay, without asserting they existed in that period.

## Neighbourhoods & squircle UI

Added selectable Under-G, LAUTECH Gate, Adenike and General destinations, blue area markers and full-map labels. Waypoints use adapted gameplay coordinates; no new survey claim. The controls, cards, navigation map and dialogs now use modern rounded/squircle surfaces (`corner-shape: squircle` with border-radius fallback). Touch targets remain at least 44px. Automated area tests confirm all four selectable coordinates and map labels. Real-device/rendered QA remains open.

## In-game opportunity notifications

Notification centre and unread badges in the game header and phone. Fictional open mics/slams, original-writing competitions and anthology calls use simulated-day deadlines and weekly refresh. Writing submissions preserve an immutable draft/author snapshot and resolve after the deadline through explicit game rules, with unread result alerts. Costs, expired calls and duplicate submissions are checked. No browser push permission, real-world posting, public submission or real-event alert feed is enabled. Old v1 saves remain compatible; imported opportunity data is validated. Automated tests cover schedule, expiry, costs, duplicate blocking, poem snapshot, results/read state and legacy saves.

## Canonical Atlas research integration — 12 October 2026
The private Atlas now defaults to the supplied Nigerian Poetry Archive & Ecosystem Research spreadsheet snapshot: 92 preserved alerts, 30 working profiles, 26 historical milestones, eight annual syntheses and ten research questions. Directory, timeline, evidence, synthesis and question views provide search, geography filters where applicable, row-level canonical citations and clickable evidence trails. Map / pilot retains the earlier independently source-linked dataset without merging incompatible histories or unresolved identities.
All alert original-source URLs are absent in the supplied ledger; alert dates are not event dates, and first evidence is not founding. Inferred timeline claims remain labelled. Phase 2 Google Doc returned PERMISSION_DENIED; its contents and corrections have not been incorporated. Connected account requires Viewer access before reconciliation. Snapshot omits mail IDs, message links and email addresses; upstream documents were read-only. No poems or copyrighted assets imported. `node test-research.cjs` checks counts, privacy, references, ID range expansion and initial UI rendering; browser visual/accessibility QA remains unavailable in this environment. No changes to game state or Vic’Adex production.

### User-named community coverage
Added five supplementary directory profiles for GoPoethick (likely Go Poetick spelling), Be Blessed, Griots and Bards, PHLS and ALS, with direct public source links and explicit provenance. Canonical 30 profiles/92 alerts remain unchanged. GoPoethick is a discovery lead because full-page retrieval was blocked. Be Blessed uses attributed participant recollection; PHLS uses a contemporaneous firsthand review; GAB uses organiser self-description; ALS uses a commissioned firsthand organisational account. No founding dates or current staffing inferred. GAB remains separate from Griots Lounge, PHLS from Port Harcourt Poetry Festival, and ALS from AWF/AIPFest. War of Words / WORDUP remains the canonical profile with its existing evidence trail. This is an initial expansion, not exhaustive coverage.

## Directory and mind map
Atlas now opens as a directory, with independent People / Places / Platforms visibility toggles, name/location search, geography selector, responsive cards and concise profiles. Sources/verification and research notes are expandable. Research tables and the geographic map are secondary views. The interactive SVG mind map follows one selected record’s sourced connections, offers six neighbours per page, keyboard selection and a corresponding textual evidence list. Filters apply to neighbours while keeping the selected centre visible; shared cities alone never create relationships.
Directory combines explicit canonical aliases with source-linked pilot records and supplementary entries. Adds source-attributed Olumide Holloway, Olumide Bisiriyu, Adedayo Agarau, Tobi Abiodun, Bogobiri House and four reported ALS co-founders. Canonical source documents unchanged. Deeper web research reviews the 2013 maiden War of Words organiser notice, Holloway’s programme chronology, the 2018 ALS/ALitFest report and Tobi Abiodun’s 2025 recollections. May mini-slam versus June maiden standalone event distinction is preserved. GoPoethick founder name variation remains unresolved; Be Blessed founding date and GAB chronology remain outstanding. No current role claims or event occurrence inferred from notices. Tests: directory identity deduplication, categories, every relationship endpoint/source, graph rendering/search and uncertainty checks. Browser visual/touch QA remains unavailable.

## Vic’Adex identity adaptation and national discovery pass
Atlas uses a restrained charcoal/ivory editorial treatment, warm accent, serif display hierarchy, squircle cards and Vic’Adex / 60 Seconds Poetry identification. Exact parent-site font/colour matching remains unverified: public text from both pages was accessible via search, but remote browser navigation failed with ERR_BLOCKED_BY_CLIENT and direct HTML fetch returned 403. No claim of pixel-exact matching; no parent-site assets reused.
National discovery snapshot adds 17 source-attributed profiles, including Loudthotz, Taruwa, Freedom Hall, COAL Jos, Enugu BookJam, Third Space Kano, Pen Warriors Ilorin, Purple Silver Makurdi, Rovingheights multi-city, Benin festival open mic, SOS, Eko Slam, PIN National Slam, ALS Slam of Champions, Mic Check, ANA Slam and YAGYDI UNILORIN. Retrieved source vs discovery-only status is explicit. All current schedules / application status remain unconfirmed. Directory adds Format filter distinguishing open mic/readings, spoken-word competitions and written poetry prizes. National coverage is not a census; weaker leads and retrieval failures are not evidence of absence. Cross-city platform notices retain their multi-city label. Third Space is a place/venue. Additional relationships retain their individual source and historical precision. Canonical records and game remain unchanged.
Final regional follow-up adds Vocal Ink’s 2017 Uyo showcase, Terra Kulture’s 2012 BasseyWorldLive / Naija Poetry Slam notice, and the 2012 Calabar Festival Slam notice: national snapshot now 20 profiles. These distinguish showcase/open mic/competition and retain notice-versus-occurrence limits; the claimed first national slam is not adopted. The Calabar hotel-name discrepancy is flagged and no exact location is mapped. Adds source-attributed Bassey Ikpi and Terra Kulture entries and three announcement relationships. Combined directory: 141 entries, 88 relationships.

## Map-first landing
Poetics home and Atlas now open on the Nigeria map. Removed the large hero and initial record-card wall. Compact search, three category toggles, Map/List/Connections switch, optional Filters, and an initially closed results panel. City selection opens associated entries; profile selection opens concise details with expandable evidence. Desktop uses a side panel; phones stack a shorter map and results. Existing city-centre GeoNames locators drive clickable count markers via Leaflet 1.9.4 and OpenStreetMap tiles; if Leaflet CDN cannot load, the OSM iframe and city buttons remain usable. No approximate hand-drawn country boundary. Unlocated and country-wide records remain searchable; a selected location without a verified city locator stays on the country map and is labelled. Map layers need internet. Browser visual/touch QA unavailable; data and interaction tests cover initial map, collapsed panel, selection, multi-city filtering, connections, empty state and reset. No new historical claims or game changes.

### Atlas navigation refinement — 12 October 2026
Added seven GeoNames-verified city-centre locators (Ibadan, Port Harcourt, Ilorin, Kaduna, Uyo, Makurdi and Benin City), bringing coverage to 17 centres. Source: https://www.geonames.org/search.html?country=NG&q= (reviewed 2026-10-12). These locate documented city associations, not venues or residences. Location filters now split multi-city associations into individual selectable cities. Added All Nigeria shortcut; List mode no longer duplicates results in a side panel. Existing data and UI stub tests cover these paths; rendered browser and phone QA remain unavailable.

### Nigeria-only GIS and standard profiles — 12 October 2026
The Atlas renders only Nigeria from a locally stored Natural Earth ADM0 GeoJSON feature. No Atlas basemap tiles, iframe, Leaflet or neighbouring-country geometry is loaded. Data is generalised 1:110m and public domain; source URL, Git blob SHA, licence and precision are stored in the GeoJSON metadata. City centres retain GeoNames attribution. Yola and Lafia bring locator coverage to 19 cities. The game map is a separate fictional experience.

Every directory entry now has a name, category, details, location, documented years with date meaning, media slot, grouped People/Places/Platforms connections, and sources/verification. Unknown years and missing relationships remain explicit. Profile and graph navigation resolve the same source-linked edges in both directions, including across active search/location filters. City locator relationships are marked as directory metadata associations; they do not establish residence, precise venue or attendance.

Additional research lives in directory-expansion.json/js, generated by scripts/expand-atlas.py, separately from the read-only canonical spreadsheet snapshot. Added Word Tour, Moses Abah (Oracle), WRR, Artmosphere, WriteHouse, Servio Gbadamosi, NuStreams, FOS, Freedom Spoke Words, AJ Dagga Tolar, UI Zoological Garden, Eko Literary Society, Kemi Bakare and UNIMAID Love Garden. Expanded existing Graciano, Be Blessed and Eko Poetry Slam entries. Word Tour dates remain unresolved; 2025 is the retrospective publication year. FOS founder/co-founder wording is attributed rather than reconciled by inference. Artmosphere's 2013 notice has conflicting edition-date wording. “Kemistry” remains separate from Kemi Bakare pending identity confirmation. Freedom Spoke Words is distinct from Freedom Hall. Existing canonical source documents and Vic’Adex production were not edited.

The floating media layer uses two user-owned Vic’Adex/60 Seconds Poetry archive assets with credits and source links. Other profiles show Photo pending; no third-party portrait was republished. Images remain hosted at the original Vic’Adex URLs. Directory, research, Nigeria GIS and interaction stub tests passed. Rendered browser/phone QA remains unavailable under the Sites managed-preview workflow.

### Three-column directory and year filter — 12 October 2026
List view now maintains three separate People, Places and Platforms columns. Each eligible entry appears once in its assigned category; empty or disabled categories retain their headings. On narrow screens the three columns remain distinct in a horizontally scrollable board, with independently scrollable entry lists. A visible documented-year selector filters all Atlas views by explicit profile evidence years, with All years and Year unverified options. A year does not imply continuous activity, founding or birth. Reset restores all years. Interaction tests verified exhaustive/unique category assignment and both dated and unverified filtering. Rendered phone QA remains pending.

### State exploration, four MECE columns and competition expansion — 12 October 2026
The interactive state map uses all 36 states and the FCT from MapSVG, redistributed by @svg-maps/nigeria under CC BY 4.0. Source and attribution are embedded in nigeria-states.json/js and shown in the UI. Original SVG paths are retained; computed bounds support click/keyboard zoom. Nasarawa spelling was normalised. These paths use native SVG coordinates, not longitude/latitude; no fabricated GeoJSON was generated from them. The separately sourced Natural Earth national GeoJSON remains available in the project. GeoNames city associations map directory entries to states; no institution residence, exact venue or complete census is inferred. Uncovered states show zero reviewed city-linked records. Nationwide/unlocated entries remain available in All Nigeria. The canonical-research return-to-map control now opens this state map rather than the legacy OSM pilot.

List view now has four mutually exclusive entry categories: People, Places, Platforms, and Prizes & Competitions. Slams, written prizes and corporate competitions live under Prizes; festival/organiser records remain Platforms. WORD UP is distinct from War of Words. Original line icons distinguish all four categories on cards, headings, profiles and state summaries. Explicitly dated, non-locator relationships contribute documented years with their labels and date qualifiers, so a judge or venue can be found in the relevant year without inventing an activity span.

Expanded the existing La Casera canonical record rather than creating a duplicate. Preserved the 2020 call separately from 2022 results; added linked company, final venue, judges and reported winners. Added YouPoetry Slam and Echowords contest metadata. Added Empowered by Words and MAPOLY from James Ademuyiwa's participant/organiser interview, with exact edition date unresolved. Renamed the existing AIPFest display record to Abuja International Poetry Festival (AIPFest); preserved its canonical ID. Added Nasara Creative, the AIPFest Grand Slam / Efe Paul Azino Prize, LIPFest Poetry Grand Slam and source-attributed result connections. The 2026 AIPFest date is an announcement, not a completed event; older projected dates are not silently treated as events.

195 directory entries and 280 source-linked relationships (including explicitly marked locator associations). State bounds/zoom, 37 state targets, keyboard activation, state/year filtering, four-column exhaustiveness and uniqueness, icons, festival/competition distinction, canonical research counts and provenance checks passed. Rendered phone QA remains unavailable. Production WordPress, source documents, hosting/domain settings and existing restricted audience were not changed.

### State count badges, Lamikanra and replacement navigation — 12 October 2026
States with matching directory entries now show a number inside a circle. Counts track year, category, format and search filters; multi-city associations count an entry once per state. Zero-count states have no badge. Badge anchors are computed interior points from the original MapSVG state paths, rather than potentially offshore bounding-box centres. Badge size scales with state zoom. The label-point generator is retained in scripts/state-label-points.py.

Added source-indexed metadata for Adebayo Lamikanra and the Poetry House Party in Ilesa (Ilesha), with the exact identity/title of the user-recalled “poetry night” and renaming/relocation chronology left open. Sources are Lamikanra’s 2016 author account and Ilesa Book Club’s 2024 tribute; full-page retrieval was blocked, so records explicitly label the indexed evidence. Added GeoNames city locators for Ilesa and Ile-Ife and Osun associations, without exposing a private house address.

Archive and Research navigation/pages were replaced by About this project and Submit an entry. Sources and verification remain within Atlas profiles. The entry form validates public evidence links, preserves uncertain dates, requires image credits and permission when an image is supplied, and saves/downloads draft entries on the visitor’s device. It does not send entries to an editorial backend or publish them in the Atlas. Device-storage failure still permits draft download. Server-side editorial intake remains incomplete.

wordsonrampage.com could not be inspected: web retrieval was inaccessible, shell requests returned 403, and no indexed results were found. No palette was invented or claimed as a brand match; the current Atlas palette remains. A screenshot or confirmed palette is needed to finish that colour request. Badge, zoom/filter, navigation, contribution-validation and storage-failure checks passed; rendered phone QA remains pending.

The map legend now toggles individual states, all states and state boundaries. State badges show separate positive counts for People, Places, Platforms and Prizes, with a labelled colour key; counts follow directory filters. Hidden states retain muted country geometry.

Vic’Adex visual adapter: exact palette and font-family declarations sourced read-only from stored Words on Rampage review CSS (post 6288). Cream #fffaf3, peach #fde9dc, teal #0b5f78, orange #e94f27, ink #171717; Comfortaa and Afacad with system fallbacks. Category swatches and map states adapt this palette. Homepage visual comparison is blocked by cloud-browser ERR_BLOCKED_BY_CLIENT; Additional CSS connector read unavailable. No production WordPress changes.

The 13 October audit adds separate atlas-audit and entry-status layers, Publications throughout the Atlas, a concise introduction and a dark shell around the light map. research/README.md records exact source scope, exclusions and remaining work. Verification is claim-scoped; recent activity is evaluated separately and expires after 12 months. The audit queue covers all entries; the full corpus and social-account audit remain incomplete.

Follow-up correction: light page, dark map canvas outside Nigeria, and arrow-free controls. research/discovery-matrix.json records 146 state/poet query attempts and browser access limitations. Search-batch primary-source enrichment brings the directory to 238 entries, 365 links and nine Publications; 47 claim-scoped reviews, with remaining claims queued.

Directory entries share a standard field schema, with source dates distinguished from event dates and missing information stated explicitly. The 2023 Cross Country Celebration notices display programme, city, named host and venue.

