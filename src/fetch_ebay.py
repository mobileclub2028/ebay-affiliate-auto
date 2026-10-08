"""eBay Browse API fetcher with mock fallback.
Real API: POST https://api.ebay.com/identity/v1/oauth2/token -> GET /buy/browse/v1/item_summary/search
No keys -> returns mock data so site build never breaks.
"""
import base64
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load(open(ROOT / "config.yaml", encoding="utf-8"))
OUT = ROOT / "data" / "deals.json"


def get_oauth_token(app_id: str, cert_id: str) -> str | None:
    try:
        creds = base64.b64encode(f"{app_id}:{cert_id}".encode()).decode()
        r = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {creds}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["access_token"]
    except Exception as e:
        print(f"[warn] oauth failed: {e}", file=sys.stderr)
        return None


def search_live(token: str, query: str, limit: int, min_price: float, max_price: float) -> list[dict]:
    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    params = {
        "q": query,
        "filter": f"price:[{min_price}..{max_price}],priceCurrency:USD,buyingOptions:{{FIXED_PRICE}}",
        "limit": str(limit),
        "sort": "price",
    }
    r = requests.get(
        url,
        params=params,
        headers={"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
        timeout=20,
    )
    r.raise_for_status()
    items = r.json().get("itemSummaries", [])
    junk = ("motherboard", "mainboard", "led board", "cable", "parts only", "for parts",
            "case", "cover", "keyboard", "charger only", "battery only", "screen protector")
    out = []
    for it in items:
        price = (it.get("price") or {})
        title = it.get("title", "")[:120]
        try:
            pval = float(price.get("value", 0) or 0)
        except (TypeError, ValueError):
            continue
        if pval < min_price:
            continue
        if any(j in title.lower() for j in junk):
            continue
        out.append({
            "item_id": it.get("itemId", "").replace("v1|", "").split("|")[0],
            "title": title,
            "price": pval,
            "currency": price.get("currency", "USD"),
            "url": it.get("itemWebUrl", ""),
            "image": (it.get("image") or {}).get("imageUrl", ""),
            "condition": it.get("condition", ""),
            "seller_feedback": (it.get("seller") or {}).get("feedbackPercentage", ""),
        })
    return out


def mock_items(query: str, limit: int) -> list[dict]:
    base = abs(hash(query)) % 200 + 250
    items = []
    for i in range(limit):
        price = round(base - i * 12.5 + (hash(query + str(i)) % 40), 2)
        fake_id = f"{abs(hash(query + str(i))) % 10**12:012d}"
        items.append({
            "item_id": fake_id,
            "title": f"{query.title()} — 16GB/512GB Good Cond. Unit #{i+1} (Demo Data)",
            "price": price,
            "currency": "USD",
            "url": f"https://www.ebay.com/itm/{fake_id}",
            "image": "",
            "condition": "Used",
            "seller_feedback": "98.5",
        })
    return items


def epn_link(item_url: str, campid: str, cfg: dict, customid: str, item_id: str = "") -> str:
    # rover 경유는 JS 리다이렉트라 광고차단에서 빈 화면이 됨.
    # 숫자 item_id가 있으면 ebay.com 직링크 + 추적파라미터로 바로 이동.
    if item_id and item_id.isdigit():
        return (
            f"https://www.ebay.com/itm/{item_id}?mkcid=1&mkrid={cfg['epn']['mkrid']}"
            f"&siteid={cfg['epn']['siteid']}&campid={campid}&toolid={cfg['epn']['toolid']}"
            f"&customid={quote_plus(customid)}&mkevt=1"
        )
    base = "https://rover.ebay.com/rover/1/711-53200-19255-0/1"
    return (
        f"{base}?campid={campid}&toolid={cfg['epn']['toolid']}"
        f"&customid={quote_plus(customid)}&mpre={quote_plus(item_url)}"
    )


def main():
    app_id = os.getenv(CONFIG["ebay"]["app_id_env"], "")
    cert_id = os.getenv(CONFIG["ebay"]["cert_id_env"], "")
    campid = os.getenv("EPN_CAMPID", CONFIG["epn"]["campid"])

    token = get_oauth_token(app_id, cert_id) if app_id and cert_id else None
    mode = "live" if token else "mock"
    print(f"[fetch] mode={mode}")

    result: dict = {"mode": mode, "niches": {}}
    for n in CONFIG["niches"]:
        slug, query = n["slug"], n["query"]
        limit = CONFIG["filters"]["limit_per_niche"]
        try:
            items = search_live(token, query, limit, n.get("min_price", 0), n["max_price"]) if token else mock_items(query, limit)
        except Exception as e:
            print(f"[warn] {slug} search failed, mock fallback: {e}", file=sys.stderr)
            items = mock_items(query, limit)

        # HOT DEAL 판정: 중앙값 대비 threshold 이상 저렴
        prices = sorted([x["price"] for x in items if x["price"] > 0])
        median = prices[len(prices) // 2] if prices else 0
        th = CONFIG["filters"]["discount_threshold_pct"]
        for x in items:
            x["median_ref"] = median
            x["discount_pct"] = round((1 - x["price"] / median) * 100, 1) if median else 0
            x["hot"] = x["discount_pct"] >= th
            x["aff_url"] = epn_link(x["url"], campid, CONFIG, f"{CONFIG['epn']['customid_prefix']}-{slug}", x.get("item_id", ""))

        items.sort(key=lambda x: x["price"])
        result["niches"][slug] = {"meta": n, "median": median, "items": items, "count": len(items)}
        print(f"[fetch] {slug}: {len(items)} items, median=${median}")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[fetch] wrote {OUT}")


if __name__ == "__main__":
    main()
