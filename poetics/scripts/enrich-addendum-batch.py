from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
path=root/'dist/atlas-audit.json';d=json.loads(path.read_text())
logpath=root/'research/south-south-claims.json';log=json.loads(logpath.read_text())
G='https://fulaninewsmedia.com/i-cease-to-be-when-fulfulde-ceases-to-be-the-role-of-poetry-in-preserving-and-promoting-the-fulfulde-language-as-well-as-saving-the-ful%C9%93e-nation'
V='https://www.vanguardngr.com/2026/08/sdu-hosts-poets-writers-in-courtesy-visit-pledges-support-for-creative-culture/'
A='https://www.blanknewsonline.com/world-poetry-day-delta-literary-forum-lights-up-asaba/'

def claim(id,text,url,status,confidence='High for the attributed statement; wider verification incomplete'):
    log['claims'].append(dict(entity=id,claim=text,sourceURL=url,status=status,confidence=confidence,origin='13 October user addendum plus retrieved source text'))
def add(id,name,cat,city,summary,url,year,tier='Source confirmed',**fields):
    p=dict(id=id,name=name,category=cat,city=city,summary=summary,verification=dict(label=tier,sourceURL=url,reviewedAt='2026-10-13',scope=summary),status=tier+'; scoped to named source',links=[dict(title='Reviewed source',url=url)],years=[dict(year=year,label='Source / role evidence, not inferred life dates',url=url)],media=[],**fields)
    old=next((x for x in d['profiles'] if x['id']==id),None)
    if old:old.update(p)
    else:d['profiles'].append(p)
    claim(id,summary,url,tier)
    return p
def edge(a,b,label,url,date=None,status='Only the source-stated role is supported'):
    e=dict(a=a,b=b,label=label,url=url,date=date,status=status)
    if not any(all(x.get(k)==e[k] for k in ['a','b','label','url']) for x in d['relationships']):d['relationships'].append(e)
    claim(a,label+' → '+b,url,status)

# A published speech documents occurrence, not its exact date or room, and does
# not resolve the matching-name 2023 host identity.
add('ccpc-gsu-speech','Cross Country Celebration — Gombe State University (speech record)','Platforms','Gombe',
    'Published speech documents a gathering on campus.',G,2024,
    eventEvidence='Held — first-person speech',kind='Poetry gathering',historical=True,
    dateFact=dict(label='Speech publication',value='24 October 2024',url=G),
    dateBasis='Publication date only. Event day, room and edition year are unresolved. “Some weeks back” refers to an earlier conversation with a friend, not a usable event date.',
    gaps='No link to the 2023 Love Garden event inferred; matching speaker/host identity awaits corroboration.')
add('gsu-campus','Gombe State University','Places','Gombe','Campus named in the speech attribution.',G,2024)
add('abdulbaki-speech','Abdulbaki Ahmad (speech attribution)','People','Gombe','Speaker credited by the published speech.',G,2024,
    gaps='Same-name 2023 itinerary host is unresolved; records remain separate.',nameVariants=['Abdulbaki Ahmad'])
add('fulfulde-speech','I Cease To Be When Fulfulde Ceases To Be','Publications','Gombe','Published address on Fulfulde and poetry.',G,2024,
    kind='Published speech',publicationState='Published — documented',
    dateFact=dict(label='Published',value='24 October 2024',url=G),
    dateBasis='Web publication date; no event date inferred.',gaps='Metadata only; speech text and photographs not copied.')
for b,label in [('gsu-campus','campus stated'),('abdulbaki-speech','credited speaker'),('fulfulde-speech','published speech evidence'),('ccpc','named programme')]:edge('ccpc-gsu-speech',b,label,G,None,'First-person occurrence evidence; event date unresolved')
edge('abdulbaki-speech','fulfulde-speech','credited speaker / author',G,2024)

# The user supplied the exact reported proposal. Additional fetched report text
# was inspected; no extra administrative biography imported. Event year is inferred.
add('ccpc-orerokpe-proposal','CCPC — Orerokpe proposal','Platforms','Orerokpe','Proposed; completion unverified.',V,2026,'Announcement verified',
    kind='Poetry gathering',eventEvidence='Proposal approved in report; upcoming, year inferred',
    dateFact=dict(label='Proposed',value='17 October (2026 inferred)',url=V),
    dateBasis='Year inferred from the 28 August 2026 report, not explicit in the event sentence. As of 13 October, the proposed day is future. University confirmation is pending.',
    gaps='Visit date has a weekday mismatch: 27 August 2026 is Thursday, not Wednesday. The 2023 Salomi Ikoyoko–Trisha and 2026 Salome Ikokoyo records are not merged.',
    phase=dict(label='Proposal; not completed',date='17 October · year inferred',url=V))
add('sdu-orerokpe','Southern Delta University — Orerokpe Campus','Places','Orerokpe','Proposed setting.',V,2026,'Announcement verified')
add('salome-ikokoyo','Salome Ikokoyo','People','Orerokpe','Proposal presenter.',V,2026,'Report supported',
    nameVariants=['Madam Salome Ikokoyo'],gaps='Possible same person as Salomi Ikoyoko (Trisha) is unverified; no identity merge.')
