"""Section divider: `01 · PROFILE` plate on a tick ruler, a glint sweeping along it.

Transparent background, so it sits on GitHub's light and dark page alike;
only the plate is filled, to keep its label readable on both.
"""
from __future__ import annotations

from ..kit import PAL, body_fonts, esc, svg

W, H = 1000, 52
BASE = 30                # ruler baseline
LFS, SPACING = 13, 3     # label font size, letter-spacing
SWEEP = 7.0              # seconds for the glint to cross the card
C = PAL


def render(cfg, num: int, title: str) -> str:
    label = f"{num:02d} · {title.upper()}"
    tw = len(label) * (LFS * 0.6 + SPACING) - SPACING
    cx, hw = W / 2, tw / 2 + 22
    gap = (cx - hw - 26, cx + hw + 26)                 # ruler stops this far from the plate

    ticks = []
    for i, x in enumerate(range(16, W - 15, 12)):
        if gap[0] < x < gap[1]:
            continue
        major = i % 8 == 0
        h = 12 if major else 5
        ticks.append(f'<rect x="{x}" y="{BASE - h / 2:.1f}" width="1" height="{h}"/>')
    ticks = "".join(ticks)

    defs = (
        f'<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<rect x="-240" y="0" width="240" height="{H}" fill="url(#g)">'
        f'<animate attributeName="x" values="-240;{W}" dur="{SWEEP}s" repeatCount="indefinite"/></rect></mask>')

    plate = (f"M{cx - hw - 12:.1f} {BASE + 10} L{cx - hw:.1f} {BASE - 14} "
             f"L{cx + hw:.1f} {BASE - 14} L{cx + hw + 12:.1f} {BASE + 10} Z")
    body = (
        f'<rect x="16" y="{BASE}" width="{gap[0] - 16:.1f}" height="1" fill="{C["gutter"]}" opacity=".6"/>'
        f'<rect x="{gap[1]:.1f}" y="{BASE}" width="{W - 16 - gap[1]:.1f}" height="1" fill="{C["gutter"]}" opacity=".6"/>'
        f'<g fill="{C["gutter_hi"]}" opacity=".7">{ticks}</g>'
        # the glint: bright copy of the ruler, seen only through the moving mask
        f'<g mask="url(#m)"><g fill="{C["cyan"]}">{ticks}</g>'
        f'<rect x="16" y="{BASE - 0.5}" width="{W - 32}" height="2" fill="{C["teal"]}"/></g>'
        f'<path d="{plate}" fill="{C["bg"]}" stroke="{C["teal"]}" stroke-width="1.4" stroke-linejoin="round"/>'
        f'<text x="{cx:.1f}" y="{BASE + 3.5:.1f}" text-anchor="middle" font-weight="700" '
        f'style="font-size:{LFS}px;letter-spacing:{SPACING}px">'
        f'<tspan fill="{C["teal"]}">{num:02d}</tspan><tspan fill="{C["comment"]}"> · </tspan>'
        f'<tspan fill="{C["fg"]}">{esc(title.upper())}</tspan></text>')
    return svg(W, H, label, body_fonts(body), defs, body)
