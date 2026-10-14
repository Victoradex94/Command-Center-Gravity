from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
d=json.loads((root/'dist/atlas-audit.json').read_text()); claims=[]
S={
 'aba':'https://happyprinceblog.wordpress.com/2019/10/20/284/',
 'identity':'https://guardian.ng/news/painting-the-gloomy-memories-of-covid-19-through-poetry/',
 'abia':'https://ojembamagazine.com/association-of-nigerian-authors-abia-state-chapter-announces-monthly-reading-for-april-2026/',
 'florence':'https://www.florencechukwuonye.com/',
 'love':'https://egotickets.com/events/festival-of-love',
 'laureates':'https://ebonyilaureates.com/clubs.html',
 'online':'https://ng.linkedin.com/company/ebonyi-laureates',
 'imo':'https://www.ananigeria.org/news/ana-imo-celebrates-anas-immediate-past-president-dr-camilus-ukah-in-a-worthy-home-coming-event-and-the-chapters-continued-promotion-of-literature',
 'books':'https://www.otowngist.com/2022/10/chidozie-chukwubuike-holds-a-public-presentation-of-two-books-of-poetry/',
 'call':'https://grassrootreporters.ng/2025/06/17/winners-of-ana-imo-short-story-competition-emerge/'
}
def add(id,name,cat,city,text,source,year=None,label='Source confirmed',**kw):
 p=dict(id=id,name=name,category=cat,city=city,summary=text,status=label+'; source-scoped',verification=dict(label=label,sourceURL=S[source],reviewedAt='2026-10-13',scope=text),links=[dict(title='Reviewed source',url=S[source])],years=[] if year is None else [dict(year=year,label='Evidence year; not an inferred founding or publication date',url=S[source])],media=[],gaps='Current activity and independent corroboration unverified.',**kw)
 old=next((x for x in d['profiles'] if x['id']==id),None)
 if old:old.update(p)
 else:d['profiles'].append(p)
 claims.append(dict(entity=id,claim=text,sourceURL=S[source],status=label,confidence='High for source attribution; independent corroboration pending',qualifiers={k:p[k] for k in ['eventEvidence','dateBasis','gaps'] if k in p}))
 return p
def edge(a,b,label,source,year=None,status='Source-stated role only; not current residence or office'):
 e=dict(a=a,b=b,label=label,url=S[source],date=year,status=status)
 if not any(all(x.get(k)==e[k] for k in ['a','b','label','url']) for x in d['relationships']):d['relationships'].append(e)
 claims.append(dict(entity=a,claim=label+' → '+b,sourceURL=S[source],status=status,confidence='High for the stated relationship'))
