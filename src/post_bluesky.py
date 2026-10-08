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
    sess = s.json()
    tok = sess.get("accessJwt") or sess.get("accessToken")
    did = sess["did"]
    if not tok:
        raise RuntimeError(f"no access token in session: {str(sess)[:200]}")

    data = json.loads(DATA.read_text(encoding="utf-8"))
    med = {}
    for slug, n in data["niches"].items():
        items = n["items"]
        med[slug] = n["median"]
    base = CONFIG.get("site_url", "").rstrip("/")
    g = lambda s: med.get(s, "")

    text = (
        f"Refurb iPhone medians (eBay US, live):\n"
        f"12 ${g('iphone-12-unlocked')} · mini ${g('iphone-12-mini-unlocked')}\n"
        f"13 ${g('iphone-13-refurbished')} · mini ${g('iphone-13-mini-unlocked')}\n"
        f"14 ${g('iphone-14-unlocked')} · 15 ${g('iphone-15-unlocked')}\n"
        f"16 ${g('iphone-16-unlocked')} · 17 ${g('iphone-17-unlocked')}\n"
        f"{base}/ #iphone #refurbished"
    )[:290]

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
