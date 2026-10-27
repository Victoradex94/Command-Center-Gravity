const fs = require('node:fs');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const window = { addEventListener() {}, matchMedia: () => ({ matches: false }) };
const context = vm.createContext({ window, console, setTimeout, clearTimeout });
for (const file of ['atlas-input.js', 'living-sim.js']) {
  vm.runInContext(fs.readFileSync(`dist/${file}`, 'utf8'), context, { filename: file });
}

const sim = window.PoeticsLivingSim;
const layout = sim.cityLayouts.Ogbomoso;
assert.equal(layout.schematic, true);
assert.deepEqual(
  Array.from(layout.venues, place => place.recordId),
  ['sifax', 'main-gate', 'under-g', 'kuye']
);
assert(layout.venues.every(place => !('lat' in place) && !('lon' in place)));

const schematic = sim.renderCityMiniMap('Ogbomoso');
for (const id of ['main-gate', 'under-g', 'kuye']) assert(schematic.includes(`data-atlas-place="${id}"`));
assert(schematic.includes('Sifax Hall'));
assert(schematic.includes('location is not plotted'));
assert(schematic.includes('SCHEMATIC / NOT TO SCALE'));
assert(schematic.includes('width:100%;max-height:none;overflow:visible'));
assert(schematic.includes('.district-map-dialog:has(.ogb-map-card) #expanded-map'));
assert(schematic.includes('max-height:none;overflow:visible'));
assert(schematic.includes('Stadium Road'));
assert(schematic.includes('nigeria-streets.openalfa.com/streets/stadium-rd-ogbomosho-north-oyo'));
assert(!schematic.includes('unnamed residential connector'));
assert(!layout.roads.some(road => String(road.sourceId).startsWith('osm-way-')));
assert(schematic.includes('© OpenStreetMap contributors · ODbL'));
assert(!schematic.includes('NaN') && !schematic.includes('undefined'));
assert(!schematic.includes('<g class="ogb-map-place is-landmark" data-atlas-place="sifax"'), 'Sifax is listed but not plotted without an exact location source');

window.PoeticsAtlas.records = window.PoeticsAtlas.records.map(record =>
  record.id === 'main-gate' ? { ...record, name: '<img src=x onerror=alert(1)>' } : record
);
const escaped = sim.renderOgbomosoSchematic();
assert(escaped.includes('&lt;img src=x onerror=alert(1)&gt;'));
assert(!escaped.includes('<img src=x onerror=alert(1)>'));

const transit = sim.getTransitAnimation('Ogbomoso', 'Lagos', {
  Ogbomoso: { lat: 8.13, lon: 4.24 },
  Lagos: { lat: 6.45, lon: 3.39 }
});
assert(Number.isFinite(transit.distanceKm));
const transitMap = sim.renderCityMiniMap('Ogbomoso', null, transit);
assert(transitMap.includes('sim-transit-route'));
assert(transitMap.includes('sim-transit-vehicle'));
assert(!/NaN|Infinity|undefined/.test(transitMap));
assert(sim.renderCityMiniMap('Lagos').includes('data-atlas-place="freedom-park"'));
assert(sim.renderCityMiniMap('Lagos').includes('SCHEMATIC / NOT TO SCALE'));
assert(!sim.renderCityMiniMap('Lagos').includes('sim-venue-node'), 'unverified venue coordinates are not drawn as pins');
for (const city of [...new Set(window.PoeticsAtlas.records.map(record => record.city).filter(Boolean))].filter(city => city !== 'Online')) {
  const cityPlaces = window.PoeticsAtlas.records.filter(record => record.city === city && ['Place', 'Venue', 'Event', 'Event series'].includes(record.type));
  if (!cityPlaces.length) continue;
  const cityMap = sim.renderCityMiniMap(city);
  for (const place of cityPlaces) assert(cityMap.includes(`data-atlas-place="${place.id}"`), `${place.name} appears in the ${city} map`);
  assert(cityMap.includes('not geographic') || cityMap.includes('not a surveyed') || cityMap.includes('not mapped'), `${city} map explains placement limits`);
}
assert(sim.renderCityMiniMap('Maiduguri').includes('Mogcolis'), 'database cities without a hand-drawn layout still receive a place map');
assert(sim.renderCityMiniMap('Aba').includes('MAP RESEARCH NEEDED'), 'cities without mapped Atlas places are not assigned the Ogbomoso map');

