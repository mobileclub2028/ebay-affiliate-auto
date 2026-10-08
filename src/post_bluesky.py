"""Bluesky US deal auto-post (free API, no approval).
Secrets: BSKY_HANDLE, BSKY_APP_PASSWORD (Settings > App passwords).
Post: top HOT DEAL per niche + site link. 1 post/day to avoid spam flags.
"""
import json
import os
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "deals.json"
CONFIG = yaml.safe_load(open(ROOT / "config.yaml", encoding="utf-8"))
ATP = "https://bsky.social/xrpc"


def main():
    handle = os.getenv("BSKY_HANDLE", "")
    app_pw = os.getenv("BSKY_APP_PASSWORD", "")
    if not handle or not app_pw:
        print("[bsky] skip: no BSKY_HANDLE/BSKY_APP_PASSWORD")
        return
    s = requests.post(f"{ATP}/com.atproto.server.createSession",
                      json={"identifier": handle, "password": app_pw}, timeout=20)
    s.raise_for_status()
    tok, did = s.json()["accessToken"], s.json()["did"]

    data = json.loads(DATA.read_text(encoding="utf-8"))
    picks = []
    for slug, n in data["niches"].items():
        hot = [x for x in n["items"] if x.get("hot")] or n["items"][:1]
        if hot:
            x = hot[0]
            picks.append((slug, x))
    picks = picks[:4]  # 1 post에 최대 4줄
    base = CONFIG.get("site_url", "").rstrip("/")
    lines = ["Refurb iPhone live medians (eBay US, affiliate links):"]
    for slug, x in picks:
        short = x["title"][:52]
        lines.append(f"- {short} ${x['price']} {base}/{slug}.html")
    lines.append("#iphone #refurbished #edeals")
    text = "\n".join(lines)[:290]  # 300자 제한 여유

    r = requests.post(
        f"{ATP}/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {tok}"},
        json={"repo": did, "collection": "app.bsky.feed.post",
              "record": {"text": text, "langs": ["en"],
                         "createdAt": __import__("datetime").datetime.now(
                             __import__("datetime").timezone.utc).isoformat()}},
        timeout=20,
    )
    print("[bsky]", r.status_code, r.text[:300])


if __name__ == "__main__":
    main()
