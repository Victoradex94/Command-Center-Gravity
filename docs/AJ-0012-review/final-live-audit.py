"""Independent final read-only audit of retained actual receipt evidence."""
import hashlib,json,pathlib,re,sqlite3
from dispatcher.slack import digest
b=pathlib.Path('docs/AJ-0012-evidence')
def data(n):return json.loads((b/n).read_text())
def journal(n):
 c=sqlite3.connect('file:'+str(b/n)+'?mode=ro',uri=True)
 try:return json.loads(c.execute('select body from state where id=1').fetchone()[0])
 finally:c.close()
s=journal('prepared-journal.sqlite');old=journal('pre-handoff-journal.sqlite')
assert s==data('final-reconciled-snapshot.json')
assert s['controlled_slack']['binding']==old['controlled_slack']['binding']
assert digest(s['controlled_slack']['binding'])==old['controlled_slack']['fingerprint']==s['controlled_slack']['fingerprint']
assert len(s['messages'])==len(s['controlled_slack']['operations'])==len(s['root_handoff']['requests'])==len(s['root_handoff']['evidence'])==3
ids=[]
for label,dest,ts in [('activity','C0C7CRRJDLY','1791139471.957359'),('attention','C0C6N5H1QCU','1791139693.278939'),('owner','D0C6J9ZKF4J','1791139894.566079')]:
 key='AJ-0012/1/1/1/VA-LIVE-SLACK-0012-01/synthetic-transport/'+label
 m=s['messages'][key];rec=s['root_handoff']['requests'][key];op=s['controlled_slack']['operations'][key];req=rec['request']
 assert req['request_sha256']==digest({k:v for k,v in req.items() if k!='request_sha256'})
 assert req['operation_id']==key and req['attempt_id']==key+'/send-attempt-1'
 assert req['destination']==dest and req['thread']=='' and req['content']==old['messages'][key]['text']
 assert req['workspace']=='T0C63317YDV' and req['sender']=='U0C6C7V10P5'
 raw=data(label+'-root-receipt.json');read=data(label+'-root-readback.json');norm=data(label+'-normalization.json')
 entries=[e for e in s['root_handoff']['evidence'] if e['request_sha256']==req['request_sha256']];assert len(entries)==1;e=entries[0]
 assert e['raw_response']==raw and e['raw_readback']==read and e['acceptance']==norm['acceptance'] and e['observation']==norm['observation']
 assert raw['isError'] is False and read['isError'] is False
 ac=raw['structuredContent'];assert json.loads(raw['content'][0]['text'])==ac
 assert ac['status']=='accepted' and ac['workspace_id']=='T0C63317YDV' and ac['destination']==dest and ac['thread_id'] is None
 ref='slack:'+dest+'::'+ts
 assert ac['message_id']==m['reference']==rec['reference']==op['reference']==ref
 assert m['state']==rec['state']==op['state']=='verified' and m['attempts']==op['calls']==1
 assert m['human_read']=='unknown'
 if label!='owner':
  rd=read['structuredContent'];assert json.loads(read['content'][0]['text'])==rd
  rm=rd['messages'][0];assert rd['channel_id']==dest and rm['message_ts']==ts
  assert rm['user_id']=='U0C6C7V10P5' and rm['text']==req['content'] and rm['text_truncated'] is False
 else:
  rendered=json.loads(read['content'][0]['text'])['messages']
  match=re.fullmatch(r'Channel: DM \(([^)]+)\)\n\n=== Message from vicadtorex-dekun &lt;botuser-T0C63317YDV-B0C7CR9QNSU@slack-bots.com&gt; \(([^)]+)\) at ([^\n]+) === \nMessage TS: ([^\n]+)\n([^\n]+)',rendered)
  assert match and match.group(1)==dest and match.group(2)=='U0C6C7V10P5' and match.group(4)==ts and match.group(5)==req['content']
 for field in ('workspace','sender','destination'):assert e['acceptance'][field]==e['observation'][field]==req[field]
 assert e['observation']['text']==req['content'] and e['observation']['thread']==''
 ids.append({'label':label,'destination':dest,'message_id':ref,'request_sha256':req['request_sha256']})
assert not s['commands'] and not s['incidents']
r=data('restart-verification.json');assert r==json.loads((b/'restart-verification.stdout').read_text())
assert r['reconciliation_pid']==data('reconciliation-process.json')['pid']==1463 and r['restart_pid']==1472
assert r['reconciliation_pid']!=r['restart_pid'] and r['restart_send_calls']==r['new_requests']==0
assert r['attempt_counters']==[1,1,1] and r['network_and_subprocess_blocked'] is True
sha=hashlib.sha256((b/'prepared-journal.sqlite').read_bytes()).hexdigest()
assert sha==r['before_sha256']==r['after_sha256']=='bf3b00c1f119b6e4500efe89ebf071064fdc17b3af4b156a2de9e2a0721a1fbf'
print(json.dumps({'result':'PASS','journal_sha256':sha,'messages':ids,'reservation_count':3,'accepted_receipt_count':3,'destination_readback_count':3,'human_read':'unknown','separate_restart_send_calls':0,'separate_restart_new_requests':0,'reviewer_sends':0,'reviewer_journal_mutations':0},indent=2))
