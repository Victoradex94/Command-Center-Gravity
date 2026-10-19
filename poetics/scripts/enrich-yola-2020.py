from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];p=root/'dist/atlas-audit.json';d=json.loads(p.read_text());U='https://www.aun.edu.ng/index.php/news-events/news/aun-sga-yola-group-hold-arts-festival-for-charity'
items=[('adamawa-arts-festival-2020','Adamawa Arts Festival — 2020','Platforms','Completed multi-arts festival including poetry and spoken word; occurrence reported by AUN.'),('adamawa-arts','Adamawa Arts','Platforms','Yola-based artists group named as a festival collaborator in AUN’s 2020 account.'),('aun-sga','AUN Student Government Association','Platforms','Student association named as festival co-organiser in the university’s 2020 report.'),('taslim-ladoja','Taslim Ladoja','People','Named SGA president in the 2020 festival report; no current office or poetry performance inferred.'),('ogungbebi-timiletin','Ogungbebi Timiletin','People','Named as one of the festival organisers; no poet identity or performance inferred.')]
for id,name,cat,summary in items:
 r=dict(id=id,name=name,category=cat,city='Yola',summary=summary,status='First-party institutional report; source-scoped',verification=dict(label='Institutional report supported',sourceURL=U,reviewedAt='2026-10-14',scope=summary),links=[dict(title='AUN first-party post-event report — 19 February 2020',url=U)],years=[dict(year=2020,label='Documented festival association, not founding or birth',url=U)],media=[],gaps='Current activity and independent corroboration unverified; no residence inference.')
 if id=='adamawa-arts-festival-2020':r.update(historical=True,eventEvidence='Held — first-party institutional report',dateFact=dict(label='Reported event dates',value='14–16 February 2020',url=U),dateBasis='Published19February2020. Broad AUN/Yola setting; exact room/venue not specified.',gaps='No exact venue-room or named poetry performer; current recurrence unverified.')
 if not any(x['id']==id for x in d['profiles']):d['profiles'].append(r)
existing_rels = {(x.get('a'), x.get('b'), x.get('label')) for x in d['relationships']}
for a,b,label in [('adamawa-arts-festival-2020','adamawa-arts','festival collaborator'),('adamawa-arts-festival-2020','aun-sga','festival co-organiser'),('taslim-ladoja','aun-sga','president in 2020 account'),('adamawa-arts-festival-2020','ogungbebi-timiletin','named organiser')]:
 e=dict(a=a,b=b,label=label,url=U,date=2020,status='Source-stated role in 2020; not current-office inference')
 if (a, b, label) not in existing_rels:
  d['relationships'].append(e)
  existing_rels.add((a, b, label))
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,indent=2)+';\n')
