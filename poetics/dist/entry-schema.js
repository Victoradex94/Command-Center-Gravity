'use strict';
(function(){
const generic=/^(Announced gathering\.|Listed venue\.|Listed host\.|Programme-listed contributor\.|Programme-listed venue\.|Named in event announcement\.)$/;
function prepare(rows,edges,atlas){
 for(const [oldId,canonicalId] of [['kapfest','kap'],['nasara-creative','nasara']]){
  const duplicate=rows.find(r=>r.id===oldId),canonical=rows.find(r=>r.id===canonicalId);
  if(!duplicate||!canonical)continue;
  const pilot=canonical.pilot,links=(canonical.links||[]).concat(duplicate.links||[]),years=(canonical.years||[]).concat(duplicate.years||[]);
  Object.assign(canonical,duplicate,{id:canonicalId,pilot,links,years});
  rows.splice(rows.indexOf(duplicate),1);
  for(const e of edges){if(e.a===oldId)e.a=canonicalId;if(e.b===oldId)e.b=canonicalId;}
 }
 const seen=new Set();for(let i=edges.length-1;i>=0;i--){const e=edges[i],key=JSON.stringify([e.a,e.b,e.label,e.url,e.date]);if(seen.has(key))edges.splice(i,1);else seen.add(key);}
 for(const r of rows){
  const p=r.pilot;
  if(p?.source==='cross2023'){
   const number=p.id.match(/cross-(?:event|host|venue)-(\d+)/)?.[1],event=rows.find(n=>n.id==='cross-event-'+number);
   if(event?.pilot){event.name='Cross Country Celebration of Poetry — '+event.city;const host=rows.find(n=>n.id==='cross-host-'+number),venue=rows.find(n=>n.id==='cross-venue-'+number);if(!event.eventEvidence)event.summary='Announced poetry gathering'+(venue?' at '+venue.name:'')+(host?', hosted by '+host.name:'')+'. Exact event date unconfirmed.';event.kind='Poetry gathering';}
   if(!r.verification){if(p.type==='Person')r.summary='Named host for the '+r.city+' programme stop; attendance unconfirmed.';if(p.type==='Venue')r.summary='Announced venue for the '+r.city+' programme stop; occurrence unconfirmed.';}
   r.dateFact=r.dateFact||{label:'Source update',value:'17 October 2023',url:atlas.sources.cross2023.url};
   r.dateBasis=r.dateBasis||'Announcement dated 17 October 2023; exact gathering date not established.';
  }
  if(generic.test(r.summary||'')){
   const related=edges.filter(e=>!e.association&&(e.a===r.id||e.b===r.id)).map(e=>({edge:e,other:rows.find(n=>n.id===(e.a===r.id?e.b:e.a))})).filter(x=>x.other);
   const first=related[0];
   if(first)r.summary=(r.category==='People'?'Named contributor':r.category==='Places'?'Documented venue':'Source-listed entry')+' connected to '+first.other.name+'. '+first.edge.label+'; participation or occurrence only as qualified by the source.';
   else r.summary='Source records this '+r.category.toLowerCase()+' entry; its specific role still needs verification.';
  }
 }
}
function standardize(r){
 const defaults={People:'Cultural practitioner',Places:'Place / venue',Platforms:'Platform / organisation',Prizes:'Prize / competition',Publications:'Publication'};
 r.entryType=r.kind||r.placeType||(r.category==='People'?defaults.People:r.format&&r.format!=='Other / not classified'?r.format:r.pilot?.type==='Event'?'Poetry event':defaults[r.category]);
 r.locationLabel=r.city||'Location not yet verified';
 r.dateBasis=r.dateBasis||'Years describe the linked source, programme, publication or relationship evidence—not an inferred birth or founding date.';
 r.dateLabel=r.dateFact?r.dateFact.label+': '+r.dateFact.value:r.years.length?'Evidence years: '+r.yearLabel:'Dates not yet verified';
 r.standardEntry={name:r.name,category:r.category,type:r.entryType,description:r.details,location:r.locationLabel,dates:r.dateLabel,dateMeaning:r.dateBasis,verification:r.verification.label,activity:r.activityStatus?.label||r.publicationState||'Not assessed',sources:r.links};
}
window.PoeticsEntrySchema={prepare,standardize};

// Presentation is derived without rewriting the research rows or their original dates.
const confidenceLevels=[
 {key:'unconfirmed',label:'Unconfirmed',definition:'The core entry has not had a recorded direct source review yet.'},
 {key:'weak',label:'Weak',definition:'Reviewed support is limited to an index, listing or a source whose basis remains unclear.'},
 {key:'strong',label:'Strong',definition:'A directly reviewed primary source or credible report supports the entry as worded, including its qualifications.'},
 {key:'very-strong',label:'Very strong',definition:'A primary source and a separately assessed independent source family corroborate the same core claim, with no unresolved core conflict.'}
];
const reviewedLabels=new Set(['Source confirmed','Report supported','Archive supported','Announcement verified','Primary biography confirmed','Organizer-attributed','Primary attribution confirmed','Catalogue supported','Single newspaper report','Institutional record supported','Institutional report supported','Report-supported; not independently corroborated','Source-supported, role-specific','Primary organiser-associated report','Primary support-programme account']);
function confidence(r,assessment=r.entryConfidenceAssessment){
 const v=r.verification||{};let key='unconfirmed',reason='A source link alone is not a recorded claim review.';
 if(window.PoeticsEntryStatus?.validDate(v.reviewedAt)&&/^https?:\/\//.test(v.sourceURL||'')&&v.label!=='Verification pending'){
  key=reviewedLabels.has(v.label)?'strong':'weak';
  reason=key==='strong'?'Recorded source review supports the qualified entry. This does not establish independent corroboration, current activity or event completion.':'The recorded review is limited or indirect; stronger direct support is still needed.';
 }
 // Several URLs, copied reports or a primary source alone never trigger this level.
 if(assessment?.level==='very-strong'&&assessment.entryId===r.id&&window.PoeticsEntryStatus?.validDate(assessment.reviewedAt)&&assessment.claim&&assessment.corroborated===true&&!assessment.unresolvedCoreConflict){
  const sources=(assessment.sources||[]).filter(s=>s.directlyRead===true&&s.family&&/^https?:\/\//.test(s.url||''));
  const primary=sources.find(s=>s.role==='primary');
  if(primary&&sources.some(s=>s.role==='independent'&&s.family!==primary.family&&s.url!==primary.url)){
   key='very-strong';reason=assessment.reason||'Explicit claim review records primary and independent-family corroboration.';
  }
 }
 return {...confidenceLevels.find(c=>c.key===key),reason,reviewedAt:v.reviewedAt||null,originalLabel:v.label||'Not assessed'};
}
function span(years){const sorted=[...new Set(years.filter(y=>Number.isInteger(y)&&y>=1800&&y<=2200))].sort((a,b)=>a-b);return sorted.length?sorted[0]===sorted.at(-1)?String(sorted[0]):sorted[0]+'–'+sorted.at(-1):'Not established';}
function yearRange(r,now=new Date()){
 const today=now.toISOString().slice(0,10),valid=window.PoeticsEntryStatus?.validDate||(()=>false);
 const activity=(r.activities||[]).filter(a=>valid(a.date)&&a.date<=today&&/^https?:\/\//.test(a.url||'')&&['held event','programme announcement','call','award','publication'].includes(a.kind));
 if(activity.length)return {label:'Years active',value:span(activity.map(a=>Number(a.date.slice(0,4)))),note:'Explicitly dated organising or creative activity only. This is not a continuous lifespan; other dated references remain in the evidence.',basis:'activity'};
 return {label:'Recorded span',value:span((r.years||[]).map(y=>Number(y.year))),note:'Earliest to latest documented reference. Gaps, announcements and relationship dates do not establish continuous activity, founding, residence or attendance.',basis:'references'};
}
window.PoeticsEntryPresentation={confidence,confidenceLevels,yearRange,span,policyVersion:1};
})();