function control(id, pressed = null) {
  const node = {
    id,
    attrs: pressed === null ? {} : { 'aria-pressed': pressed },
    setAttribute(name, value) { this.attrs[name] = value; }
  };
  return node;
}
function makeDialog() {
  const controls = new Map();
  let placeButtons = [];
  const expanded = { innerHTML: '' };
  const dialog = {
    id: '', className: '', listeners: {},
    set innerHTML(html) {
      this.html = html;
      for (const match of html.matchAll(/<button id="([^"]+)" aria-pressed="(true|false)"/g)) {
        controls.set(`#${match[1]}`, control(match[1], match[2]));
      }
      for (const match of html.matchAll(/<button id="([^"]+)"/g)) {
        if (!controls.has(`#${match[1]}`)) controls.set(`#${match[1]}`, control(match[1]));
      }
      placeButtons = [...html.matchAll(/data-map-place="([^"]+)"/g)].map(match => ({ dataset: { mapPlace: match[1] }, onclick: null }));
    },
    get innerHTML() { return this.html; },
    showModal() { this.open = true; }, close() { this.open = false; }, remove() { this.removed = true; },
    addEventListener(name, handler) { this.listeners[name] = handler; },
    querySelector(selector) {
      if (selector === '#expanded-map') return expanded;
      return controls.get(selector) || null;
    },
    querySelectorAll(selector) { return selector === '[data-map-place]' ? placeButtons : []; }
  };
  return { dialog, expanded };
}
const { dialog, expanded } = makeDialog();
const document = {
  body: { append(node) { assert.equal(node, dialog); } },
  createElement(tag) { assert.equal(tag, 'dialog'); return dialog; },
  querySelector(selector) { return selector === '#district-map-dialog' ? null : null; },
  querySelectorAll() { return []; }
};
window.document = document;
window.Poetics3D = { position: () => ({ x: 0, z: 0, angle: 0, target: null }) };
context.document = document;
vm.runInContext(fs.readFileSync('dist/gamemap.js', 'utf8'), context, { filename: 'gamemap.js' });
const gameAssets = fs.readFileSync('dist/game-assets.js', 'utf8');
const worldAsset = gameAssets.match(/world\.[a-f0-9]{12}\.js/);
assert(worldAsset, 'the city-world module is listed as a lazy game asset');
const worldSource = fs.readFileSync(`dist/${worldAsset[0]}`);
assert.equal(crypto.createHash('sha256').update(worldSource).digest('hex').slice(0, 12), worldAsset[0].match(/[a-f0-9]{12}/)[0], 'the lazy world asset filename matches its contents');
vm.runInContext(worldSource.toString('utf8'), context, { filename: worldAsset[0] });

assert.equal(window.PoeticsLivingSim, sim, 'the map module must not replace the complete simulation API');
assert.equal(typeof sim.enhanceScene, 'function', 'scene enhancement remains available after all lazy game modules load');
assert.equal(typeof window.PoeticsMap.open, 'function', 'the district map keeps its separate map API');
assert(window.PoeticsLivingSim.renderCityMiniMap('Ogbomoso').includes('SCHEMATIC / NOT TO SCALE'));
assert(window.PoeticsWorld('Maiduguri').includes('Mogcolis'), 'the playable city scene uses its Atlas place map');
assert(!window.PoeticsWorld('Maiduguri').includes('awaiting local map research'));
assert(window.PoeticsWorld('Ogbomoso').includes('id="city-canvas"'), 'Ogbomoso keeps its existing explorable scene');
window.PoeticsMap.open();
assert(dialog.innerHTML.includes('href="https://www.openstreetmap.org/#map=13/8.1515/4.26"'), 'the online area reference has a direct fallback outside the iframe');
assert(dialog.innerHTML.includes('href="https://www.openstreetmap.org/copyright"'), 'contributor credit and ODbL notice remain available if the iframe fails');
const buttons = selector => dialog.querySelector(selector);
buttons('#show-places-map').onclick();
assert(expanded.innerHTML.includes('SCHEMATIC / NOT TO SCALE'));
assert.equal(buttons('#show-places-map').attrs['aria-pressed'], 'true');
assert.equal(buttons('#show-game-map').attrs['aria-pressed'], 'false');
buttons('#show-osm-map').onclick();
assert(expanded.innerHTML.includes('openstreetmap.org/export/embed.html'));
assert(expanded.innerHTML.includes('4.23%2C8.12%2C4.29%2C8.183'));
assert(!expanded.innerHTML.includes('OpenStreetMap provides area-level context only'));
assert(!expanded.innerHTML.includes('marker='));
buttons('#show-game-map').onclick();
assert(expanded.innerHTML.includes('class="navigation-map"'));
assert.equal(buttons('#show-game-map').attrs['aria-pressed'], 'true');
buttons('#close-district-map').onclick();
assert.equal(dialog.removed, true);

console.log('PASS Ogbomoso Atlas anchors, all-city Atlas Place/Venue/Event coverage, unlocated Sifax record, escaped labels, transit fallback and accessible Game/Places/OSM view switching. UI checks use a DOM stub, not browser visual QA.');
