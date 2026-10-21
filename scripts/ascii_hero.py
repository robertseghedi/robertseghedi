#!/usr/bin/env python3
"""Generates assets/ascii-hero.gif: an animated ASCII header for the profile README.

Run from the repo root: python3 scripts/ascii_hero.py  (needs Pillow, macOS Menlo font)
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COLS, ROWS = 200, 30
CW, RH = 6, 12  # cell size in px (monospace advance ~0.6em at 10px)
PAD_Y = 12
W, H = COLS * CW, ROWS * RH + PAD_Y * 2
SCALE = 1.5  # output px per layout px, for sharper glyphs on retina
FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
SEED = 7

TITLE = "ROBERT SEGHEDI"
SUBTITLE = "co-founder @ peal.dev  //  shipping at 3am from Romania"
RAMP = ".,:-=+*#%@"
PALETTE = ["#431407", "#7c2d12", "#c2410c", "#ea580c", "#f97316", "#fb923c"]
BG = "#0d1117"
WAVES = 12  # buckets that light up one after another
STEPS = 24  # frames per loop
FRAME_MS = 200

FONT = {
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    " ": ["000"] * 7,
}

rng = random.Random(SEED)
_lattice = {}


def lattice(ix, iy):
    if (ix, iy) not in _lattice:
        _lattice[(ix, iy)] = rng.random()
    return _lattice[(ix, iy)]


def smooth(t):
    return t * t * (3 - 2 * t)


def value_noise(x, y):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = smooth(x - ix), smooth(y - iy)
    a, b = lattice(ix, iy), lattice(ix + 1, iy)
    c, d = lattice(ix, iy + 1), lattice(ix + 1, iy + 1)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def fbm(x, y):
    return 0.6 * value_noise(x, y) + 0.3 * value_noise(x * 2.1, y * 2.1) + 0.1 * value_noise(x * 4.3, y * 4.3)


def title_mask():
    """Pixels of the title, each font pixel = 2 cols x 1 row (roughly square)."""
    glyphs = [FONT[ch] for ch in TITLE]
    width = sum(len(g[0]) * 2 + 2 for g in glyphs) - 2
    x0, y0 = (COLS - width) // 2, 9
    mask = set()
    x = x0
    for g in glyphs:
        for r, line in enumerate(g):
            for c, bit in enumerate(line):
                if bit == "1":
                    mask.add((x + c * 2, y0 + r))
                    mask.add((x + c * 2 + 1, y0 + r))
        x += len(g[0]) * 2 + 2
    return mask, (x0 - 4, y0 - 2, x0 + width + 4, y0 + 7 + 5)


def main():
    mask, (bx0, by0, bx1, by1) = title_mask()
    sub_row = by1 - 2
    cells = []
    for y in range(ROWS):
        for x in range(COLS):
            # diagonal wave + jitter decides when a cell lights up
            wave = (x * 0.09 + y * 0.35 + rng.random() * 1.6) % WAVES
            bucket = int(wave)
            if (x, y) in mask:
                ch = rng.choice("@#%")
                cells.append((x, y, ch, "t", bucket))
                continue
            if bx0 <= x <= bx1 and by0 <= y <= by1:
                continue  # keep the title area quiet
            n = fbm(x / 14, y / 5)
            # brighter toward bottom-left and top-right, like a light leak
            leak = max(1 - math.hypot(x / COLS, (ROWS - y) / ROWS * 0.6) * 1.6, 0)
            leak2 = max(1 - math.hypot((COLS - x) / COLS, y / ROWS * 0.6) * 2.2, 0)
            v = n * 0.85 + leak * 0.6 + leak2 * 0.4 - 0.3
            if v <= 0 or rng.random() > 0.35 + v * 1.2:
                continue
            v = min(v, 0.999)
            ch = RAMP[min(max(int((v + rng.uniform(-0.15, 0.15)) * len(RAMP)), 0), len(RAMP) - 1)]
            level = min(int(v * len(PALETTE) * 1.4), len(PALETTE) - 1)
            cells.append((x, y, ch, f"c{level}", bucket))

    def hex_rgb(c):
        return tuple(int(c[i : i + 2], 16) for i in (1, 3, 5))

    def blend(c, a):
        return tuple(round(b + (f - b) * a) for f, b in zip(hex_rgb(c), hex_rgb(BG)))

    def brightness(k):
        return 0.14 + 0.86 * max(math.cos((k / STEPS - 0.45) * math.pi * 2.2), 0) ** 2

    def s(v):
        return round(v * SCALE)

    size = (s(W), s(H))
    glyph_font = ImageFont.truetype(FONT_PATH, s(10))
    sub_font = ImageFont.truetype(FONT_PATH, s(15))

    # static layer: background, title, subtitle (no gradients: they band after quantizing)
    base = Image.new("RGB", size, BG)
    draw = ImageDraw.Draw(base)
    for x, y, ch, cls, _ in cells:
        if cls == "t":
            draw.text((s(x * CW), s(PAD_Y + y * RH + 10)), ch, font=glyph_font, fill="#fdba74", anchor="ls")
    parts = [(t, "#c2410c") for t in SUBTITLE.partition("peal.dev")]
    parts[1] = (parts[1][0], "#f97316")
    sub_w = sum(draw.textlength(t, font=sub_font) for t, _ in parts)
    x = (size[0] - sub_w) / 2
    for t, color in parts:
        draw.text((x, s(PAD_Y + sub_row * RH + 12)), t, font=sub_font, fill=color, anchor="ls")
        x += draw.textlength(t, font=sub_font)

    frames = []
    for k in range(STEPS):
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        for x, y, ch, cls, bucket in cells:
            if cls == "t":
                continue
            a = brightness((k + round(bucket * STEPS / WAVES)) % STEPS)
            fill = blend(PALETTE[int(cls[1:])], a)
            draw.text((s(x * CW), s(PAD_Y + y * RH + 10)), ch, font=glyph_font, fill=fill, anchor="ls")
        frames.append(frame)

    # one shared palette keeps colors stable between frames
    palette = frames[0].quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]

    dest = Path(__file__).resolve().parent.parent / "assets" / "ascii-hero.gif"
    dest.parent.mkdir(exist_ok=True)
    frames[0].save(dest, save_all=True, append_images=frames[1:], duration=FRAME_MS, loop=0, optimize=True)
    print(f"{dest} — {len(cells)} glyphs, {len(frames)} frames, {dest.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
