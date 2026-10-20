from dataclasses import dataclass
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];path=root/'dist/atlas-audit.json';d=json.loads(path.read_text())

@dataclass
class ProfileData:
    id: str
    name: str
    cat: str
    city: str
    summary: str
    url: str
    year: int
    meaning: str = 'Source evidence'

def review(url,scope):return {'label':'Source confirmed','reviewedAt':'2026-10-13','sourceURL':url,'scope':scope}
def add(data: ProfileData):
 p={'id':data.id,'name':data.name,'category':data.cat,'city':data.city,'summary':data.summary,'verification':review(data.url,data.summary),'status':'Source-scoped metadata reviewed 13 October 2026','links':[{'title':'Reviewed primary source','url':data.url}],'years':[{'year':data.year,'label':data.meaning,'url':data.url}],'media':[]}
 if data.cat=='Publications':p['publicationState']='Published — documented'
 if not any(x['id']==data.id for x in d['profiles']):d['profiles'].append(p)
 return next(x for x in d['profiles'] if x['id']==data.id)
def edge(a,b,label,url,date,status='Read primary source; role limited to stated evidence'):
 e={'a':a,'b':b,'label':label,'url':url,'date':date,'status':status}
 if not any(all(x.get(k)==e[k] for k in ['a','b','label','url']) for x in d['relationships']):d['relationships'].append(e)
