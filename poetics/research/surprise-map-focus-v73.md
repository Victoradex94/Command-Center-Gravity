# Surprise map focus — Version 73

The Surprise me action now moves the map to a supported state recorded in the chosen entry's explicit location fields. A single-city Place still opens its mapped city/state view where that layer is available. For records covering several mapped states, the focus prefers the currently filtered state, then a state in the active geopolitical zone, then the alphabetically first recorded state. It does not infer location from relationships.

“Within filters” keeps the state, city, zone, category, year, format, and search selections. “Anywhere in Atlas” retains its existing behavior of clearing filters first. When the focused state differs from the state filter, the map nameplate identifies it as an entry focus and provides “Back to filtered map”; the URL records the focus so copied links restore the same view.

Changing a filter or choosing another state/city clears the temporary map focus. Counts and entry data are unchanged. The behavior is covered by the Atlas navigation test, including filter preservation, URL restore, return-to-filtered-map and state zoom. This is source/test verification; no fresh rendered-browser QA was available for this release.
