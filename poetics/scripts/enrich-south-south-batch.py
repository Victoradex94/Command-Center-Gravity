"""Append only claim-scoped evidence; never replace the original source snapshots."""
from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
path = root / 'dist/atlas-audit.json'
d = json.loads(path.read_text())
claims = []
NW = 'https://newswings.com.ng/poets-in-nigeria-pin-initiative-set-to-hold-cross-country-poetry-celebration/'
Z = 'https://writezakama.wordpress.com/2023/10/17/update-on-cross-country-celebration-of-poetry/'
PIN = 'https://www.linkedin.com/posts/poets-in-nigeria-initiative_introducing-the-cross-country-celebration-activity-7070398230315831297-K_cy'
EK = 'https://www.linkedin.com/posts/funke-awodiya-b5bba165_on-october-21st-poets-in-nigeria-initiative-activity-7122227136219742208-OjZI'
ET = 'https://topnewsng.com/poets-in-nigeria-takes-poetry-to-ekiti-varsity-solicit-govt-recognition-support/'
AW = 'https://profile.unizik.edu.ng/nau4594'
B = 'https://naijapoetryfest.com.ng/battle-of-the-stanzas-bots-takes-benin-city-by-storm-with-renaissance-of-the-poetic/'
BR = 'https://periscopenga.com/2025/08/glitz-glamour-as-battle-of-stanzas-redefines-poetry-events-in-nigeria-births-first-anthology-of-poems-in-edo/'
BOOK = 'https://naijapoetryfest.com.ng/stanzas-from-the-bronze-capital-a-defining-voice-in-edos-literary-journey/'
BIO = 'https://www.genevapeaceforum.ch/en/speaker/godson-osarenren'
F = 'https://guardian.ng/art/when-festival-poetry-calabar-2016-stood-on-novelty-sociability-footing/'
FC = 'https://poetsinnigeria.org.ng/index.php/festival-poetry-competition-call-for-entries/'
FR = 'https://crossriverwatch.com/2017/01/3-days-poetry-fiesta-ends-in-calabar/'
DELTA = 'https://www.africanwriter.com/drum-beats-for-nduka-otiono-in-the-delta/'
INK = 'https://lockersupdate.wordpress.com/2016/10/07/theinkpotters-openmicnight-4/'
PH = 'https://www.newsplatformng.com/2018/06/port-harcourt-literary-society-changing.html'
PHN = 'https://newbooksnigeria.wordpress.com/project-tag/port-harcourt-literary-society/'
NEO = 'https://neofloetry.wordpress.com/tag/phls/'

def review(url, scope, tier):
    return dict(label=tier, sourceURL=url, reviewedAt='2026-10-13', scope=scope)

def log(entity, claim, url, status, confidence='High — explicit source statement', **extra):
    claims.append(dict(entity=entity, claim=claim, sourceURL=url, status=status,
                       confidence=confidence, **extra))

def add(id, name, category, city, summary, url, year=None, tier='Source confirmed', **extra):
    p=dict(id=id, name=name, category=category, city=city, summary=summary,
           verification=review(url, summary, tier), status=tier+'; claim-scoped review 13 October 2026',
           years=[dict(year=year,label='Dated evidence; see date basis',url=url)] if year else [],
           links=[dict(title='Reviewed source',url=url)],media=[], **extra)
    existing=next((x for x in d['profiles'] if x['id']==id),None)
    if existing: existing.update(p)
    else: d['profiles'].append(p)
    log(id,summary,url,tier)
    return existing or p

def patch(id,url,summary,tier='Source confirmed',**extra):
    p=d['overrides'].setdefault(id,{})
    p.update(summary=summary,verification=review(url,summary,tier),**extra)
    links=p.setdefault('links',[])
    if not any(x['url']==url for x in links):links.append(dict(title='Reviewed follow-up',url=url))
    log(id,summary,url,tier)
    return p

def edge(a,b,label,url,date=None,status='Explicit source role; no residence or current staffing inferred'):
    e=dict(a=a,b=b,label=label,url=url,date=date,status=status)
    if not any(all(x.get(k)==e[k] for k in ['a','b','label','url']) for x in d['relationships']):d['relationships'].append(e)
    log(a,label+' → '+b,url,status,date=date)

# Classify events before extracting named roles. Multiple reproductions of the
# same PIN release are a single evidence family, not independent occurrence proof.
add('ccpc','Cross Country Celebration of Poetry','Platforms','Nigeria',
    'PIN volunteer-hosted poetry programme; organiser recalls a first edition in October 2021.',PIN,2021,
    format='Festival / showcase',dateBasis='October 2021 is an organiser-reported first edition, not a verified founding date.',
    gaps='National attendance totals and completion of every local stop are not independently established.')
