"""Independent read-only audit of retained live evidence; no connector calls."""
import copy,hashlib,json,sqlite3
from pathlib import Path
from collections import Counter
ROOT=Path('/workspace/Command-Center-Gravity')
LIVE=ROOT/'docs/AJ-0010-live'
OUT=Path('/tmp/aj0010-live-review')
checks=[]
def check(condition,label):
    assert condition,label
    checks.append(label)
def read(name):return json.loads((LIVE/name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def payload(value):
    check(value.get('isError') is False,'explicit connector success')
    check(isinstance(value.get('structuredContent'),dict) and 'error' not in value['structuredContent'],'structured response without error')
    return value['structuredContent']
def literal(cell):
    v=cell.get('userEnteredValue',{})
    check(v=={} or set(v)=={'stringValue'},'literal/nonformula cell')
    return v.get('stringValue','')
def mask(capture):
    result=copy.deepcopy(capture)
    for cell in result['cells'][1][:17]:cell.pop('userEnteredValue',None)
    return result
before_hashes={str(p.relative_to(ROOT)):sha(p) for p in LIVE.iterdir() if p.is_file()}
fixture=json.loads((ROOT/'docs/AJ-0010-fixture-plan.json').read_text())
check(sha(ROOT/'docs/AJ-0010-fixture-plan.json')=='c448dd13a66e038f1bc9bd554dba124002a05b5ff80780cc6a1a0c4edf746e48','exact retained fixture hash')
config=read('config.json');book=config['spreadsheet_id'];sheet=config['sheet_id'];scope=f'google-sheets/{book}/{sheet}'
check(book=='1yk-mBJf4RQhRC7M7QK0cHRMQhqHWStC-yQpbB2KxksE' and sheet==1505506183,'exact designated sandbox scope')
check(book!='19mGYxNeyldQEK4N194Q8Yz7L6m_z7LSvFmHGzwuqA84','sandbox is not production workbook')
empty=['']*17;create=fixture['create']['cells'];update=fixture['update']['cells']
check(len(create)==len(update)==17,'exact17 intended cells each')
check([i for i,(a,b) in enumerate(zip(create,update)) if a!=b]==[4,10,11,12,16],'only intended E K L M Q values differ')
for cells,revision in ((create,1),(update,2)):
    lineage=dict(token.strip().split('=',1) for token in cells[16].split(';'))
    check(lineage=={'SpecRevision':'1','RunEpoch':'1','Attempt':'1','Nonce':'VA-LIVE-SHEETS-0010-01','RecordRevision':str(revision),'ProtocolVersion':'v1.1.0','CatalogueVersion':'1.0.0'},f'exact revision{revision} and unchanged execution lineage')
baseline=read('execute-before.json');final=read('execute-after.json')
check(read('setup-verified-capture.json')==baseline,'setup verified actual baseline equals execute-before')
check(mask(baseline)==mask(final),'entire exposed neighbours formats validation notes metadata ACL unchanged across both logical writes')
check(final==read('reconcile-before.json')==read('reconcile-after.json'),'exact entire post-update capture unchanged on restart')
check([literal(c) for c in baseline['cells'][1][:17]]==empty,'target initially empty17 cells')
check([literal(c) for c in final['cells'][1][:17]]==update,'final17 cells exactly saved update')
check([literal(c) for c in baseline['cells'][0][:17]]==fixture['header_A1_Q1'],'exact17 schema headers')
statuses=['Intake','Ready','Working','Review','Blocked','Done','Cancelled']
for i,row in enumerate(baseline['cells']):
    check(len(row)==18 and literal(row[17])==f'AJ-0010 sentinel R{i+1}',f'row{i+1} complete18 and sentinel')
    for cell in row:
        fmt=cell.get('userEnteredFormat',{})
        check(fmt.get('numberFormat',{}).get('type')=='TEXT' and fmt.get('wrapStrategy')=='WRAP','TEXT/WRAP formatting')
    if i:
        for col,options in ((4,statuses),(13,['Yes','No'])):
            rule=row[col]['dataValidation']
            check(rule.get('strict') is True and rule['condition']=={'type':'ONE_OF_LIST','values':[{'userEnteredValue':s} for s in options]},f'row{i+1} exact validation at{col}')
        check([literal(c) for c in row[:17]]==empty,'all initial data rows empty')
for cell in baseline['cells'][0][:17]:
    check(cell['userEnteredFormat']['textFormat']['bold'] is True,'header bold')
    check(cell['userEnteredFormat']['backgroundColor']=={'red':0.8980392,'green':0.8980392,'blue':0.8980392},'actual Google-normalized header RGB retained')
for capture in (baseline,final,read('reconcile-after.json')):
    for name,id_ in (('file',book),('root',config['root_folder_id'])):
        file=capture[name]
        check(file['id']==id_ and file['shared'] is False and file['drive_id'] is None,'private My Drive identity')
        check(file['source_visibility_status']=='permission_metadata_available','actual permission metadata available')
        perms=file['permissions']
        check(len(perms)==1 and perms[0]['type']=='user' and perms[0]['role']=='owner' and perms[0]['emailAddress']==config['owner_email'],'exact authenticated owner-only permissions')
        check(not any(p.get('inherited') for p in perms[0].get('permissionDetails',[])),'no exposed inherited permission')
    check(capture['file']['parent_ids']==[config['root_folder_id']],'workbook directly under private My Drive root')
    props=capture['metadata']['sheets'][0]['properties']
    check(len(capture['metadata']['sheets'])==1 and props['sheetId']==sheet and props['title']=='Agent Jobs Sandbox' and props['gridProperties']=={'rowCount':6,'columnCount':18,'frozenRowCount':1},'exact single6x18 frozen-header grid')
logs={};sessions={};cell_readbacks=[]
for mode,count in (('execute',46),('reconcile',8)):
    requests=sorted(LIVE.glob(f'{mode}-tool-*-request.json'))
    responses=sorted(LIVE.glob(f'{mode}-tool-*-response.json'))
    check(len(requests)==len(responses)==count,f'{mode} complete exact request-response pairs')
    logs[mode]=[]
    for index,p in enumerate(requests,1):
        req=json.loads(p.read_text());res=read(p.name.replace('-request','-response'))
        check(req['sequence']==index,f'{mode} consecutive sequence{index}')
        sessions.setdefault(mode,set()).add(req['bridge_session'])
        body=payload(res);tool=req['tool'];args=req['arguments']
        check(tool in ['mcp__codex_apps__google_drive_'+s for s in ('get_file_metadata','get_spreadsheet_metadata','get_spreadsheet_cells','batch_update_spreadsheet')],'only supported scoped tools')
        if tool.endswith('get_file_metadata'):
            check(args['fileId'] in (book,'root'),'file read target only sandbox or root')
            check(body==baseline['root' if args['fileId']=='root' else 'file'],'every intermediate permission/Drive metadata response unchanged')
        else:
            check(args['spreadsheet_id']==book,'spreadsheet call sandbox only')
        if tool.endswith('get_spreadsheet_metadata'):
            check(body==baseline['metadata'],'every intermediate spreadsheet metadata response unchanged')
        if tool.endswith('get_spreadsheet_cells'):
            check(args['ranges']==["'Agent Jobs Sandbox'!A1:R6"],'complete exact bounded read range')
            rows=body['sheets'][0]['data'][0]['rowData']
            cells=[r['values'] for r in rows]
            check(len(cells)==6 and all(len(r)==18 for r in cells),'complete6x18 live readback')
            expected=update if mode=='reconcile' or index>34 else create if index>17 else empty
            check([literal(c) for c in cells[1][:17]]==expected,f'{mode}{index} exact17 phase values')
            cell_only=copy.deepcopy(cells)
            for c in cell_only[1][:17]:c.pop('userEnteredValue',None)
            check(cell_only==mask(baseline)['cells'],f'{mode}{index} all non-target-values CellData unchanged')
            cell_readbacks.append({'mode':mode,'sequence':index,'revision':2 if expected==update else 1 if expected==create else 0})
        logs[mode].append((req,res))
    check(len(sessions[mode])==1,f'{mode} one bridge session')
check(sessions['execute'].isdisjoint(sessions['reconcile']),'fresh bridge session on restart')
write_indexes=[r['sequence'] for r,s in logs['execute'] if r['tool'].endswith('batch_update_spreadsheet')]
check(write_indexes==[17,34],'exactly2 logical mutation calls at17and34')
check(not any(r['tool'].endswith('batch_update_spreadsheet') for r,s in logs['reconcile']),'zero replay mutation calls during reconcile')
for file in ('writer.sqlite','receipts.sqlite'):
    check(not (LIVE/(file+'-wal')).exists() and not (LIVE/(file+'-journal')).exists(),'no unapplied sidecar journal for immutable read')
with sqlite3.connect('file:'+str((LIVE/'writer.sqlite').resolve())+'?mode=ro&immutable=1',uri=True) as db:
    check(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','writer SQLite integrity')
    state=json.loads(db.execute('SELECT body FROM journal WHERE id=1').fetchone()[0])
with sqlite3.connect('file:'+str((LIVE/'receipts.sqlite').resolve())+'?mode=ro&immutable=1',uri=True) as db:
    check(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','receipt SQLite integrity')
    identity=json.loads(db.execute('SELECT body FROM identity WHERE id=1').fetchone()[0])
    receipts={attempt:json.loads(body) for attempt,body in db.execute('SELECT attempt,body FROM receipts')}
check(identity==config,'receipt DB exact target identity')
check(state==read('execute-writer-state.json')==read('reconcile-writer-state.json'),'writer DB and both exported states identical; no restart write/audit replay')
check(state['schema']==2 and state['scope']==scope and state['coordinator']=='Dẹkun','writer scope/schema/coordinator')
check(state['owner']=={'actor':'AJ-0010 executor sole sandbox proxy','epoch':1},'one retained explicit writer owner')
check(state['circuits']==state['permission_stops']==state['renewals']=={},'no circuits permission stops or renewal bypass')
ids=[fixture[n]['operation_id'] for n in ('create','update')]
check(set(state['operations'])==set(ids) and set(receipts)=={id_+'/0' for id_ in ids},'exact stable operation and attempt identities')
for name,index in (('create',17),('update',34)):
    id_=fixture[name]['operation_id'];op=state['operations'][id_];receipt=receipts[id_+'/0']
    check(op['request']==fixture[name],'writer exact original fixture request')
    check(op['outcome']=='SUCCESS' and op['recovery_used']==0 and not op['circuit_open'],'success with no recovery')
    check(len(op['submissions'])==1 and op['submissions'][0]==receipt['submission'],'exact one durable matching submission')
    check(receipt['exception_type'] is None,'no transport exception in original receipt')
    req,res=logs['execute'][index-1]
    check(receipt['request']==req['arguments'] and receipt['response']==res==read(name+'-supervisor-original-response.json'),'original supervisor response call log and receipt match')
    body=payload(res)
    check(body=={'spreadsheetId':book,'replies':[{}],'updatedSpreadsheet':None},'actual native one-update acknowledgement')
    update_request=req['arguments']['requests']
    check(len(update_request)==1 and set(update_request[0])=={'updateCells'},'one updateCells only')
    u=update_request[0]['updateCells']
    check(u['range']=={'sheetId':sheet,'startRowIndex':1,'endRowIndex':2,'startColumnIndex':0,'endColumnIndex':17} and u['fields']=='userEnteredValue','only A2Q2 values target')
    check(len(u['rows'])==1 and [literal(c) for c in u['rows'][0]['values']]==fixture[name]['cells'],'exact17 intended values in provider request')
    sub=receipt['submission']
    check(sub['operation_id']==id_ and sub['attempt_id']==id_+'/0' and sub['scope']==scope and sub['position']==2,'bound original provider attempt')
    check(sub['before'] is None if name=='create' else sub['before']['cells']==create,'correct submission before state')
    # Each immediate post-ack four-read capture is independently rebuilt from original tool responses.
    post={'file':payload(logs['execute'][index][1]),'root':payload(logs['execute'][index+1][1]),'metadata':payload(logs['execute'][index+2][1]),'cells':[r['values'] for r in payload(logs['execute'][index+3][1])['sheets'][0]['data'][0]['rowData']]}
    check(mask(receipt['baseline'])==mask(post),'exact entire exposed structure/ACL preserved for each individual operation')
    check([literal(c) for c in post['cells'][1][:17]]==fixture[name]['cells'],'original immediate post-ack17 readback')
    observations=[e['observation'] for e in state['audit'] if e['kind']=='operation_observed' and e['operation']==id_]
    check(len(observations)==1 and observations[0]['effect']=='applied' and observations[0]['settled'] is True and observations[0]['effects_resolved'] is True,'one exact positive settled observation')
    check(observations[0]['digest']==op['digest']==sub['digest'],'operation digest bound in evidence')
    check(digest(receipt) in observations[0]['evidence'] and digest(post) in observations[0]['evidence'],'receipt and readback hashes bind original evidence')
for mode in ('execute','reconcile'):
    result=read(mode+'-result.json');process=read(mode+'-process.json')
    check(result['submissions']==2 and result['recovery_used']==0,'exact retained submission budget')
    check(result['current_snapshot']['rows'][0]['cells']==update,'fresh final snapshot matches update')
    check(process['exit_code']==0 and (' '+mode+' ') in process['command'],'process command/mode and actual terminal exit0')
    emitted=json.loads(process['output'].strip())
    check(emitted['kind']=='session_complete' and emitted['mode']==mode and emitted['outcomes']==result['outcomes'],'terminal output agrees with saved result')
check(read('execute-process.json')['tool_session_id']!=read('reconcile-process.json')['tool_session_id'],'distinct terminal process sessions')
workbook=payload(read('workbook-original-response.json'))
check(workbook['fileId']==book and workbook['title']==fixture['workbook_title'],'one retained workbook-create result with exact title/ID')
check(read('workbook-intent.json')['search_response']['structuredContent']['results']==[],'creation preflight found no equivalent title')
setup=payload(read('setup-original-response.json'))
check(setup['spreadsheetId']==book and setup['replies']==[{}]*7,'one retained seven-request setup acknowledgement')
check(read('setup-intent.json')['request']['spreadsheet_id']==book,'setup target same sandbox')
def actual_sheet_ids(value):
    if isinstance(value,dict):return {key:sheet if key=='sheetId' else actual_sheet_ids(item) for key,item in value.items()}
    if isinstance(value,list):return [actual_sheet_ids(item) for item in value]
    return value
check(read('setup-intent.json')['request']['requests']==actual_sheet_ids(fixture['setup_requests_with_example_sheet_id_0']),'setup requests exactly fixture with grounded sheet ID only')
check(read('workbook-intent.json')['request']=={'mime_type':'application/vnd.google-apps.spreadsheet','title':fixture['workbook_title']},'exact one bounded workbook creation intent')
check(read('setup-verification.json')['actual_header_rgb']==0.8980392,'provider format normalization retained honestly')
for key,value in before_hashes.items():check(sha(ROOT/key)==value,'read-only review preserved '+key)
summary={'status':'PASS','assertions':len(checks),'scope':scope,'owner_email':config['owner_email'],'fixture_sha256':sha(ROOT/'docs/AJ-0010-fixture-plan.json'),'execute_calls':len(logs['execute']),'execute_reads':44,'logical_mutations':write_indexes,'reconcile_reads':len(logs['reconcile']),'replay_mutations':0,'journal_operations':ids,'attempts':list(receipts),'recovery_used':0,'cell_readbacks':cell_readbacks,'process_sessions':[read('execute-process.json')['tool_session_id'],read('reconcile-process.json')['tool_session_id']],'before_capture_sha256':digest(baseline),'after_capture_sha256':digest(final),'writer_db_sha256':sha(LIVE/'writer.sqlite'),'receipt_db_sha256':sha(LIVE/'receipts.sqlite'),'limits':['Local retained evidence independently reviewed; reviewer made no connector calls.','Exactly2 logical submissions and zero replay visible in retained call logs/journals; hidden provider retries are not observable.','Synchronous success and full readback are scoped completion evidence, not CAS/distributed exclusion/exactly-once.','Reconcile returned cached historical SUCCESS for prior operations and separately performed fresh current readbacks; no live crash/fault injection.','Setup requested RGB .9 was normalized to0.8980392; initial precision failure preserved, no setup retry evidenced; logical-write structure comparisons use exact actual baseline.']}
(OUT/'verification-results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(OUT/'evidence-manifest.json').write_text(json.dumps(before_hashes,indent=2)+'\n')
(OUT/'checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
