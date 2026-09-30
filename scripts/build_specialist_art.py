#!/usr/bin/env python3
"""Build the three card textures for Tuck Treadwell and Meg A. Watts.

The strip window is anchored to the HEAD, not to the silhouette and not to a
fraction of the canvas. Two earlier attempts got this wrong in opposite ways:

  - a fraction of the badge (y0=0.2833, template-matched off his own 2025 pair)
    cut the hat off on a more zoomed-in portrait;
  - the widest row of the alpha mask grabs the SHOULDERS, which on both of these
    characters are far wider than the head, and zooms out to a speck.

So the head box is found with a face cascade and grown to include hat and hair,
and the window is sized so the head's own width fills HEAD_FILL of the strip's
content box.
"""
from __future__ import annotations

import os
import sys

import cv2
import numpy as np
from PIL import Image

OUT = r"F:\Expeditions\Toolkit\specialists\build"

BAGE = (364, 364)
BG = (380, 92)
BGSMALL = (124, 52)
BG_CONTENT = (23, 0, 115, 92)       # x, y, w, h inside the 380x92 canvas
SMALL_CONTENT = (27, 0, 67, 52)     # x, y, w, h inside the 124x52 canvas

HEAD_FILL = 0.80                    # head HEIGHT as a fraction of the strip content height
BADGE_SIDE = 0.955                  # subject width as a fraction of the badge
BADGE_TOP = 0.045                   # backdrop kept above the crown, fraction of the badge

DEFAULT_SUBJECTS: list[tuple[str, str]] = []


def subjects() -> list[tuple[str, str]]:
    """`slug=path` pairs on the command line, or the pair this was written for."""
    args = sys.argv[1:]
    if not args:
        return DEFAULT_SUBJECTS
    return [tuple(a.split("=", 1)) for a in args]


def load_rgba(path: str) -> np.ndarray:
    """Portrait as float RGBA, cut out if it arrived opaque.

    A pre-cut source is preferred: cutting off a dark backdrop drags the backdrop
    colour into partial-alpha hair pixels and leaves the wisps muddy.
    """
    im = Image.open(path).convert("RGBA")
    a = np.array(im).astype(np.float32)
    if (a[..., 3] > 250).mean() > 0.97:
        from rembg import remove, new_session
        cut = remove(im, session=new_session("isnet-general-use"),
                     alpha_matting=True, alpha_matting_foreground_threshold=240,
                     alpha_matting_background_threshold=15, alpha_matting_erode_size=8)
        a = np.array(cut.convert("RGBA")).astype(np.float32)
        print("    cut with isnet-general-use")
    body = np.percentile(a[..., 3][a[..., 3] > 200], 50)
    a[..., 3] = np.clip(a[..., 3] * (255.0 / body), 0, 255)
    return a


def head_box(a: np.ndarray) -> tuple[int, int, int, int]:
    """x0, y0, x1, y1 of the head including hat and hair.

    The cascade finds the FACE. A face box is not a head box: it excludes the hat
    above and the hair at the sides, which is the whole point here. So it is
    grown outward and then clipped back to the actual alpha silhouette, which
    keeps it honest against the real artwork.
    """
    rgb = (a[..., :3] * (a[..., 3:4] / 255.0)).astype(np.uint8)
    grey = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    cascade = cv2.CascadeClassifier(
        os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    faces = cascade.detectMultiScale(grey, 1.1, 5, minSize=(120, 120))
    if len(faces) == 0:
        raise RuntimeError("no face found; refusing to guess a head box")
    # 🚨 Take the largest face in the UPPER frame, not the largest overall. On a
    # broad character carrying gear the cascade also fires on the torso, and that
    # false positive is bigger than the real face: Hank Snatchblock's "face" was
    # reported at y558 when his chin sits near y690, giving a 1036px head.
    upper = [f for f in faces if (f[1] + f[3] / 2) < a.shape[0] * 0.55]
    x, y, w, h = max(upper or list(faces), key=lambda f: f[2] * f[3])
    cx = x + w / 2
    mask = a[..., 3] > 16
    ys = np.where(mask.any(axis=1))[0]
    top = int(max(ys.min(), y - h * 0.95))     # crown sits well above the brow
    bot = int(min(a.shape[0], y + h * 1.20))   # chin and jaw
    # 🚨 Measure the head's WIDTH across the crown-to-brow band only. Measuring
    # down to the chin puts the shoulders inside the row range, and on a
    # broad-shouldered character carrying gear the silhouette there is the BODY:
    # Hank Snatchblock came out 1114px wide of a 1254px frame, which zoomed his
    # strips out to a full torso with a thumbnail-sized face.
    brow = int(min(a.shape[0], y + h * 0.35))
    cols = np.where(mask[top:brow].any(axis=0))[0]
    if len(cols):
        x0, x1 = int(cols.min()), int(cols.max())
    else:                                      # bare-headed, no hat to measure
        x0, x1 = int(cx - w * 0.85), int(cx + w * 0.85)
    # never narrower than the face itself, never wider than a head can be
    x0 = min(x0, int(x)); x1 = max(x1, int(x + w))
    # 1.9x the face width covers any headgear; 3x reaches the shoulders, and
    # on Hank Snatchblock that let the crown lookup find his shoulder and
    # report a 1036px head.
    x0 = max(x0, int(cx - w * 0.95)); x1 = min(x1, int(cx + w * 0.95))
    # 🚨 Take the crown from the SILHOUETTE inside the head's columns, not from
    # the cascade. `y - h*0.95` is a guess about how far the headgear rises, and
    # it clipped Hank Snatchblock's hard hat and Dodge Sparrowhawk's goggles.
    # The topmost opaque row in those columns is the real top of the head.
    rows = np.where(mask[:, x0:x1].any(axis=1))[0]
    if len(rows):
        top = int(rows.min())
    return x0, top, x1, bot


def premult_resize(a: np.ndarray, size: tuple[int, int]) -> Image.Image:
    al = a[..., 3:4] / 255.0
    pm = np.concatenate([a[..., :3] * al, a[..., 3:4]], axis=2)
    im = Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8), "RGBA").resize(size, Image.LANCZOS)
    r = np.array(im).astype(np.float32)
    al2 = np.maximum(r[..., 3:4] / 255.0, 1e-4)
    r[..., :3] = np.clip(r[..., :3] / al2, 0, 255)
    return Image.fromarray(r.astype(np.uint8), "RGBA")


