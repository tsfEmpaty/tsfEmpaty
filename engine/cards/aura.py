"""Logseq Aura Dark theme as a card: a Logseq window painted in the theme itself.

Left sidebar, a page with properties and blocks, a code block styled as a window card,
the theme's colour system in the right sidebar. Alive: the last block is typed and
erased in a loop (Logseq markup: [[ref]], #tag, `code`, **bold**), a TODO flips to DONE,
the palette rows light up in turn. t=0 shows the first phrase written and the TODO done.
"""
from __future__ import annotations

import random
import re

from ..kit import Timeline, body_fonts, esc, intervals, svg, tok_text

W = 1000
AU = dict(
    editor="#1e1f29", sidebar="#1a1b24", chrome="#17181f", hover="#23242f", active="#2a2c37",
    border="#12131a", soft="#2a2c3a", text="#e0e0e0", content="#c8cbd8", secondary="#a6accd",
    muted="#6b7a99", faint="#3e4460", icon="#555870", purple="#c792ea", purple_l="#d4aaff",
    peri="#82aaff", green="#c3e88d", gold="#ffcb6b", amber="#ffd580", teal="#7fdbca",
    cyan="#89ddff", peach="#f78c6c", rose="#f07178", punct="#697098",
)
PALETTE = [("Purple", "purple", "#C792EA"), ("Periwinkle", "peri", "#82AAFF"), ("Mint Teal", "teal", "#7FDBCA"),
           ("Sage Green", "green", "#C3E88D"), ("Warm Gold", "gold", "#FFCB6B"), ("Amber", "amber", "#FFD580"),
           ("Slate", "muted", "#6B7A99")]