add('aba-poetry-club','Aba Poetry Club','Platforms','Aba','Club documented by its president’s 2019 address. Exact founding year unverified.','aba',2019)
add('aba-festival-2019','Aba Literary Festival (2019)','Platforms','Aba','President’s address documents the gathering.','aba',2019,eventEvidence='Held — first-person address',historical=True,dateFact=dict(label='Stated event',value='28 September 2019',url=S['aba']),dateBasis='Address published 20 October 2019; independent completion report not found.')
add('accima-hall','ACCIMA — Conference Hall','Places','Aba','Festival venue named in the address.','aba',2019)
add('aba-museum','National Museum of Colonial History, Aba','Places','Aba','Club host facility in the 2019 account; not the festival venue.','aba',2019)
add('happyprince','Agu Prince Osinayah (HappyPrince)','People','Aba','Aba Poetry Club founder; identity also reported by The Guardian.','identity',2023,nameVariants=['Agu, Prince Osinayah','HappyPrince'])
add('aba-story-2018','Aba is a Story (2018)','Platforms','Aba','Guest-poet visit recalled in the president’s address.','aba',2018,eventEvidence='Held — retrospective participant account',historical=True,dateBasis='Year explicitly recalled; day and venue unverified.')
add('umuahia-literary-society','Umuahia Literary Society (ULS)','Platforms','Umuahia','Named club interface in the 2019 address.','aba',2019)
for a,b,l in [('aba-festival-2019','aba-poetry-club','club president’s address'),('aba-festival-2019','accima-hall','stated venue'),('aba-poetry-club','aba-museum','host facility as of 2019'),('aba-poetry-club','umuahia-literary-society','interface named'),('aba-story-2018','aba-poetry-club','programme recalled'),('aba-story-2018','dike','guest poet recalled')]:edge(a,b,l,'aba',2019 if a!='aba-story-2018' else 2018)
edge('happyprince','aba-poetry-club','founder reported','identity',2023)
add('ana-abia','Association of Nigerian Authors — Abia Chapter','Platforms','Aba','Chapter named in its attributed reading notice.','abia',2026)
add('ana-abia-april-2026','ANA Abia — April 2026 Monthly Reading','Platforms','Aba','Poetry and spoken-word reading announced.','abia',2026,label='Announcement verified',eventEvidence='Announced; occurrence unverified',dateFact=dict(label='Scheduled',value='24 April 2026',url=S['abia']),dateBasis='Notice published 22 April; no qualifying completion report found.',phase=dict(label='Announced; not verified as held',date='24 April 2026',url=S['abia']))
add('ibiza-aba','Ibiza Hotels — Okigwe Road','Places','Aba','Announced reading venue.','abia',2026,label='Announcement verified')
add('nnaemeka-nwokocha','Nnaemeka Nwokocha','People','Aba','Secretary signing the April 2026 notice.','abia',2026)
edge('ana-abia-april-2026','ana-abia','announced chapter reading','abia',2026,'Announcement only')
edge('ana-abia-april-2026','ibiza-aba','announced venue','abia',2026,'Announcement only; attendance not established')
edge('nnaemeka-nwokocha','ana-abia','secretary in notice','abia',2026)
add('florence-chukwuonye','Florence Njideka Chukwuonye','People','Aba','Author’s site describes historical club membership; currently UK-based.','florence',None,nameVariants=['Florence Chukwuonye'])
edge('florence-chukwuonye','aba-poetry-club','historical membership stated','florence')
edge('florence-chukwuonye','ana-abia','historical welfare officer / vice chairman stated','florence')
add('tranquillity-turbulence','Tranquillity in Turbulence','Publications','Nigeria','Poetry collection listed by its author.','florence',None,publicationState='Author-listed publication',dateBasis='Publication date, publisher and ISBN unverified.')
edge('florence-chukwuonye','tranquillity-turbulence','author’s bookshelf attribution','florence')
add('abakaliki-love-2018','Festival of Love — ORUKA (2018)','Platforms','Abakaliki','Poetry and spoken-word programme advertised.','love',2018,label='Announcement verified',eventEvidence='Announced; occurrence unverified',dateFact=dict(label='Scheduled',value='14 February 2018',url=S['love']),dateBasis='Past Event ticket label does not prove occurrence.',phase=dict(label='Announced; not verified as held',date='14 February 2018',url=S['love']))
add('speak-out-loud-abakaliki','Speak Out Loud — Abakaliki listing','Platforms','Abakaliki','Organizer credited in the ticket listing.','love',2018,label='Announcement verified')
add('monabliss-abakaliki','Monabliss Hotels & Suites','Places','Abakaliki','Advertised Festival of Love venue.','love',2018,label='Announcement verified')
edge('abakaliki-love-2018','speak-out-loud-abakaliki','announced organizer','love',2018,'Announcement only; similarly named platforms not merged')
edge('abakaliki-love-2018','monabliss-abakaliki','announced venue','love',2018,'Announcement only')
add('ebonyi-laureates-book-club','Ebonyi Laureates — Book Club','Platforms','Ebonyi','Organizer reports two 2025 open mics on unity and New Yam themes.','laureates',2025,eventEvidence='Held programmes — organizer self-report',dateBasis='Dates, venues and physical/online format absent; no individual local event inferred.',nameVariants=['Laureates Science, Innovation and Education Initiative — Book Club'])
add('ebonyi-literary-evening-2026','Ebonyi Laureates — Literary Evening (2026)','Platforms','Online','Discussion, poetry and open mic advertised on Microsoft Teams.','online',2026,label='Announcement verified',eventEvidence='Announced; occurrence unverified',dateFact=dict(label='Scheduled online',value='27 June 2026',url=S['online']),dateBasis='Virtual programme; not counted as an event held in Abakaliki.',phase=dict(label='Announced online; not verified as held',date='27 June 2026',url=S['online']))
edge('ebonyi-literary-evening-2026','ebonyi-laureates-book-club','announced host','online',2026,'Announcement only; online setting')
add('ana-imo','Association of Nigerian Authors — Imo Chapter','Platforms','Owerri','Chapter’s official report documents poetry activity.','imo',2024)
add('ana-imo-poetry-2024','ANA Imo — Poetry Prize (May 2024)','Prizes','Owerri','Chapter reports a poetry prize endowed by Nwokedi.','imo',2024,eventEvidence='Held — official chapter report',historical=True,dateFact=dict(label='Reported prize month',value='May 2024',url=S['imo']),dateBasis='Exact day, venue and winners unverified; Owerri is chapter association, not confirmed competition venue.')
add('sylvester-nwokedi','Sylvester Nwokedi (Mbem Ijele)','People','Owerri','Poetry-prize endower named by the chapter.','imo',2024,nameVariants=['Mbem Ijele'])
add('ana-imo-homecoming-2023','ANA Imo — Ukah Homecoming (2023)','Platforms','Owerri','Chapter reports reception with readings and recitals.','imo',2023,eventEvidence='Held — official chapter report',historical=True,dateFact=dict(label='Reported event',value='17 December 2023',url=S['imo']),dateBasis='Official report published 1 September 2024.')
add('whelan-research-owerri','Whelan Research Academy','Places','Owerri','Reception venue; chapter secretariat in the report.','imo',2023)
add('camillus-ukah','Camillus Ukah','People','Owerri','Honouree in the chapter account.','imo',2023,nameVariants=['Camilus Ukah','Camillus Chima Uka','Camillus Chima Ukah'])
add('osinachi-emeghara','Osinachi Emeghara','People','Owerri','Chapter chairman in the 2024 report.','imo',2024)
for a,b,l in [('ana-imo-poetry-2024','ana-imo','chapter prize'),('sylvester-nwokedi','ana-imo-poetry-2024','endower reported'),('ana-imo-homecoming-2023','ana-imo','chapter reception'),('ana-imo-homecoming-2023','whelan-research-owerri','reported venue'),('ana-imo-homecoming-2023','camillus-ukah','honouree'),('osinachi-emeghara','ana-imo','chairman in source')]:edge(a,b,l,'imo',2024 if a!='ana-imo-homecoming-2023' else 2023)
add('ana-imo-igbo-poetry-2025','ANA Imo — Igbo Poetry Competition (2025 call)','Prizes','Owerri','July competition announced in an attributed chapter release.','call',2025,label='Announcement verified',eventEvidence='Announced; occurrence unverified',dateFact=dict(label='Scheduled month',value='July 2025',url=S['call']),dateBasis='No poetry results found; short-story results are not poetry results.',phase=dict(label='Announced; results unverified',date='July 2025',url=S['call']))
edge('ana-imo-igbo-poetry-2025','ana-imo','announced chapter competition','call',2025,'Announcement only')
edge('sylvester-nwokedi','ana-imo-igbo-poetry-2025','competition announcement attributed','call',2025,'Announcement only')
add('chukwubuike-launch-2022','Chidozie Chukwubuike — Poetry Book Presentation (2022)','Platforms','Owerri','Report documents presentation of two collections.','books',2022,eventEvidence='Held — participant-authored report',historical=True,dateBasis='Report dated 10 October 2022 says last Saturday; exact event date not normalized.')
add('chidozie-chukwubuike','Chidozie Chukwubuike','People','Owerri','Author presenting the two collections.','books',2022)
for id,title in [('jangolova','Jangolova & Other Poems'),('wriggling-freedom','Wriggling to Freedom (A Decuplet in Verse)')]:
 add(id,title,'Publications','Nigeria','Collection named in the presentation report.','books',2022,publicationState='Presented publication — reported',dateBasis='2022 is presentation evidence; original publication year, publisher and ISBN unverified.')
 edge('chidozie-chukwubuike',id,'author credited','books')
 edge('chukwubuike-launch-2022',id,'presented collection','books',2022)
add('deborah-uzoma','Deborah Uzoma','People','Owerri','Named poetry performer and report byline.','books',2022)
add('chukwuebuka-amaechi','Chukwuebuka Amaechi','People','Owerri','Reviewer of Wriggling to Freedom.','books',2022)
for b,l in [('chidozie-chukwubuike','presenting author'),('whelan-research-owerri','reported venue'),('sylvester-nwokedi','poetry performer'),('deborah-uzoma','poetry performer')]:edge('chukwubuike-launch-2022',b,l,'books',2022)
edge('chukwuebuka-amaechi','wriggling-freedom','reviewer at presentation','books',2022)
(root/'dist/atlas-audit.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,indent=2)+';\n')
(root/'research/southeast-claims.json').write_text(json.dumps(dict(reviewedAt='2026-10-13',sources=S,claims=claims),ensure_ascii=False,indent=2)+'\n')
print('Saved',len(claims),'source-scoped claims; idempotent profile and edge updates')