edge('ccpc-orerokpe-proposal','sdu-orerokpe','proposed campus',V,'17 October; year inferred 2026','Proposal only, not held')
edge('salome-ikokoyo','ccpc-orerokpe-proposal','proposal presenter',V,2026,'Reported proposal; identity variant unresolved')

# Full report text was returned by targeted search after direct opens timed out.
# Author Albert Ograka is the forum secretary; this is insider event evidence.
add('dlf-world-poetry-2024','Delta Literary Forum — World Poetry Day (2024)','Platforms','Asaba','Secretary reports a held poetry gathering.',A,2024,
    kind='Poetry gathering',eventEvidence='Held — insider report',historical=True,
    dateFact=dict(label='Reported event',value='21 March 2024',url=A),
    dateBasis='Insider account published 22 March 2024. No inference of present activity.',
    gaps='Source text was retrieved through search after direct fetch timeouts. Independent event corroboration and publisher metadata for the cited books remain pending.')
add('chike-secretariat','Chike Edozien Secretariat','Places','Asaba','Reported gathering venue.',A,2024)
for id,name,summary in [('albert-ograka','Albert Ograka','Forum secretary and report author.'),('alonu-azua','Alonu Azua / Azua Alonu','Forum chairman in this account.'),('nkechi-maduemezia','Nkechi Maduemezia','Reported poetry reader.'),('melvis-ugo','Melvis Ugo Chidera','Reported performer and chair’s representative.')]:
    p=add(id,name,'People','Asaba',summary,A,2024)
    if id=='alonu-azua':p['nameVariants']=['Alonu Azua','Azua Alonu']
add('ogaga-ifowodo','Ogaga Ifowodo','People','Nigeria','Author credited in a book reference.',A,2024,
    nameVariants=['Ogaga Ifowode'],gaps='A book citation is not evidence of attendance at the Asaba event.')
for id,title,author in [('izuma','Izuma','albert-ograka'),('ash-flakes','Ash Flakes','david-diai'),('oil-lamp','Oil Lamp','ogaga-ifowodo')]:
    p=add(id,title,'Publications','Nigeria','Poetry collection cited in the account.',A,2024,
      publicationState='Cited publication — bibliographic verification pending',
      dateBasis='2024 is the citing report year, not the publication year.',gaps='Publisher, original date, edition and ISBN not verified.')
    if id=='ash-flakes':p['nameVariants']=['Ash Flakes','Ashflakes']
    edge(author,id,'author attributed',A,None,'Bibliographic attribution in insider report; publisher metadata pending')
    edge('dlf-world-poetry-2024',id,'cited in account',A,2024,'Citation / reading context, not author attendance')
for b,label in [('delta-literary-forum','reported host'),('chike-secretariat','reported venue'),('alonu-azua','reported opening address'),('nkechi-maduemezia','reported reader'),('melvis-ugo','reported performer'),('david-diai','reported reader')]:edge('dlf-world-poetry-2024',b,label,A,'2024-03-21','Insider report; independent corroboration pending')
edge('albert-ograka','delta-literary-forum','secretary as of 2024',A,2024)
edge('alonu-azua','delta-literary-forum','chairman as of 2024',A,2024)
edge('david-diai','izuma','reported reader of poems',A,'2024-03-21')
claim('dlf-world-poetry-2024','Four schools reported participating; institution and student identities not expanded in this batch.',A,'Insider report only')
p=d['overrides'].setdefault('delta-literary-forum',{})
p.update(verification=dict(label='Source confirmed',sourceURL=A,reviewedAt='2026-10-13',scope='Insider histories for 2009 and 2024; current activity unverified.'),links=[dict(title='2024 secretary’s report',url=A)],gaps='2009 and 2024 records do not prove uninterrupted operation or current activity.')

# Preserve contradictory venue/winner/judge strings as variants, never silently
# normalise them into a venue identity or winning-person connection.
for id in ['bots-2025','bots-contest-2025']:
    p=next(x for x in d['profiles'] if x['id']==id)
    p['gaps']+=' Pre-event source names Edo Innovation Hub; retrospective names Sir Victor Uwaifo Creative Hub. Organiser names Oghenovo (Floreb); outlet names Oghenevho. Judge variants: Aiko Obobaifo / Aiko Ebobaigbe. They remain unresolved.'
    p['sourceVariants']={'venue':['Sir Victor Uwaifo Creative Hub','Edo Innovation Hub'],'winner':['Oghenovo (Floreb the poet)','Oghenevho'],'judge':['Aiko Obobaifo','Aiko Ebobaigbe']}
claim('bots-2025','Venue, winner and judge variants retained; no uncertain identity merge. Periscope is co-organiser-associated, not independent.',
      'https://periscopenga.com/2025/08/glitz-glamour-as-battle-of-stanzas-redefines-poetry-events-in-nigeria-births-first-anthology-of-poems-in-edo/','Unresolved variants')

path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,indent=2)+';\n')
logpath.write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n')
print('Saved addendum records and claim ledger')
