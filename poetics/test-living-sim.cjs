const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

global.window = global;
vm.runInThisContext(fs.readFileSync('./dist/atlas-input.js', 'utf8'), { filename: 'atlas-input.js' });
const Sim = require('./dist/living-sim.js');

console.log('Testing Living Simulation module...');

// 1. Verify city mini-maps exist for key cities
assert(Sim.cityLayouts['Ogbomoso']);
assert(Sim.cityLayouts['Lagos']);
assert(Sim.cityLayouts['Abuja']);
assert(Sim.cityLayouts['Jos']);
assert(Sim.cityLayouts['Kano']);
assert(Sim.cityLayouts['Enugu']);
assert(Sim.cityLayouts['Calabar']);
assert(Sim.cityLayouts['Zaria']);
assert(Sim.cityLayouts['Gombe']);

// Mini-map renders SVG with documented venues
const ogbSvg = Sim.renderCityMiniMap('Ogbomoso');
assert(ogbSvg.includes('Sifax Hall'));
assert(ogbSvg.includes('LAUTECH Main Gate'));
assert(ogbSvg.includes('<svg'));

const lagosSvg = Sim.renderCityMiniMap('Lagos');
assert(lagosSvg.includes('Freedom Park'));
assert(lagosSvg.includes('MUSON Centre'));

// 2. Archival Venue Vignettes (GTA-style texture wrapping & historic waypoints)
assert(typeof Sim.renderVenueVignette === 'function');
const fpVignette = Sim.renderVenueVignette('freedom-park');
assert(fpVignette.includes('Freedom Park'));
assert(fpVignette.includes('LIPFest'));
assert(fpVignette.includes('brick-pattern'));
assert(fpVignette.includes('Efe Paul Azino'));

const sifaxVignette = Sim.renderVenueVignette('sifax');
assert(sifaxVignette.includes('Sifax Hall'));
assert(sifaxVignette.includes('WORDS ON RAMPAGE'));
assert(sifaxVignette.includes('LAUTECH'));

const josVignette = Sim.renderVenueVignette('alliance-jos');
assert(josVignette.includes('Alliance Fran'));
assert(josVignette.includes('Victor Words Meshak'));

// 3. Transit animation logic
const coords = {
  'Lagos': { lat: 6.454, lon: 3.394 },
  'Ogbomoso': { lat: 8.133, lon: 4.240 },
  'Kano': { lat: 12.000, lon: 8.516 }
};

// Road corridor (short distance ~200km)
const road = Sim.getTransitAnimation('Lagos', 'Ogbomoso', coords);
assert.equal(road.isPlane, false);
assert(road.modeIcon.includes('Road'));

// Flight corridor (long distance > 250km)
const flight = Sim.getTransitAnimation('Lagos', 'Kano', coords);
assert.equal(flight.isPlane, true);
assert(flight.modeIcon.includes('Flight'));

// 4. Convening pull
const conv7 = Sim.getActiveConvening(7);
assert.equal(conv7.hostCity, 'Lagos');
assert(conv7.name.includes('LIPFest'));

const conv14 = Sim.getActiveConvening(14);
assert.equal(conv14.hostCity, 'Abuja');
assert(conv14.name.includes('AIPFest'));

// Established poets present in their cities/platforms
const efe = Sim.simulatedPoets.find(p => p.name.includes('Efe Paul'));
assert.equal(efe.homeCity, 'Lagos');
assert.equal(efe.platform, 'LIPFest');

console.log('PASS Living Poetics Simulation: city mini-maps, archival venue vignettes (GTA texture mapping), transit animation (car/plane), and convening calendar verified.');