TB = 40                     # titlebar
SB = 200                    # left sidebar width
RS = W - 232                # right sidebar x
MX = SB + 34                # main column x
FSZ = 13
CW = FSZ * 0.6
TYPE_Y = 408                # baseline of the typed block, under the code card
H = TYPE_Y + 30

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
    if max(lens) > (RS - 28 - MX - 20) / CW:
        raise SystemExit(f"aura.typing: фраза длиннее {(RS - 28 - MX - 20) / CW:.0f} символов")
    S, P = schedule(lens)
    tl = Timeline(P)
    body, defs = [], []
    A = body.append
    f13 = f' style="font-size:{FSZ}px"'

    defs.append(f'<clipPath id="win"><rect width="{W}" height="{H}" rx="14"/></clipPath>')
    A(f'<g clip-path="url(#win)"><rect width="{W}" height="{H}" fill="{AU["editor"]}"/>')

    # ── titlebar ──
    A(f'<rect width="{W}" height="{TB}" fill="{AU["chrome"]}"/><rect y="{TB - 1}" width="{W}" height="1" fill="{AU["border"]}"/>')
    A(f'<g fill="none" stroke="{AU["icon"]}" stroke-width="1.6" stroke-linecap="round">'
      f'<rect x="18" y="13" width="16" height="14" rx="3"/><path d="M24 13v14"/>'
      f'<circle cx="{SB + 46}" cy="19" r="5"/><path d="M{SB + 50} 23l4 4"/></g>')
    A(f'<text x="{SB + 64}" y="24" fill="{AU["faint"]}"{f13}>Search or create page</text>')
    A(f'<rect x="{W - 186}" y="9" width="116" height="22" rx="11" fill="{AU["hover"]}"/>'
      f'<circle cx="{W - 172}" cy="20" r="4" fill="{AU["purple"]}"/>'
      f'<text x="{W - 162}" y="24" fill="{AU["secondary"]}" style="font-size:12px">Aura Dark</text>')
    for j, k in enumerate("ti"):
        x = W - 58 + j * 22
        A(f'<rect x="{x}" y="10" width="18" height="20" rx="4" fill="{AU["active"]}" stroke="{AU["soft"]}"/>'
          f'<text x="{x + 9}" y="24" fill="{AU["secondary"]}" text-anchor="middle" style="font-size:12px">{k}</text>')

    # ── left sidebar ──
    A(f'<rect y="{TB}" width="{SB}" height="{H - TB}" fill="{AU["sidebar"]}"/>'
      f'<rect x="{SB - 1}" y="{TB}" width="1" height="{H - TB}" fill="{AU["border"]}"/>')
    nav = ["Journals", "Flashcards", "Graph view", "All pages"]
    for i, item in enumerate(nav):
        y = TB + 32 + i * 30
        A(_icon(i, 22, y - 11))
        A(f'<text x="48" y="{y}" fill="{AU["secondary"]}"{f13}>{item}</text>')
    fy = TB + 32 + len(nav) * 30 + 14
    A(f'<text x="20" y="{fy}" fill="{AU["faint"]}" font-weight="700" style="font-size:10px;letter-spacing:1.5px">FAVORITES</text>')
    favs = ["aura-dark-theme", "custom.css", "Color system"]
    for i, item in enumerate(favs):
        y = fy + 28 + i * 28
        if i == 0:
            A(f'<rect x="10" y="{y - 18}" width="{SB - 20}" height="26" rx="6" fill="{AU["active"]}"/>')
        A(f'<text x="22" y="{y}" fill="{AU["faint"]}"{f13}>#</text>'
          f'<text x="38" y="{y}" fill="{AU["purple"] if i == 0 else AU["secondary"]}"{f13}>{esc(item)}</text>')
    A(f'<text x="20" y="{H - 18}" fill="{AU["faint"]}" style="font-size:11px">Hack Nerd Font Mono</text>')

    # ── page ──
    A(f'<text x="{MX}" y="{TB + 46}" fill="{AU["text"]}" font-weight="700" style="font-size:24px">{esc(spec["title"])}</text>')
    py = TB + 62
    A(f'<rect x="{MX - 8}" y="{py}" width="{RS - 28 - MX + 8}" height="72" rx="6" fill="{AU["hover"]}"/>')
    props = [("type", "[[theme]]"), ("port-of", "[[Aura Dark]] by Vinay"),
             ("works-with", "`--ls-*` `--lx-*` tokens")]
    for i, (k, v) in enumerate(props):
        A(tok_text(MX + 4, py + 21 + i * 21, [(k, AU["teal"]), (":: ", AU["punct"])] + rich(v, AU["content"]), f13))

    def bullet(y):
        return (f'<circle cx="{MX + 4}" cy="{y - 4.5}" r="6" fill="{AU["active"]}"/>'
                f'<circle cx="{MX + 4}" cy="{y - 4.5}" r="3" fill="{AU["secondary"]}"/>')

    tx = MX + 20
    y1, y2, y3 = py + 104, py + 132, py + 160
    A(bullet(y1) + tok_text(tx, y1, rich("Deep purple dark theme for #logseq, ported from [[VS Code]]", AU["content"]), f13))

    # TODO ↔ DONE
    A(bullet(y2))
    todo_iv = intervals(S["todo"], P)
    rest = rich(" UI, menus, page content and code blocks", AU["content"])
    for state, iv in todo_iv.items():
        o, a = tl.vis(iv)
        done = state == "DONE"
        box = (f'<rect x="{tx}" y="{y2 - 11}" width="13" height="13" rx="3" fill="{AU["purple"]}"/>'
               f'<path d="M{tx + 3} {y2 - 4.5}l2.5 2.5 4.5-5" fill="none" stroke="{AU["editor"]}" stroke-width="1.8" '
               f'stroke-linecap="round" stroke-linejoin="round"/>' if done else
               f'<rect x="{tx + .75}" y="{y2 - 10.25}" width="11.5" height="11.5" rx="3" fill="none" stroke="{AU["muted"]}" stroke-width="1.5"/>')
        word = [("DONE" if done else "TODO", AU["muted"] if done else AU["gold"], "b")]
        line = [(t[0], AU["muted"]) for t in rest] if done else rest
        strike = (f'<rect x="{tx + 22 + 5 * CW:.1f}" y="{y2 - 4.5}" width="{(width(rest) - 1) * CW:.1f}" height="1.2" '
                  f'fill="{AU["muted"]}"/>' if done else "")
        A(f'<g opacity="{o}">{a}{box}{tok_text(tx + 22, y2, word + line, f13)}{strike}</g>')

    A(bullet(y3) + tok_text(tx, y3, rich("Code blocks styled as **window cards**:", AU["content"]), f13))
    # code block card
    cy0, cw_ = y3 + 14, RS - 28 - tx
    A(f'<rect x="{tx}" y="{cy0}" width="{cw_}" height="104" rx="8" fill="{AU["chrome"]}" stroke="{AU["soft"]}"/>'
      f'<rect x="{tx}" y="{cy0 + 26}" width="{cw_}" height="1" fill="{AU["soft"]}"/>')
    for j, c in enumerate(("rose", "gold", "green")):
        A(f'<circle cx="{tx + 16 + j * 14}" cy="{cy0 + 13}" r="4.5" fill="{AU[c]}"/>')
    A(f'<text x="{tx + cw_ - 14}" y="{cy0 + 17}" fill="{AU["muted"]}" text-anchor="end" style="font-size:11px">css</text>')
    css_lines = [
        [(".dark-theme", AU["gold"]), (" {", AU["punct"])],
        [("  --ls-primary-background-color", AU["peri"]), (": ", AU["punct"]), ("#1e1f29", AU["peach"]), (";", AU["punct"])],
        [("  --ls-link-text-color", AU["peri"]), (": ", AU["punct"]), ("#c792ea", AU["peach"]), (";", AU["punct"])],
        [("}", AU["punct"])],
    ]
    for j, ln in enumerate(css_lines):
        A(tok_text(tx + 14, cy0 + 44 + j * 15.5, ln, ' style="font-size:12px"'))

    # typed block
    A(bullet(TYPE_Y))
    for k, toks in enumerate(phrases):
        ev = [(t, f"{w * CW:.1f}") for t, w in S["w"][k]]
        defs.append(f'<clipPath id="ty{k}"><rect x="{tx}" y="{TYPE_Y - 16}" height="22" width="{ev[0][1]}">'
                    f'{tl.disc("width", ev)}</rect></clipPath>')
        A(f'<g clip-path="url(#ty{k})">{tok_text(tx, TYPE_Y, toks, f13)}</g>')
    cx = [(t, f"{tx + c * CW:.1f}") for t, c in S["caret"]]
    A(f'<rect class="blink" x="{cx[0][1]}" y="{TYPE_Y - 13}" width="1.6" height="17" fill="{AU["purple_l"]}">'
      f'{tl.disc("x", cx)}</rect>')

    # ── right sidebar: colour system ──
    A(f'<rect x="{RS}" y="{TB}" width="{W - RS}" height="{H - TB}" fill="{AU["sidebar"]}"/>'
      f'<rect x="{RS}" y="{TB}" width="1" height="{H - TB}" fill="{AU["border"]}"/>')
    A(f'<text x="{RS + 20}" y="{TB + 32}" fill="{AU["muted"]}" font-weight="700" style="font-size:10px;letter-spacing:1.5px">COLOR SYSTEM</text>')
    step = 1.1
    period = len(PALETTE) * step + 1.5
    a1, a2 = 100 * 0.15 / period, 100 * 0.9 / period
    css = [f"@keyframes hl{{0%{{opacity:0}}{a1:.2f}%,{a2:.2f}%{{opacity:1}}{a2 + a1:.2f}%,100%{{opacity:0}}}}",
           ".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"]
    for i, (name, key, hexv) in enumerate(PALETTE):
        y = TB + 66 + i * 42
        css.append(f".h{i}{{opacity:0;animation:hl {period:.2f}s ease-in-out {i * step:.2f}s infinite}}")
        A(f'<rect class="h{i}" x="{RS + 10}" y="{y - 22}" width="{W - RS - 20}" height="36" rx="8" fill="{AU["active"]}"/>'
          f'<rect x="{RS + 20}" y="{y - 14}" width="20" height="20" rx="6" fill="{AU[key]}"/>'
          f'<text x="{RS + 52}" y="{y}" fill="{AU["content"]}"{f13}>{name}</text>'
          f'<text x="{W - 20}" y="{y}" fill="{AU["muted"]}" text-anchor="end" style="font-size:12px">{hexv}</text>')

    A("</g>")
    A(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{AU["soft"]}"/>')
    out = "".join(body)
    return svg(W, H, f"{spec['repo']} — {spec['title']}", body_fonts(out) + "".join(css), "".join(defs), out)


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
