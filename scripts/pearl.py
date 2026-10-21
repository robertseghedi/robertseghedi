#!/usr/bin/env python3
"""Generates assets/pearl.gif: a single ASCII pearl with light slowly drifting across it.

Run from the repo root: python3 scripts/pearl.py  (needs Pillow and macOS system fonts)
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CW, RH = 6, 12  # character cell in layout px
W, H = 1200, 380
SCALE = 1.5  # output px per layout px, for sharper glyphs on retina
CX, CY, R = W / 2, 150, 118  # the pearl
RAMP = " .,:-=+*#%@"
BG = (255, 255, 255)  # GitHub light background, so the edges disappear
INK = (17, 17, 17)
ACCENT = "#f97316"
NAME = "robert seghedi"
MONO = "/System/Library/Fonts/Menlo.ttc"
SANS = "/System/Library/Fonts/HelveticaNeue.ttc"
FRAMES = 48
FRAME_MS = 80
SWING = math.radians(65)  # how far the light travels left/right of the viewer


def s(v):
    return round(v * SCALE)


def norm(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def shade(dx, dy, light):
    """Lambert + a tight specular highlight, so it reads as a pearl rather than a ball."""
    nz = math.sqrt(max(1 - dx * dx - dy * dy, 0))
    n = (dx, dy, nz)
    diffuse = max(sum(a * b for a, b in zip(n, light)), 0)
    half = norm((light[0], light[1], light[2] + 1))
    spec = max(sum(a * b for a, b in zip(n, half)), 0) ** 40
    return min(0.06 + 0.8 * diffuse + 0.6 * spec, 1)


def main():
    glyph_font = ImageFont.truetype(MONO, s(10))
    name_font = ImageFont.truetype(SANS, s(17))

    base = Image.new("RGB", (s(W), s(H)), BG)
    draw = ImageDraw.Draw(base)
    # lowercase name, wide tracking, one orange full stop: the only color on the page
    tracking = s(4)
    name_w = sum(draw.textlength(ch, font=name_font) + tracking for ch in NAME) - tracking
    dot_w = draw.textlength(".", font=name_font)
    x = (s(W) - name_w - dot_w) / 2
    for ch in NAME:
        draw.text((x, s(H - 48)), ch, font=name_font, fill=(110, 119, 129), anchor="ls")
        x += draw.textlength(ch, font=name_font) + tracking
    draw.text((x - tracking + s(2), s(H - 48)), ".", font=name_font, fill=ACCENT, anchor="ls")

    cells = []
    for row in range(int((CY - R) // RH), int((CY + R) // RH) + 2):
        for col in range(int((CX - R) // CW), int((CX + R) // CW) + 2):
            dx = (col * CW + CW / 2 - CX) / R
            dy = (row * RH + RH / 2 - CY) / R
            if dx * dx + dy * dy <= 1:
                cells.append((col, row, dx, dy))

    frames = []
    for k in range(FRAMES):
        a = SWING * math.sin(2 * math.pi * k / FRAMES)
        light = norm((math.sin(a), -0.45, math.cos(a)))
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        for col, row, dx, dy in cells:
            v = shade(dx, dy, light)
            ch = RAMP[min(int(v * len(RAMP)), len(RAMP) - 1)]
            if ch == " ":
                continue
            fill = tuple(round(b + (i - b) * (0.12 + 0.88 * v)) for i, b in zip(INK, BG))
            draw.text((s(col * CW), s(row * RH + 10)), ch, font=glyph_font, fill=fill, anchor="ls")
        frames.append(frame)

    palette = frames[0].quantize(colors=64, method=Image.Quantize.MEDIANCUT)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]

    dest = Path(__file__).resolve().parent.parent / "assets" / "pearl.gif"
    dest.parent.mkdir(exist_ok=True)
    frames[0].save(dest, save_all=True, append_images=frames[1:], duration=FRAME_MS, loop=0, optimize=True)
    print(f"{dest} — {len(cells)} cells, {len(frames)} frames, {dest.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
