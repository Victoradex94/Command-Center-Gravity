'use strict';
(function(){
const shapes={Publications:'<path d="M3 4h7a3 3 0 0 1 3 3v14a4 4 0 0 0-4-2H3V4Zm18 0h-5a3 3 0 0 0-3 3m0 14a4 4 0 0 1 4-2h4V4"/>',People:'<circle cx="12" cy="7" r="3"/><path d="M5 21v-3a7 7 0 0 1 14 0v3"/>',Places:'<path d="M19 9c0 5-7 12-7 12S5 14 5 9a7 7 0 1 1 14 0Z"/><circle cx="12" cy="9" r="2"/>',Platforms:'<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',Prizes:'<path d="M8 3h8v5a4 4 0 0 1-8 0V3ZM8 5H4v3a4 4 0 0 0 4 4m8-7h4v3a4 4 0 0 1-4 4M12 12v6m-4 3h8m-6-3h4v3"/>'};
window.PoeticsIcon=category=>`<svg class="entry-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${shapes[category]||shapes.Platforms}</svg>`;
})();
