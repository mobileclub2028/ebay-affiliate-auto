"""상위 HOT DEAL을 Telegram 채널로 전송."""
import json
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "deals.json"


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        print("[telegram] skip: no TELEGRAM_BOT_TOKEN/CHAT_ID")
        return
    data = json.loads(DATA.read_text(encoding="utf-8"))
    lines = []
    for slug, n in data["niches"].items():
        hot = [x for x in n["items"] if x["hot"]][:3] or n["items"][:2]
        for x in hot:
            fire = "🔥" if x["hot"] else "💰"
            lines.append(f"{fire} <b>${x['price']}</b> {x['title']}\n"
                         f"<a href=\"{x['aff_url']}\">Check on eBay</a> (-{x['discount_pct']}%)")
    text = "📊 <b>Daily Refurb Deals (eBay US)</b>\n\n" + "\n\n".join(lines[:9])
    text += "\n\n<i>Disclosure: affiliate links. Prices change quickly.</i>"
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text, "parse_mode": "HTML",
                            "disable_web_page_preview": False}, timeout=20)
    print("[telegram]", r.status_code, r.text[:200])


if __name__ == "__main__":
    main()