def crop_pad(a: np.ndarray, box, size) -> Image.Image:
    """Crop, padding with transparency where the box falls outside the source."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    h, w = a.shape[:2]
    out = np.zeros((y1 - y0, x1 - x0, 4), np.float32)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(w, x1), min(h, y1)
    out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = a[sy0:sy1, sx0:sx1]
    return premult_resize(out, size)


def build_badge(a: np.ndarray) -> Image.Image:
    """Whole bust in frame, both shoulders in, air above the crown, bust to the bottom."""
    mask = a[..., 3] > 16
    ys = np.where(mask.any(axis=1))[0]
    xs = np.where(mask.any(axis=0))[0]
    bw = xs.max() - xs.min()
    scale = (BAGE[0] * BADGE_SIDE) / bw
    win_w = BAGE[0] / scale
    win_h = BAGE[1] / scale
    cx = (xs.min() + xs.max()) / 2
    top = ys.min() - BADGE_TOP * win_h
    return crop_pad(a, (cx - win_w / 2, top, cx + win_w / 2, top + win_h), BAGE)


def build_strips(a: np.ndarray) -> tuple[Image.Image, Image.Image]:
    """Size the window to the head's HEIGHT, never its width.

    🚨 The content box is 115x92, wider than it is tall. A head is not. Sizing by
    head WIDTH makes the result depend on headgear: Hank Snatchblock's hard hat
    gave a 905px box and a full-torso strip with a thumbnail face, while Dodge
    Sparrowhawk's narrower goggles gave 574px and a face cropped at both the
    goggles and the chin. Head height is stable across characters, so the window
    is driven by it and the width simply follows the content box's aspect.
    """
    hx0, hy0, hx1, hy1 = head_box(a)
    cw, ch = BG_CONTENT[2], BG_CONTENT[3]
    win_h = (hy1 - hy0) / HEAD_FILL
    win_w = win_h * cw / ch
    cx = (hx0 + hx1) / 2
    content = crop_pad(a, (cx - win_w / 2, hy0, cx + win_w / 2, hy0 + win_h), (cw, ch))
    print(f"    head {hx1-hx0}x{hy1-hy0}px at y{hy0} -> window {win_w:.0f}x{win_h:.0f}")
    bg = Image.new("RGBA", BG, (0, 0, 0, 0))
    bg.paste(content, BG_CONTENT[:2])
    small = Image.new("RGBA", BGSMALL, (0, 0, 0, 0))
    small.paste(content.resize(SMALL_CONTENT[2:], Image.LANCZOS), SMALL_CONTENT[:2])
    return bg, small


def checker(im: Image.Image, sq=8) -> Image.Image:
    bg = Image.new("RGB", im.size, (198, 198, 198))
    px = bg.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if ((x // sq) + (y // sq)) % 2:
                px[x, y] = (132, 132, 132)
    bg.paste(im, (0, 0), im)
    return bg


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for prefix, src in subjects():
        print(prefix)
        a = load_rgba(src)
        badge = build_badge(a)
        bg, small = build_strips(a)
        sheet = Image.new("RGB", (400, 540), (38, 38, 38))
        y = 10
        for name, im in ((f"{prefix}_bage", badge), (f"{prefix}_bg", bg), (f"{prefix}_bgSmall", small)):
            p = os.path.join(OUT, name + ".png")
            im.save(p, optimize=True)
            al = np.array(im)[..., 3]
            print(f"    {name}.png {im.size} transparent={100*(al==0).mean():.1f}% {os.path.getsize(p)}B")
            sheet.paste(checker(im), (12, y))
            y += im.size[1] + 16
        sheet.save(os.path.join(OUT, f"{prefix}_preview.png"))


if __name__ == "__main__":
    main()
