from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];r=root/'research';p=root/'dist/atlas-audit.json';d=json.loads(p.read_text());claims=[]
K='https://thenigerianpost.com.ng/a-tapestry-of-words-the-cross-country-poetry-celebration-in-kogi-2/'
U='https://profile.unizik.edu.ng/NAU4594';I='https://writezakama.wordpress.com/2023/10/17/update-on-cross-country-celebration-of-poetry/';T='https://ansa.com.ng/team/'
def add(id,name,cat,city,text,url,year=None,label='Report supported',**kw):
 row=dict(id=id,name=name,category=cat,city=city,summary=text,status=label+'; source-scoped',verification=dict(label=label,sourceURL=url,reviewedAt='2026-10-13',scope=text),links=[dict(title='Reviewed source',url=url)],years=[] if year is None else [dict(year=year,label='Role / event evidence, not founding or publication year',url=url)],media=[],gaps='Independent corroboration and present activity unverified.',**kw)
 old=next((x for x in d['profiles'] if x['id']==id),None)
 if old:old.update(row)
 else:d['profiles'].append(row)
 claims.append(dict(entity=id,claim=text,sourceURL=url,status=label,confidence='High for source attribution; independent event corroboration absent'))
def edge(a,b,label,url,date=None,status='Only the source-stated relationship; not current residence or headquarters'):
 e=dict(a=a,b=b,label=label,url=url,date=date,status=status)
 if not any(all(x.get(k)==e[k] for k in ['a','b','label','url']) for x in d['relationships']):d['relationships'].append(e)
 claims.append(dict(entity=a,claim=label+' → '+b,sourceURL=url,status=status,confidence='High for attributed role'))
# Correct current access/provenance without rewriting failed-access history.
old='https://profile.unizik.edu.ng/nau4594'
def replace(x):
 if isinstance(x,dict):return {k:replace(v) for k,v in x.items()}
 if isinstance(x,list):return [replace(v) for v in x]
 return U if x==old else x
d=replace(d)
for id in ['ccpc-awka-2023','uche-nnyagu','awka-window']:
 row=next(x for x in d['profiles'] if x['id']==id)
 row['gaps']='Official profile opened directly 13 October 2026. Exact event day and additional participants remain unverified.'
 row['verification']['reviewedAt']='2026-10-13'
 claims.append(dict(entity=id,claim='Direct official profile read: October 2023 panelist / setting supported; exact day unknown.',sourceURL=U,status='Primary profile confirmed',confidence='High for attributed participation'))
add('vincent-eze-awka','Vincent Eze (Awka itinerary)','People','Awka','Named planned host in the 2023 itinerary; attendance unverified.',I,2023,'Announcement verified')
edge('vincent-eze-awka','ccpc-awka-2023','announced host only',I,2023,'Itinerary; role performance / attendance not verified')
add('ccpc-lokoja-2024','Cross Country Poetry Celebration — Lokoja (2024)','Platforms','Lokoja','Post-event report documents poetry, spoken word and cultural performances.',K,2024,eventEvidence='Held — single report family; independent corroboration pending',historical=True,dateFact=dict(label='Reported event',value='26 October 2024',url=K),dateBasis='Report published 28 October. Kogi Reports repeats substantial wording; not independent corroboration. No link to the separate 2023 Kogi itinerary or venue host inferred.')
add('ful-faculty-arts','Federal University Lokoja — Faculty of Arts','Places','Lokoja','Venue named in the post-event report.',K,2024,nameVariants=['Faculty of Art,cFederal University Lokoja','Faculty of Art, Federal University Lokoja'],dateBasis='Normalized readable label; source typo preserved. No exact room or campus coordinate inferred.')
add('ansa','Association of Nigerian Student Authors (ANSA)','Platforms','Nigeria','Named co-organizer; identity also supported by ANSA’s own site.',K,2024)
add('naya','National Association of Young Authors (NAYA)','Platforms','Nigeria','Named collaborator in the report.',K,2024)
add('gaya','Global Association of Young Authors (GAYA)','Platforms','Nigeria','Named collaborator in the report.',K,2024)
add('penkup-international','PENKUP International','Platforms','Nigeria','Named sponsor in the report.',K,2024)
add('maymunah-kadiri','Maymunah Kadiri (ANSA poet)','People','Lokoja','Reported speaker and Q&A participant; ANSA’s site identifies the poet.',K,2024,dateBasis='Lokoja is this event association, not residence. No merge with similarly named people outside this literary context.')
for b,l in [('ful-faculty-arts','reported venue'),('ansa','co-organizer reported'),('c2','co-organizer reported'),('naya','collaborator reported'),('gaya','collaborator reported'),('penkup-international','sponsor reported'),('maymunah-kadiri','speech and Q&A participant reported')]:edge('ccpc-lokoja-2024',b,l,K,2024,'Single post-event report family; independent corroboration pending')
edge('maymunah-kadiri','ansa','president in 2024 report',K,2024)
add('dont-love-yourself','Don’t Love Yourself','Publications','Nigeria','Chapbook attributed to Maymunah Kadiri by ANSA’s own team profile.',T,None,'Primary attribution confirmed',publicationState='Chapbook listed — publisher metadata unverified',dateBasis='Undated team profile; publication date, publisher, ISBN and genre unverified.')
edge('maymunah-kadiri','dont-love-yourself','author attributed',T,None,'Primary professional biography; bibliographic metadata pending')
for id in ['ansa','maymunah-kadiri']:
 row=next(x for x in d['profiles'] if x['id']==id)
 if not any(l['url']==T for l in row['links']):row['links'].append(dict(title='ANSA primary identity / author profile',url=T))
claims.append(dict(entity='ansa',claim='ANSA page heading expands Student Authors, but Maymunah biography erroneously expands Nigerian Authors. Do not merge ANSA with ANA; undated leadership not current-office proof.',sourceURL=T,status='Source inconsistency preserved',confidence='Identity supported by page heading; biography acronym expansion inconsistent'))
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,indent=2)+';\n')
(r/'kogi-awka-claims.json').write_text(json.dumps(dict(reviewedAt='2026-10-13',claims=claims,sourceFamilies={'Kogi post-event':['The Nigerian Post original and -2 URL','Kogi Reports substantial repeated wording','Accurate News indexed repetition; direct blocked'],'Awka participation':['Official UNIZIK profile'],'Awka planned host':['2023 national itinerary'],'Identity/publication':['ANSA undated primary team page']}),indent=2,ensure_ascii=False)+'\n')
p=r/'south-south-sources.json';s=json.loads(p.read_text());
def correct(x):
 if isinstance(x,dict):
  if x.get('url')==old:x.update(url=U,access='Full text read; direct uppercase URL also opened on 13 October 2026',accessHistory='Prior failed attempts, if recorded, superseded by current direct retrieval; no exact event day established.')
  for v in x.values():correct(v)
 elif isinstance(x,list):
  for v in x:correct(v)
correct(s);p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print('Saved',len(claims),'claims; corrected Awka access; preserved source-family limits')
