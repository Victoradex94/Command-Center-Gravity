from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
data={'reviewed':'2026-10-13','profiles':[],'overrides':{},'relationships':[]}
FIRST='https://loudthotzpoetry.wordpress.com/2011/12/10/first-gong-on-sale/'
LOUD='https://loudthotzpoetry.wordpress.com/page/2/'
CHISOM='https://loudthotzpoetry.wordpress.com/2011/12/12/the-common-nigerian-a-poem-read-by-chisom-ohuaka-at-the-season-2-finale-of-loudthotz-open-poetry-reading/'
MAROKO='https://lagospoetryfestival.com/maroko/'
LAB='https://lagospoetryfestival.com/lab/'
COHORT='https://lagospoetryfestival.com/meet-the-inaugural-cohort-of-the-lipfest-craft-and-development-lab/'
PIN='https://jaylit.com/pacella-chukwuma-eke-muna-jay-sukpa-win-2025-pin-national-poetry-slam/'
IG='https://www.instagram.com/p/DUk5dXMDCH9/'
LEDGER='https://docs.google.com/spreadsheets/d/1xsO-ONEJQMMxE-Vzhw7BCYfPVFG6Ov2v75WGUpHgCHs/edit'
def review(kind,url,note):
 return {'label':kind,'reviewedAt':data['reviewed'],'sourceURL':url,'scope':note}
def profile(id,name,cat,city,summary,url,year,label='Source evidence',tier='Source confirmed'):
 p={'id':id,'name':name,'category':cat,'city':city,'summary':summary,'status':tier+'; reviewed 13 October 2026','verification':review(tier,url,summary),'links':[{'title':'Reviewed evidence', 'url':url}],'years':[{'year':year,'label':label,'url':url}],'media':[]}
 data['profiles'].append(p);return p
def edge(a,b,label,url,date,status='Reviewed primary source; limited to stated relationship'):
 data['relationships'].append({'a':a,'b':b,'label':label,'url':url,'date':date,'status':status})
def override(id,verification,**patch): data['overrides'][id]={'verification':verification,**patch}
profile('first-gong','First Gong','Publications','Lagos','Loudthotz poetry anthology offered for sale in December 2011.',FIRST,2011,'Organiser sales notice')['publicationState']='Published — documented'
edge('first-gong','loudthotz','anthology associated with reading series',FIRST,'2011-12-10')
profile('maroko','Márọkọ́','Publications','Lagos','Print and digital journal published by LIPFest; the reviewed page contains 2022 and 2023 calls.',MAROKO,2023,'Issue II call')['publicationState']='Journal — documented'
edge('maroko','c4','journal published by festival',MAROKO,'2023')
profile('chisom','Chisom Ohuaka','People','Lagos','Named reader in the Loudthotz season-two finale archive.',CHISOM,2011,'Reading archive published')
edge('chisom','loudthotz','reader in season-two finale',CHISOM,2011)
profile('orange-academy','Orange Academy','Places','Lagos','Announced venue for the Loudthotz finale on 8 December 2011.',LOUD,2011,'Venue announcement')
edge('loudthotz','orange-academy','announced finale venue',LOUD,'2011-12-08')
override('loudthotz',review('Source confirmed',FIRST,'Historical anthology association confirmed; current calendar unverified.'),links=[{'title':'First Gong organiser notice','url':FIRST}])
lab=profile('lip-craft-lab','LIPFest Craft and Development Lab','Platforms','Online / Lagos','Virtual craft and mentorship programme; 2026 applications closed on 3 July.',LAB,2026,'2026 programme schedule')
lab['format']='Workshop / mentorship'
lab['activities']=[{'date':'2026-07-18','kind':'programme announcement','url':COHORT}]
lab['phase']={'label':'Entries closed','date':'2026-07-03','url':LAB}
lab['gaps']='Official roster currently lists eleven biographies while introductory copy and the July report say ten; roster size needs reconciliation. Planned showcase is not a confirmed occurrence.'
edge('lip-craft-lab','c4','festival programme',LAB,'2026')
override('c4',review('Source confirmed',COHORT,'2026 programme organising activity confirmed, not completion of the festival.'),activities=[{'date':'2026-07-18','kind':'programme announcement','url':COHORT}],links=[{'title':'Official 2026 cohort announcement','url':COHORT}])
for key,name in [('felix-eshiet','Felix Eshiet'),('joemario-umana','Joemario Umana'),('roseline-mgbodichinma','Roseline Mgbodichinma'),('salmah-usman','Salmah Suleiman Usman')]:
 profile(key,name,'People','Nigeria','Named in the official 2026 LIPFest Lab roster.',COHORT,2026,'Official roster published')
 edge(key,'lip-craft-lab','named cohort member',COHORT,'2026-07-18')
