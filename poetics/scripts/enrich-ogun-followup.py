from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
p=root/'dist/atlas-audit.json';d=json.loads(p.read_text())
G='https://guardian.ng/art/ogun-marks-2024-cross-country-poetry-celebration-with-funfair/'
L='https://ng.linkedin.com/in/inioluwa-sanyaolu-333997364'
for id,name,summary,url,status in [
 ('martins-akinyemi','Martins A. Akinyemi','Named goodwill-message contributor in the Guardian account of the 2024 Abeokuta poetry gathering. A goodwill message does not establish physical attendance.',G,'Single newspaper report'),
 ('inioluwa-sanyaolu','Inioluwa Sanyaolu','Self-reported October 2024 certificates for presenting a poem and volunteering at the Cross Country Poetry Celebration, Abeokuta location. Exact day and venue not established by the profile.',L,'Participant self-report via indexed profile')]:
 row=dict(id=id,name=name,category='People',city='Abeokuta',summary=summary,status=status,verification=dict(label=status,sourceURL=url,reviewedAt='2026-10-14',scope=summary),links=[dict(title='Source-stated role; exact day unresolved',url=url)],years=[dict(year=2024,label='Reported contribution year, not residence or birth',url=url)],media=[],gaps='No residence inference. Profile direct fetch returned 999; relevant certification section read through search.' if url==L else 'Message delivery mode and physical attendance unverified.')
 if not any(x['id']==id for x in d['profiles']):d['profiles'].append(row)
 edge=dict(a='ccpc-abeokuta-2024',b=id,label='participant self-reports poetry presentation and volunteering' if url==L else 'reported goodwill message contributor',url=url,date=2024,status=status)
 if not any(x.get('a')==edge['a'] and x.get('b')==id for x in d['relationships']):d['relationships'].append(edge)
r=next(x for x in d['profiles'] if x['id']=='ccpc-abeokuta-2024')
r['links'].append(dict(title='Participant self-report: October 2024 Abeokuta certificates; exact venue/day not stated',url=L))
r['gaps']='Guardian occurrence account plus separate participant self-report through indexed profile. Exact day still unverified; participant profile does not corroborate USC venue or host roles.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,indent=2)+';\n')
