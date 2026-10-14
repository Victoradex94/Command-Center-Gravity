from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];path=root/'dist/atlas-audit.json';d=json.loads(path.read_text())
def rev(url,note,tier):return {'label':tier,'sourceURL':url,'reviewedAt':'2026-10-13','scope':note}
def add(id,name,cat,city,summary,url,year=None,tier='Report supported',meaning='Source evidence'):
 p={'id':id,'name':name,'category':cat,'city':city,'summary':summary,'verification':rev(url,summary,tier),'status':tier+'; claim-scoped review 13 October 2026','years':[{'year':year,'label':meaning,'url':url}] if year else [],'links':[{'title':'Reviewed source','url':url}],'media':[]}
 if not any(x['id']==id for x in d['profiles']):d['profiles'].append(p)
 return next(x for x in d['profiles'] if x['id']==id)
def edge(a,b,label,url,date=None,status='Published account; only the stated role is supported'):
 e={'a':a,'b':b,'label':label,'url':url,'date':date,'status':status}
 if not any(all(x.get(k)==e[k] for k in ['a','b','label','url']) for x in d['relationships']):d['relationships'].append(e)
A='https://aceworldpgs.com/highlight-of-first-poetry-slam-in/'
K='https://culturecustodian.com/poetic-wednesdays-unveils-reclaiming-languages-as-the-theme-for-kapfest-3-0/'
U='https://www.premiumtimesng.com/news/more-news/892736-authors-artists-converge-on-uyo-as-boldoz-book-and-arts-festival-celebrates-literature-culture.html'
S='https://sevhage.com/wp-content/uploads/2025/02/poetry-club-udus-issue-i-final.pdf'
slam=add('pin-awka-slam','PIN Awka Poetry Slam — undated report','Prizes','Awka','Report names CP Kings as winner and Unizik FM Hall as venue.',A)
slam.update(format='Spoken-word competition',historical=True,gaps='Readable report lacks a date. Indexed forum posting suggests 2018, but full forum access failed. Exact event date and the “first in Anambra” claim remain uncorroborated.')
add('pin-awka','Poets in Nigeria — Awka Connect Centre','Platforms','Awka','Local PIN centre named as slam host.',A)
add('unizik-fm-hall','Unizik FM Hall','Places','Awka','Venue named in the slam report.',A)
add('chisom-udeoba','Chisom Onyinyechukwu Udeoba','People','Awka','Lead representative and named reporter.',A)
add('cp-kings','CP Kings','People','Awka','Reported slam winner; full identity unverified.',A)
edge('pin-awka','c2','local PIN centre named',A);edge('pin-awka-slam','pin-awka','reported host',A)
edge('chisom-udeoba','pin-awka','reported lead representative',A)
edge('cp-kings','pin-awka-slam','reported winner',A);edge('pin-awka-slam','unizik-fm-hall','reported venue',A)
for id,name in [('chike-okoye','Chike Okoye'),('ngozi-emmanuel','Ngozi Marion Emmanuel'),('buisi-mandela','Prompoet Buisi Mandela'),('reginald-eze','Reginald Eze')]:
 add(id,name,'People','Awka','Named slam judge.',A);edge(id,'pin-awka-slam','reported judge',A)
kap=add('kapfest','Kano International Poetry Festival (KAPFEST)','Platforms','Kano','Poetic Wednesdays flagship festival; 2026 theme announced at the June pop-up.',K,2026,'Report supported','Theme-unveiling activity')
kap.update(format='Festival / showcase',activities=[{'date':'2026-06-06','kind':'programme announcement','url':K,'basis':'Published report of the June theme-unveiling event.'}],phase={'label':'Edition announced','date':'October 2026','url':K},gaps='Exact October dates appear in social index leads but have not been directly checked. Announcement does not establish occurrence.')
add('af-kano','Alliance Française, Kano','Places','Kano','Reported venue for the 6 June 2026 pop-up.',K,2026)
add('naseeba-babale','Naseeba Babale','People','Kano','Named executive director and panellist.',K,2026)
for id,name,role in [('nana-sule','Nana Sule','panellist'),('misbahu-elhamza','Misbahu El-Hamza','moderator'),('hidaya-mahmud','Hidaya Mahmud','performer'),('mujahid-abdulaziz','Mujahid Abdulaziz','performer')]:
 add(id,name,'People','Kano','Named June pop-up '+role+'.',K,2026);edge(id,'poeticwed','reported pop-up '+role,K,'2026-06-06')
