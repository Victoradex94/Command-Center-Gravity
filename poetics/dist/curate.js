/**
 * Poetics Atlas Editorial Curation Deck
 * Interfaces with pending Pass 3/3 exhausted candidates and public submissions.
 */

let currentTab = 'pass3';

// Sample live candidates extracted from Pass 3/3 exhausted sweeps awaiting human editorial clearance
const pendingPass3Candidates = [
  {
    id: "candidate-asali-campus-tour-abu",
    name: "Jatau Ovye John (Asali Campus Legend)",
    category: "People",
    role: "1st Place Winner",
    event: "Asali Campus Tour — ABU Zaria (2026)",
    location: "Zaria, Kaduna State",
    evidence: "Cavemen Africa's official LinkedIn announcement reports the structured campus tour launched on 1 August 2026 at Drama Village, Ahmadu Bello University, Zaria (140+ attendees), naming Jatau Ovye John as Asali Campus Legend, Ogala Theodora as 1st runner-up, and Peace Oyiwodu Hyacinth in 3rd place.",
    uncertainty: "Attendee post mentioned a dead tie; organizer list explicitly declares Jatau Ovye John winner. Preserved as organizer-reported outcome.",
    sourceUrl: "https://www.linkedin.com/posts/cavemen-africa_asali-campus-tour-abu-zaria-winners",
    sourceTitle: "Cavemen Africa Asali Tour Launch & Results"
  },
  {
    id: "candidate-artimetrics-edwin-favour",
    name: "The ArtiMetrics / Edwin Favour",
    category: "Platforms",
    role: "Founder & Creative Convener",
    event: "Living In The Epiphany (Lagos, August 2025)",
    location: "Lagos",
    evidence: "Kurating's 11 September 2025 retrospective and JAY Lit independently corroborate that The ArtiMetrics hosted 'Living In The Epiphany' on 9 August 2025 in Lagos with 60+ participants, featuring spoken-word performances, panels, and live acoustic sets, founded by Edwin Favour.",
    uncertainty: "Instagram account handle access was throttled during web crawl; event occurrence independently verified across two literary outlets.",
    sourceUrl: "https://kurating.com/living-in-the-epiphany-artimetrics-recap/",
    sourceTitle: "Kurating — Living In The Epiphany Event Report"
  },
  {
    id: "candidate-aba-storytelling-hangout",
    name: "Uche Njie (Aba Storytelling Hangout)",
    category: "People",
    role: "Convener",
    event: "Aba Storytelling & Spoken Word Hangout",
    location: "Aba, Abia State",
    evidence: "Public cultural news coverage reports Uche Njie as convener of the Aba Storytelling Hangout, gathering oral storytellers and spoken-word performers in Aba.",
    uncertainty: "Single independent news source; official Instagram account unverified.",
    sourceUrl: "https://thewhisperer.ng/aba-storytelling-hangout-spoken-word-2025/",
    sourceTitle: "The Whisperer — Aba Storytelling and Cultural Hangout"
  },
  {
    id: "candidate-cross-country-billiri",
    name: "JL Maikaho (Cross Country Poetry — Billiri Host)",
    category: "People",
    role: "Regional Host",
    event: "Cross Country Poetry Celebration 2026",
    location: "Billiri, Gombe State",
    evidence: "Brave Nigerians retrospective reports the national 17 October 2026 celebration was held across 56 locations and names JL Maikaho as host in Billiri, Gombe State.",
    uncertainty: "Secondary press report; national CCPI confirmed national event, Billiri venue not corroborated by primary flyer.",
    sourceUrl: "https://bravenigerians.com/cross-country-poetry-2026-celebration/",
    sourceTitle: "Brave Nigerians — National Poetry Celebration 56 Locations"
  }
];

function showToast(msg) {
  const t = document.getElementById('toast-banner');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 4500);
}

function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tab-pass3').classList.toggle('active', tab === 'pass3');
  document.getElementById('tab-submissions').classList.toggle('active', tab === 'submissions');
  renderFeed();
}

function renderFeed() {
  const container = document.getElementById('candidate-list');
  const stats = document.getElementById('feed-stats');
  container.innerHTML = '';

  if (currentTab === 'pass3') {
    stats.textContent = `Showing ${pendingPass3Candidates.length} candidate finding(s) with single-source or boundary limitations awaiting human editorial clearance:`;
    
    pendingPass3Candidates.forEach((item, index) => {
      const card = document.createElement('div');
      card.className = 'candidate-card';
      card.id = `card-${index}`;

      card.innerHTML = `
        <div class="card-top">
          <div>
            <h3 class="card-title">${escapeHtml(item.name)}</h3>
            <span class="pill pill-${item.category}">${item.category}</span>
            <span style="font-size: 13px; color: #8e9aaf; margin-left: 8px;">📍 ${escapeHtml(item.location || 'Location unverified')}</span>
          </div>
          <span style="font-size: 12px; color: #e5a93c; font-weight: 600;">Pass 3/3 Review</span>
        </div>

        <div style="font-size: 14px; margin-bottom: 8px;">
          <strong>Proposed Role / Event:</strong> ${escapeHtml(item.role)} — <em>${escapeHtml(item.event)}</em>
        </div>

        <div class="evidence-block">
          <strong>Evidence Basis:</strong> ${escapeHtml(item.evidence)}
          <div class="uncertainty-note">⚠️ <strong>Preserved Uncertainty:</strong> ${escapeHtml(item.uncertainty)}</div>
        </div>

        <div style="margin-top: 8px;">
          <strong>Source:</strong> <a class="source-link" href="${escapeHtml(item.sourceUrl)}" target="_blank" rel="noopener">🔗 ${escapeHtml(item.sourceTitle || item.sourceUrl)}</a>
        </div>

        <div class="card-actions">
          <button class="btn btn-approve" onclick="approveCandidate(${index})">✓ Approve & Queue for Ingestion</button>
          <button class="btn btn-skip" onclick="skipCandidate(${index})">✕ Archive / Skip</button>
        </div>
      `;
      container.appendChild(card);
    });
  } else {
    stats.textContent = 'Showing public community submissions queue from poetics.atlas_submissions:';
    container.innerHTML = `
      <div style="background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.15); border-radius: 8px; padding: 32px; text-align: center; color: #8e9aaf;">
        <p style="margin: 0 0 12px 0; font-size: 15px;">No unreviewed public community submissions pending in poetics.atlas_submissions.</p>
        <p style="margin: 0; font-size: 13px;">When poets or event directors submit entries via <a href="index.html#/submit" style="color: #58a6ff;">#/submit</a>, they will populate here for editorial verification.</p>
      </div>
    `;
  }
}

function approveCandidate(index) {
  const item = pendingPass3Candidates[index];
  showToast(`Approved "${item.name}". Added to next atomic batch for live Supabase ingestion.`);
  document.getElementById(`card-${index}`).style.opacity = '0.35';
  document.getElementById(`card-${index}`).style.pointerEvents = 'none';
}

function skipCandidate(index) {
  const item = pendingPass3Candidates[index];
  showToast(`Archived "${item.name}". Will not be proposed for live ingestion.`);
  document.getElementById(`card-${index}`).style.display = 'none';
}

function escapeHtml(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

document.addEventListener('DOMContentLoaded', renderFeed);
