## 2026-10-21 - Map geometry rendering overhead
**Learning:** In `dist/state-urban-map.js`, generating SVG paths dynamically via `Array.prototype.map` and array destructurings within nested loops caused huge garbage collection and CPU overhead when dealing with large MultiPolygon datasets (e.g., thousands of coordinates).
**Action:** When working with massive arrays of numeric data (like geospatial coordinates), prefer plain `for` loops and direct array element access over functional array methods and destructuring to minimize memory allocations.

## 2026-10-21 - Optimization of projection calculations in PoeticsStateUrbanMap
**Learning:** `viewGeometry` caches view objects based on `state` + `focused.city`, storing pre-calculated SVG paths (`outline` and `cities.path`) and points (`cities.point`). Caching avoids re-computing the `merc` function and string concatenations. The `polys` and `merc` functions are critical paths for these map computations.
**Action:** Ensure any modifications to SVG paths string generation or projection maths remain accurate. The cache makes it so rendering the same geometry multiple times is fast. Let's see if we can optimize string building or array iteration in `projection` and `path` for the initial cache miss.
