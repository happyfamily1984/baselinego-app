"""Build Android launcher icons from a site's icon (apple-touch-icon / manifest / favicon); fall back to a letter icon.

Usage: python3 make_icon.py <site_url> <android_res_dir> <fallback_letter>
"""
import io, json, re, sys, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

UA = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Mobile Safari/537.36"
SIZES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
        return r.read(), r.geturl()


def candidates(site):
    html, final = get(site)
    html = html.decode("utf-8", "replace")
    out = []
    for rel in ("apple-touch-icon", "icon", "shortcut icon"):
        for m in re.finditer(r"<link[^>]+>", html, re.I):
            tag = m.group(0)
            if re.search(rf'rel=["\'][^"\']*{rel}', tag, re.I):
                href = re.search(r'href=["\']([^"\']+)', tag)
                if href:
                    out.append(urllib.parse.urljoin(final, href.group(1)))
    man = re.search(r'<link[^>]+rel=["\']manifest["\'][^>]*href=["\']([^"\']+)', html, re.I) or \
        re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']manifest', html, re.I)
    if man:
        try:
            murl = urllib.parse.urljoin(final, man.group(1))
            icons = json.loads(get(murl)[0]).get("icons", [])
            icons.sort(key=lambda i: -int((i.get("sizes", "0x0").split("x")[0] or 0) if "x" in i.get("sizes", "") else 0))
            out = [urllib.parse.urljoin(murl, i["src"]) for i in icons] + out
        except Exception as e:
            print("manifest error", e)
    out.append(urllib.parse.urljoin(final, "/apple-touch-icon.png"))
    out.append(urllib.parse.urljoin(final, "/favicon.ico"))
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    print("site title:", title.group(1).strip() if title else "-")
    return out


def letter_icon(letter):
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((16, 16, 496, 496), fill=(30, 64, 175, 255))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 300)
    except OSError:
        font = ImageFont.load_default()
    box = d.textbbox((0, 0), letter, font=font)
    d.text(((512 - (box[2] - box[0])) / 2 - box[0], (512 - (box[3] - box[1])) / 2 - box[1]), letter, fill="white", font=font)
    return img


def main(site, res_dir, letter):
    best = None
    try:
        for url in candidates(site):
            try:
                data, _ = get(url)
                img = Image.open(io.BytesIO(data))
                if getattr(img, "n_frames", 1) > 1 or url.endswith(".ico"):
                    img = max((img.copy() for _ in [0]), key=lambda i: i.size[0])
                img = img.convert("RGBA")
                print("icon candidate", url, img.size)
                if best is None or img.size[0] > best.size[0]:
                    best = img
                if best.size[0] >= 180:
                    break
            except Exception as e:
                print("skip", url, e)
    except Exception as e:
        print("site fetch failed:", e)
    if best is None or best.size[0] < 48:
        print("using letter icon")
        best = letter_icon(letter)
    # pad onto white rounded square so transparent/small logos look fine
    side = max(best.size)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 255))
    canvas.paste(best, ((side - best.size[0]) // 2, (side - best.size[1]) // 2), best)
    for name, px in SIZES.items():
        d = Path(res_dir) / f"mipmap-{name}"
        d.mkdir(parents=True, exist_ok=True)
        canvas.resize((px, px), Image.LANCZOS).save(d / "ic_launcher.png")
    print("icons written")


if __name__ == "__main__":
    main(*sys.argv[1:4])
