#!/usr/bin/env python3
"""Run HTTP cutover checks from a network that can reach this staging project.
Uses only a publishable key from POETICS_PUBLISHABLE_KEY. Never supply a secret key.
Optional --test-submission creates one explicitly labelled pending-review test;
capture its ID and have the owner inspect it. It never edits the Atlas graph.
"""
import argparse, json, os, urllib.request, urllib.error
BASE = "https://tknahlnirtnanzqqvufb.supabase.co/rest/v1"
p=argparse.ArgumentParser()
p.add_argument("--test-submission", action="store_true")
a=p.parse_args()
key=os.environ.get("POETICS_PUBLISHABLE_KEY","")
if not key.startswith("sb_publishable_"):
    raise SystemExit("Set POETICS_PUBLISHABLE_KEY to the project's publishable key.")
def call(path, body=None, keyed=True, profile=None):
    headers={"Accept":"application/json"}
    if keyed: headers["apikey"]=key
    if profile: headers["Accept-Profile"]=profile
    if body is not None: headers["Content-Type"]="application/json"
    req=urllib.request.Request(BASE+path, data=None if body is None else json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r: return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:
        raw=e.read()
        try: value=json.loads(raw)
        except ValueError: value={"error":"Non-JSON HTTP error"}
        return e.code,value
status,data=call("/rpc/read_poetics_atlas_snapshot",keyed=False)
assert status in (401,403), ("Missing-key denial failed",status)
print("PASS missing-key request denied:",status)
status,data=call("/rpc/read_poetics_atlas_snapshot")
assert status==200, ("Approved read failed",status)
assert len(data.get("rows",[]))==458 and len(data.get("edges",[]))==673, "Unexpected snapshot; reconcile before cutover"
print("PASS approved read: 458 rows / 673 edges")
status,data=call("/nodes?select=id&limit=1",profile="poetics")
assert status in (401,403,406), ("Private schema was not denied",status)
print("PASS private schema denied:",status)
status,data=call("/rpc/submit_poetics_atlas_record",{"p_submission":{}})
assert status in (400,422), ("Invalid submission was not rejected",status)
print("PASS invalid submission rejected:",status)
if a.test_submission:
    test={"name":"MIGRATION-HTTP-TEST-20261017","category":"Platforms",
          "details":"Synthetic staging migration access test; not research evidence.",
          "location":"Staging test","source":"https://example.invalid/poetics-cutover-test",
          "contributor":"Migration access verification"}
    status,data=call("/rpc/submit_poetics_atlas_record",{"p_submission":test})
    assert status==200 and isinstance(data,str), ("Approved submission failed",status)
    print("PASS submission accepted; owner must verify pending_review. submission_id:",data)
    print("Do not classify this test as evidence. Record owner verification and test disposition.")
else:
    print("Valid HTTP write not tested; use --test-submission only for the labelled staging test.")
print("Record timestamp, statuses and output in the private audit. This script does not declare cutover.")
