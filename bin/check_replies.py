#!/usr/bin/env python3
import json, os, subprocess, time
VENTURE='/Users/bretthalverson/Projects/revenue-lab/ventures/venue-inquiry-leak-audit'
LOG=os.path.join(VENTURE,'logs/outreach.jsonl')
STATE=os.path.expanduser('~/.hermes/state/venue-inquiry-leak-audit-watch.json')
keywords=['Venue audit','private-events page audit','inquiry leak','reply “audit”','reply "audit"']
contacts=[]
if os.path.exists(LOG):
    for line in open(LOG):
        try:
            o=json.loads(line)
            if o.get('status')=='sent': contacts.append(o.get('email','').lower())
        except Exception: pass
seen={}
if os.path.exists(STATE):
    try: seen=json.load(open(STATE))
    except Exception: seen={}
cmd=['himalaya','envelope','list','--page-size','50','--output','json']
p=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
alerts=[]
if p.returncode==0:
    try: msgs=json.loads(p.stdout)
    except Exception: msgs=[]
    for m in msgs:
        mid=str(m.get('id') or m.get('hash') or m.get('message-id') or m)
        frm=str(m.get('from','')).lower(); sub=str(m.get('subject',''))
        hit_contact=any(c and c in frm for c in contacts)
        hit_kw=any(k.lower() in sub.lower() for k in keywords)
        if (hit_contact or hit_kw) and not seen.get(mid):
            alerts.append({'id':mid,'from':m.get('from'),'subject':sub,'date':m.get('date')})
            seen[mid]=time.time()
os.makedirs(os.path.dirname(STATE),exist_ok=True)
json.dump(seen,open(STATE,'w'),indent=2)
if alerts:
    print('VENUE_INQUIRY_AUDIT_REPLIES '+json.dumps(alerts,indent=2))
else:
    print('no new venue audit replies')