edge('ccpc','c2','organiser identifies PIN initiative',PIN,2021)
stops=[
 ('cross-event-5','Calabar','cross-venue-5','Calabar Municipal Garden','cross-host-5','Victory Udie',
  [('bruno-nwagbo','Ebubechukwu Nwagbo Bruno')]),
 ('ccpc-benin-2023','Benin City','randheki-hotel','Randheki (Gold) Hotel','ehis-ferguson','Ehis Ferguson',
  [('testimony-odey','Testimony Odey'),('diongoli-queen','Diongoli Queen-Deborah Ebitaripreye')]),
 ('ccpc-ph-2023','Port Harcourt','elechi-conference','Captain Elechi Amadi Polytechnic — Conference Hall','salomi-ikoyoko','Salomi Ikoyoko (Trisha)',
  [('sunday-igbikiberebima','Sunday Igbikiberebima')]),
 ('ccpc-ikot-2023','Ikot Ekpene','akwa-poly','Akwa Ibom Polytechnic','godswill-enang','Godswill Enang',
  [('omodot-jackson','Omodot Jackson')]),
 ('ccpc-yenagoa-2023','Yenagoa','bayelsa-peace-park','Bayelsa Peace Park','rowland-ofiyou','Rowland Ofiyou',
  [('lue-trust','Lue Trust Benjamin')]),
 ('ccpc-issele-2023','Issele-Uku','pilgrim-baptist-school','Pilgrim Baptist Grammar School','bright-chukwuemeke','Bright Chukwuemeke',[])
]
for event,city,venue,vname,host,hname,cohosts in stops:
    summary='Announced poetry gathering at '+vname+'. Local occurrence unverified.'
    kw=dict(kind='Poetry gathering',format='Festival / showcase',eventEvidence='Announced; occurrence unverified',
            dateFact=dict(label='Scheduled',value='21 October 2023',url=NW),
            dateBasis='PIN statement published 16 October 2023 schedules this stop for 21 October. No readable local completion report found in this batch.',
            gaps='Host and venue are planned roles, not proof of attendance. The syndicated list is one evidence family.',
            phase=dict(label='Occurrence unverified',date='Scheduled 21 October 2023',url=NW))
    if event=='cross-event-5':patch(event,NW,summary,'Announcement verified',**kw)
    else:add(event,'Cross Country Celebration of Poetry — '+city+' (2023)','Platforms',city,summary,NW,2023,'Announcement verified',**kw)
    for id,name,category,role in [(venue,vname,'Places','announced venue'),(host,hname,'People','announced host')]+[(i,n,'People','announced co-host') for i,n in cohosts]:
        summary=role.capitalize()+' for the 2023 '+city+' stop; occurrence unverified.'
        if id in ['cross-venue-5','cross-host-5']:patch(id,NW,summary,'Announcement verified')
        else:add(id,name,category,city,summary,NW,2023,'Announcement verified',
                 dateBasis='2023 is the announcement year; location reflects the proposed role, not residence.')
        edge(event,id,role,NW,'Scheduled 2023-10-21','Announcement only; attendance and local completion unverified')
    edge(event,'ccpc','announced 2023 city stop',NW,'Scheduled 2023-10-21','Announcement only; not evidence all 44 stops happened')

# Do not let the old view-layer wording overwrite newly qualified facts.
for n in range(7):
    id='cross-event-'+str(n)
    if id=='cross-event-5':continue
    p=d['overrides'].setdefault(id,{})
    p.update(eventEvidence='Announced; occurrence unverified',
      dateFact=dict(label='Scheduled',value='21 October 2023',url=NW),
      dateBasis='Scheduled date in the published PIN statement; city-level occurrence still unverified.',
      verification=review(NW,'Scheduled date confirmed; host/venue remain announcement roles.','Announcement verified'))
    if not any(x['url']==NW for x in p.setdefault('links',[])):p['links'].append(dict(title='PIN statement carried by News Wings',url=NW))
    log(id,'Scheduled 21 October 2023; city occurrence not established',NW,'Announcement verified')

