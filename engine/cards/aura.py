"""Logseq Aura Dark theme card: what the project is on the left, the theme itself on the right.

Left: kicker, title, a few lines about it, numbers, repo link.
Right: a Logseq window painted in the theme — sidebar, page with properties, blocks,
a code block styled as a window card. Bottom: the theme's colour system as chips.
Alive: the last block is typed and erased in a loop (Logseq markup: [[ref]], #tag,
`code`, **bold**), a TODO flips to DONE, palette chips light up in turn.
t=0 shows the first phrase written and the TODO done.
"""
from __future__ import annotations

import random
import re

from ..kit import Timeline, body_fonts, esc, intervals, star, svg, tok_text

W, H = 1000, 468
AU = dict(
    editor="#1e1f29", sidebar="#1a1b24", chrome="#17181f", hover="#23242f", active="#2a2c37",
    border="#12131a", soft="#2a2c3a", text="#e0e0e0", content="#c8cbd8", secondary="#a6accd",
    muted="#6b7a99", faint="#3e4460", icon="#555870", purple="#c792ea", purple_l="#d4aaff",
    peri="#82aaff", green="#c3e88d", gold="#ffcb6b", amber="#ffd580", teal="#7fdbca",
    cyan="#89ddff", peach="#f78c6c", rose="#f07178", punct="#697098", bg="#14151c",
)
PALETTE = [("Purple", "purple"), ("Periwinkle", "peri"), ("Mint Teal", "teal"), ("Sage Green", "green"),
           ("Warm Gold", "gold"), ("Amber", "amber"), ("Slate", "muted")]

LX = 44                          # left column
WX, WY, WW, WH = 468, 44, 490, 330   # the Logseq window
SBW = 148                        # its sidebar
MX = WX + SBW + 20               # its page column (bullets)
TX = MX + 16                     # block text
RIGHT = WX + WW - 16
STRIP = WY + WH + 30             # palette strip separator
FSZ = 12
CW = FSZ * 0.6
TYPE_Y = WY + 310                # baseline of the typed block

MARKUP = re.compile(r"(\[\[)(.+?)(\]\])|(#[\w-]+)|`([^`]+)`|\*\*(.+?)\*\*|([^\[#`*]+|.)")


def rich(s: str, base: str) -> list[tuple]:
    """Logseq markup → tokens. Brackets stay visible (faint), backticks and ** do not."""
    out = []
    for m in MARKUP.finditer(s):
        lb, ref, rb, tag, code, bold, txt = m.groups()
        if ref:
            out += [(lb, AU["punct"]), (ref, AU["purple"]), (rb, AU["punct"])]
        elif tag:
            out.append((tag, AU["teal"]))
        elif code:
            out.append((code, AU["green"]))
        elif bold:
            out.append((bold, AU["gold"], "b"))
        else:
            out.append((txt, base))
    return out


def width(tokens) -> int:
    return sum(len(t[0]) for t in tokens)


def schedule(lens: list[int]):
    rnd = random.Random(3)
    m = len(lens)
    S = dict(w={k: [(0, lens[0] if k == 0 else 0)] for k in range(m)}, caret=[(0, lens[0])], todo=[(0, "DONE")])
    t = 2.2
    for i in range(m):
        cur, nxt = i, (i + 1) % m
        for c in range(lens[cur] - 1, -1, -1):          # backspace, held down
            t += 0.022
            S["w"][cur].append((t, c))
            S["caret"].append((t, c))
        t += 0.35
        for c in range(1, lens[nxt] + 1):
            t += 0.058 * rnd.uniform(0.6, 1.5)
            S["w"][nxt].append((t, c))
            S["caret"].append((t, c))
        t += 2.6 if nxt else 0.8
        if i == 0:
            S["todo"].append((t - 1.6, "TODO"))
        if i == m - 2 or m == 1:
            S["todo"].append((t - 1.2, "DONE"))
    return S, round(t, 2)


