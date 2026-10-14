from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];p=root/'dist/atlas-audit.json';d=json.loads(p.read_text())
A='https://thenationonlineng.net/writers-brace-up-in-abia/amp/'
Y='https://independent.ng/at-70-im-still-hopeful-of-seeing-my-script-on-screen-adebiyi/'
def add(id,name,category,city,summary,**extra):
 row=dict(id=id,name=name,category=category,city=city,summary=summary,status='Participant account; source-scoped',verification=dict(label='Report supported',sourceURL=A,reviewedAt='2026-10-13',scope=summary),links=[dict(title='Article text retrieved through search; direct fetch blocked',url=A)],years=[dict(year=2024,label='Report evidence, not publication or founding year',url=A)],media=[],**extra)
 old=next((x for x in d['profiles'] if x['id']==id),None)
 if old:old.update(row)
 else:d['profiles'].append(row)
def edge(a,b,label,url=A,date=2024):
 row=dict(a=a,b=b,label=label,url=url,date=date,status='Source-stated role; independent corroboration pending')
 if not any(all(e.get(k)==row[k] for k in ['a','b','label','url']) for e in d['relationships']):d['relationships'].append(row)
add('ana-abia-august-2024','ANA Abia — August Reading (2024)','Platforms','Aba','Reported chapter gathering.',historical=True,eventEvidence='Held — single newspaper report',dateFact=dict(label='Reported event',value='30 August 2024',url=A),dateBasis='Published 8 September; full text via search, direct 403. Independent corroboration pending.')
add('abia-polytechnic','Abia State Polytechnic','Places','Aba','Reported venue.',gaps='Exact room unverified.')
add('ijioma-ijiriji','Ijioma (Ijiriji)','People','Aba','Reported spoken-word performer.',nameVariants=['Ijiriji'],gaps='Full identity unresolved.')
add('chris-nkoro','Chris Nkoro','People','Aba','Reported poetry reader.')
add('chukwudifu-uzomah','Chukwudifu Emma Uzomah','People','Aba','Chapter chair and cited author.')
add('chibueze-orie','Chibueze Prince Orie','People','Aba','Reported poetry performer.',nameVariants=['Chibueze Orie'])
add('flames-discord','The Flames of Discord','Publications','Nigeria','Book cited in programme.',publicationState='Cited book — metadata unresolved',dateBasis='2024 is citation year; genre, publication date and imprint unknown.')
for b,label in [('ana-abia','chapter programme'),('abia-polytechnic','venue'),('ijioma-ijiriji','spoken-word performer'),('chris-nkoro','poetry reader'),('chibueze-orie','poetry performer'),('flames-discord','song source cited')]:edge('ana-abia-august-2024',b,label)
edge('chukwudifu-uzomah','ana-abia','chair in account');edge('chukwudifu-uzomah','flames-discord','author attributed')
row=next(x for x in d['profiles'] if x['id']=='rhapsodies-corper');row.update(dateFact=dict(label='First publication recalled by author',value='1998',url=Y),dateBasis='Author interview, 18 November 2023. Publisher/ISBN not verified.',publicationState='Author-recalled publication; imprint unresolved')
row['years']=[dict(year=1998,label='Author-recalled publication year',url=Y)]
if not any(l['url']==Y for l in row['links']):row['links'].append(dict(title='Author interview',url=Y))
edge('yemi-adebiyi','rhapsodies-corper','author recalls first publication',Y,1998)
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,indent=2)+';\n')
p=root/'research/discovery-matrix.json';m=json.loads(p.read_text());m['followUpBatches']=[x for x in m['followUpBatches'] if x['id']!='2026-10-13-hourly-first-check']+[dict(id='2026-10-13-hourly-first-check',matrix='hourly-first-check-queries.json',queryCount=4)];m['cumulativeQueryCount']=m['queryCount']+sum(x['queryCount'] for x in m['followUpBatches']);p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print('First check: added supported records; attributed book year; no publisher/ISBN or completed Ojokoro inference')