profile('romeo-oriogun','Romeo Oriogun','People','Nigeria / diaspora','Named mentor for the LIPFest Lab.',COHORT,2026,'Mentor announcement')
edge('romeo-oriogun','lip-craft-lab','announced mentor',COHORT,'2026-07-18')
edge('sonuga','lip-craft-lab','announced mentor',COHORT,'2026-07-18')
edge('tobi','lip-craft-lab','named cohort member',COHORT,'2026-07-18')
override('tobi',review('Source confirmed',COHORT,'Official biography identifies Oloruntobiloba Abiodun as Tobi Abiodun.'),searchAliases=['Toby Abiodun','Oloruntobiloba Abiodun'],links=[{'title':'Official LIPFest Lab biography','url':COHORT}])
profile('ekondo-review','Ekondo Review','Publications','Online / Nigeria','Literary magazine named in the official cohort biographies.',COHORT,2026,'Editorial roles in 2026 biography')['publicationState']='Journal — documented'
edge('felix-eshiet','ekondo-review','founding editor-in-chief in biography',COHORT,'2026-07-18')
edge('joemario-umana','ekondo-review','poetry editor in biography',COHORT,'2026-07-18')
for key,name,summary,placement in [('muna','Muna','Reported second-place winner of the 2025 PIN slam.','reported second place'),('jay-sukpa','Jay Sukpa','Reported third-place winner of the 2025 PIN slam.','reported third place')]:
 profile(key,name,'People','Lagos',summary,PIN,2025,'Competition year, report published 16 January 2026','Report supported')
 edge(key,'pin-slam',placement,PIN,'2025','Reviewed results report; event year differs from report date')
edge('pacella','pin-slam','reported first place',PIN,'2025','Reviewed results report; event year differs from report date')
override('pacella',review('Report supported',PIN,'First place in the 2025 PIN slam reported; other claims retain their own evidence.'),links=[{'title':'2025 PIN slam results reported in 2026','url':PIN}])
override('pin-slam',review('Report supported',PIN,'2025 results independently read; exact event day not established.'),phase={'label':'Completed','date':'2025','url':PIN},links=[{'title':'2026 report of 2025 slam results','url':PIN}])
m=profile('motoni-slam','Mọ́tòní Olódùn Slam','Prizes','Ogbomoso','Open Mic Ogbomoso anniversary slam dated 31 January 2026 in the organiser-caption ledger.',IG,2026,'Slam date in preserved organiser caption','Archive supported')
m.update(format='Spoken-word competition',oneOff=True,phase={'label':'Completed','date':'2026-01-31','url':IG},gaps='Live Instagram post could not be retrieved; caption preserved in Open Mic Instagram Evidence IG-OMO-025. Outcomes await independent corroboration.')
archiveStatus='Preserved organiser-caption ledger reviewed; live Instagram unavailable'
edge('motoni-slam','omo','anniversary slam of open-mic series',IG,'2026-01-31',archiveStatus)
edge('motoni-slam','60sp','host in preserved archive relationship record',LEDGER+'#gid=2115309023&range=A8:H8','2026-01-31',archiveStatus)
profile('kinora','Kinora by the Assembly','Places','Ogbomoso','Venue named in the preserved January 2026 slam caption.',IG,2026,'Preserved event-caption evidence','Archive supported')
edge('motoni-slam','kinora','venue named in organiser caption',IG,'2026-01-31',archiveStatus)
for key,name,place in [('dairo-goodness','Dairo Goodness','first place'),('emmanuel-akintoye','Emmanuel Akintoye','second place'),('esohe-cole','Esohe Cole','third place')]:
 profile(key,name,'People','Ogbomoso','Named among the slam winners in the preserved organiser recap; exact placement needs confirmation.',IG,2026,'Preserved organiser recap','Archive supported')
 edge(key,'motoni-slam','named among top three',IG,'2026-01-31',archiveStatus)
override('omo',review('Archive supported',IG,'2026 anniversary slam documented in preserved organiser recap.'),activities=[{'date':'2026-01-31','kind':'held event','url':IG,'basis':'Preserved organiser caption; live post inaccessible'}],links=[{'title':'2026 anniversary slam recap (preserved caption reviewed)','url':IG}])
override('father',review('Archive supported',LEDGER+'#gid=721478436','Owner curatorial map identifies the collaborative anthology album; track-level credits need audiovisual confirmation.'),category='Publications',format='Spoken-word album',publicationState='Album — documented')
(root/'dist/atlas-audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
print(len(data['profiles']),'new profiles;',len(data['relationships']),'new sourced relationships;',len(data['overrides']),'existing entry reviews.')
