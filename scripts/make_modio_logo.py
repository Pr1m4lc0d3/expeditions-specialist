#!/usr/bin/env python3
"""Compose a mod.io logo from a specialist's badge.

mod.io will not create a mod without a logo, and it shows the image small in
browse listings, so the card has to read at thumbnail size: big face, short
name, high contrast, nothing else.

    python make_modio_logo.py                       # every specialist in Media/Mods
    python make_modio_logo.py SpecialistDesc_Treadwell.pak

mod.io wants at least 512 x 288 and uses 16:9. This writes 1280 x 720.
"""
from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import specialist as sp  # noqa: E402

W, H = 1280, 720
BANNER = "pUrpLmUnk3y Presents"


def _font(size: int, bold: bool = False):
    for name in (("seguibl.ttf", "segoeuib.ttf", "arialbd.ttf") if bold
                 else ("segoeui.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def compose(badge: Image.Image, name: str, subtitle: str = "") -> Image.Image:
    badge = badge.convert("RGBA")
    # background: the badge itself, blown up and blurred, so the card picks up
    # the character's own colours instead of a flat swatch
    bg = badge.resize((W, W), Image.LANCZOS).crop((0, (W - H) // 2, W, (W - H) // 2 + H))
    bg = bg.convert("RGB").filter(ImageFilter.GaussianBlur(42))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (18, 18, 20)), 0.55)

    card = Image.new("RGB", (W, H))
    card.paste(bg, (0, 0))

    # subject on the right, bled off the bottom edge
    size = 660
    face = badge.resize((size, size), Image.LANCZOS)
    card.paste(face, (W - size - 40, H - size + 30), face)

    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, 470, H], fill=(14, 14, 16))
    for i in range(70):                      # soft edge into the portrait
        a = int(255 * (1 - i / 70))
        d.line([(470 + i, 0), (470 + i, H)], fill=(14, 14, 16, a))

    d.text((54, 250), BANNER, font=_font(30), fill=(176, 142, 232))
    # Fit the name to the panel instead of assuming it fits. At 66px "Bonnie
    # Sweete" and "Tuck Treadwell" both ran off the panel and over the face.
    avail = 470 - 54 - 24
    lines = _wrap(name, 16)
    size = 66
    while size > 34:
        f = _font(size, bold=True)
        if max(d.textlength(l, font=f) for l in lines) <= avail:
            break
        size -= 2
    f = _font(size, bold=True)
    y = 296
    for line in lines:
        d.text((54, y), line, font=f, fill=(245, 245, 248))
        y += int(size * 1.15)
    if subtitle:
        d.text((54, y + 14), subtitle, font=_font(32), fill=(150, 150, 158))
    return card


def _wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines[:3]


CLASSES = {0: "Mechanic", 1: "Logistics Specialist", 2: "Hydrologist",
           3: "Jaeger", 4: "Operator", 5: "Manager"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pak", nargs="*")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    out = Path(args.out) if args.out else Path(__file__).parent.parent / "dist" / "logos"
    out.mkdir(parents=True, exist_ok=True)
    paks = [Path(p) for p in args.pak] or [
        p for p in sorted(sp.mods_dir().glob("SpecialistDesc_*.pak")) if p.stat().st_size]

    for pak in paks:
        v = sp.read_descriptor(pak)["SslValue"]
        with zipfile.ZipFile(pak) as z:
            hit = [n for n in z.namelist()
                   if n.lower().endswith(f"/{str(v['bage']).lower()}.png")]
            if not hit:
                print(f"  {pak.name}: no badge texture, skipped"); continue
            badge = Image.open(io.BytesIO(z.read(hit[0])))
        card = compose(badge, v["uiName"], CLASSES.get(v.get("speciality"), ""))
        dest = out / (pak.stem + ".png")
        card.save(dest, optimize=True)
        print(f"  {v['uiName']:18s} -> {dest.name}  {dest.stat().st_size // 1024} KB")
    print(f"\nwritten to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
