(function(root){
'use strict';

// 1. City mini-map coordinates and layout based on documented Atlas places
const cityLayouts = {
  "Ogbomoso": {
    bounds: [4.23, 8.12, 4.28, 8.18],
    venues: [
      { id: "sifax", name: "Sifax Hall", type: "Venue", lat: 8.156, lon: 4.263, desc: "Historic home of Words on Rampage gatherings" },
      { id: "lautech-gate", name: "LAUTECH Main Gate", type: "Place", lat: 8.166, lon: 4.268, desc: "Entrance on Old Ogbomoso-Ilorin Road" },
      { id: "under-g", name: "Under-G Gate & Court", type: "Place", lat: 8.148, lon: 4.249, desc: "Vibrant student avenue & acoustic hub" },
      { id: "kuye", name: "Kuye District", type: "Place", lat: 8.140, lon: 4.242, desc: "Documented student residential quarter" }
    ],
    roads: [
      [[4.268, 8.175], [4.268, 8.150]], // Old Ogbomoso-Ilorin Road
      [[4.249, 8.148], [4.268, 8.166]]  // Under-G Link
    ]
  },
  "Lagos": {
    bounds: [3.35, 6.42, 3.45, 6.53],
    venues: [
      { id: "freedom-park", name: "Freedom Park (Broad St)", type: "Venue", lat: 6.452, lon: 3.395, desc: "Historic cultural venue hosting LIPFest readings" },
      { id: "muson", name: "MUSON Centre", type: "Venue", lat: 6.445, lon: 3.398, desc: "Classical concert hall and spoken word stages" },
      { id: "unilag-jp", name: "J. P. Clark Centre, UNILAG", type: "Venue", lat: 6.518, lon: 3.388, desc: "University literary hub honoring poetic lineage" },
      { id: "angels-muse", name: "Angels & Muse (Ikoyi)", type: "Venue", lat: 6.448, lon: 3.435, desc: "Contemporary art space and salon" }
    ],
    roads: [
      [[3.388, 6.518], [3.395, 6.452]], // Mainland to Island Expressway
      [[3.395, 6.452], [3.435, 6.448]]  // Broad St to Ikoyi
    ]
  },
  "Abuja": {
    bounds: [7.44, 9.02, 7.55, 9.10],
    venues: [
      { id: "merit-house", name: "Merit House (Maitama)", type: "Venue", lat: 9.082, lon: 7.485, desc: "National academy venue and festival convening hall" },
      { id: "simply-poetry", name: "Simply Poetry Centre", type: "Platform", lat: 9.055, lon: 7.492, desc: "Epicentre of theatrical spoken word in the FCT" },
      { id: "ana-house", name: "ANA National Secretariat", type: "Place", lat: 9.040, lon: 7.470, desc: "Writers Association headquarters" }
    ],
    roads: [
      [[7.470, 9.040], [7.492, 9.055]],
      [[7.492, 9.055], [7.485, 9.082]]
    ]
  },
  "Jos": {
    bounds: [8.85, 9.88, 8.95, 9.96],
    venues: [
      { id: "alliance-jos", name: "Alliance Française de Jos", type: "Venue", lat: 9.928, lon: 8.892, desc: "Acoustic open mics in the cool plateau evening" }
    ],
    roads: [
      [[8.870, 9.910], [8.892, 9.928]]
    ]
  },
  "Kano": {
    bounds: [8.48, 11.96, 8.56, 12.04],
    venues: [
      { id: "american-space-kano", name: "American Space, State Library", type: "Venue", lat: 11.995, lon: 8.520, desc: "KAPFEST & youth poetry workshops" },
      { id: "buk", name: "Bayero University Kano (BUK)", type: "Place", lat: 12.002, lon: 8.510, desc: "Academic center of Hausa & English poetic dialogue" }
    ],
    roads: [
      [[8.510, 12.002], [8.520, 11.995]]
    ]
  },
  "Enugu": {
    bounds: [7.46, 6.41, 7.54, 6.48],
    venues: [
      { id: "slang-global", name: "SLANG Global Hub", type: "Platform", lat: 6.441, lon: 7.498, desc: "Eastern spoken word academy & youth open mics" }
    ],
    roads: [
      [[7.480, 6.430], [7.498, 6.441]]
    ]
  },
  "Calabar": {
    bounds: [8.30, 4.93, 8.36, 4.99],
    venues: [
      { id: "calabar-garden", name: "Calabar Municipal Garden", type: "Venue", lat: 4.958, lon: 8.326, desc: "Riverside festival garden and spoken word salon" }
    ],
    roads: [
      [[8.310, 4.945], [8.326, 4.958]]
    ]
  },
  "Zaria": {
    bounds: [7.68, 11.08, 7.76, 11.15],
    venues: [
      { id: "hotspot-kafe", name: "Hotspot Kafe", type: "Venue", lat: 11.111, lon: 7.722, desc: "University arts circle cafe near ABU Samaru" }
    ],
    roads: [
      [[7.700, 11.100], [7.722, 11.111]]
    ]
  },
  "Gombe": {
    bounds: [11.14, 10.26, 11.20, 10.32],
    venues: [
      { id: "gsu-love-garden", name: "Love Garden, GSU", type: "Venue", lat: 10.289, lon: 11.167, desc: "Savannah campus amphitheatre and student readings" }
    ],
    roads: [
      [[11.150, 10.275], [11.167, 10.289]]
    ]
  }
};

// 2. Dynamic NPC Poets with home platforms and scheduled travel
const simulatedPoets = [
  { id: "efe-paul", name: "Efe Paul Azino", homeCity: "Lagos", platform: "LIPFest", specialty: "delivery", bonus: 5, quote: "In Lagos, you have ten seconds to arrest the room." },
  { id: "dike-c", name: "Dike Chukwumerije", homeCity: "Abuja", platform: "Simply Poetry", specialty: "delivery", bonus: 5, quote: "Spoken word is theatre stripped of costumes." },
  { id: "titilope-s", name: "Titilope Sonuga", homeCity: "Lagos", platform: "Freedom Park", specialty: "delivery", bonus: 5, quote: "Vulnerability on stage is your greatest armor." },
  { id: "salim-y", name: "Salim Yunusa", homeCity: "Kano", platform: "KAPFEST", specialty: "craft", bonus: 4, quote: "A poem should carry the honor of its language and community." },
  { id: "vic-meshak", name: "Victor Words Meshak", homeCity: "Jos", platform: "Alliance Française", specialty: "delivery", bonus: 3, quote: "Let the breath carry the line before you rush to the rhyme." },
  { id: "dr-eugo", name: "Dr. Eugo (Ugochukwu Otike)", homeCity: "Enugu", platform: "SLANG Global", specialty: "craft", bonus: 4, quote: "Proverbs are the palm oil with which words are eaten." },
  { id: "victory-u", name: "Victory Udie", homeCity: "Calabar", platform: "Municipal Garden", specialty: "delivery", bonus: 3, quote: "Poetry here moves like the tide." },
  { id: "vic-adex", name: "Vic'Adex", homeCity: "Ogbomoso", platform: "60 Seconds Poetry", specialty: "craft", bonus: 4, quote: "Compress your world into 60 seconds. Precision makes brevity powerful." }
];

// 3. Convening Events pulling poets across regions
const conveningCalendar = [
  { day: 7, name: "LIPFest (Lagos International Poetry Festival)", hostCity: "Lagos", pull: "national", desc: "Nigeria's flagship poetry festival convening voices from every state." },
  { day: 14, name: "AIPFest (Abuja International Poetry Festival)", hostCity: "Abuja", pull: "national", desc: "The capital convenes poets, essayists, and dramatists for national dialogues." },
  { day: 21, name: "Words on Rampage Anniversary", hostCity: "Ogbomoso", pull: "regional", desc: "Historic gathering celebrating collegiate and regional spoken word pioneers." },
  { day: 28, name: "KAPFEST (Kano Poetry Festival)", hostCity: "Kano", pull: "regional", desc: "Bilingual festival celebrating oral cadence and Northern lyricism." }
];

function getActiveConvening(day) {
  return conveningCalendar.find(c => (day % 28) === (c.day % 28) || Math.abs((day % 28) - (c.day % 28)) <= 1);
}

function getPoetLocation(poet, day) {
  const convening = getActiveConvening(day);
  if (convening) {
    if (convening.pull === 'national' || poet.homeCity === convening.hostCity || Math.random() < 0.6) {
      return convening.hostCity;
    }
  }
  // Otherwise at home or occasionally touring
  return poet.homeCity;
}

// 4. City mini-map rendering
function renderCityMiniMap(cityName, currentVenueId = null) {
  const layout = cityLayouts[cityName] || cityLayouts["Ogbomoso"];
  const width = 460;
  const height = 300;
  const [minLon, minLat, maxLon, maxLat] = layout.bounds;

  const project = (lon, lat) => [
    Math.round(((lon - minLon) / (maxLon - minLon)) * (width - 60) + 30),
    Math.round((1 - (lat - minLat) / (maxLat - minLat)) * (height - 60) + 30)
  ];

  let roadsSvg = "";
  if (layout.roads) {
    roadsSvg = layout.roads.map(rd => {
      const p1 = project(rd[0][0], rd[0][1]);
      const p2 = project(rd[1][0], rd[1][1]);
      return `<line x1="${p1[0]}" y1="${p1[1]}" x2="${p2[0]}" y2="${p2[1]}" stroke="rgba(255,255,255,0.18)" stroke-width="8" stroke-linecap="round"/><line x1="${p1[0]}" y1="${p1[1]}" x2="${p2[0]}" y2="${p2[1]}" stroke="#ffd166" stroke-width="1.5" stroke-dasharray="6 4"/>`;
    }).join('');
  }

  const venuesSvg = layout.venues.map(v => {
    const [x, y] = project(v.lon, v.lat);
    const isSelected = v.id === currentVenueId;
    return `
      <g class="sim-venue-node" data-venue="${v.id}" transform="translate(${x},${y})" style="cursor:pointer">
        <circle r="${isSelected ? 14 : 9}" fill="${isSelected ? '#e63946' : '#2a9d8f'}" stroke="#fff" stroke-width="2"/>
        <text x="0" y="-14" fill="#fff" font-size="11" font-weight="600" text-anchor="middle" filter="drop-shadow(0px 1px 2px #000)">${v.name}</text>
      </g>
    `;
  }).join('');

  return `
    <div class="city-minimap-container" style="background:#161b22;border:1px solid rgba(255,255,255,0.12);border-radius:8px;padding:12px;margin:12px 0;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <h4 style="margin:0;font-size:15px;color:#58a6ff;">📍 ${cityName} Mini-Map (Documented Atlas Venues)</h4>
        <span style="font-size:12px;color:#8b949e;">Interactive Simulation Stage</span>
      </div>
      <svg viewBox="0 0 ${width} ${height}" style="width:100%;height:auto;max-height:300px;background:#0d1117;border-radius:6px;border:1px solid rgba(255,255,255,0.08);">
        <rect width="${width}" height="${height}" fill="#0d1117"/>
        ${roadsSvg}
        ${venuesSvg}
      </svg>
      <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;">
        ${layout.venues.map(v => `
          <button class="venue-select-btn ${v.id === currentVenueId ? 'active-venue' : ''}" data-venue-btn="${v.id}" style="padding:4px 10px;font-size:12px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.2);border-radius:4px;color:#e6edf3;cursor:pointer;">
            🎪 ${v.name}
          </button>
        `).join('')}
      </div>
    </div>
  `;
}

// 5. Transit Animation (Plane for flight corridors, Car for regional roads)
function getTransitAnimation(fromCity, toCity, coords) {
  const from = (coords && coords[fromCity]) || { lat: 8.13, lon: 4.24 };
  const to = (coords && coords[toCity]) || { lat: 6.45, lon: 3.39 };

  // Calculate distance in km roughly
  const dLat = (to.lat - from.lat) * 111;
  const dLon = (to.lon - from.lon) * 111 * Math.cos(from.lat * Math.PI / 180);
  const distanceKm = Math.round(Math.sqrt(dLat * dLat + dLon * dLon));

  // Determine mode: distance > 250km uses Plane, otherwise Car
  const isPlane = distanceKm > 250;
  const modeIcon = isPlane ? "✈️ Flight" : "🚗 Road Corridor";

  return {
    isPlane,
    distanceKm,
    modeIcon,
    fromCity,
    toCity,
    transitHtml: `
      <div class="transit-animation-banner" style="background:rgba(47,111,235,0.15);border:1px solid #2f6feb;border-radius:8px;padding:12px 16px;margin:12px 0;display:flex;align-items:center;justify-content:space-between;animation:fadeIn 0.3s ease;">
        <div>
          <strong style="color:#58a6ff;font-size:15px;">${modeIcon} in Transit:</strong>
          <span style="color:#e6edf3;font-size:14px;margin-left:6px;">${fromCity} ➔ ${toCity} (${distanceKm} km)</span>
        </div>
        <div class="transit-vehicle-anim" style="font-size:24px;animation:transitMove 1.5s infinite alternate ease-in-out;">
          ${isPlane ? '✈️' : '🚙'}
        </div>
      </div>
    `
  };
}

const api = {
  cityLayouts,
  simulatedPoets,
  conveningCalendar,
  getActiveConvening,
  getPoetLocation,
  renderCityMiniMap,
  getTransitAnimation
};

if (typeof module !== 'undefined') module.exports = api;
root.PoeticsLivingSim = api;

})(typeof window !== 'undefined' ? window : globalThis);
