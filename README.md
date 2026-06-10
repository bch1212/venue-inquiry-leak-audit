# Venue Inquiry Leak Audit

A same-day, fixed-price audit for independent event venues that are leaking high-intent wedding/corporate/private-event inquiries because planners cannot quickly find capacity, pricing cues, availability CTA, or a reliable contact path.

## Offer

- **Buyer:** owner/operator, events manager, or marketing manager at independent event venues, restaurants with private rooms, breweries, galleries, and boutique hotels.
- **Trigger:** inquiries slow down, venue launches/relaunches a private-events page, or peak wedding/corporate booking season is approaching.
- **Value proposition:** “I’ll find and prioritize the 5 website fixes most likely to turn more venue shoppers into qualified tour/quote inquiries within 24 hours.”
- **Format:** concierge audit + public-page crawl evidence + prioritized copy/CTA fixes.
- **Price anchor:** $149 for one venue site; $399 for a 3-location/group audit; optional $499 implementation copy pack.
- **Guarantee/refund boundary:** if the delivered audit does not identify at least 3 concrete inquiry-friction fixes, refund the audit fee. No guarantee of bookings or revenue.
- **MVP scope:** audit public pages only, produce a PDF/Markdown report, and provide revised CTA/contact/planner-info copy blocks.
- **Non-goals:** no ad spend, no SEO backlink campaign, no form submissions, no compliance/legal claims, no website deployment unless sold as follow-up.
- **Fastest first-dollar path:** send a personalized cold email with one observed leak and ask the venue to reply “audit” for a $149 same-day report; invoice/payment link after interest.

## Files

- `bin/audit_venue.py` — no-dependency Python crawler/scorer.
- `samples/sample-input.csv` — sample venues/URLs.
- `reports/sample-report.md` — generated sample audit.
- `sales/offer.md` — landing page + email copy.
- `data/prospects.csv` — ranked public prospect list.
- `logs/outreach.jsonl` — append-only outreach log.
- `public/index.html` — static landing page for GitHub Pages.

## Verify locally

```bash
cd /Users/bretthalverson/Projects/revenue-lab/ventures/venue-inquiry-leak-audit
python3 bin/audit_venue.py https://www.peachedsocialhouse.com -o reports/sample-report.md
python3 -m py_compile bin/audit_venue.py
python3 -m http.server 8123 --directory public
```

The audit never submits forms; it only fetches public pages and reports evidence.
