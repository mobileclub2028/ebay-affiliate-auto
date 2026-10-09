"""Daily vertical Shorts generator (1080x1920, ~20s).
Input: data/deals.json. Output: shorts/YYYY-MM-DD.mp4 + caption.txt
Render: Pillow PNG + edge-tts narration + ffmpeg mux. No API keys.
"""
import asyncio
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "deals.json"
CONFIG = yaml.safe_load(open(ROOT / "config.yaml", encoding="utf-8"))
OUTDIR = ROOT / "shorts"

W, H = 1080, 1920
NAVY = (10, 25, 60)
ORANGE = (255, 110, 20)
WHITE = (255, 255, 255)
GRAY = (170, 180, 195)


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def font(size: int):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf"]:
        if Path(p).exists():
            from PIL import ImageFont as F
            return F.truetype(p, size)
    from PIL import ImageFont as F
    return F.load_default()


def pick_deals(data: dict) -> list[dict]:
    pool = []
    for slug, n in data["niches"].items():
        for x in n["items"][:6]:
            pool.append((slug, x))
    pool.sort(key=lambda t: t[1].get("discount_pct", 0), reverse=True)
    seen, out = set(), []
    for slug, x in pool:
        if slug in seen:
            continue
        seen.add(slug)
        out.append((slug, x))
        if len(out) == 3:
            break
    return out


def render_png(picks: list, path: Path):
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 300], fill=ORANGE)
    d.text((60, 60), "REFURB IPHONE", font=font(64), fill=WHITE)
    d.text((60, 150), "eBay US live deals  •  today", font=font(44), fill=WHITE)
    y = 420
    for i, (slug, x) in enumerate(picks, 1):
        model = slug.replace("-unlocked", "").replace("-", " ").upper()
        title = x["title"][:48]
        d.rounded_rectangle([60, y, W - 60, y + 400], radius=32, fill=(20, 45, 90),
                            outline=ORANGE, width=4)
        d.text((100, y + 30), f"#{i} {model}", font=font(52), fill=ORANGE)
        d.text((100, y + 110), f"${x['price']}", font=font(110), fill=WHITE)
        d.text((100, y + 250), title, font=font(36), fill=GRAY)
        y += 450
    d.text((60, H - 220), "Full trackers — link in bio", font=font(44), fill=WHITE)
    d.text((60, H - 150), "Affiliate links. Prices change fast.", font=font(34), fill=GRAY)
    img.save(path)


async def narrate(script: str, mp3: Path):
    import edge_tts
    tts = edge_tts.Communicate(script, voice="en-US-AvaNeural")
    await tts.save(str(mp3))


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    picks = pick_deals(data)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    OUTDIR.mkdir(exist_ok=True)
    png = OUTDIR / f"{day}.png"
    mp3 = OUTDIR / f"{day}.mp3"
    mp4 = OUTDIR / f"{day}.mp4"
    cap = OUTDIR / f"{day}.txt"

    render_png(picks, png)
    lines = ["Today's refurbished iPhone deals on eBay US."]
    for slug, x in picks:
        model = slug.replace("-unlocked", "").replace("-", " ")
        lines.append(f"{model} at {int(x['price'])} dollars.")
    lines.append("Full price trackers are linked in bio. Prices change fast.")
    script = " ".join(lines)
    asyncio.run(narrate(script, mp3))

    subprocess.run([ffmpeg_exe(), "-y", "-loop", "1", "-i", str(png), "-i", str(mp3),
                    "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac",
                    "-b:a", "128k", "-pix_fmt", "yuv420p", "-shortest", str(mp4)],
                   check=True, capture_output=True)
    base = CONFIG.get("site_url", "").rstrip("/")
    tags = "#iphone #refurbished #edeals #techtok"
    cap.write_text(
        f"Refurb iPhone deals (eBay US, {day}) — full trackers: {base}/ "
        f"Affiliate links. Prices change fast. {tags}", encoding="utf-8")
    print(f"[shorts] {mp4} + caption")


if __name__ == "__main__":
    main()
