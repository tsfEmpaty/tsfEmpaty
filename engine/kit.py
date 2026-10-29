"""Shared pieces: palette, fonts embedded as subset woff2, SVG frame and the
discrete-timeline helpers every animated card is built from.

Animation model: one card = one loop of period P seconds. Every moving thing is
a SMIL <animate> with dur=P and repeatCount=indefinite, so all of them stay in
lock-step forever. The value an element has at t=0 is also written as its
plain attribute, so a viewer without animation still sees a complete frame.
"""
from __future__ import annotations

import base64
import html
import io
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

FONT_DIR = Path(__file__).parent / "fonts"
FS = 15                 # base font size, px
CW = FS * 0.6           # JetBrains Mono advance is exactly 0.6 em

# Tokyo Night (night) — the colours most nvim screenshots are recognised by.
PAL = dict(
    bg="#1a1b26", bg_dark="#16161e", bg_hl="#292e42", border="#2f334d",
    fg="#c0caf5", fg_dark="#a9b1d6", comment="#565f89", gutter="#3b4261",
    gutter_hi="#737aa2", blue="#7aa2f7", cyan="#7dcfff", teal="#73daca",
    green="#9ece6a", magenta="#bb9af7", orange="#ff9e64", yellow="#e0af68",
    red="#f7768e", punct="#89ddff", type="#2ac3de",
)

REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ── fonts ────────────────────────────────────────────────────────────────────
_FACES = {
    (400, "normal"): "jetbrains-mono-latin-400-normal.woff2",
    (700, "normal"): "jetbrains-mono-latin-700-normal.woff2",
    (400, "italic"): "jetbrains-mono-latin-400-italic.woff2",
}


def font_css(text: str, faces=((400, "normal"), (700, "normal"))) -> str:
    """@font-face rules with the faces subset to exactly the characters used."""
    rules = []
    for weight, style in faces:
        # recalcTimestamp=False: same text → byte-identical SVG, so CI commits only real changes
        f = TTFont(FONT_DIR / _FACES[(weight, style)], recalcTimestamp=False)
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = []
        sub = subset.Subsetter(opts)
        sub.populate(text=text + " ")
        sub.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        rules.append(f"@font-face{{font-family:JBM;font-weight:{weight};font-style:{style};"
                     f"src:url(data:font/woff2;base64,{b64}) format(\"woff2\")}}")
    return "".join(rules) + (f"text{{font-family:JBM,ui-monospace,SFMono-Regular,Menlo,Consolas,"
                             f"monospace;font-size:{FS}px;white-space:pre}}")


def missing_glyphs(text: str) -> set[str]:
    cmap = TTFont(FONT_DIR / _FACES[(400, "normal")]).getBestCmap()
    return {c for c in set(text) if ord(c) not in cmap and c not in "\n\t"}


# ── timeline ─────────────────────────────────────────────────────────────────
class Timeline:
    """Collects discrete animations; renders them once the period is known."""

    def __init__(self, period: float):
        self.P = period

    def disc(self, attr: str, events: list[tuple[float, object]]) -> str:
        """events: (time, value). The first event must be at t=0."""
        ev: dict[float, object] = {}
        for t, v in sorted(events, key=lambda e: e[0]):
            ev[round(max(0.0, min(t, self.P - 0.001)), 3)] = v
        items = sorted(ev.items())
        assert items and items[0][0] == 0, f"{attr}: needs a value at t=0"
        # drop events that do not change anything
        clean = [items[0]]
        for t, v in items[1:]:
            if v != clean[-1][1]:
                clean.append((t, v))
        if len(clean) == 1:
            return ""
        kt, last = [], -1.0
        for t, _ in clean:
            k = max(t / self.P, last + 0.00002)
            kt.append(k)
            last = k
        vals = ";".join(_fmt(v) for _, v in clean)
        keys = ";".join(f"{k:.5f}" for k in kt)
        return (f'<animate attributeName="{attr}" values="{vals}" keyTimes="{keys}" '
                f'dur="{self.P:.3f}s" calcMode="discrete" repeatCount="indefinite"/>')

    def vis(self, intervals: list[tuple[float, float]]) -> tuple[str, str]:
        """Visible during the given [a, b) intervals → (initial opacity, <animate>)."""
        ev: list[tuple[float, object]] = [(0.0, 0)]
        for a, b in intervals:
            ev += [(a, 1), (b, 0)]
        ev.sort(key=lambda e: e[0])
        # when an interval starts at 0 the (0,1) must win over the seed (0,0)
        init = 1 if any(a <= 0 < b for a, b in intervals) else 0
        ev = [(0.0, init)] + [e for e in ev if e[0] > 0]
        return str(init), self.disc("opacity", ev)


def _fmt(v) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def intervals(changes: list[tuple[float, object]], P: float) -> dict:
    """[(t, value)] state changes → {value: [(start, end), ...]}."""
    ch = sorted(changes, key=lambda c: c[0])
    out: dict = {}
    for k, (t, v) in enumerate(ch):
        end = ch[k + 1][0] if k + 1 < len(ch) else P + 1
        if end > t:
            out.setdefault(v, []).append((t, end))
    return out


# ── text ─────────────────────────────────────────────────────────────────────
def tok_text(x, y, tokens, extra=""):
    """One <text> of coloured tokens: (text, colour[, 'b'|'i'|'bi'])."""
    spans = []
    for tok in tokens:
        text, col = tok[0], tok[1]
        style = tok[2] if len(tok) > 2 else ""
        a = ' font-weight="700"' if "b" in style else ""
        a += ' font-style="italic"' if "i" in style else ""
        spans.append(f'<tspan fill="{col}"{a}>{esc(text)}</tspan>')
    return f'<text x="{x:.1f}" y="{y:.1f}"{extra}>{"".join(spans)}</text>'


def plain(markup: str) -> str:
    """Characters that actually end up as text (rough: strip tags)."""
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


def body_fonts(body: str, faces=((400, "normal"), (700, "normal"))) -> str:
    """font_css for whatever text the finished body contains; warns about glyphs the font lacks."""
    text = plain(body)
    miss = missing_glyphs(text)
    if miss:
        print(f"  ! нет в шрифте: {''.join(sorted(miss))}")
    return font_css(text, faces)


def svg(w: float, h: float, label: str, css: str, defs: str, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
            f'viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="{esc(label)}">'
            f"<title>{esc(label)}</title><style>{css}{REDUCED}</style><defs>{defs}</defs>{body}</svg>")
