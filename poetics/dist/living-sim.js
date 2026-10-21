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


// 4b. Archival Venue Photo Vignettes & Historical Waypoints (GTA-style texture wrapping)
const venueArchivalData = {
  "freedom-park": {
    name: "Freedom Park (Lagos Island)",
    era: "c. 2010–2024 Spoken Word Renaissance",
    desc: "Built over the colonial Broad Street Prison ruins, Freedom Park became the electric stage of Lagos performance poetry and the annual Lagos International Poetry Festival (LIPFest).",
    svgTexture: `<svg viewBox="0 0 400 180" style="width:100%;height:auto;border-radius:6px;background:#1a1512;">
      <defs>
        <pattern id="brick-pattern" width="20" height="10" patternUnits="userSpaceOnUse">
          <rect width="20" height="10" fill="#4a2e2b" stroke="#2b1a18" stroke-width="1"/>
          <line x1="0" y1="5" x2="20" y2="5" stroke="#2b1a18" stroke-width="1"/>
          <line x1="10" y1="0" x2="10" y2="5" stroke="#2b1a18" stroke-width="1"/>
          <line x1="0" y1="5" x2="0" y2="10" stroke="#2b1a18" stroke-width="1"/>
        </pattern>
      </defs>
      <!-- Brick prison wall texture -->
      <rect width="400" height="180" fill="url(#brick-pattern)"/>
      <rect x="0" y="0" width="400" height="180" fill="rgba(0,0,0,0.3)"/>
      <!-- Iron entrance gate arch -->
      <path d="M140 180 V80 Q200 30 260 80 V180" fill="#111" stroke="#888" stroke-width="4"/>
      <!-- Stage spotlight glow -->
      <circle cx="200" cy="110" r="50" fill="rgba(255,209,102,0.25)" filter="blur(6px)"/>
      <!-- Festival Banner billboard -->
      <rect x="60" y="24" width="280" height="34" fill="#0b5f78" rx="4" stroke="#e6edf3" stroke-width="1.5"/>
      <text x="200" y="46" fill="#fffaf0" font-family="'Comfortaa', sans-serif" font-weight="700" font-size="13" text-anchor="middle" letter-spacing="1">LIPFest · FREEDOM PARK STAGE</text>
      <!-- Amphi-bench outlines -->
      <rect x="30" y="145" width="340" height="12" fill="#2b231d" rx="2"/>
      <rect x="50" y="162" width="300" height="12" fill="#241d18" rx="2"/>
    </svg>`,
    atmosphere: "Night air off the Marina, iron railings, finger-snapping echoing between brick walls.",
    poetsPresent: ["Efe Paul Azino", "Titilope Sonuga"]
  },
  "sifax": {
    name: "Sifax Hall (LAUTECH, Ogbomoso)",
    era: "c. 2015 Words on Rampage Gathering",
    desc: "The documented hall where the historic Words on Rampage gathering convened after a sudden relocation from 250LT, becoming a milestone in southwestern campus literary history.",
    svgTexture: `<svg viewBox="0 0 400 180" style="width:100%;height:auto;border-radius:6px;background:#202521;">
      <!-- University Hall Exterior -->
      <rect x="20" y="40" width="360" height="130" fill="#d9cfba" stroke="#555" stroke-width="2"/>
      <!-- Corrugated Roof Line -->
      <polygon points="10,40 200,8 390,40" fill="#807055" stroke="#443928" stroke-width="2"/>
      <!-- Hall Entrance Doors -->
      <rect x="160" y="90" width="80" height="80" fill="#2c3a47" stroke="#1a252f" stroke-width="2"/>
      <!-- Student Gathering Silhouette -->
      <circle cx="175" cy="130" r="10" fill="#1b262c"/>
      <circle cx="200" cy="125" r="11" fill="#1b262c"/>
      <circle cx="225" cy="132" r="10" fill="#1b262c"/>
      <!-- Historic WOR Event Banner -->
      <rect x="50" y="55" width="300" height="26" fill="#e63946" rx="3" stroke="#fff" stroke-width="1"/>
      <text x="200" y="73" fill="#fff" font-family="'Afacad', sans-serif" font-weight="700" font-size="12" text-anchor="middle">WORDS ON RAMPAGE 2015 · SIFAX HALL</text>
    </svg>`,
    atmosphere: "Whirring ceiling fans, crowded wooden benches, student notebooks rustling in the afternoon heat.",
    poetsPresent: ["Vic'Adex", "Tomi"]
  },
  "lautech-gate": {
    name: "LAUTECH Main Gate (Old Ogbomoso-Ilorin Rd)",
    era: "c. 2010s Campus Gateway",
    desc: "The primary arched entrance welcoming traveling poets, writers, and students off the Old Ogbomoso-Ilorin highway.",
    svgTexture: `<svg viewBox="0 0 400 180" style="width:100%;height:auto;border-radius:6px;background:#172126;">
      <!-- Highway Road Surface -->
      <rect x="0" y="130" width="400" height="50" fill="#3a3d40"/>
      <line x1="0" y1="155" x2="400" y2="155" stroke="#ffd166" stroke-width="2" stroke-dasharray="16 12"/>
      <!-- Entrance Pylons -->
      <rect x="100" y="30" width="32" height="110" fill="#ece3cf" stroke="#8b8c80" stroke-width="1.5"/>
      <rect x="268" y="30" width="32" height="110" fill="#ece3cf" stroke="#8b8c80" stroke-width="1.5"/>
      <!-- Overarching Beam -->
      <rect x="80" y="20" width="240" height="25" fill="#0b5f78" rx="2" stroke="#fff" stroke-width="1"/>
      <text x="200" y="37" fill="#fffaf0" font-family="'Comfortaa', sans-serif" font-weight="700" font-size="11" text-anchor="middle">LAUTECH MAIN GATE · OGBOMOSO</text>
      <!-- Moving Yellow Shared Cab / Bus -->
      <rect x="170" y="135" width="60" height="30" fill="#e9c46a" rx="4" stroke="#333" stroke-width="1"/>
      <rect x="180" y="138" width="18" height="12" fill="#5c80a8"/>
      <circle cx="185" cy="165" r="5" fill="#111"/>
      <circle cx="215" cy="165" r="5" fill="#111"/>
    </svg>`,
    atmosphere: "Interstate motor sounds, roadside fruit stalls, students sharing yellow cabs under the midday sun.",
    poetsPresent: []
  },
  "under-g": {
    name: "Under-G Gate & Court",
    era: "c. 2010s Acoustic & Reading Hub",
    desc: "Second university gate leading into the lively Under-G student village, filled with print shops, cafes, and open-mic lounges.",
    svgTexture: `<svg viewBox="0 0 400 180" style="width:100%;height:auto;border-radius:6px;background:#181e18;">
      <!-- Shopfronts -->
      <rect x="30" y="60" width="100" height="100" fill="#c7b594" stroke="#555" stroke-width="1.5"/>
      <rect x="150" y="60" width="100" height="100" fill="#e1d5bc" stroke="#555" stroke-width="1.5"/>
      <rect x="270" y="60" width="100" height="100" fill="#b0a282" stroke="#555" stroke-width="1.5"/>
      <!-- Signboards -->
      <rect x="40" y="70" width="80" height="16" fill="#2a9d8f"/>
      <text x="80" y="82" fill="#fff" font-size="9" text-anchor="middle" font-weight="bold">PRINT & BIND</text>
      <rect x="160" y="70" width="80" height="16" fill="#e76f51"/>
      <text x="200" y="82" fill="#fff" font-size="9" text-anchor="middle" font-weight="bold">LION'S LOUNGE</text>
      <!-- Evening string lights -->
      <path d="M20 40 Q200 65 380 40" fill="none" stroke="#ffd166" stroke-width="1" stroke-dasharray="3 7"/>
    </svg>`,
    atmosphere: "Generator hum, photocopiers humming as chapbooks are stapled, evening suya aroma.",
    poetsPresent: ["Bayo", "Sade"]
  },
  "muson": {
    name: "MUSON Centre (Onikan, Lagos)",
    era: "c. 2000s–Present Classical & Spoken Stage",
    desc: "Lagos' premier conservatory auditorium hosting acoustic poetry recitals, national awards, and orchestral spoken-word collabs.",
    svgTexture: `<svg viewBox="0 0 400 180" style="width:100%;height:auto;border-radius:6px;background:#0d1520;">
      <!-- White neoclassical colonnade facade -->
      <rect x="30" y="50" width="340" height="120" fill="#f8f9fa" stroke="#ccc" stroke-width="1.5"/>
      <polygon points="20,50 200,15 380,50" fill="#e9ecef" stroke="#adb5bd" stroke-width="2"/>
      <!-- Columns -->
      <line x1="80" y1="50" x2="80" y2="170" stroke="#ced4da" stroke-width="8"/>
      <line x1="140" y1="50" x2="140" y2="170" stroke="#ced4da" stroke-width="8"/>
      <line x1="200" y1="50" x2="200" y2="170" stroke="#ced4da" stroke-width="8"/>
      <line x1="260" y1="50" x2="260" y2="170" stroke="#ced4da" stroke-width="8"/>
      <line x1="320" y1="50" x2="320" y2="170" stroke="#ced4da" stroke-width="8"/>
      <!-- Title plate -->
      <rect x="120" y="32" width="160" height="16" fill="#0b5f78" rx="2"/>
      <text x="200" y="44" fill="#fff" font-size="10" text-anchor="middle" font-weight="bold">MUSON CENTRE · ONIKAN</text>
    </svg>`,
    atmosphere: "Polished hardwood stage, acoustics carrying every syllable, hushed theatre audience.",
    poetsPresent: ["Titilope Sonuga"]
  },
  "merit-house": {
    name: "Merit House (Maitama, Abuja)",
    era: "c. 2010s FCT Festival Stage",
    desc: "National convention amphitheatre in Maitama where major civic poetry slams, national recitals, and AIPFest sessions convene.",
    svgTexture: `<svg viewBox="0 0 400 180" style="width:100%;height:auto;border-radius:6px;background:#141d26;">
      <rect x="40" y="45" width="320" height="125" fill="#e3ded3" stroke="#555" stroke-width="2"/>
      <rect x="50" y="25" width="300" height="20" fill="#2b580c" rx="2"/>
      <text x="200" y="39" fill="#fff" font-size="11" text-anchor="middle" font-weight="bold">MERIT HOUSE · ABUJA</text>
      <!-- Diplomatic glass atrium -->
      <rect x="130" y="70" width="140" height="95" fill="#438a5e" fill-opacity="0.6" stroke="#2b580c" stroke-width="2"/>
    </svg>`,
    atmosphere: "High vaulted hall, diplomatic guests, resonant microphone system.",
    poetsPresent: ["Dike Chukwumerije"]
  },
  "alliance-jos": {
    name: "Alliance Française de Jos",
    era: "c. 2010s Plateau Spoken Word Hub",
    desc: "Historic cultural centre nestled in the cool Jos hills, renowned for intimate poetry sessions, acoustic guitars, and bilingual verse.",
    svgTexture: `<svg viewBox="0 0 400 180" style="width:100%;height:auto;border-radius:6px;background:#151d18;">
      <!-- Stone pavilion -->
      <rect x="40" y="55" width="320" height="115" fill="#8d99ae" stroke="#2b2d42" stroke-width="2"/>
      <polygon points="30,55 200,20 370,55" fill="#d90429" stroke="#700" stroke-width="2"/>
      <!-- French / Cultural Emblem -->
      <circle cx="200" cy="40" r="10" fill="#fff"/>
      <text x="200" y="80" fill="#edf2f4" font-size="11" text-anchor="middle" font-weight="bold">ALLIANCE FRANÇAISE DE JOS</text>
      <!-- Mountain plateau backdrop -->
      <polygon points="0,50 80,15 160,50" fill="#2b3a2f"/>
      <polygon points="240,50 320,10 400,50" fill="#2b3a2f"/>
    </svg>`,
    atmosphere: "Crisp evening plateau breeze, hot ginger tea, warm acoustic chords behind spoken word.",
    poetsPresent: ["Victor Words Meshak"]
  }
};

