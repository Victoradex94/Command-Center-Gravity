from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];p=root/'dist/atlas-audit.json';d=json.loads(p.read_text());claims=[]
O='https://guardian.ng/art/ogun-marks-2024-cross-country-poetry-celebration-with-funfair/'
L='https://independent.ng/yemi-adebiyi-to-host-cross-country-poetry-celebration-in-lagos/'
N='https://www.unlv.edu/people/chidiebere-nwuguru'
U='https://www.uncannymagazine.com/issues/uncanny-magazine-issue-fifty-eight/'
M='https://mizna.org/journal-slider/24-1-myth-and-memory/'
P='https://www.ananigeria.org/documents/ANA%20MAGAZINE%202019.pdf#page=25'
def add(id,name,cat,city,text,url,year=None,label='Source confirmed',**kw):
 row=dict(id=id,name=name,category=cat,city=city,summary=text,status=label+'; claim-scoped',verification=dict(label=label,sourceURL=url,reviewedAt='2026-10-13',scope=text),links=[dict(title='Reviewed source',url=url)],years=[] if year is None else [dict(year=year,label='Source / event evidence; see date basis',url=url)],media=[],gaps='Independent event corroboration or present activity unverified.',**kw)
 old=next((x for x in d['profiles'] if x['id']==id),None)
 if old:old.update(row)
 else:d['profiles'].append(row)
 claims.append(dict(entity=id,claim=text,sourceURL=url,status=label,confidence='High for source-stated claim; wider biography/activity not inferred'))
def edge(a,b,label,url,date=None,status='Only the source-stated role'):
 e=dict(a=a,b=b,label=label,url=url,date=date,status=status)
 if not any(all(x.get(k)==e[k] for k in ['a','b','label','url']) for x in d['relationships']):d['relationships'].append(e)
 claims.append(dict(entity=a,claim=label+' → '+b,sourceURL=url,status=status,confidence='High for attribution'))
