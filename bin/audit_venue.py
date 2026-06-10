#!/usr/bin/env python3
"""Venue Inquiry Leak Audit: lightweight website checker for event venues.

Fetches a venue homepage and selected linked pages, then scores whether a high-intent
planner can quickly find pricing/capacity/contact/rental info and request a quote.
No paid APIs, no forms submitted.
"""
from __future__ import annotations
import argparse, json, re, ssl, sys, time
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

UA = "Mozilla/5.0 VenueInquiryLeakAudit/1.0 (+https://bch1212.github.io/venue-inquiry-leak-audit/)"
KEYWORDS = {
    "event_intent": ["wedding", "event", "private event", "corporate", "rental", "venue", "celebration", "reception"],
    "decision_info": ["capacity", "guest", "pricing", "package", "floor plan", "catering", "preferred vendor", "parking"],
    "cta": ["inquire", "request", "book", "contact", "tour", "availability", "quote", "proposal"],
    "trust": ["testimonial", "review", "gallery", "portfolio", "featured", "award", "instagram"],
}
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]; self.text=[]; self.mailtos=[]; self.forms=0; self.title=""
        self._title=False
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=='a' and d.get('href'):
            h=d['href']; self.links.append(h)
            if h.lower().startswith('mailto:'): self.mailtos.append(h[7:].split('?')[0])
        if tag=='form': self.forms += 1
        if tag=='title': self._title=True
    def handle_endtag(self, tag):
        if tag=='title': self._title=False
    def handle_data(self, data):
        s=data.strip()
        if s: self.text.append(s)
        if self._title: self.title += data.strip()

@dataclass
class PageFinding:
    url: str
    status: int | None
    bytes: int
    elapsed_ms: int
    title: str
    emails: list[str]
    phones: list[str]
    forms: int
    hits: dict[str,int]
    error: str | None = None

def fetch(url: str, timeout=12) -> tuple[int|None, bytes, int, str|None]:
    start=time.time()
    try:
        req=Request(url,headers={'User-Agent':UA})
        ctx=ssl.create_default_context()
        with urlopen(req,timeout=timeout,context=ctx) as r:
            return getattr(r,'status',200), r.read(900_000), int((time.time()-start)*1000), None
    except Exception as e:
        return None, b'', int((time.time()-start)*1000), str(e)

def parse_page(url: str) -> tuple[PageFinding, list[str]]:
    status, body, ms, err = fetch(url)
    if err:
        return PageFinding(url,status,0,ms,"",[],[],0,{k:0 for k in KEYWORDS},err), []
    text=body.decode('utf-8','ignore')
    p=LinkParser(); p.feed(text)
    visible=' '.join(p.text)
    low=visible.lower()
    hits={k:sum(low.count(w) for w in words) for k,words in KEYWORDS.items()}
    emails=sorted(set([e for e in EMAIL_RE.findall(text) if not e.lower().endswith(('.png','.jpg','.jpeg','.gif','.webp'))] + p.mailtos))
    phones=sorted(set(PHONE_RE.findall(visible)))[:8]
    internal=[]; host=urlparse(url).netloc.replace('www.','')
    for h in p.links:
        u=urljoin(url,h.split('#')[0])
        pu=urlparse(u)
        if pu.scheme in ('http','https') and pu.netloc.replace('www.','')==host:
            if any(x in pu.path.lower() for x in ['event','wedding','private','venue','contact','book','rental','corporate']):
                internal.append(u)
    return PageFinding(url,status,len(body),ms,p.title[:120],emails[:10],phones,p.forms,hits,None), list(dict.fromkeys(internal))[:6]

def score(findings: list[PageFinding]) -> tuple[int, list[str], list[str]]:
    alltext={k:sum(f.hits.get(k,0) for f in findings) for k in KEYWORDS}
    emails=sum(len(f.emails) for f in findings); phones=sum(len(f.phones) for f in findings); forms=sum(f.forms for f in findings)
    speed_bad=any(f.elapsed_ms>3000 for f in findings if f.status)
    score=100; leaks=[]; wins=[]
    if not (emails or phones or forms): score-=25; leaks.append('No obvious email/phone/form found in crawled pages')
    else: wins.append('Contact path found')
    if alltext['cta']<2: score-=18; leaks.append('Weak inquiry/book-a-tour call-to-action density')
    else: wins.append('Inquiry CTA language present')
    if alltext['decision_info']<4: score-=20; leaks.append('Capacity/pricing/package/parking details are thin or hard to find')
    else: wins.append('Planner decision details appear on-page')
    if alltext['event_intent']<5: score-=12; leaks.append('Private event / wedding intent keywords are sparse')
    if alltext['trust']<2: score-=10; leaks.append('Trust assets (gallery/reviews/testimonials/social proof) are under-signaled')
    if speed_bad: score-=8; leaks.append('One or more key pages loaded slower than 3 seconds from this check')
    if any(f.error for f in findings): score-=7; leaks.append('Some relevant pages failed to fetch, which can indicate discoverability or blocking issues')
    return max(0,score), leaks, wins

def audit(url: str):
    if not url.startswith(('http://','https://')): url='https://'+url
    first, links=parse_page(url)
    findings=[first]
    for link in links[:5]:
        pf,_=parse_page(link); findings.append(pf)
    s, leaks, wins=score(findings)
    recs=[]
    if any('CTA' in x or 'call-to-action' in x for x in leaks): recs.append('Add a sticky “Check date availability” or “Request event quote” CTA above the fold and after gallery sections.')
    if any('Capacity' in x or 'details' in x for x in leaks): recs.append('Publish a one-screen planner block: capacity ranges, starting rental fee/package cue, parking, catering rules, and tour link.')
    if any('Contact' in x or 'email/phone/form' in x for x in leaks): recs.append('Expose events@/sales@ email, phone, and form on every private-events page; avoid burying contact only in footer.')
    if not recs: recs.append('Turn current strengths into a faster quote funnel: add a 5-question inquiry form and auto-reply promise under 4 business hours.')
    return {"url":url,"score":s,"leaks":leaks,"wins":wins,"recommendations":recs,"findings":[asdict(f) for f in findings]}

def markdown(report: dict) -> str:
    out=[f"# Venue Inquiry Leak Audit — {report['url']}","",f"**Inquiry-readiness score:** {report['score']}/100",""]
    out.append('## Likely inquiry leaks')
    for x in report['leaks'] or ['No major leak detected by lightweight crawl.'] : out.append(f"- {x}")
    out.append('\n## Quick revenue fixes')
    for x in report['recommendations']: out.append(f"- {x}")
    out.append('\n## Evidence crawl')
    for f in report['findings']:
        out.append(f"- `{f['status']}` {f['url']} — {f['elapsed_ms']}ms, forms={f['forms']}, emails={len(f['emails'])}, phones={len(f['phones'])}, hits={f['hits']}")
    out.append('\n*Lightweight public-page audit only; no forms were submitted.*')
    return '\n'.join(out)+'\n'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('url'); ap.add_argument('--json',action='store_true'); ap.add_argument('-o','--output')
    a=ap.parse_args(); r=audit(a.url); data=json.dumps(r,indent=2)
    rendered=data if a.json else markdown(r)
    if a.output: open(a.output,'w').write(rendered)
    print(rendered)
if __name__=='__main__': main()
