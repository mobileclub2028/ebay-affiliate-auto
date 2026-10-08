"""deals.json -> 정적 HTML 사이트 빌드 (SEO + EPN 링크 + 광고표기)."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "deals.json"
DIST = ROOT / "docs"  # GitHub Pages용

CARD = """
<article class="card">
  <div class="badge">{badge}</div>
  <h3><a href="{aff}" target="_blank" rel="nofollow sponsored noopener">{title}</a></h3>
  <p class="price">${price} <span class="off">{off}</span></p>
  <p class="meta">{cond} · Seller {fb}% · Median ${median}</p>
  <a class="btn" href="{aff}" target="_blank" rel="nofollow sponsored noopener">Check Live Price on eBay</a>
</article>
"""

PAGE_TPL = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — RefurbPrice US</title>
<meta name="description" content="{desc}">
<style>body{{font-family:system-ui,Arial;max-width:900px;margin:0 auto;padding:24px;line-height:1.6}}
.card{{border:1px solid #ddd;border-radius:12px;padding:16px;margin:14px 0}}
.price{{font-size:22px;font-weight:700}}.off{{color:#b00;font-size:14px}}
.btn{{display:inline-block;background:#0064d2;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none}}
.badge{{font-size:12px;color:#fff;background:#e53238;display:inline-block;padding:2px 8px;border-radius:99px}}
.disc{{background:#fff8e1;padding:12px;border-radius:8px;font-size:13px}}</style>
</head><body>
<p><a href="index.html">← All trackers</a></p>
<h1>{title}</h1>
<p class="disc">Disclosure: This page contains eBay affiliate links. If you buy, we may earn a commission at no extra cost to you.</p>
<p>Updated <time>{updated}</time> · Median ${median} · {count} live listings · Prices change fast on eBay.</p>
<h2>Buying tips (save money)</h2>
<ol><li>Filter 95%+ feedback sellers only.</li><li>Compare battery cycle / SSD health photos.</li>
<li>Auction ending in &lt;2h is often 10-20% cheaper — check HOT DEALs first.</li></ol>
{cards}
<script type="application/ld+json">{jsonld}</script>
</body></html>"""

INDEX_TPL = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RefurbPrice US — Live Used Tech Price Trackers</title>
<meta name="description" content="Live eBay price trackers for used ThinkPad, iPhone, Dell XPS. Updated daily.">
<style>body{{font-family:system-ui,Arial;max-width:900px;margin:0 auto;padding:24px;line-height:1.6}}
.card{{border:1px solid #ddd;border-radius:12px;padding:16px;margin:14px 0}}
.btn{{display:inline-block;background:#0064d2;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none}}</style>
</head><body>
<h1>RefurbPrice US</h1>
<p>Daily-updated eBay price trackers. Disclosure: affiliate links included.</p>
{cards}
<footer><p>© RefurbPrice US · Prices in USD · Data: eBay Browse API</p></footer>
</body></html>"""


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    DIST.mkdir(exist_ok=True)
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    idx_cards = []
    for slug, n in data["niches"].items():
        meta, items, median = n["meta"], n["items"], n["median"]
        cards = []
        for x in items[:12]:
            badge = "🔥 HOT DEAL" if x["hot"] else ("MOCK" if data["mode"] == "mock" else "LIVE")
            cards.append(CARD.format(
                badge=badge, title=x["title"], aff=x["aff_url"],
                price=x["price"], off=f"-{x['discount_pct']}%" if x["hot"] else "",
                cond=x["condition"], fb=x["seller_feedback"], median=median,
            ))
        jsonld = json.dumps({"@context": "https://schema.org", "@type": "ItemList",
                             "name": meta["title"], "numberOfItems": len(items)})
        (DIST / f"{slug}.html").write_text(PAGE_TPL.format(
            title=meta["title"], desc=f"{meta['query']} live eBay prices, median ${median}. Updated {updated}.",
            updated=updated, median=median, count=len(items),
            cards="\n".join(cards), jsonld=jsonld), encoding="utf-8")
        idx_cards.append(f'<div class="card"><h2><a href="{slug}.html">{meta["title"]}</a></h2>'
                         f'<p>Median ${median} · {len(items)} listings</p>'
                         f'<a class="btn" href="{slug}.html">View Tracker</a></div>')
        print(f"[build] {slug}.html")
    (DIST / "index.html").write_text(INDEX_TPL.format(cards="\n".join(idx_cards)), encoding="utf-8")
    print(f"[build] index.html -> {DIST}")


if __name__ == "__main__":
    main()
