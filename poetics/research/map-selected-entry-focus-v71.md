# Atlas selected-entry map focus — Version 71

User direction: make displayed entries affect the map. Location entries should open their mapped place; people and platforms should colour every state supported by the entry’s recorded location field.

- Selecting an entry from List returns to Map so its location response remains visible. Selecting a Places record with exactly one city recognized by the map opens that city/state view. Selecting an entry from List switches back to Map so the geographic response stays visible. The displayed geometry remains a city-centre locator or available urban extent, never an inferred venue outline.
- Any selected record with state associations in its recorded `city` field highlights all those state polygons using its existing category colour. The count heatmap remains underneath at reduced opacity. The map note explains this overlay.
- A person/platform’s state coverage is bounded by the locations explicitly recorded on that profile. No relationships, residence, attendance, or geographic presence are inferred from shared names or untyped graph proximity. Entries without a recognized mapped location do not create a focus state.
- Selecting the city on a state map highlights its existing locator/urban extent only when the selected record has exactly one recognized city in that state.
- Record counts, evidence, source links, and historical dataset are unchanged.

Checks: navigation regression and direct renderer tests in `test-atlas-navigation.cjs`; release checks follow.