function renderVenueVignette(venueId) {
  const data = venueArchivalData[venueId] || {
    name: "Documented Poetry Venue",
    era: "Historic Atlas Record",
    desc: "A verified Nigerian spoken word and poetry venue recorded in the Poetics Atlas.",
    svgTexture: `<svg viewBox="0 0 400 180" style="width:100%;height:auto;border-radius:6px;background:#161b22;"><rect width="400" height="180" fill="#161b22"/><text x="200" y="95" fill="#8b949e" font-size="13" text-anchor="middle">Historic Poetry Venue Archive</text></svg>`,
    atmosphere: "Local gathering of voices, sharing original verse across generations.",
    poetsPresent: []
  };

  return `
    <div class="venue-vignette-card" style="background:#161b22;border:1px solid rgba(255,255,255,0.15);border-radius:8px;padding:16px;margin:16px 0;animation:fadeIn 0.25s ease;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
        <div>
          <span style="font-size:11px;font-weight:700;color:#e63946;text-transform:uppercase;letter-spacing:1px;">Archival Waypoint · GTA Polygon Facade</span>
          <h3 style="margin:4px 0 2px 0;color:#fff;font-size:18px;">${data.name}</h3>
          <span style="font-size:12px;color:#8b949e;">${data.era}</span>
        </div>
        <span style="background:rgba(42,157,143,0.15);border:1px solid #2a9d8f;color:#52b788;font-size:11px;padding:4px 8px;border-radius:4px;font-weight:600;">
          Atlas Grounded
        </span>
      </div>

      <div class="venue-svg-wrapper" style="border:1px solid rgba(255,255,255,0.12);border-radius:6px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.5);">
        ${data.svgTexture}
      </div>

      <p style="margin:12px 0 8px 0;color:#c9d1d9;font-size:14px;line-height:1.5;">${data.desc}</p>
      
      <div style="background:rgba(255,255,255,0.03);border-left:3px solid #ffd166;padding:8px 12px;margin:10px 0;border-radius:0 4px 4px 0;">
        <strong style="font-size:12px;color:#ffd166;display:block;margin-bottom:2px;">Scene Atmosphere:</strong>
        <em style="font-size:13px;color:#e6edf3;">"${data.atmosphere}"</em>
      </div>

      ${data.poetsPresent && data.poetsPresent.length ? `
        <div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <strong style="font-size:12px;color:#8b949e;">Poets Recorded Here:</strong>
          ${data.poetsPresent.map(p => `<span style="background:rgba(255,255,255,0.08);padding:2px 8px;border-radius:12px;font-size:12px;color:#58a6ff;">✦ ${p}</span>`).join('')}
        </div>
      ` : ''}
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
  renderVenueVignette,
  venueArchivalData,
  getTransitAnimation
};

if (typeof module !== 'undefined') module.exports = api;
root.PoeticsLivingSim = api;

})(typeof window !== 'undefined' ? window : globalThis);
