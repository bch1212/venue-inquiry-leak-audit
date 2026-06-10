#!/usr/bin/env python3
import csv, json, os, subprocess, time, textwrap
from email.utils import formatdate, make_msgid

MAX_SEND=int(os.environ.get('MAX_SEND','10'))
DRY=os.environ.get('DRY_RUN','0')=='1'
FROM=os.environ.get('OUTREACH_FROM','Brett Halverson <brett@vikinetic.com>')
CSV='data/prospects_enriched.csv'
LOG='logs/outreach.jsonl'
SENT=set()
if os.path.exists(LOG):
    for line in open(LOG):
        try:
            o=json.loads(line); 
            if o.get('status')=='sent': SENT.add(o.get('email'))
        except Exception: pass

def subject(name): return f"quick private-events page audit for {name}"
def body(r):
    name=r['name']; angle=r.get('personalization_angle') or 'your private-events inquiry path'
    return f"""Hi {name} team,

I’m doing a small batch of same-day “inquiry leak” audits for Austin-area event venues.

The audit checks whether a planner can quickly find capacity/package cues, availability or tour CTA, a reliable contact path, and trust proof before they bounce to another venue.

For {name}, I’d focus especially on {angle}.

Offer: I’ll deliver a concise prioritized report within 24 hours for $149. If it doesn’t surface at least 3 concrete fixes, I’ll refund it. No ad spend or site access needed — public pages only.

If useful, reply “audit” with the best URL to review. If not relevant, reply “no” and I won’t follow up.

Best,
Brett
"""

def send(to, sub, msg):
    mime=f"From: {FROM}\nTo: {to}\nSubject: {sub}\nDate: {formatdate(localtime=True)}\nMessage-ID: {make_msgid()}\n\n{msg}"
    if DRY:
        return 0,'DRY_RUN',''
    p=subprocess.run(['himalaya','template','send'],input=mime,text=True,capture_output=True,timeout=90)
    return p.returncode,p.stdout,p.stderr

with open(CSV,newline='') as f: rows=list(csv.DictReader(f))
sent=0
with open(LOG,'a') as log:
    for r in rows:
        emails=[e for e in (r.get('verified_emails') or r.get('email') or '').split(';') if e]
        if not emails: continue
        to=emails[0].strip()
        if to in SENT: continue
        sub=subject(r['name']); msg=body(r)
        code,out,err=send(to,sub,msg)
        status='sent' if code==0 else 'error'
        rec={'ts':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'name':r['name'],'email':to,'subject':sub,'status':status,'returncode':code,'stdout':out[-500:],'stderr':err[-500:]}
        log.write(json.dumps(rec)+'\n'); log.flush(); print(rec)
        if status=='sent': sent+=1
        if sent>=MAX_SEND: break
print('sent_count',sent)