add('ccpc-ekiti-2023','Cross Country Celebration of Poetry — Ado Ekiti (2023)','Platforms','Ado Ekiti',
    'Host account and press coverage describe a held gathering at EKSU.',EK,2023,
    eventEvidence='Held — host account and press report',kind='Poetry gathering',format='Festival / showcase',
    dateFact=dict(label='Host-reported event',value='21 October 2023',url=EK),
    dateBasis='Host supplies 21 October; contemporaneous news report dated 22 October supports occurrence but calls it “today”. Exact date is host-attributed.',
    historical=True,gaps='The two sources differ in dating language; no claim that every national stop occurred.',
    )
add('funke-awodiya','Funke Awodiya','People','Ado Ekiti','Identifies herself as Ekiti host in a post-event account.',EK,2023)
add('adetutu-hall','Adetutu Hall, Ekiti State University','Places','Ado Ekiti','Hall identified in the host’s post-event account.',EK,2023)
for dest,role in [('funke-awodiya','host-reported organiser'),('adetutu-hall','host-reported venue'),('ccpc','reported city edition')]:edge('ccpc-ekiti-2023',dest,role,EK,'2023-10-21','Host-reported date; press occurrence corroboration')
next(p for p in d['profiles'] if p['id']=='ccpc-ekiti-2023')['links'].append(dict(title='Contemporaneous press report',url=ET))
add('ccpc-awka-2023','Cross Country Celebration of Poetry — Awka (2023)','Platforms','Awka',
    'University profile records a panel appearance at Awka Window on America in October 2023.',AW,2023,
    kind='Poetry gathering',eventEvidence='Participation documented; exact day unverified',
    dateFact=dict(label='Documented participation',value='October 2023',url=AW),
    dateBasis='Institution-hosted practitioner profile supplies month only. National scheduled day is not substituted.',historical=True)
add('uche-nnyagu','Emmanuel Uche Nnyagu','People','Awka','University profile records an October 2023 panel role.',AW,2023)
add('awka-window','Awka Window on America','Places','Awka','Named setting of the recorded panel appearance.',AW,2023)
edge('uche-nnyagu','ccpc-awka-2023','panel role in university profile',AW,'2023-10')
edge('ccpc-awka-2023','awka-window','setting named in university profile',AW,'2023-10')
edge('ccpc-awka-2023','ccpc','named programme participation',AW,'2023-10')

# Benin: held-event organiser account with outlet coverage. Outlet page is posted
# under a co-organiser account, so it is not treated as independent corroboration.
add('bots-2025','Battle of the Stanzas — Benin City (2025)','Platforms','Benin City',
    'Organiser reports a festival and contest at Sir Victor Uwaifo Creative Hub.',B,2025,
    format='Festival / showcase',eventEvidence='Held — organiser reported',historical=True,
    dateFact=dict(label='Organiser-reported event',value='30 August 2025',url=B),
    dateBasis='Exact date from organiser retrospective; outlet coverage posted under co-organiser account supports occurrence.',
    gaps='No “first ever” claim adopted. Winner spelling and judge-name variants need clarification.')
add('benin-writers','Benin Writers Society','Platforms','Benin City','Named festival co-organiser.',B,2025)
add('uwaifo-hub','Sir Victor Uwaifo Creative Hub','Places','Benin City','Venue in the held-event accounts.',B,2025)
add('godson-osarenren','Godson Osarenren','People','Nigeria','Founder and lead convener of Naija Poetry Fest; festival director in host biography.',BIO,2025)
add('douglas-ogbankwa','Douglas Ogbankwa','People','Benin City','Festival co-convener named in organiser account.',B,2025)
add('bots-contest-2025','Battle of the Stanzas Poetry Contest (2025)','Prizes','Benin City',
    'Contest reported within the festival; winner identity needs clarification.',B,2025,
    format='Spoken-word competition',historical=True,eventEvidence='Held — organiser reported',
    dateFact=dict(label='Festival date',value='30 August 2025',url=B),
    gaps='Organiser says Oghenovo (Floreb) was among the top five; outlet calls Oghenevho the winner. No winner edge added.')
add('bronze-capital','Stanzas from the Bronze Capital','Publications','Benin City',
    'Poetry anthology with a documented festival launch and editorial credits.',BOOK,2025,
    publicationState='Published — documented',dateFact=dict(label='Launch reported',value='30 August 2025',url=B),
    gaps='Contributor roster, publisher imprint and ISBN await the book’s preliminary pages. “First anthology in Edo” not adopted.')
