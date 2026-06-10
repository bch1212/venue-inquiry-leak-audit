#!/usr/bin/env python3
import csv, json, re, ssl, time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

EMAIL_RE=re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",re.I)
UA='Mozilla/5.0 VenueInquiryProspectResearch/1.0'
BAD=('example.com','sentry.io','wixpress.com','squarespace.com','schema.org','domain.com')
class P(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.mailtos=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='a' and d.get('href'):
            h=d['href']; self.links.append(h)
            if h.lower().startswith('mailto:'): self.mailtos.append(h[7:].split('?')[0])

def fetch(url):
    try:
        with urlopen(Request(url,headers={'User-Agent':UA}),timeout=12,context=ssl.create_default_context()) as r:
            return r.read(600000).decode('utf-8','ignore')
    except Exception:
        return ''

def good(e):
    el=e.lower().strip('.,;:')
    return '@' in el and not any(b in el for b in BAD) and not el.endswith(('.png','.jpg','.jpeg','.webp','.gif','.js','.css'))

def crawl(row):
    root=row['url']; root = root if root.startswith('http') else 'https://'+root
    html=fetch(root); p=P(); p.feed(html)
    host=urlparse(root).netloc.replace('www.','')
    urls=[root]
    for h in p.links:
        u=urljoin(root,h.split('#')[0]); pu=urlparse(u)
        if pu.scheme in ('http','https') and pu.netloc.replace('www.','')==host and any(x in pu.path.lower() for x in ['contact','event','wedding','venue','private','inquir','book']):
            urls.append(u)
    emails=set([x for x in p.mailtos if good(x)] + [x for x in EMAIL_RE.findall(html) if good(x)])
    for u in list(dict.fromkeys(urls))[1:6]:
        h=fetch(u); pp=P(); pp.feed(h)
        emails.update(x for x in pp.mailtos if good(x)); emails.update(x for x in EMAIL_RE.findall(h) if good(x))
        time.sleep(.2)
    return sorted(emails), list(dict.fromkeys(urls))[:6]

inp='data/prospects.csv'; out='data/prospects_enriched.csv'; log='logs/prospect_research.jsonl'
with open(inp,newline='') as f: rows=list(csv.DictReader(f))
fields=list(rows[0].keys())+['verified_emails','crawled_urls']
with open(out,'w',newline='') as fo, open(log,'a') as lo:
    w=csv.DictWriter(fo,fieldnames=fields); w.writeheader()
    for r in rows:
        emails,urls=crawl(r); r['verified_emails']=';'.join(emails); r['crawled_urls']=';'.join(urls); w.writerow(r)
        lo.write(json.dumps({'ts':time.time(),'name':r['name'],'url':r['url'],'emails':emails,'crawled_urls':urls})+'\n')
        print(r['name'], emails[:3])
