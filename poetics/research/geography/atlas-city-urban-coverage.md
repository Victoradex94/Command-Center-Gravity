# Atlas city / urban-extent coverage audit

Scope: current GitHub main5dddd6a / Sites57; 39 mapped cities. No app/data import.

| Atlas city | Atlas state | Name match | Containing area at existing centre | Status |
|---|---|---|---|---|
| Aba | Abia | Aba (Africapolis_2020.9) | Not established | name-match-location-review-needed |
| Abakaliki | Ebonyi | Abakaliki (Africapolis_2020.17) | Not established | name-match-location-review-needed |
| Abeokuta | Ogun | Abeokuta (Africapolis_2020.29) | Abeokuta (Africapolis_2020.29) | name-match-spatial-confirmed |
| Abuja | Federal Capital Territory | Abuja (Africapolis_2020.133) | Abuja (Africapolis_2020.133) | name-match-spatial-confirmed |
| Ado Ekiti | Ekiti | Ado ekiti (Africapolis_2020.201) | Not established | name-match-location-review-needed |
| Asaba | Delta | Asaba (Africapolis_2020.1305) | Not established | name-match-location-review-needed |
| Awka | Anambra | — | Not established | no-qualifying-match-in-this-pass |
| Bauchi | Bauchi | Bauchi (Africapolis_2020.1727) | Not established | name-match-location-review-needed |
| Benin City | Edo | Benin city (Africapolis_2020.1822) | Benin city (Africapolis_2020.1822) | name-match-spatial-confirmed |
| Calabar | Cross River | Calabar (Africapolis_2020.2322) | Calabar (Africapolis_2020.2322) | name-match-spatial-confirmed |
| Damaturu | Yobe | Damaturu (Africapolis_2020.2566) | Not established | name-match-location-review-needed |
| Enugu | Enugu | Enugu (Africapolis_2020.3119) | Enugu (Africapolis_2020.3119) | name-match-spatial-confirmed |
| Gombe | Gombe | Gombe (Africapolis_2020.3565) | Gombe (Africapolis_2020.3565) | name-match-spatial-confirmed |
| Ibadan | Oyo | Ibadan (Africapolis_2020.3853) | Ibadan (Africapolis_2020.3853) | name-match-spatial-confirmed |
| Ikot Ekpene | Akwa Ibom | — | Not established | no-qualifying-match-in-this-pass |
| Ile-Ife | Osun | — | Ife 1 (Africapolis_2020.3903) | different-name-containing-area-review-needed |
| Ilesa | Osun | — | Ilesha (Africapolis_2020.4019) | different-name-containing-area-review-needed |
| Ilorin | Kwara | Ilorin (Africapolis_2020.4030) | Ilorin (Africapolis_2020.4030) | name-match-spatial-confirmed |
| Issele-Uku | Delta | Issele uku (Africapolis_2020.4127) | Not established | name-match-location-review-needed |
| Jalingo | Taraba | Jalingo (Africapolis_2020.4178) | Not established | name-match-location-review-needed |
| Jos | Plateau | Jos (Africapolis_2020.4226) | Jos (Africapolis_2020.4226) | name-match-spatial-confirmed |
| Kaduna | Kaduna | Kaduna (Africapolis_2020.4291) | Kaduna (Africapolis_2020.4291) | name-match-spatial-confirmed |
| Kano | Kano | Kano (Africapolis_2020.4519) | Kano (Africapolis_2020.4519) | name-match-spatial-confirmed |
| Karu | Nasarawa | — | Not established | no-qualifying-match-in-this-pass |
| Lafia | Nasarawa | — | Lafia 1 (Africapolis_2020.5194) | different-name-containing-area-review-needed |
| Lagos | Lagos | Lagos (Africapolis_2020.5199) | Lagos (Africapolis_2020.5199) | name-match-spatial-confirmed |
| Lokoja | Kogi | Lokoja (Africapolis_2020.5309) | Not established | name-match-location-review-needed |
| Maiduguri | Borno | Maiduguri (Africapolis_2020.5538) | Maiduguri (Africapolis_2020.5538) | name-match-spatial-confirmed |
| Makurdi | Benue | Makurdi (Africapolis_2020.5585) | Makurdi (Africapolis_2020.5585) | name-match-spatial-confirmed |
| Ogbomoso | Oyo | — | Ogbomosho (Africapolis_2020.6985) | different-name-containing-area-review-needed |
| Orerokpe | Delta | Orerokpe (Africapolis_2020.7114) | Not established | name-match-location-review-needed |
| Owerri | Imo | — | Not established | no-qualifying-match-in-this-pass |
| Port Harcourt | Rivers | Port harcourt (Africapolis_2020.7357) | Port harcourt (Africapolis_2020.7357) | name-match-spatial-confirmed |
| Sokoto | Sokoto | Sokoto (Africapolis_2020.8156) | Not established | name-match-location-review-needed |
| Umuahia | Abia | Umuahia (Africapolis_2020.8764) | Not established | name-match-location-review-needed |
| Uyo | Akwa Ibom | Uyo (Africapolis_2020.8806) | Not established | name-match-location-review-needed |
| Yenagoa | Bayelsa | Yenagoa (Africapolis_2020.9076) | Not established | name-match-location-review-needed |
| Yola | Adamawa | — | Jimeta (Africapolis_2020.4211) | different-name-containing-area-review-needed |
| Zaria | Kaduna | Zaria (Africapolis_2020.9129) | Zaria (Africapolis_2020.9129) | name-match-spatial-confirmed |

Other location labels (not automatically treated as cities): Ebonyi, Global, Nasarawa, Nigeria, Nigeria relevance, Northern Nigeria, Ogun, Online, UK, Yoruba cultural sphere, city verification pending, diaspora, multi-location.

No new identities/imports; point containment is evidence of footprint overlap, not proof of same city/legal boundary. Name-only matches need geographic check. Noncity labels not forcibly geocoded.

Yola’s point lies inside the feature named Jimeta. Keep that as a containing-area candidate, not a Yola rename. Ile-Ife/Ife1, Lafia/Lafia1 and spelling variants Ilesa/Ilesha and Ogbomoso/Ogbomosho have spatial support, but still require state/alias review. Owerri, Awka, Ikot Ekpene and Karu have neither a normalized exact name nor an existing source coordinate qualifying a footprint in this pass. This is not absence of settlements or poetry.

## State geometry access checkpoint

Official geoBoundaries API https://www.geoboundaries.org/api/current/gbOpen/NGA/ADM1/ directly read15Oct2026: boundaryID NGA-ADM1-27671186,37units, GRID3, represented2022,CCBY4, build12Dec2023. API advertises simplified download https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/NGA/ADM1/geoBoundaries-NGA-ADM1_simplified.geojson . Connected GitHub reads of repository file and advertised raw URL returned Git LFS pointer only: expected827817bytes, SHA256 edd28050c7f1ae40471424605f74e4d2df83502e4f301089761ae18f8ae2fbbf. No state geometries retrieved; do not claim alignment/rollout from metadata. No network restriction bypass attempted. User browser download/upload is needed with current capabilities.

No keyword web query this pass. Exact local operations: normalize each city name to lowercase alphanumerics and compare only ISO3=NGA agglosName; for each existing sourced city point, bounding-box prefilter and point-in-MultiPolygon excluding holes; record every positive and negative row. No fuzzy candidate imported.