add('lanre-sonde','Lanre Sonde','People','Nigeria','Named anthology editor.',BOOK,2025)
for dest,role in [('c14','co-organiser'),('benin-writers','co-organiser'),('uwaifo-hub','reported held venue'),('bots-contest-2025','festival contest'),('bronze-capital','anthology launch')]:edge('bots-2025',dest,role,B,'2025-08-30')
for id,role in [('godson-osarenren','co-convener'),('douglas-ogbankwa','co-convener')]:edge(id,'bots-2025',role,B,'2025-08-30')
edge('godson-osarenren','c14','founder / lead convener in host biography',BIO)
edge('douglas-ogbankwa','benin-writers','founder credited by anthology page',BOOK,2025)
for id,role in [('lanre-sonde','credited editor'),('godson-osarenren','credited editor'),('eriata','foreword credited')]:edge(id,'bronze-capital',role,BOOK,2025)
for id in ['bots-2025','bots-contest-2025','bronze-capital']:
    next(p for p in d['profiles'] if p['id']==id)['links'].append(dict(title='Corroborating outlet account; co-organiser-associated',url=BR))
patch('c14',BIO,'Naija Poetry Fest community; founder Godson Osarenren also directs Battle of the Stanzas.',links=[dict(title='Benin organiser retrospective',url=B)])

# Calabar: independent local coverage supports occurrence; the detailed Guardian
# narrative is by a foundation trustee and therefore treated as participant evidence.
add('fpc-2016','Festival Poetry Calabar — 2016 edition','Platforms','Calabar',
    'Three-day festival with readings, performance and a writing contest.',F,2016,
    format='Festival / showcase',eventEvidence='Held — participant account and local report',historical=True,
    dateFact=dict(label='Reported event',value='26–28 December 2016',url=F),
    dateBasis='Participant narrative supplies dates; CrossRiverWatch supports a completed three-day event. Source publication dates are January 2017.')
add('festival-poetry-foundation','Festival Poetry Foundation','Platforms','Calabar','Festival organising foundation.',FC,2016)
add('henshaw-foundation','James Ene Henshaw Foundation','Platforms','Calabar','Local report names festival collaboration.',FR,2016,'Report supported')
add('henshaw-centre','James Henshaw Foundation Centre','Places','Calabar','Reported venue for most festival activities.',F,2016)
add('fpc-onsite-2016','Festival Poetry Calabar On-the-Spot Competition (2016)','Prizes','Calabar','Writing contest reported during the second festival day.',F,2016,
    format='Written poetry prize',historical=True,eventEvidence='Held — participant reported')
add('clean-green-2016','Clean & Green Poetry Prize (2016 call)','Prizes','Calabar','Organiser call invited environment-themed poems for the festival.',FC,2016,
    format='Written poetry prize',eventEvidence='Call verified; awards unverified',
    dateFact=dict(label='Submission deadline',value='15 December 2016',url=FC),
    gaps='Six advertised awards are planned rewards; no recipient list verified in this batch.')
for id,name,role in [('amarachi-attamah','Amarachi Attamah','reported performer'),('kalejaye-folajimi','Kalejaye Folajimi','reported performer'),('bassey-asuquo','Bassey Asuquo','reported contest adjudicator')]:
    add(id,name,'People','Calabar',role.capitalize()+' in the 2016 festival account.',F,2016)
    edge(id,'fpc-onsite-2016' if id=='bassey-asuquo' else 'fpc-2016',role,F,2016)
for dest,role,url in [('c8','festival edition',F),('festival-poetry-foundation','organiser',FC),('henshaw-foundation','collaborator in local report',FR),('henshaw-centre','reported venue',F),('fpc-onsite-2016','reported writing contest',F)]:edge('fpc-2016',dest,role,url,2016)
edge('clean-green-2016','festival-poetry-foundation','organiser call',FC,2016,'Call only; completion and winners unverified')
edge('clean-green-2016','c8','announced festival selection',FC,2016,'Call only; not the on-site contest')
edge('eriata','festival-poetry-foundation','chairman in 2017 local coverage',FR,2017,'Historical office reported; not current staffing')
next(p for p in d['profiles'] if p['id']=='fpc-2016')['links'].append(dict(title='Independent local report',url=FR))
patch('c8',FR,'Festival platform with a completed second edition documented in local 2017 coverage.','Report supported',links=[dict(title='Participant dates and performance account',url=F)])

# Geographic gap: Delta has a readable participant account; do not elevate the
# inaccessible 2024 page's index snippet into an audited event entry.
add('delta-literary-forum','Delta Literary Forum','Platforms','Asaba','Literary movement documented in its chairman’s 2009 account.',DELTA,2009,
    format='Open mic / reading',gaps='2009 quarterly/monthly plans do not establish uninterrupted operation or current activity.')
