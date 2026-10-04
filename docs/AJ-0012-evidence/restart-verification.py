"""Reopen the actual AJ-0012 journal; no network, subprocess, or send allowed."""
import hashlib,json,os,pathlib,sqlite3,sys
from tests.offline_suite import reject_external
from dispatcher.engine import Dispatcher
from dispatcher.store import InMemoryRepository
from dispatcher.slack import SlackBoundary,SlackJournal,digest
from dispatcher.slack_handoff import RootHandoff,ORDER
sys.addaudithook(reject_external)
p=pathlib.Path('docs/AJ-0012-evidence')
previous=json.loads((p/'reconciliation-process.json').read_text())
assert previous['pid']!=os.getpid()
journal_path=p/'prepared-journal.sqlite'
before_hash=hashlib.sha256(journal_path.read_bytes()).hexdigest()
j=SlackJournal(journal_path)
before=j.snapshot()
assert before==json.loads((p/'final-reconciled-snapshot.json').read_text())
archive=sqlite3.connect('file:'+str(p/'pre-handoff-journal.sqlite')+'?mode=ro',uri=True)
original=json.loads(archive.execute('SELECT body FROM state WHERE id=1').fetchone()[0]);archive.close()
assert before['controlled_slack']['binding']==original['controlled_slack']['binding']
assert before['controlled_slack']['fingerprint']==original['controlled_slack']['fingerprint']
assert len(before['root_handoff']['requests'])==len(before['root_handoff']['evidence'])==3
assert before['commands']=={} and before['incidents']=={}
checks=[]
for key in ORDER:
    m=before['messages'][key]; op=before['controlled_slack']['operations'][key]
    record=before['root_handoff']['requests'][key]; req=record['request']
    assert req['request_sha256']==digest({k:v for k,v in req.items() if k!='request_sha256'})
    assert req['operation_id']==key and req['attempt_id']==key+'/send-attempt-1'
    assert (req['destination'],req['content'],req['thread'])==(m['destination'],m['text'],m['thread'])
    assert m['state']==record['state']==op['state']=='verified'
    assert m['attempts']==op['calls']==1 and m['human_read']=='unknown'
    assert m['reference']==record['reference']==op['reference']
    entries=[e for e in before['root_handoff']['evidence'] if e['request_sha256']==req['request_sha256']]
    assert len(entries)==1
    e=entries[0]; a=e['acceptance']; o=e['observation']
    assert a['reference']==o['reference']==m['reference']
    for f in ('workspace','sender','destination'):assert a[f]==o[f]==req[f]
    assert o['text']==req['content'] and o['thread']==req['thread']==''
    label=key.rsplit('/',1)[-1]
    assert e['raw_response']==json.loads((p/(label+'-root-receipt.json')).read_text())
    assert e['raw_readback']==json.loads((p/(label+'-root-readback.json')).read_text())
    checks.append({'operation':key,'reference':m['reference'],'destination':m['destination'],'attempts':m['attempts'],'human_read':m['human_read']})
repo=InMemoryRepository()
boundary=SlackBoundary(Dispatcher(repo),j,lambda *args:False)
h=RootHandoff(boundary,lambda:True)
send_calls=[]
def forbidden_send(*args):
    send_calls.append(args)
    raise AssertionError('No further send or handoff is authorised')
h.send=forbidden_send
for key in ORDER:assert boundary.deliver(key,h)=='verified'
assert h.prepare_next() is None
assert send_calls==[] and repo.all()==()
after=j.snapshot()
assert after==before
j.close()
result=dict(reconciliation_pid=previous['pid'],restart_pid=os.getpid(),same_journal=str(journal_path),before_sha256=before_hash,after_sha256=hashlib.sha256(journal_path.read_bytes()).hexdigest(),network_and_subprocess_blocked=True,root_reported_actual_provider_sends=3,retained_actual_acceptances=3,retained_actual_destination_readbacks=3,restart_send_calls=0,new_requests=0,attempt_counters=[1,1,1],logical_journal_unchanged=True,original_bindings_unchanged=True,checks=checks,limitations='Reconciles authentic root-supplied original destination readbacks retained in journal; no fresh Slack read or send during restart. Does not assert global duplicate absence from partial channel history or human reading.')
with (p/'restart-verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result,indent=2))
