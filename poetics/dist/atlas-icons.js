'use strict';
(function(){
// One selected illustrated set across cards, filters, lists and map counts.
// Decorative SVG wrappers preserve existing callers; visible category labels
// or their accessible parent labels continue to carry the category meaning.
const images={"People":"media/atlas-icons/people.defbe74a2641.webp","Places":"media/atlas-icons/places.99f980638728.webp","Platforms":"media/atlas-icons/platforms.8d1156512b02.webp","Prizes":"media/atlas-icons/prizes.9c5f180ca90d.webp","Publications":"media/atlas-icons/publications.f18f3d630fd9.webp"};
window.PoeticsIcon=category=>{const key=Object.hasOwn(images,category)?category:'Platforms';return `<svg xmlns="http://www.w3.org/2000/svg" class="entry-icon entry-icon-illustrated" data-category-icon="${key}" viewBox="0 0 100 100" aria-hidden="true" focusable="false"><image href="${images[key]}" width="100" height="100" preserveAspectRatio="xMidYMid meet"/></svg>`;};
})();