M='https://animalheartpress.net/purchase-memento/'
K='https://www.wrr.ng/download/kaleidoscope-the-bplp-2023-anthology/'
R='https://www.wrr.ng/download/a-revolution-thinks-itself-a-bird-eriata-oribhabor-poetry-prize-2023-anthology/'
F='https://www.lulu.com/shop/chisom-ohuaka-and-philip-dr-feel-chukwu-and-dr-ode-andrew-eyeoyibo/first-gong-vol-6-the-purge/paperback/product-1we2pk6v.html'
C='https://www.wrr.ng/download/con-scio-magazine-current-issue-6-vol-1-june-2026/'
P='https://www.mps.ng/updates/press-release'
KD='https://www.mps.ng/updates/kaduna-to-host-next-stage-of-2026-poetry-challenge'
B='https://bbaaf.wordpress.com/'
add(ProfileData('memento','Memento: An Anthology of Contemporary Nigerian Poetry','Publications','Nigeria','Anthology edited by Adedayo Agarau; publisher gives a 30 March 2020 release.',M,2020,'Publisher release date'))
add(ProfileData('animal-heart-press','Animal Heart Press','Platforms','Online','Publisher of Memento; geographic base not established here.',M,2020,'Memento publication'))
edge('agarau','memento','editor',M,'2020-03-30');edge('memento','animal-heart-press','publisher',M,'2020-03-30')
for id in ['daisy','logan','tobi']:edge(id,'memento','listed contributor',M,2020)
add(ProfileData('kaleidoscope','Kaleidoscope (BPLP 2023 anthology)','Publications','Nigeria','Publisher catalogue identifies a 2023 prize anthology; download page created 10 March 2024.',K,2023,'Catalogue edition year'))
add(ProfileData('bplp','Brigitte Poirson Literature Prize','Prizes','Nigeria','Prize whose 2023 shortlisted poetry and fiction appear in Kaleidoscope.',K,2023,'Prize edition'))
for id,name in [('brigitte-poirson','Brigitte Poirson'),('iquo-dianaabasi','Iquo DianaAbasi'),('sueddie','Su’eddie Vershima Agema')]:add(ProfileData(id,name,'People','Nigeria','Named editor of Kaleidoscope.',K,2023,'Anthology editorial credit'))
for id in ['brigitte-poirson','iquo-dianaabasi','sueddie','kukogho']:edge(id,'kaleidoscope','listed editor',K,2023)
edge('kaleidoscope','bplp','collects shortlisted work',K,2023);edge('kaleidoscope','wrr','publisher catalogue',K,2023)
add(ProfileData('revolution-bird','A Revolution Thinks Itself a Bird','Publications','Nigeria','EOPP 2023 anthology edited by Kukogho Iruesiri Samson; publisher lists Pacella among contributors.',R,2023,'Catalogue / prize edition year'))
add(ProfileData('eopp','Eriata Oribhabor Poetry Prize (EOPP)','Prizes','Nigeria','Poetry prize represented by its 2023 anthology of selected poems.',R,2023,'Reviewed prize edition'))
edge('kukogho','revolution-bird','editor',R,2023);edge('pacella','revolution-bird','listed contributor',R,2023)
edge('revolution-bird','eopp','collects selected prize poems',R,2023);edge('revolution-bird','wrr','publisher catalogue',R,2023)
add(ProfileData('first-gong-6','First Gong Vol. 6: The Purge','Publications','Lagos','Lulu catalogue: Loudthotz readings from 2015; publication dated 1 April 2016.',F,2016,'Catalogue publication date'))
for id,name in [('philip-chukwu','Philip “Dr. Feel” Chukwu'),('ode-eyeoyibo','Ode Andrew Eyeoyibo')]:add(ProfileData(id,name,'People','Nigeria','Credited by the First Gong Vol. 6 catalogue.',F,2016,'Catalogue credit'))
for id in ['chisom','philip-chukwu','ode-eyeoyibo']:edge(id,'first-gong-6','catalogue author credit',F,'2016-04-01')
edge('first-gong-6','first-gong','volume of anthology series',F,2016)
edge('first-gong-6','loudthotz','collects 2015 reading poems',F,2015)
edge('loudthotz','orange-academy','2015 reading venue in catalogue',F,2015)
issue=add(ProfileData('conscio-6','CỌ́N-SCÌÒ, issue 6 (June 2026)','Publications','Nigeria','WRR magazine issue; page names contributors and editors. Catalogue title fields disagree.',C,2026,'Issue month; web record created 31 May 2026'))
issue['gaps']='Page heading says CURRENT but title field says BREATHE. PDF title-page verification pending.'
edge('conscio-6','wrr','publisher',C,'2026-06')
for id in ['felix-eshiet','servio','kukogho']:edge(id,'conscio-6','listed contributor',C,'2026-06')
edge('sueddie','conscio-6','fiction and features editor',C,'2026-06');edge('kukogho','conscio-6','editor-in-chief and production credit',C,'2026-06')
d['overrides']['wrr']={'verification':review(C,'Recent issue and named publishing roles confirmed; page creation date is not the physical release day.'),'activities':[{'date':'2026-05-31','kind':'publication','url':C,'basis':'Publisher’s June 2026 issue catalogue; web record created 31 May.'}],'links':[{'title':'June 2026 magazine issue','url':C}]}
add(ProfileData('mps-media','MPS Media','Platforms','Nigeria','Organiser of the MPS Media Poetry Challenge.',P,2026,'Organiser press release'))
challenge=add(ProfileData('mps-challenge','MPS Media Poetry Challenge — Arewa Edition','Prizes','Bauchi / Kaduna / Abuja','Organiser reports August 2026 Bauchi stages; later Kaduna and Abuja stages were announced.',P,2026,'Held Bauchi stages / announced later stages'))
challenge.update(format='Spoken-word competition',activities=[{'date':'2026-08-14','kind':'held event','url':P,'basis':'Organiser retrospectively reports completed Bauchi stages.'}],gaps='Regional representation does not prove events occurred in every represented state. Later stages need outcome reports.')
add(ProfileData('ahmed-adamu','Ahmed Adamu','People','Abuja','Named initiator and organiser of the MPS challenge.',P,2026,'Organiser account'))
edge('mps-challenge','mps-media','organiser',P,'2026-08-21');edge('ahmed-adamu','mps-challenge','initiator and organiser',P,'2026-08-21')
add(ProfileData('yaradua-hall','Umaru Musa Yar’Adua Hall, Murtala Square','Places','Kaduna','Announced September 2026 MPS zonal venue.',KD,2026,'Venue announcement'))
edge('mps-challenge','yaradua-hall','announced zonal venue',KD,'2026-09-12 / 2026-09-18','Organiser announcement; occurrence not confirmed')
festival=add(ProfileData('bbaaf','Benue Book and Arts Festival (BBAAF)','Platforms','Makurdi','Organiser’s 2022 programme names festival directors and poetry-slam venues.',B,2022,'Programme announcement'))
festival.update(format='Festival / showcase',gaps='Past programme verified; current calendar not established.')
add(ProfileData('oko-owi-ocho','Oko Owi Ocho','People','Makurdi','Co-director signing the 2022 festival announcement.',B,2022,'Director credit'))
edge('sueddie','bbaaf','festival director, 2022',B,'2022-06');edge('oko-owi-ocho','bbaaf','festival co-director, 2022',B,'2022-06')
add(ProfileData('steam-lounge','Steam Lounge, Old GRA','Places','Makurdi','Announced venue for the 2022 Benue festival and slam.',B,2022,'Programme venue'))
add(ProfileData('bbaaf-slam-2022','BBAAF Poetry Slam 2022','Prizes','Makurdi','Organiser announced a slam for 25 June 2022 at Steam Lounge.',B,2022,'Announced competition date')).update(format='Spoken-word competition',gaps='Results or occurrence evidence not recovered; an elapsed date does not prove completion.')
edge('bbaaf-slam-2022','bbaaf','festival programme',B,'2022-06-25');edge('bbaaf-slam-2022','steam-lounge','announced venue',B,'2022-06-25')
for id in ['kukogho','romeo-oriogun','iquo-dianaabasi']:edge(id,'bbaaf','announced 2022 guest',B,'2022-06','Organiser programme; not an attendance claim')
path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n')
print('Search-batch imports added with primary-source role qualifications.')