def render(cfg) -> str:
    spec = cfg["aura"]
    meta = cfg["stats"]["repos"][spec["repo"]]
    phrases = [rich(p.replace("{stars}", str(meta["stars"])), AU["content"]) for p in spec["typing"]]
    lens = [width(p) for p in phrases]
    cols = int((RIGHT - TX) / CW)
    if max(lens) > cols:
        raise SystemExit(f"aura.typing: фраза длиннее {cols} символов")
    S, P = schedule(lens)
    tl = Timeline(P)
    body, defs = [], []
    A = body.append
    f12 = f' style="font-size:{FSZ}px"'

    defs.append(f'<clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>'
                f'<clipPath id="win"><rect x="{WX}" y="{WY}" width="{WW}" height="{WH}" rx="10"/></clipPath>'
                f'<radialGradient id="glow" cx="{WX + WW * .6}" cy="{WY + WH * .45}" r="420" '
                f'gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{AU["purple"]}" stop-opacity=".16"/>'
                f'<stop offset="1" stop-color="{AU["purple"]}" stop-opacity="0"/></radialGradient>')
    A(f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{AU["bg"]}"/>'
      f'<rect width="{W}" height="{H}" fill="url(#glow)"/>')

    # ── left: what it is ──
    A(f'<circle cx="{LX + 6}" cy="81" r="7" fill="{AU["purple"]}"/><circle cx="{LX + 10}" cy="78" r="6" fill="{AU["bg"]}"/>')
    A(f'<text x="{LX + 22}" y="86" fill="{AU["purple"]}" style="font-size:12px;letter-spacing:4px">'
      f'{esc(spec["kicker"].upper())}</text>')
    A(f'<text x="{LX - 2}" y="146" fill="{AU["text"]}" font-weight="700" style="font-size:48px">{esc(spec["title"])}</text>')
    A(f'<text x="{LX - 2}" y="194" fill="{AU["purple"]}" style="font-size:38px">{esc(spec["subtitle"])}</text>')
    for i, line in enumerate(spec["about"]):
        A(f'<text x="{LX}" y="{238 + i * 22}" fill="{AU["secondary"]}" style="font-size:14px">{esc(line)}</text>')
    stats = [("7", "colors"), ("2", "token sets"), ("1", "nerd font"), (str(meta["stars"]), "stars")]
    sx = LX
    for num, lab in stats:
        A(f'<text x="{sx}" y="320" fill="{AU["text"]}" font-weight="700" style="font-size:28px">{num}</text>'
          f'<text x="{sx}" y="340" fill="{AU["muted"]}" style="font-size:10px;letter-spacing:2px">{lab.upper()}</text>')
        sx += max(len(lab) * 8, len(num) * 17) + 30
    A(f'<text x="{LX}" y="{WY + WH - 4}" fill="{AU["muted"]}" style="font-size:12px">github.com/{esc(spec["repo"])}</text>')

    # ── right: a Logseq window in the theme ──
    A(f'<g clip-path="url(#win)"><rect x="{WX}" y="{WY}" width="{WW}" height="{WH}" fill="{AU["editor"]}"/>')
    A(f'<rect x="{WX}" y="{WY}" width="{WW}" height="30" fill="{AU["chrome"]}"/>'
      f'<rect x="{WX}" y="{WY + 29}" width="{WW}" height="1" fill="{AU["border"]}"/>')
    for j, c in enumerate(("rose", "gold", "green")):
        A(f'<circle cx="{WX + 16 + j * 14}" cy="{WY + 15}" r="4.5" fill="{AU[c]}"/>')
    A(f'<text x="{WX + WW / 2}" y="{WY + 19}" fill="{AU["muted"]}" text-anchor="middle" style="font-size:11px">'
      f'Logseq · aura-dark-theme</text>')
    for j, k in enumerate("ti"):
        x = WX + WW - 52 + j * 20
        A(f'<rect x="{x}" y="{WY + 6}" width="16" height="18" rx="4" fill="{AU["active"]}" stroke="{AU["soft"]}"/>'
          f'<text x="{x + 8}" y="{WY + 19}" fill="{AU["secondary"]}" text-anchor="middle" style="font-size:11px">{k}</text>')
    # sidebar
    A(f'<rect x="{WX}" y="{WY + 30}" width="{SBW}" height="{WH - 30}" fill="{AU["sidebar"]}"/>'
      f'<rect x="{WX + SBW - 1}" y="{WY + 30}" width="1" height="{WH - 30}" fill="{AU["border"]}"/>')
    for i, item in enumerate(["Journals", "Flashcards", "Graph view", "All pages"]):
        y = WY + 58 + i * 26
        A(_icon(i, WX + 14, y - 11))
        A(f'<text x="{WX + 38}" y="{y}" fill="{AU["secondary"]}"{f12}>{item}</text>')
    fy = WY + 178
    A(f'<text x="{WX + 14}" y="{fy}" fill="{AU["faint"]}" font-weight="700" style="font-size:9px;letter-spacing:1.5px">FAVORITES</text>')
    for i, item in enumerate(["aura-dark-theme", "custom.css", "Color system"]):
        y = fy + 24 + i * 24
        if i == 0:
            A(f'<rect x="{WX + 6}" y="{y - 16}" width="{SBW - 12}" height="22" rx="5" fill="{AU["active"]}"/>')
        A(f'<text x="{WX + 14}" y="{y}" fill="{AU["faint"]}"{f12}>#</text>'
          f'<text x="{WX + 28}" y="{y}" fill="{AU["purple"] if i == 0 else AU["secondary"]}"{f12}>{esc(item)}</text>')

    # page
    A(f'<text x="{MX - 4}" y="{WY + 62}" fill="{AU["text"]}" font-weight="700" style="font-size:18px">Aura Dark</text>')
    A(f'<rect x="{MX - 8}" y="{WY + 74}" width="{RIGHT - MX + 8}" height="46" rx="6" fill="{AU["hover"]}"/>')
    for i, (k, v) in enumerate((("type", "[[theme]]"), ("port-of", "[[Aura Dark]] by Vinay"))):
        A(tok_text(MX, WY + 93 + i * 19, [(k, AU["teal"]), (":: ", AU["punct"])] + rich(v, AU["content"]), f12))

    def bullet(y):
        return (f'<circle cx="{MX + 3}" cy="{y - 4}" r="5.5" fill="{AU["active"]}"/>'
                f'<circle cx="{MX + 3}" cy="{y - 4}" r="2.6" fill="{AU["secondary"]}"/>')

    y1, y2, y3 = WY + 146, WY + 172, WY + 198
    A(bullet(y1) + tok_text(TX, y1, rich("Deep purple UI for #logseq", AU["content"]), f12))
    A(bullet(y2))
    rest = rich(" Nerd Font glyphs bundled", AU["content"])
    for state, iv in intervals(S["todo"], P).items():
        o, a = tl.vis(iv)
        done = state == "DONE"
        box = (f'<rect x="{TX}" y="{y2 - 10}" width="12" height="12" rx="3" fill="{AU["purple"]}"/>'
               f'<path d="M{TX + 3} {y2 - 4}l2.2 2.2 4-4.6" fill="none" stroke="{AU["editor"]}" stroke-width="1.7" '
               f'stroke-linecap="round" stroke-linejoin="round"/>' if done else
               f'<rect x="{TX + .75}" y="{y2 - 9.25}" width="10.5" height="10.5" rx="3" fill="none" stroke="{AU["muted"]}" stroke-width="1.5"/>')
        word = [("DONE" if done else "TODO", AU["muted"] if done else AU["gold"], "b")]
        line = [(t[0], AU["muted"]) for t in rest] if done else rest
        strike = (f'<rect x="{TX + 20 + 5 * CW:.1f}" y="{y2 - 4}" width="{(width(rest) - 1) * CW:.1f}" height="1.2" '
                  f'fill="{AU["muted"]}"/>' if done else "")
        A(f'<g opacity="{o}">{a}{box}{tok_text(TX + 20, y2, word + line, f12)}{strike}</g>')
    A(bullet(y3) + tok_text(TX, y3, rich("Code as **window cards**:", AU["content"]), f12))
    cy0, cw_ = y3 + 12, RIGHT - TX
    A(f'<rect x="{TX}" y="{cy0}" width="{cw_}" height="76" rx="7" fill="{AU["chrome"]}" stroke="{AU["soft"]}"/>'
      f'<rect x="{TX}" y="{cy0 + 20}" width="{cw_}" height="1" fill="{AU["soft"]}"/>')
    for j, c in enumerate(("rose", "gold", "green")):
        A(f'<circle cx="{TX + 12 + j * 11}" cy="{cy0 + 10}" r="3.5" fill="{AU[c]}"/>')
    A(f'<text x="{TX + cw_ - 10}" y="{cy0 + 14}" fill="{AU["muted"]}" text-anchor="end" style="font-size:10px">css</text>')
    css_lines = [
        [(".dark-theme", AU["gold"]), (" {", AU["punct"])],
        [("  --ls-link-text-color", AU["peri"]), (": ", AU["punct"]), ("#c792ea", AU["peach"]), (";", AU["punct"])],
        [("}", AU["punct"])],
    ]
    for j, ln in enumerate(css_lines):
        A(tok_text(TX + 10, cy0 + 36 + j * 15, ln, ' style="font-size:11px"'))
    # typed block
    A(bullet(TYPE_Y))
    for k, toks in enumerate(phrases):
        ev = [(t, f"{w * CW:.1f}") for t, w in S["w"][k]]
        defs.append(f'<clipPath id="ty{k}"><rect x="{TX}" y="{TYPE_Y - 15}" height="20" width="{ev[0][1]}">'
                    f'{tl.disc("width", ev)}</rect></clipPath>')
        A(f'<g clip-path="url(#ty{k})">{tok_text(TX, TYPE_Y, toks, f12)}</g>')
    cx = [(t, f"{TX + c * CW:.1f}") for t, c in S["caret"]]
    A(f'<rect class="blink" x="{cx[0][1]}" y="{TYPE_Y - 12}" width="1.5" height="15" fill="{AU["purple_l"]}">'
      f'{tl.disc("x", cx)}</rect>')
    A(f'</g><rect x="{WX + .5}" y="{WY + .5}" width="{WW - 1}" height="{WH - 1}" rx="10" fill="none" '
      f'stroke="{AU["purple"]}" stroke-opacity=".55" stroke-width="1.5"/>')

    # ── bottom: colour system ──
    A(f'<rect y="{STRIP}" width="{W}" height="{H - STRIP}" fill="{AU["border"]}" opacity=".6"/>'
      f'<rect y="{STRIP}" width="{W}" height="1" fill="{AU["soft"]}"/>')
    my = STRIP + (H - STRIP) / 2
    A(f'<text x="{LX}" y="{my + 4}" fill="{AU["muted"]}" style="font-size:11px;letter-spacing:3px">PALETTE</text>')
    step = 1.1
    period = len(PALETTE) * step + 1.5
    a1, a2 = 100 * 0.15 / period, 100 * 0.9 / period
    css = [f"@keyframes hl{{0%{{opacity:0}}{a1:.2f}%,{a2:.2f}%{{opacity:1}}{a2 + a1:.2f}%,100%{{opacity:0}}}}",
           ".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"]
    x = LX + 106
    for i, (name, key) in enumerate(PALETTE):
        w = len(name) * 7.2 + 36
        css.append(f".h{i}{{opacity:0;animation:hl {period:.2f}s ease-in-out {i * step:.2f}s infinite}}")
        A(f'<rect x="{x:.1f}" y="{my - 14}" width="{w:.1f}" height="28" rx="6" fill="{AU["sidebar"]}" stroke="{AU["soft"]}"/>'
          f'<rect class="h{i}" x="{x:.1f}" y="{my - 14}" width="{w:.1f}" height="28" rx="6" fill="none" '
          f'stroke="{AU[key]}" stroke-width="1.5"/>'
          f'<rect x="{x + 9:.1f}" y="{my - 6}" width="12" height="12" rx="3" fill="{AU[key]}"/>'
          f'<text x="{x + 28:.1f}" y="{my + 4}" fill="{AU["content"]}"{f12}>{name}</text>')
        x += w + 8
    meta_txt = f'{meta["stars"]} · {meta["forks"]} forks'
    A(f'<text x="{W - LX}" y="{my + 4}" fill="{AU["secondary"]}" text-anchor="end"{f12}>{meta_txt}</text>')
    A(star(W - LX - len(meta_txt) * CW - 10, my, 6, AU["gold"]))

    A("</g>")
    A(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{AU["soft"]}"/>')
    out = "".join(body)
    return svg(W, H, f"{spec['repo']} — {spec['title']} {spec['subtitle']}",
               body_fonts(out) + "".join(css), "".join(defs), out)


def _icon(i: int, x: float, y: float) -> str:
    """Tiny line icons for the sidebar: journals, flashcards, graph, pages."""
    s = f'fill="none" stroke="{AU["icon"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"'
    shapes = [
        f'<rect x="{x}" y="{y + 1}" width="14" height="13" rx="2"/><path d="M{x} {y + 5}h14M{x + 4} {y - 1}v3M{x + 10} {y - 1}v3"/>',
        f'<rect x="{x + 3}" y="{y}" width="11" height="13" rx="2"/><path d="M{x} {y + 3}v9a2 2 0 0 0 2 2h7"/>',
        f'<circle cx="{x + 3}" cy="{y + 11}" r="2.2"/><circle cx="{x + 12}" cy="{y + 3}" r="2.2"/>'
        f'<circle cx="{x + 12}" cy="{y + 12}" r="2.2"/><path d="M{x + 5} {y + 10}l5-5M{x + 5} {y + 11}h5"/>',
        f'<path d="M{x} {y + 2}h14M{x} {y + 7}h14M{x} {y + 12}h9"/>',
    ]
    return f'<g {s}>{shapes[i]}</g>'
