"""Send today's shorts mp4 + caption to Telegram (for 1-tap Shorts/TikTok upload)."""
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
SHORTS = ROOT / "shorts"


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        print("[shorts-tg] skip: no TELEGRAM secrets")
        return
    mps = sorted(SHORTS.glob("*.mp4"))
    if not mps:
        print("[shorts-tg] skip: no mp4")
        return
    f = mps[-1]
    cap = f.with_suffix(".txt").read_text(encoding="utf-8") if f.with_suffix(".txt").exists() else f.name
    with open(f, "rb") as v:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendVideo",
                          data={"chat_id": chat, "caption": cap[:900]},
                          files={"video": v}, timeout=120)
    print("[shorts-tg]", r.status_code, r.text[:200])


if __name__ == "__main__":
    main()
