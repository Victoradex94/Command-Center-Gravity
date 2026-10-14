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
})();
