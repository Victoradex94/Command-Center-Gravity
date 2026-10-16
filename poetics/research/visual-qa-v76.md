# Published Version 76 — bounded browser QA

16 October 2026, Africa/Lagos. Independently opened a fresh connected Edge tab at the existing restricted Atlas URL after native deployment succeeded.

- Published source: `e22287464f447cfec4f664c3b9ddf7be7b870b2e`.
- Saved version: `appgprj_6acce9493e8c81919635a9e7438b820c~appgver_6ff1c071f0f081919d36963373e131c8`.
- Deployment: `appgdep_6ad287d2e704819180e2b1cc82247247`, succeeded. Custom audience preserved.
- Fresh visible release: Preview 76. Browse entries: 453. The DOM lists the new `atlas-input.1534274b6a7f.js` and `directory.6d85a71cd280.js` assets.

## Rendered observations

Desktop screenshot and full-page national map were inspected. The cream page, dark Nigeria map surroundings, purple total buttons, five category icons, compact filters, heat scale, attribution and font appearance are retained.

At the requested phone-size check (390×844), the national map and count markers rendered, the category legend appeared below the geography, and All Nigeria / Surprise / its scope selector were visible in their own rows. The scoped DOM readings showed viewport/page/body widths of 390/390/390 (375px client width also observed with scrollbar), without page-level horizontal overflow. The exploration action box measured x28 to x362; both controls fit within the content area. The filter fields and top-city shortcuts retain their own intentional horizontal scrolling.

Screenshots: `qa-v76-desktop.jpg`, `qa-v76-mobile.jpg`.

## Interactions checked in the actual browser

- State selector → Lagos: detailed urban map loaded; result heading 64 entries and category totals 28/11/16/6/3.
- Category selector → People: Lagos result heading changed to 28 entries.
- Clear all restored the national map.
- Surprise selected Global Association of Young Authors (GAYA), which has no mapped state/city: Nigeria stayed visible with the explanatory message and profile.
- A subsequent Surprise selected Douglas Ogbankwa: shareable URL gained `focus=Edo`, and the nameplate displayed Entry focus · State / Edo with Filters unchanged.

Viewport override was reset. The final published tab is retained as the deliverable. No live WordPress, domain, sharing, or audience changes.

## Limits

This is a bounded desktop/phone-width rendered check and ordinary control interaction, not actual touch/pen, screen-reader, or all-device testing. The phone national badges and state labels remain small. A screenshot capture intermittently clipped the right edge despite in-bounds DOM geometry; a general capture/layout diagnosis is not claimed. No browser network timings, Lighthouse score, slow-network simulation, or universal speed guarantee were obtained. Local performance measurements are in `performance-v76-verification.json` with their scope.
