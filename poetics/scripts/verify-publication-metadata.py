from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];p=root/'dist/atlas-audit.json';d=json.loads(p.read_text())
P='https://africaworldpressbooks.com/the-oil-lamp-poems-by-ogaga-ifowodo/'
W='https://search.worldcat.org/es/title/The-oil-lamp/oclc/57434359'
D='https://www.africanwriter.com/odyssey-poems-by-david-diai/'
def profile(id):return next(x for x in d['profiles'] if x['id']==id)
oil=profile('oil-lamp');oil.update(name='The Oil Lamp',nameVariants=['Oil Lamp','The Oil Lamp: Poems'],
  summary='Ogaga Ifowodo collection catalogued by Africa World Press and WorldCat.',
  publicationState='Published — publisher and library metadata',
  bibliography={'Publisher':'Africa World Press','Catalogued year':'2005 (WorldCat copyright record)','ISBN-13':'9781592213603; 9781592213597','ISBN-10':'159221360X; 1592213596','Library record':'OCLC 57434359'},
  dateFact={'label':'Catalogued copyright year','value':'2005','url':W},
  dateBasis='WorldCat lists ©2005. Retail paperback listings give 2006 and different pagination; edition details remain unreconciled.',
  gaps='Publisher SKU is 9781592213603, matched by WorldCat. ISBN check digits pass but that alone does not verify an edition. WorldCat lists 60 pages; retail paperback listings list 82. No poem text copied.',
  verification={'label':'Source confirmed','sourceURL':P,'reviewedAt':'2026-10-13','scope':'Publisher title/author/SKU and library publisher/year/ISBN metadata reviewed; edition pagination/date variation retained.'})
oil['years'].append({'year':2005,'label':'WorldCat copyright year, not the 2024 event date','url':W})
oil['links'] += [{'title':'Publisher catalogue','url':P},{'title':'WorldCat record OCLC 57434359','url':W}]
ash=profile('ash-flakes');ash.update(name='Ashflakes',nameVariants=['Ash Flakes','ASHFLAKES'],
  summary='David Diai collection; author-attributed web excerpt states December 2008 publication.',
  publicationState='Published — author attribution; imprint unverified',
  bibliography={'Author-stated publication':'December 2008','Publisher':'Not verified','ISBN':'Not verified'},
  dateFact={'label':'Author-stated publication','value':'December 2008','url':D},
  dateBasis='Date from an author-attributed excerpt footer retrieved through search; not a verified publisher imprint. The 2024 report is a later citation.',
  gaps='Direct open timed out; readable indexed footer states the month/year. Publisher, ISBN and edition remain unverified. Older author biographies may have been updated; do not date publication from their page headers.')
ash['years'].append({'year':2008,'label':'Author-stated publication month/year','url':D})
ash['links'].append({'title':'Author-attributed publication footer','url':D})
profile('izuma')['bibliography']={'Author':'Albert Ograka (2024 source attribution)','Publication year':'Not verified','Publisher':'Not verified','ISBN':'Not verified'}
profile('izuma')['gaps']='Publication year, publisher and ISBN unresolved. A retailer biography mentions Izuma And Other Poems, but that edition/title relationship is not established. No ISBN from another Ograka book assigned.'
bronze=profile('bronze-capital');bronze['bibliography']={'Editors':'Lanre Sonde; Godson Osarenren (organiser credits)','Foreword':'Eriata Oribhabor (organiser credits)','Reported length':'109 pages; physical book not inspected','Launch':'30 August 2025 (organiser retrospective)','Publisher / ISBN':'Not verified','Contributors':'Complete roster not verified'}
bronze['gaps']='No readable title/copyright pages or contributor roster retrieved in the 12-query metadata batch. Organiser confirms editorial/foreword credits and reported length. Advance publicity has 30/31 August variants; retrospective supplies 30 August. Imprint, ISBN and edition publication date remain unresolved.'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(root/'dist/atlas-audit.js').write_text('window.PoeticsAudit='+json.dumps(d,ensure_ascii=False,indent=2)+';\n')
print('Updated four existing publications; no new identities or attendance links')
