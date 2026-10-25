(function(root){
'use strict';
root.PoeticsCreateBundledAtlasSnapshot=function(atlas){
 const categoryByType={Person:'People',Place:'Places',Venue:'Places',Prize:'Prizes',Publication:'Publications'};
 const entryTypes={People:'Cultural practitioner',Places:'Place / venue',Platforms:'Platform / organisation',Prizes:'Prize / competition',Publications:'Publication'};
 const rows=atlas.records.map(record=>{
  const source=atlas.sources[record.source]||{},url=source.url||'',category=categoryByType[record.type]||'Platforms';
  return {...record,category,summary:record.description||'',details:record.description||'',locationLabel:record.city||'Location not yet verified',entryType:entryTypes[category],verification:{label:'Verification pending',scope:source.scope||'Bundled source; claim review pending.',sourceURL:url,sourceLocator:''},links:url?[{url,title:source.title||record.source}]:[],media:[],years:record.year?[{year:record.year}]:[],dateBasis:'Years describe linked source evidence, not a founding date.',availability:'Availability not assessed in bundled fallback.'};
 });
 const ids=new Set(rows.map(record=>record.id));
 const edges=atlas.edges.flatMap(edge=>{const source=atlas.sources[edge[3]];return ids.has(edge[0])&&ids.has(edge[1])&&source?.url?[{a:edge[0],b:edge[1],label:edge[2],date:edge[4]??null,url:source.url,status:'Source association; claim review pending.'}]:[];});
 return {rows,edges};
};
})(window);