add('ccpc-abeokuta-2024','CCPC — Abeokuta (2024)','Platforms','Abeokuta','Guardian reports poetry performances and participation certificates.',''+O,2024,eventEvidence='Held — single newspaper report',historical=True,dateBasis='Published 2 November 2024, says last weekend; exact event day not stated. National date not substituted.')
add('usc-cathedral-hall','USC (Cathedral) Hall','Places','Abeokuta','Reported event venue.',O,2024)
add('babatunde-sanyaolu','Babatunde Sanyaolu','People','Abeokuta','Reported host.',O,2024)
add('adesola-adenekan','Adeṣọla Adenẹkan','People','Abeokuta','Reported co-host.',O,2024,nameVariants=['Adesola Adenekan'])
for b,l in [('usc-cathedral-hall','reported venue'),('babatunde-sanyaolu','host reported'),('adesola-adenekan','co-host reported'),('c2','programme initiative attributed'),('ccpc','named programme')]:edge('ccpc-abeokuta-2024',b,l,O,2024,'Single newspaper post-event report')
add('ccpc-ojokoro-2024','CCPC — Ojokoro (2024 announcement)','Platforms','Lagos','Advance notice advertises a poetry gathering.',L,2024,label='Announcement verified',eventEvidence='Announced; occurrence unverified',dateFact=dict(label='Scheduled',value='26 October 2024',url=L),dateBasis='Notice published 28 September 2024. No qualifying completion account established in this pass.',phase=dict(label='Announced; not verified as held',date='26 October 2024',url=L))
add('ojokoro-library','Ojokoro Community Library','Places','Lagos','Announced venue.',L,2024,label='Announcement verified')
for id,name,text in [('yemi-adebiyi','Yemi Adebiyi','Announced host and named poetry-book author.'),('adedapo-conde','Adedapo Conde','Announced co-host.'),('mercy-eno','Mercy Eno','Announced co-host.')]:add(id,name,'People','Lagos',text,L,2024,label='Announcement verified')
for b,l in [('ojokoro-library','announced venue'),('yemi-adebiyi','announced host'),('adedapo-conde','announced co-host'),('mercy-eno','announced co-host'),('c2','announced initiative')]:edge('ccpc-ojokoro-2024',b,l,L,2024,'Advance announcement; attendance and occurrence unverified')
add('rhapsodies-corper','Rhapsodies of a Corper','Publications','Nigeria','Poetry book attributed to Yemi Adebiyi.',L,None,publicationState='Cited book; bibliographic metadata pending',dateBasis='Publisher, ISBN and original date not verified; 1998 interview lead not imported without full review.')
edge('yemi-adebiyi','rhapsodies-corper','author attributed',L)
row=next(x for x in d['profiles'] if x['id']=='nwuguru-chidiebere');row.update(nameVariants=['Nwuguru Chidiebere Sullivan','Chidiebere Nwuguru'],summary='UNLV biography identifies the writer and Izzi, Abakaliki ancestry; 2023 event role remains announced only.',verification=dict(label='Primary biography confirmed',sourceURL=N,reviewedAt='2026-10-13',scope='Name variants and writer identity; not Abakaliki event occurrence.'),gaps='UNLV is an undated current profile; it does not confirm the planned 2023 gathering. No ancestry-to-residence inference.');row['links'].append(dict(title='University identity biography',url=N)) if not any(x['url']==N for x in row['links']) else None
claims.append(dict(entity='nwuguru-chidiebere',claim='Full name in UNLV biography matches itinerary identity; institutional biography supports writer identity, not event completion.',sourceURL=N,status='Primary biography',confidence='High for name variant match'))
add('uncanny-58','Uncanny Magazine — Issue 58','Publications','Nigeria / diaspora','Publisher credits Nwuguru Chidiebere Sullivan’s poetry.',U,2024,publicationState='Publisher-documented issue',dateFact=dict(label='Issue period',value='May / June 2024',url=U),dateBasis='Publisher gives staged release dates; no poem text reproduced.')
add('mizna-24-1','Mizna 24.1 — Myth and Memory','Publications','Nigeria / diaspora','Publisher’s feature list names Nwuguru Chidiebere Sullivan.',M,2023,publicationState='Publisher-documented issue',dateFact=dict(label='Issue period',value='Summer 2023',url=M),dateBasis='Publisher news dated 21 June 2023; exact contributed work/genre not established by the feature list.')
edge('nwuguru-chidiebere','uncanny-58','poetry contributor credited',U,2024,'Publisher table of contents')
edge('nwuguru-chidiebere','mizna-24-1','featured contributor credited',M,2023,'Publisher feature list; contributed work/genre unverified')
# Re-read actual ABIA CHAPTER page: the earlier screenshot locator was wrong.
for id in ['ana-abia-okara-2019','abia-hotels-aba','ana-abia-yusuf-2019']:
 row=next(x for x in d['profiles'] if x['id']==id);row['verification']['sourceURL']=P
 for item in row.get('links',[]):
  if 'ANA%20MAGAZINE' in item.get('url',''):item['url']=P
 if row.get('dateFact'):row['dateFact']['url']=P
row=next(x for x in d['profiles'] if x['id']=='ana-abia-yusuf-2019');row['dateBasis']='Chapter names winning schools: Intellectual Giant Christian School Academy, Renascent Educational School and Victory Model Schools, Aba. Ranks, prize amounts and competition venue not specified. Prior imported school/amount metadata withdrawn after rechecking PDF page 25.'
d['relationships']=[e for e in d['relationships'] if not(e['a']=='ana-abia-yusuf-2019' and e['b']=='abia-hotels-aba')]
claims.append(dict(entity='ana-abia-yusuf-2019',claim='Corrected school names; removed unsupported amounts and venue link. Reading venue remains supported. PDF page 25, printed 25.',sourceURL=P,status='Correction after primary-text recheck',confidence='High for explicit chapter wording'))
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,indent=2)+';\n')
(root/'research/handoff-followup-claims.json').write_text(json.dumps(dict(reviewedAt='2026-10-13',claims=claims),ensure_ascii=False,indent=2)+'\n');print('Saved',len(claims),'claims and correction')
