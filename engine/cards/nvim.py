"""The header card: a Neovim session that edits profile.py forever.

Loop (one segment per `now` phrase):
  cursor travels to the `now` line (j-presses, /search or NG — alternating),
  ci" wipes the old phrase, INSERT types the next one, Esc, :w, :!python %,
  and the terminal split on the right reprints the neofetch-style profile.
After the last phrase the file is back in its first state, so the loop is seamless.
"""
from __future__ import annotations

import random

from ..kit import CW, FS, PAL, Timeline, esc, font_css, missing_glyphs, svg

W = 1000
LH = 22
TOP = 34            # bufferline height
PAD = 12            # gap under the bufferline
LEFT_W = 596        # editor pane width
GUT_NUM_X = 46      # right edge of line numbers
CODE_X = 62
TERM_X = LEFT_W + 22
TERM_COLS = int((W - TERM_X - 14) // CW)
LABEL_COLS = 9

C = PAL
KW, STR, TYPE, ATTR, PUN, DEC, FUN, CMT, NUM = (
    C["magenta"], C["green"], C["type"], C["teal"], C["punct"], C["yellow"], C["blue"], C["comment"], C["orange"])


# ── the python file ─────────────────────────────────────────────────────────
def build_code(cfg) -> tuple[list[list[tuple]], int, int]:
    """Lines of (text, colour[, 'b'|'i']) tokens, index of the `now` line, column of its phrase."""
    L: list[list[tuple]] = []
    L.append([("# profile.py · this file edits itself", CMT, "i")])
    L.append([("from", KW), (" dataclasses ", C["fg"]), ("import", KW), (" dataclass", C["fg"])])
    L.append([])
    L.append([])
    L.append([("@dataclass", DEC), ("(", PUN), ("frozen", C["fg"]), ("=", PUN), ("True", NUM), (")", PUN)])
    L.append([("class", KW), (" Engineer", TYPE), (":", PUN)])

    def field(name, typ, value_tokens):
        return [("    ", C["fg"]), (name, ATTR), (": ", PUN), (typ, TYPE), (" = ", PUN)] + value_tokens

    s = lambda v: [('"', STR), (v, STR), ('"', STR)]
    L.append(field("name", "str", s(cfg["name"])))
    L.append(field("grade", "str", s(cfg["grade"])))
    L.append(field("role", "str", s(cfg["role"])))
    L.append(field("stack", "tuple", [("(", PUN)]))
    items = [i for g in cfg["stack"] for i in g["items"]]
    line: list[tuple] = [("        ", C["fg"])]
    width = 8
    max_cols = int((LEFT_W - CODE_X - 10) // CW)
    for it in items:
        piece = len(it) + 4  # "it", + space
        if width + piece > max_cols and width > 8:
            L.append(line)
            line, width = [("        ", C["fg"])], 8
        line += [(f'"{it}"', STR), (", ", PUN)]
        width += piece
    L.append(line)
    L.append([("    ", C["fg"]), (")", PUN)])
    L.append(field("focus", "str", s(cfg["focus"])))
    now_idx = len(L)
    L.append(field("now", "str", [('"', STR)]))        # phrase + closing quote are animated
    qcol = len("    now: str = \"")
    L.append([])
    L.append([])
    L.append([("if", KW), (" __name__ ", C["fg"]), ("==", PUN), (' "__main__"', STR), (":", PUN)])
    L.append([("    Engineer", TYPE), ("().", PUN), ("neofetch", FUN), ("()", PUN)])
    return L, now_idx, qcol


def wrap(words: list[str], width: int, sep=" · ") -> list[str]:
    lines, cur = [], ""
    for w in words:
        cand = w if not cur else cur + sep + w
        if len(cand) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


# ── the neofetch output ─────────────────────────────────────────────────────
def build_output(cfg) -> tuple[list[dict], dict[str, list[dict]]]:
    """Static output rows and, per phrase, the rows of the `now` entry."""
    vw = TERM_COLS - LABEL_COLS
    rows: list[dict] = [
        dict(kind="name", text=cfg["name"].upper()),
        dict(kind="text", parts=[(f'{cfg["grade"]} · {cfg["role"]}', C["magenta"], "b")]),
        dict(kind="rule"),
    ]
    for g in cfg["stack"]:
        for k, chunk in enumerate(wrap(g["items"], vw)):
            rows.append(dict(kind="text", parts=[((g["label"] if k == 0 else "").ljust(LABEL_COLS), C["cyan"], "b"),
                                                 (chunk, C["fg"], "")]))
    for k, chunk in enumerate(wrap(cfg["focus"].split(), vw, " ")):
        rows.append(dict(kind="text", parts=[(("focus" if k == 0 else "").ljust(LABEL_COLS), C["cyan"], "b"),
                                             (chunk, C["fg"], "")]))
    now_rows = {}
    for q in cfg["now"]:
        parts = wrap(q.split(), vw, " ")
        now_rows[q] = [dict(kind="text", parts=[(("now" if k == 0 else "").ljust(LABEL_COLS), C["yellow"], "b"),
                                                (chunk, C["green"], "")]) for k, chunk in enumerate(parts)]
    return rows, now_rows


# ── schedule ────────────────────────────────────────────────────────────────
def schedule(cfg, now_idx: int, qcol: int, n_out: int):
    """Walk the loop once and record every state change as (time, value) lists."""
    rnd = random.Random(7)
    quotes = cfg["now"]
    N = len(quotes)
    S = dict(mode=[(0, "NORMAL")], cmd=[(0, "")], showcmd=[(0, "")], mod=[(0, False)],
             cur=[(0, (0, 0, "block"))], quote={q: [] for q in quotes}, close=[(0, qcol + len(quotes[0]))],
             runs=[], qwin={q: [] for q in quotes})
    S["quote"][quotes[0]].append((0, len(quotes[0])))
    shown_q, shown_from = quotes[0], 0.0
    t = 0.0
    navs = ["j", "search", "G"]
    for i in range(N):
        old, new = quotes[i], quotes[(i + 1) % N]
        t += 0.6
        nav = navs[i % 3]
        if nav == "j":
            for ln in range(1, now_idx + 1):
                t += 0.07
                S["cur"].append((t, (ln, 0, "block")))
        elif nav == "search":
            S["mode"].append((t, "COMMAND"))
            for k, s in enumerate(["/", "/n", "/no", "/now"]):
                S["cmd"].append((t + k * 0.13, s))
            t += 4 * 0.13 + 0.2
            S["mode"].append((t, "NORMAL"))
            S["cur"].append((t, (now_idx, 4, "block")))
        else:
            num = str(now_idx + 1)
            keys = [num[:k] for k in range(1, len(num) + 1)]
            for k, s in enumerate(keys):
                S["showcmd"].append((t + k * 0.13, s))
            t += len(keys) * 0.13 + 0.1
            S["showcmd"].append((t, ""))
            S["cur"].append((t, (now_idx, 4, "block")))
        t += 0.45
        for k, s in enumerate(["c", "ci", 'ci"']):
            S["showcmd"].append((t + k * 0.12, s))
        t += 0.4
        S["showcmd"].append((t, ""))
        S["quote"][old].append((t, 0))
        S["close"].append((t, qcol))
        S["mode"].append((t, "INSERT"))
        S["cmd"].append((t, "-- INSERT --"))
        S["cur"].append((t, (now_idx, qcol, "bar")))
        S["mod"].append((t, True))
        t += 0.3
        for k in range(1, len(new) + 1):
            t += (0.11 if new[k - 1] == " " else 0.055) * rnd.uniform(0.6, 1.5)
            S["quote"][new].append((t, k))
            S["close"].append((t, qcol + k))
            S["cur"].append((t, (now_idx, qcol + k, "bar")))
        t += 0.45
        S["mode"].append((t, "NORMAL"))
        S["cmd"].append((t, ""))
        S["cur"].append((t, (now_idx, qcol + len(new) - 1, "block")))
        t += 0.6
        S["mode"].append((t, "COMMAND"))
        S["cmd"] += [(t, ":"), (t + 0.15, ":w")]
        t += 0.45
        S["mode"].append((t, "NORMAL"))
        S["cmd"].append((t, '"profile.py" written'))
        S["mod"].append((t, False))
        t += 0.7
        S["mode"].append((t, "COMMAND"))
        cmdline = ":!python %"
        for k in range(1, len(cmdline) + 1):
            S["cmd"].append((t, cmdline[:k]))
            t += 0.06
        t += 0.25
        S["mode"].append((t, "NORMAL"))
        S["runs"].append(t)
        # the `now` rows of the terminal swap at the moment their slot is reprinted
        S["qwin"][shown_q].append((shown_from, t))
        shown_q, shown_from = new, t + 0.3 + (n_out + 0.5) * 0.045
        t += 0.3 + (n_out + 2) * 0.045 + 2.6
        S["showcmd"] += [(t, "g"), (t + 0.12, "gg")]
        t += 0.24
        S["showcmd"].append((t, ""))
        S["cmd"].append((t, ""))
        S["cur"].append((t, (0, 0, "block")))
        t += 0.3
    P = round(t, 2)
    S["qwin"][shown_q].append((shown_from, P + 1))
    return S, P


def intervals(changes: list[tuple[float, object]], P: float) -> dict:
    """[(t, value)] state changes → {value: [(start, end), ...]}."""
    ch = sorted(changes, key=lambda c: c[0])
    out: dict = {}
    for k, (t, v) in enumerate(ch):
        end = ch[k + 1][0] if k + 1 < len(ch) else P + 1
        if end > t:
            out.setdefault(v, []).append((t, end))
    return out


# ── render ──────────────────────────────────────────────────────────────────
def tok_text(x, y, tokens, extra=""):
    spans = []
    for tok in tokens:
        text, col = tok[0], tok[1]
        style = tok[2] if len(tok) > 2 else ""
        a = ' font-weight="700"' if "b" in style else ""
        a += ' font-style="italic"' if "i" in style else ""
        spans.append(f'<tspan fill="{col}"{a}>{esc(text)}</tspan>')
    return f'<text x="{x:.1f}" y="{y:.1f}"{extra}>{"".join(spans)}</text>'


def render(cfg) -> str:
    code, now_idx, qcol = build_code(cfg)
    out_rows, now_rows = build_output(cfg)
    n_now = max(len(r) for r in now_rows.values())
    n_out = len(out_rows) + n_now + 3
    S, P = schedule(cfg, now_idx, qcol, n_out)
    tl = Timeline(P)

    for q in cfg["now"]:
        if qcol + len(q) + 1 > (LEFT_W - CODE_X) / CW:
            raise SystemExit(f"now-фраза слишком длинная для редактора: {q!r}")

    term_rows_n = 4 + n_out + 1
    rows = max(len(code), term_rows_n) + 1
    ed_top = TOP + PAD
    base = lambda i: ed_top + i * LH + 16
    st_y = ed_top + rows * LH + 4
    cmd_y = st_y + 26
    H = cmd_y + 30

    body, defs = [], []
    A = body.append

    # frame
    defs.append(f'<clipPath id="win"><rect width="{W}" height="{H}" rx="14"/></clipPath>')
    A(f'<g clip-path="url(#win)"><rect width="{W}" height="{H}" fill="{C["bg"]}"/>')

    # bufferline
    A(f'<rect width="{W}" height="{TOP}" fill="{C["bg_dark"]}"/>')
    A(f'<rect x="0" y="0" width="190" height="{TOP}" fill="{C["bg"]}"/>'
      f'<rect x="0" y="{TOP-2}" width="190" height="2" fill="{C["blue"]}"/>')
    A(f'<rect x="16" y="11" width="11" height="11" rx="3" fill="{C["blue"]}"/>'
      f'<rect x="21" y="16" width="11" height="11" rx="3" fill="{C["yellow"]}"/>')
    A(f'<text x="42" y="22" fill="{C["fg"]}" font-weight="700">profile.py</text>')
    oi, os_ = tl.vis(intervals(S["mod"], P).get(True, []))
    A(f'<circle cx="168" cy="17" r="4" fill="{C["orange"]}" opacity="{oi}">{os_}</circle>')
    A(f'<text x="174" y="22" fill="{C["comment"]}" opacity="{1 - int(oi)}">×'
      f'{tl.disc("opacity", [(t, 0 if v else 1) for t, v in S["mod"]])}</text>')
    A(f'<text x="212" y="22" fill="{C["comment"]}">profile.toml</text>')
    A(f'<text x="{W-18}" y="22" fill="{C["comment"]}" text-anchor="end">NVIM v0.11</text>')

    # split + right winbar
    A(f'<rect x="{LEFT_W}" y="{TOP}" width="1" height="{st_y-TOP}" fill="{C["border"]}"/>')

    # cursorline + cursor (behind text)
    cur_ev = S["cur"]
    ys = [(t, f"{ed_top + c[0]*LH:.0f}") for t, c in cur_ev]
    A(f'<rect x="0" y="{ed_top}" width="{LEFT_W}" height="{LH}" fill="{C["bg_hl"]}">{tl.disc("y", ys)}</rect>')
    xs = [(t, f"{CODE_X + c[1]*CW:.1f}") for t, c in cur_ev]
    ws = [(t, f"{CW:.1f}" if c[2] == "block" else "2") for t, c in cur_ev]
    cy = [(t, f"{ed_top + c[0]*LH + 2:.0f}") for t, c in cur_ev]
    cursor = (f'<rect x="{CODE_X}" y="{ed_top+2}" width="{CW:.1f}" height="{LH-4}" fill="{C["fg"]}" opacity=".8">'
              f'{tl.disc("x", xs)}{tl.disc("y", cy)}{tl.disc("width", ws)}</rect>')
    A(cursor)

    # gutter: line numbers (current one brighter) + git signs
    for i in range(len(code)):
        A(f'<text x="{GUT_NUM_X}" y="{base(i)}" fill="{C["gutter"]}" text-anchor="end">{i+1}</text>')
    cur_lines = intervals([(t, c[0]) for t, c in cur_ev], P)
    for ln, iv in cur_lines.items():
        o, a = tl.vis(iv)
        A(f'<text x="{GUT_NUM_X}" y="{base(ln)}" fill="{C["yellow"]}" font-weight="700" text-anchor="end" '
          f'opacity="{o}">{ln+1}{a}</text>')
    A(f'<rect x="6" y="{ed_top + now_idx*LH + 3}" width="3" height="{LH-6}" fill="{C["yellow"]}"/>')
    stack_lines = [i for i, l in enumerate(code) if l and l[0][0] == "        "]
    for i in stack_lines[-1:]:
        A(f'<rect x="6" y="{ed_top + i*LH + 3}" width="3" height="{LH-6}" fill="{C["green"]}"/>')

    # code
    for i, toks in enumerate(code):
        if toks:
            A(tok_text(CODE_X, base(i), toks))
    # animated phrase + closing quote on the `now` line
    qx = CODE_X + qcol * CW
    for k, q in enumerate(cfg["now"]):
        ev = [(0, 0)] + S["quote"][q]
        ev = [(t, f"{w*CW:.1f}") for t, w in ev]
        w0 = ev[-1][1] if False else (f"{len(q)*CW:.1f}" if q == cfg["now"][0] else "0")
        cid = f"q{k}"
        defs.append(f'<clipPath id="{cid}"><rect x="{qx:.1f}" y="{ed_top}" height="{rows*LH}" width="{w0}">'
                    f'{tl.disc("width", [(0, w0)] + [e for e in ev if e[0] > 0])}</rect></clipPath>')
        A(f'<text x="{qx:.1f}" y="{base(now_idx)}" fill="{STR}" clip-path="url(#{cid})">{esc(q)}</text>')
    cx = [(t, f"{CODE_X + c*CW:.1f}") for t, c in S["close"]]
    A(f'<text x="{cx[0][1]}" y="{base(now_idx)}" fill="{STR}">"{tl.disc("x", cx)}</text>')

    # ── terminal pane ──
    A(f'<text x="{TERM_X}" y="{base(0)}" fill="{C["comment"]}" font-style="italic">term://~/profile//zsh</text>')
    A(tok_text(TERM_X, base(2), [("~/profile", C["blue"], "b"), (" $ ", C["magenta"], "b"),
                                  ("python profile.py", C["fg"])]))
    runs = S["runs"]

    def out_vis(k):
        """visibility of output row k: hidden from each run until its print time"""
        hide = [(r, r + 0.3 + k * 0.045) for r in runs]
        iv, start = [], 0.0
        for a, b in hide:
            iv.append((start, a))
            start = b
        iv.append((start, P + 1))
        return tl.vis(iv)

    r0 = 4
    k = 0
    for row in out_rows:
        o, a = out_vis(k)
        y = base(r0 + k)
        if row["kind"] == "name":
            A(f'<text x="{TERM_X}" y="{y+2}" fill="{C["blue"]}" font-weight="700" '
              f'style="font-size:{FS+5}px;letter-spacing:1px" opacity="{o}">{esc(row["text"])}{a}</text>')
        elif row["kind"] == "rule":
            A(f'<rect x="{TERM_X}" y="{y-6}" width="{(TERM_COLS-4)*CW:.0f}" height="2" fill="{C["border"]}" '
              f'opacity="{o}">{a}</rect>')
        else:
            A(f'<g opacity="{o}">{a}{tok_text(TERM_X, y, row["parts"])}</g>')
        k += 1
    # now rows: their own row-print visibility AND which phrase is current
    for q, qrows in now_rows.items():
        wins = S["qwin"][q]
        for j, row in enumerate(qrows):
            o, a = tl.vis(wins)
            A(f'<g opacity="{o}">{a}{tok_text(TERM_X, base(r0 + k + j), row["parts"])}</g>')
    k += n_now + 1
    o, a = out_vis(k)
    palette = [C["red"], C["orange"], C["yellow"], C["green"], C["teal"], C["cyan"], C["blue"], C["magenta"]]
    blocks = "".join(f'<rect x="{TERM_X + i*30}" y="{base(r0+k)-14}" width="26" height="16" rx="2" fill="{c}"/>'
                     for i, c in enumerate(palette))
    A(f'<g opacity="{o}">{a}{blocks}</g>')
    k += 2
    o, a = out_vis(k)
    A(f'<g opacity="{o}">{a}{tok_text(TERM_X, base(r0+k), [("~/profile", C["blue"], "b"), (" $ ", C["magenta"], "b")])}'
      f'<rect class="blink" x="{TERM_X + 12*CW:.1f}" y="{base(r0+k)-13}" width="{CW:.1f}" height="17" fill="{C["fg"]}"/></g>')

    # ── statusline ──
    A(f'<rect x="0" y="{st_y}" width="{W}" height="26" fill="{C["bg_dark"]}"/>')
    mode_col = {"NORMAL": C["blue"], "INSERT": C["green"], "COMMAND": C["yellow"]}
    fills = [(t, mode_col[m]) for t, m in S["mode"]]
    A(f'<rect x="0" y="{st_y}" width="96" height="26" fill="{C["blue"]}">{tl.disc("fill", fills)}</rect>')
    for m, iv in intervals(S["mode"], P).items():
        o, a = tl.vis(iv)
        A(f'<text x="48" y="{st_y+18}" fill="{C["bg_dark"]}" font-weight="700" text-anchor="middle" '
          f'opacity="{o}">{m}{a}</text>')
    A(f'<rect x="96" y="{st_y}" width="92" height="26" fill="{C["bg_hl"]}"/>')
    bx, by = 112, st_y + 6
    A(f'<g fill="none" stroke="{C["magenta"]}" stroke-width="1.6"><circle cx="{bx}" cy="{by+2}" r="2"/>'
      f'<circle cx="{bx}" cy="{by+12}" r="2"/><circle cx="{bx+8}" cy="{by+4}" r="2"/>'
      f'<path d="M{bx} {by+4}v6M{bx+8} {by+6}q0 4 -8 5"/></g>')
    A(f'<text x="128" y="{st_y+18}" fill="{C["magenta"]}">main</text>')
    A(f'<text x="204" y="{st_y+18}" fill="{C["fg"]}">profile.py</text>')
    oi, os_ = tl.vis(intervals(S["mod"], P).get(True, []))
    A(f'<text x="{204 + 11*CW:.0f}" y="{st_y+18}" fill="{C["orange"]}" opacity="{oi}">[+]{os_}</text>')
    A(f'<text x="{W-112}" y="{st_y+18}" fill="{C["comment"]}" text-anchor="end">utf-8 · python</text>')
    A(f'<rect x="{W-100}" y="{st_y}" width="100" height="26" fill="{C["blue"]}">{tl.disc("fill", fills)}</rect>')
    locs = intervals([(t, f"{c[0]+1}:{c[1]+1}") for t, c in cur_ev], P)
    for s, iv in locs.items():
        o, a = tl.vis(iv)
        A(f'<text x="{W-50}" y="{st_y+18}" fill="{C["bg_dark"]}" font-weight="700" text-anchor="middle" '
          f'opacity="{o}">{s}{a}</text>')

    # ── cmdline + showcmd ──
    for s, iv in intervals(S["cmd"], P).items():
        if not s:
            continue
        o, a = tl.vis(iv)
        col = C["fg"] if not s.startswith("-- ") else C["green"]
        weight = ' font-weight="700"' if s.startswith("-- ") else ""
        A(f'<text x="12" y="{cmd_y+19}" fill="{col}"{weight} opacity="{o}">{esc(s)}{a}</text>')
    for s, iv in intervals(S["showcmd"], P).items():
        if not s:
            continue
        o, a = tl.vis(iv)
        A(f'<text x="{W-150}" y="{cmd_y+19}" fill="{C["fg_dark"]}" opacity="{o}">{esc(s)}{a}</text>')

    A("</g>")
    A(f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="14" fill="none" stroke="{C["border"]}"/>')

    all_text = "".join(body) + "×·"
    css = font_css(_plain(all_text), faces=((400, "normal"), (700, "normal"), (400, "italic")))
    css += ".blink{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
    miss = missing_glyphs(_plain(all_text))
    if miss:
        print(f"  ! нет в шрифте: {''.join(sorted(miss))}")
    return svg(W, H, f'{cfg["name"]} — {cfg["grade"]} {cfg["role"]}', css, "".join(defs), "".join(body))


def _plain(markup: str) -> str:
    """Characters that actually end up as text (rough: strip tags)."""
    import re
    import html
    return html.unescape(re.sub(r"<[^>]+>", "", markup))
