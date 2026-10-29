"""Keycaps row: every key is pressed in turn, like someone typing on them."""
from __future__ import annotations

from ..kit import PAL, esc, font_css, svg

W = 1000
KEY_H, DEPTH, GAP = 52, 6, 12
VAL_FS, LBL_FS = 16, 10

COLORS = {  # face, side, label, value
    "teal":   ("#3fc9b4", "#24877a", "#14514a", "#0b2b27"),
    "blue":   ("#7aa2f7", "#4b67b0", "#22325c", "#101a33"),
    "violet": ("#bb9af7", "#7c5fb8", "#3d2a63", "#1f1336"),
    "orange": ("#ff9e64", "#b86a3d", "#6b3818", "#3a1b08"),
    "pink":   ("#f7768e", "#b04a5e", "#62202e", "#3a0f18"),
    "yellow": ("#e0af68", "#a07636", "#5c3f12", "#2e1f06"),
    "green":  ("#9ece6a", "#678f3c", "#33501a", "#1a2c0b"),
    "dark":   ("#2a2f4a", "#161a2c", "#8189b8", "#c0caf5"),
}


def render(cfg) -> str:
    badges = cfg.get("badges", [])
    cw = VAL_FS * 0.6
    widths = [max(len(b["value"]) * cw, len(b["label"]) * LBL_FS * 0.6) + 30 for b in badges]
    # wrap into rows that fit
    rows, cur, cur_w = [], [], 0.0
    for b, w in zip(badges, widths):
        if cur and cur_w + GAP + w > W - 40:
            rows.append(cur)
            cur, cur_w = [], 0.0
        cur.append((b, w))
        cur_w += (GAP if len(cur) > 1 else 0) + w
    if cur:
        rows.append(cur)

    n = len(badges)
    step, period = 0.9, max(len(badges), 1) * 0.9 + 3.0
    d1, d2, d3 = 100 * 0.06 / period, 100 * 0.3 / period, 100 * 0.42 / period
    css = [f"@keyframes press{{0%{{transform:none}}{d1:.2f}%,{d2:.2f}%{{transform:translateY({DEPTH-2}px)}}"
           f"{d3:.2f}%,100%{{transform:none}}}}"]
    body, idx = [], 0
    H = 20 + len(rows) * (KEY_H + DEPTH + 18) + 6
    for r, row in enumerate(rows):
        total = sum(w for _, w in row) + GAP * (len(row) - 1)
        x = (W - total) / 2
        y = 18 + r * (KEY_H + DEPTH + 18)
        for b, w in row:
            face, side, lbl, val = COLORS.get(b.get("color", "dark"), COLORS["dark"])
            cls = f"k{idx}"
            css.append(f".{cls}{{animation:press {period:.2f}s ease-out {idx*step:.2f}s infinite}}")
            body.append(
                f'<rect x="{x:.1f}" y="{y+DEPTH:.1f}" width="{w:.1f}" height="{KEY_H}" rx="10" fill="{side}"/>'
                f'<g class="{cls}">'
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{KEY_H}" rx="10" fill="{face}"/>'
                f'<rect x="{x+4:.1f}" y="{y+3:.1f}" width="{w-8:.1f}" height="{KEY_H-12}" rx="8" fill="#fff" opacity=".10"/>'
                f'<text x="{x+14:.1f}" y="{y+17:.1f}" fill="{lbl}" style="font-size:{LBL_FS}px">{esc(b["label"])}</text>'
                f'<text x="{x+w/2:.1f}" y="{y+39:.1f}" fill="{val}" font-weight="700" text-anchor="middle" '
                f'style="font-size:{VAL_FS}px">{esc(b["value"])}</text></g>')
            x += w + GAP
            idx += 1
    text = "".join(b["label"] + b["value"] for b in badges)
    return svg(W, H, "badges", font_css(text) + "".join(css), "", "".join(body))
