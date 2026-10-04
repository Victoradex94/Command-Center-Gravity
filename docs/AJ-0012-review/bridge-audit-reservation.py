"""Read-only independent audit; never calls the handoff or Slack."""
import hashlib,json,pathlib,sqlite3
from dispatcher.slack import digest
base=pathlib.Path('docs/AJ-0012-evidence')
def read_journal(name):
    c=sqlite3.connect('file:'+str(base/name)+'?mode=ro',uri=True)
    try:return json.loads(c.execute('select body from state where id=1').fetchone()[0])
    finally:c.close()
s=read_journal('prepared-journal.sqlite');old=read_journal('pre-handoff-journal.sqlite')
req=json.loads((base/'first-root-request.json').read_text());key=req['operation_id']
assert s==json.loads((base/'first-root-reservation-snapshot.json').read_text())
assert s['controlled_slack']['binding']==old['controlled_slack']['binding']
assert s['controlled_slack']['fingerprint']==old['controlled_slack']['fingerprint']==digest(s['controlled_slack']['binding'])
assert key=='AJ-0012/1/1/1/VA-LIVE-SLACK-0012-01/synthetic-transport/activity'
assert req['destination']=='C0C7CRRJDLY' and req['thread']==''
assert req['content']==old['messages'][key]['text']
assert req['route']=='user_message.send_message(channel=slack)'
assert req['workspace']=='T0C63317YDV' and req['sender']=='U0C6C7V10P5'
assert req['request_sha256']==digest({k:v for k,v in req.items() if k!='request_sha256'})
assert set(s['root_handoff']['requests'])==set(s['controlled_slack']['operations'])=={key}
assert s['root_handoff']['requests'][key]==dict(request=req,state='reserved',reference='')
assert s['controlled_slack']['operations'][key]==dict(calls=1,request_sha256=req['request_sha256'],state='root-request-reserved')
assert s['messages'][key]['state']=='sending' and s['messages'][key]['attempts']==1
assert not s['root_handoff']['evidence'] and not s['commands'] and not s['incidents']
for k,m in s['messages'].items():
    assert m['human_read']=='unknown' and m['reference']==''
    if k!=key:assert m==old['messages'][k] and m['state']=='pending' and m['attempts']==0
print('PASS: original binding intact; first activity request durably reserved; two untouched pending intents; no receipts/acceptance/presence/human-read claim.')
print('Request SHA256: '+req['request_sha256'])
print('Journal SHA256: '+hashlib.sha256((base/'prepared-journal.sqlite').read_bytes()).hexdigest())