edge('kapfest','poeticwed','flagship festival',K,2026)
edge('poeticwed','af-kano','reported pop-up venue',K,'2026-06-06')
edge('naseeba-babale','poeticwed','executive director in report',K,'2026-06-06')
edge('salim','kapfest','reported 2025 curator',K,2025);edge('naseeba-babale','kapfest','reported 2025 curator',K,2025)
d['overrides']['poeticwed']={'verification':rev(K,'2026 pop-up and named roles reviewed; staffing is source-dated.','Report supported'),'activities':[{'date':'2026-06-06','kind':'held event','url':K}],'links':[{'title':'June 2026 pop-up report','url':K}]}
boldoz=add('boldoz-fest','Boldoz Book and Arts Festival','Platforms','Uyo','Third edition reported held on 19–20 June 2026, with poetry performances.',U,2026)
boldoz.update(format='Festival / showcase',activities=[{'date':'2026-06-20','kind':'held event','url':U,'basis':'Premium Times results/coverage report.'}])
add('enobong-etuk','Enobong Etuk','People','Uyo','Reported festival curator and bookstore founder.',U,2026)
add('boldoz-books','Boldoz Bookstores','Places','Uyo','Bookstore named in the curator’s founder credit; event venue not established.',U,2026)
edge('enobong-etuk','boldoz-fest','reported curator',U,'2026-06-19 / 2026-06-20')
edge('enobong-etuk','boldoz-books','reported founder',U,2026)
for id,name in [('nkereuwem-albert','Nkereuwem Albert'),('tomilola-adeyemo','Tomilola Coco Adeyemo'),('emediong-edem','Emediong Edem')]:
 add(id,name,'People','Uyo','Featured author in the festival report.',U,2026);edge(id,'boldoz-fest','reported featured author',U,'2026-06')
book=add('udus-anthology-2025','Poetry Club UDUS Anthology 2025','Publications','Sokoto','Club anthology with publishing and editorial credits in preliminary pages.',S,2025,'Source confirmed','Publication year')
book.update(publicationState='Published — documented',gaps='ISBN validation and comprehensive contributor biography checks pending; no poems or photographs copied.')
club=add('poetry-club-udus','Poetry Club UDUS','Platforms','Sokoto','Club history records registration in May 2019.',S,2019,'Source confirmed','Registration in anthology history')
club['years'].append({'year':2025,'label':'Anthology copyright year','url':S})
add('sevhage','SEVHAGE','Platforms','Makurdi','Named publishing imprint.',S,2025,'Source confirmed')
add('konya-shamsrumi','Konya Shamsrumi','Platforms','Karu / Nasarawa','Named co-publishing imprint.',S,2025,'Source confirmed')
edge('udus-anthology-2025','poetry-club-udus','club anthology',S,2025)
for id in ['sevhage','konya-shamsrumi']:edge('udus-anthology-2025',id,'credited imprint',S,2025)
for id,name in [('abdulbasit-balogun','Abdulbasit Balogun Opeyemi'),('gaius-bala','Gaius Bangda Bala')]:
 add(id,name,'People','Sokoto','Founder named in club history.',S,2019,'Source confirmed');edge(id,'poetry-club-udus','founder in retrospective history',S,2019)
add('abdulbasit-oluwanishola','Abdulbasit Oluwanishola','People','Sokoto','Club leader and anthology co-editor, as of 2025.',S,2025,'Source confirmed')
add('michael-imossan','Michael Imossan','People','Nigeria','Anthology co-editor and contributor.',S,2025,'Source confirmed')
add('jide-badmus','Jide Badmus','People','Nigeria','Named anthology contributor.',S,2025,'Source confirmed')
edge('abdulbasit-oluwanishola','poetry-club-udus','editor-in-chief as of 2025',S,2025)
for id in ['abdulbasit-oluwanishola','michael-imossan']:edge(id,'udus-anthology-2025','co-editor in foreword',S,2025)
edge('jide-badmus','udus-anthology-2025','listed contributor',S,2025)
edge('sueddie','udus-anthology-2025','credited SEVHAGE editor',S,2025)
edge('jide-badmus','conscio-6','poetry editor', 'https://www.wrr.ng/download/con-scio-magazine-current-issue-6-vol-1-june-2026/','2026-06')
for r in d['profiles']:
 if r['verification']['sourceURL']==S:r['verification']['sourceLocator']='Publisher PDF: preliminary credits and club history, PDF pages 2–12; poem texts not reproduced.'
path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
print('Regional source batch added.')
