# Selected-entry map focus — Version 72

User direction: displayed entries should drive the map. A location opens its mapped city/state view; people and platforms colour all states supported by their recorded location fields. Surprise results follow the same behavior where their scope allows it.

- Selecting a Places record with exactly one city recognized by the map opens that city/state view. Selecting an entry from List returns to Map so the geographic response stays visible.
- “Anywhere in Atlas” resets filters as before and opens the selected location’s mapped city/state when it is a single known city. “Within filters” preserves the active scope and highlights the selected entry’s recorded state(s).
- Any selected record with mapped state associations in its recorded `city` field highlights those state polygons using its existing category colour. The count heatmap remains underneath at reduced opacity. A map note explains the overlay.
- Person/platform coverage is bounded by locations explicitly recorded on that profile. No relationship proximity, residence, attendance, or geographic presence is inferred. Additions require source-backed location records.
- At state level, a single recognized city is highlighted using its existing city marker/urban extent. The marker is a locator, not an exact venue position.
- Record counts, evidence, source links, and historical dataset are unchanged.