add('dlf-otiono-2009','Delta Literary Forum — Nduka Otiono evening (2009)','Platforms','Asaba',
    'Chairman’s account reports an inaugural guest-writer gathering.',DELTA,2009,
    kind='Literary reading',format='Open mic / reading',eventEvidence='Held — participant reported',historical=True,
    dateFact=dict(label='Participant-reported event',value='30 July 2009',url=DELTA),
    dateBasis='Date in chairman David Diai’s account published 4 August 2009; independent event corroboration pending.')
add('lander-anchorage','Lander Brothers Anchorage','Places','Asaba','Venue named in the reading account.',DELTA,2009)
add('david-diai','David Diai','People','Asaba','Chairman and reporter of the 2009 gathering.',DELTA,2009)
add('nduka-otiono','Nduka Otiono','People','Nigeria / diaspora','Guest writer in the Asaba reading account.',DELTA,2009)
for dest,role in [('delta-literary-forum','reported host'),('lander-anchorage','reported venue'),('nduka-otiono','reported guest reader')]:edge('dlf-otiono-2009',dest,role,DELTA,'2009-07-30','Participant report; independent corroboration pending')
edge('david-diai','delta-literary-forum','chairman as of 2009',DELTA,2009)

# Bayelsa supporter's original announcement is sufficient for a notice, not a held event.
add('ink-potters','The Ink Potters','Platforms','Yenagoa','Poetry platform named in a supporter’s open-mic notice.',INK,2016,
    format='Open mic / reading',gaps='Present operation and leadership unverified.')
add('ink-openmic-4','The Ink Potters — Open Mic Night 4 (2016)','Platforms','Yenagoa',
    'Poetry and spoken-word night announced at La Gold Hotel.',INK,2016,'Announcement verified',
    format='Open mic / reading',eventEvidence='Announced; occurrence unverified',
    dateFact=dict(label='Scheduled',value='14 October 2016',url=INK),
    dateBasis='Supporter’s notice published 7 October 2016; no completion report read.')
add('la-gold-hotel','La Gold Hotel','Places','Yenagoa','Announced open-mic venue.',INK,2016,'Announcement verified')
edge('ink-openmic-4','ink-potters','platform in supporter notice',INK,'Scheduled 2016-10-14','Announcement only')
edge('ink-openmic-4','la-gold-hotel','announced venue',INK,'Scheduled 2016-10-14','Announcement only')

# PHLS: results account follows an announcement; exact day still ambiguous.
add('phls-slam-2018','Port Harcourt Literary Society Poetry Slam (2018)','Prizes','Port Harcourt',
    'Results report names Tobi Abiodun as senior-category winner.',PH,2018,'Report supported',
    format='Spoken-word competition',eventEvidence='Held — results reported',historical=True,
    dateFact=dict(label='Results report',value='6 June 2018',url=PH),
    dateBasis='May 25 was announced; report says “last Friday” with a June 6 publication date. Exact held date not reconciled.',
    gaps='Junior winner name appears as Ude Ugo; no identity link to Ude Ugo Anna inferred.')
add('phls-library','Port Harcourt Literary Society Library / Book Centre','Places','Port Harcourt','Venue in results coverage and earlier open-mic notice.',PH,2018,'Report supported')
add('amu-nnadi','Chijioke Amu-Nnadi','People','Port Harcourt','Resident poet in the 2018 report.',PH,2018,'Report supported')
add('andrew-patience','Andrew Patience Finye','People','Jos','Named 2018 slam judge; full name in published announcement.',PHN,2018)
edge('phls-slam-2018','c1004','reported organiser',PH,2018)
edge('phls-slam-2018','phls-library','reported venue',PH,2018)
edge('tobi','phls-slam-2018','reported senior-category winner',PH,2018)
edge('amu-nnadi','c1004','resident poet as of 2018',PH,2018)
for id in ['efe','andrew-patience','obii','graciano']:edge(id,'phls-slam-2018','reported judge',PH,2018)
patch('c1004',PH,'Society with a monthly open mic and teen programme reported in 2018; slam results are documented.','Report supported',gaps='Historical recurring schedule does not establish current activity.',links=[dict(title='2018 announcement and judge names',url=PHN)])

path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,indent=2)+';\n')
(root/'research/south-south-claims.json').write_text(json.dumps(dict(batch='2026-10-13-south-south',claims=claims),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(claims=len(claims),profiles=len(d['profiles']),relationships=len(d['relationships']))))
