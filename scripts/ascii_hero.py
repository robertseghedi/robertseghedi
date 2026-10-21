#!/usr/bin/env python3
"""Generates assets/ascii-hero.svg: an animated ASCII header for the profile README.

Run from the repo root: python3 scripts/ascii_hero.py
"""
import math
import random
from pathlib import Path

COLS, ROWS = 200, 30
CW, RH = 6, 12  # cell size in px (monospace advance ~0.6em at 10px)
PAD_Y = 12
W, H = COLS * CW, ROWS * RH + PAD_Y * 2
SEED = 7

TITLE = "ROBERT SEGHEDI"
SUBTITLE = "co-founder @ peal.dev  //  shipping at 3am from Romania"
RAMP = ".,:-=+*#%@"
PALETTE = ["#431407", "#7c2d12", "#c2410c", "#ea580c", "#f97316", "#fb923c"]
BG = "#0d1117"
WAVES = 16  # number of animation-delay buckets
PERIOD = 4.8  # seconds

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

    css = [
        f"text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace;font-size:10px}}",
        f".g text{{animation:p {PERIOD}s ease-in-out infinite;opacity:.18}}",
        "@keyframes p{0%,100%{opacity:.14}45%{opacity:1}60%{opacity:.85}}",
        f".t{{fill:#fdba74;animation-name:q!important}}",
        "@keyframes q{0%,100%{opacity:.7}45%{opacity:1}}",
        ".s{fill:#c2410c;font-size:15px;letter-spacing:1px}",
        "@media (prefers-reduced-motion:reduce){.g text,.scan{animation:none!important;opacity:.8}}",
        ".scan{animation:m 7s linear infinite}",
        f"@keyframes m{{from{{transform:translateX(-300px)}}to{{transform:translateX({W + 300}px)}}}}",
    ]
    css += [f".c{i}{{fill:{c}}}" for i, c in enumerate(PALETTE)]
    css += [f".d{i}{{animation-delay:-{PERIOD * i / WAVES:.2f}s!important}}" for i in range(WAVES)]

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{TITLE}">',
        f"<title>{TITLE}</title>",
        f"<style>{''.join(css)}</style>",
        "<defs>",
        '<linearGradient id="sg" x1="0" x2="1"><stop offset="0" stop-color="#f97316" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#f97316" stop-opacity=".07"/><stop offset="1" stop-color="#f97316" stop-opacity="0"/></linearGradient>',
        '<radialGradient id="glow" cx=".5" cy=".42" r=".45"><stop offset="0" stop-color="#f97316" stop-opacity=".12"/>'
        '<stop offset="1" stop-color="#f97316" stop-opacity="0"/></radialGradient>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#glow)"/>',
        '<g class="g">',
    ]
    for x, y, ch, cls, bucket in cells:
        ch = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}.get(ch, ch)
        out.append(f'<text x="{x * CW}" y="{PAD_Y + y * RH + 10}" class="{cls} d{bucket}">{ch}</text>')
    out.append("</g>")
    sub_y = PAD_Y + sub_row * RH + 12
    sub = SUBTITLE.replace("peal.dev", "<tspan class=\"c4\">peal.dev</tspan>")
    out.append(f'<text x="{W / 2}" y="{sub_y}" text-anchor="middle" class="s">{sub}</text>')
    out.append(f'<rect class="scan" x="0" y="0" width="300" height="{H}" fill="url(#sg)"/>')
    out.append("</svg>")

    dest = Path(__file__).resolve().parent.parent / "assets" / "ascii-hero.svg"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text("\n".join(out))
    print(f"{dest} — {len(cells)} glyphs, {dest.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
