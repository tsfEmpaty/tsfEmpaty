"""Algorithms repo as a LeetCode-style card.

Left: solved ring (easy / medium / hard) and per-source chips — live numbers from stats.
Right: the code editor "submits" the showcase solutions in turn: lines appear,
Submit is pressed, Pending → Judging → Accepted with the solution's own complexity note.
The loop starts and ends on the first problem already accepted, so t=0 is a full frame.
"""
from __future__ import annotations

import math
import re

from ..kit import Timeline, body_fonts, esc, intervals, star, svg, tok_text

W = 1000
LC = dict(
    bg="#1a1a1a", panel="#262626", head="#303030", border="#3a3a3a", track="#3a3a3a",
    fg="#eff1f6", fg2="#9da3ae", dim="#62666d", orange="#ffa116", green="#2cbb5d",
    easy="#00b8a3", medium="#ffc01e", hard="#ff375f", other="#5c6370",
)
SYN = dict(kw="#c586c0", ctl="#569cd6", fn="#dcdcaa", builtin="#4ec9b0", str="#ce9178",
           num="#b5cea8", cmt="#6a9955", fg="#d4d4d4", pun="#d4d4d4")
DIFF_LABEL = dict(easy="Easy", medium="Med.", hard="Hard")

# layout
PY, PH = 64, 350
LX, LW = 16, 392
RX, RW = 420, 564
H = PY + PH + 16
CFS, CLH = 12.5, 18.5            # code font size / line height
CODE_Y = PY + 98                 # baseline of the first code line
GUT_X, CODE_X = RX + 34, RX + 46
RES_Y = PY + PH - 62             # top of the result strip
N_VIS = int((RES_Y - 8 - (CODE_Y - 14)) // CLH)   # code lines that fit above it

KW = {"def", "class", "return", "lambda", "yield", "import", "from", "as", "pass", "global", "nonlocal"}
CTL = {"if", "elif", "else", "for", "while", "in", "not", "and", "or", "is", "break", "continue",
       "try", "except", "finally", "with", "None", "True", "False"}
BUILTIN = {"len", "range", "abs", "max", "min", "sum", "sorted", "enumerate", "zip", "list", "dict",
           "set", "int", "str", "float", "print", "self"}
TOKEN = re.compile(r"(#.*)|('[^']*'|\"[^\"]*\")|(\b\d+\b)|([A-Za-z_]\w*)|(\s+)|(.)")


def highlight(line: str) -> list[tuple]:
    """A tiny Python highlighter: comments, strings, numbers, keywords, calls."""
    out: list[tuple] = []
    for m in TOKEN.finditer(line):
        cmt, s, num, word, ws, other = m.groups()
        if cmt:
            col = SYN["cmt"]
        elif s:
            col = SYN["str"]
        elif num:
            col = SYN["num"]
        elif word:
            nxt = line[m.end():m.end() + 1]
            col = (SYN["kw"] if word in KW else SYN["ctl"] if word in CTL else
                   SYN["builtin"] if word in BUILTIN else SYN["fn"] if nxt == "(" else SYN["fg"])
        else:
            col = SYN["fg"] if ws else SYN["pun"]
        text = m.group()
        if out and out[-1][1] == col:
            out[-1] = (out[-1][0] + text, col)
        else:
            out.append((text, col))
    return out


def schedule(n: int, code_lens: list[int]):
    """Problems are shown in order 0 (accepted at t=0), 1, …, n-1, 0 again — seamless loop."""
    S = dict(prob=[(0, 0)], res=[(0, "accepted")], press=[(0, 0)], bar=[(0, 0)],
             lines={k: [] for k in range(n)})
    S["lines"][0].append([0, None])                # problem 0 fully written at t=0
    t = 2.6
    for k in list(range(1, n)) + [0]:
        prev = (k - 1) % n
        for iv in S["lines"][prev]:
            if iv[1] is None:
                iv[1] = t
        S["prob"].append((t, k))
        S["res"].append((t, "idle"))
        t += 0.4
        S["lines"][k].append([t, None])            # lines reveal one by one from here
        S.setdefault("reveal", {})[k] = t
        t += code_lens[k] * 0.16 + 0.7
        S["press"] += [(t, 1), (t + 0.22, 0)]
        t += 0.25
        S["res"].append((t, "pending"))
        t += 0.6
        S["res"].append((t, "judging"))
        for step in range(1, 11):
            S["bar"].append((t + step * 0.12, step / 10))
        t += 1.35
        S["res"].append((t, "accepted"))
        S["bar"].append((t, 0))
        t += 3.6 if k else 1.0                     # last hold is short: it continues into t=0's hold
    P = round(t, 2)
    return S, P


def render(cfg) -> str:
    st = cfg["stats"]["algorithms"]
    spec = cfg["algorithms"]
    meta = cfg["stats"]["repos"][spec["repo"]]
    probs = st["showcase"]
    if not probs:
        raise SystemExit("algorithms.showcase пуст — нечего показывать")
    n = len(probs)
    for p in probs:
        p["code"] = p["code"][:N_VIS]
    n_lines = max(len(p["code"]) for p in probs)
    S, P = schedule(n, [len(p["code"]) for p in probs])
    tl = Timeline(P)
    body, defs = [], []
    A = body.append

    A(f'<rect width="{W}" height="{H}" rx="14" fill="{LC["bg"]}"/>')

    # ── top bar ──
    A(f'<rect x="20" y="15" width="24" height="24" rx="6" fill="{LC["orange"]}"/>'
      f'<path d="M29 22l-4 5 4 5M35 22l4 5-4 5" fill="none" stroke="{LC["bg"]}" stroke-width="2.2" '
      f'stroke-linecap="round" stroke-linejoin="round"/>')
    owner, name = spec["repo"].split("/")
    A(tok_text(56, 33, [(owner, LC["fg2"]), (" / ", LC["dim"]), (name, LC["fg"], "b")],
               ' style="font-size:17px"'))
    A(f'<text x="{56 + (len(owner) + len(name) + 3) * 17 * 0.6 + 14:.0f}" y="32" fill="{LC["dim"]}" '
      f'style="font-size:12px">{esc(spec.get("tagline", ""))}</text>')
    meta_txt = " · ".join(x for x in (meta["language"], meta["license"]) if x and x != "NOASSERTION")
    A(f'<text x="{W - 24}" y="32" fill="{LC["fg2"]}" text-anchor="end" style="font-size:13px">'
      f'{meta["stars"]} · {esc(meta_txt)}</text>')
    sx = W - 24 - (len(meta_txt) + 3 + len(str(meta["stars"]))) * 13 * 0.6 - 10
    A(star(sx, 27, 7, LC["medium"]))

    # ── left panel: solved ring + sources ──
    A(f'<rect x="{LX}" y="{PY}" width="{LW}" height="{PH}" rx="10" fill="{LC["panel"]}"/>')
    A(f'<text x="{LX + 20}" y="{PY + 30}" fill="{LC["fg2"]}" style="font-size:13px">Solved problems</text>')
    total = st["total"]
    by = st["by_diff"]
    parts = [(by[d], LC[d]) for d in ("easy", "medium", "hard")]
    other = total - sum(by.values())
    if other > 0:
        parts.append((other, LC["other"]))
    rcx, rcy, r = LX + 96, PY + 130, 60
    circ = 2 * math.pi * r
    A(f'<circle cx="{rcx}" cy="{rcy}" r="{r}" fill="none" stroke="{LC["track"]}" stroke-width="7"/>')
    acc, gapl = 0.0, 5.0
    for cnt, col in parts:
        if not cnt:
            continue
        seg = circ * cnt / max(total, 1)
        L = max(seg - gapl, 1)
        A(f'<circle cx="{rcx}" cy="{rcy}" r="{r}" fill="none" stroke="{col}" stroke-width="7" '
          f'stroke-linecap="round" stroke-dasharray="{L:.1f} {circ:.1f}" stroke-dashoffset="{-acc:.1f}" '
          f'transform="rotate(-90 {rcx} {rcy})">'
          f'<animate attributeName="stroke-dasharray" values="0 {circ:.1f};{L:.1f} {circ:.1f}" dur="1.4s" '
          f'begin="0s" fill="freeze" calcMode="spline" keySplines=".2 .7 .3 1"/></circle>')
        acc += seg
    A(f'<text x="{rcx}" y="{rcy + 6}" fill="{LC["fg"]}" font-weight="700" text-anchor="middle" '
      f'style="font-size:34px">{total}</text>')
    A(f'<text x="{rcx}" y="{rcy + 26}" fill="{LC["fg2"]}" text-anchor="middle" style="font-size:12px">solved</text>')
    bx, bw = LX + 196, 172
    top = max(by.values()) or 1
    for i, d in enumerate(("easy", "medium", "hard")):
        y = PY + 82 + i * 48
        A(f'<text x="{bx}" y="{y}" fill="{LC[d]}" style="font-size:13px">{DIFF_LABEL[d] if d != "medium" else "Medium"}</text>')
        A(f'<text x="{bx + bw}" y="{y}" fill="{LC["fg"]}" font-weight="700" text-anchor="end" '
          f'style="font-size:13px">{by[d]}</text>')
        A(f'<rect x="{bx}" y="{y + 9}" width="{bw}" height="5" rx="2.5" fill="{LC["track"]}"/>')
        w = bw * by[d] / top
        if w:
            A(f'<rect x="{bx}" y="{y + 9}" width="{w:.1f}" height="5" rx="2.5" fill="{LC[d]}">'
              f'<animate attributeName="width" values="0;{w:.1f}" dur="1.2s" begin="0s" fill="freeze" '
              f'calcMode="spline" keySplines=".2 .7 .3 1"/></rect>')
    A(f'<rect x="{LX + 20}" y="{PY + 222}" width="{LW - 40}" height="1" fill="{LC["border"]}"/>')
    A(f'<text x="{LX + 20}" y="{PY + 246}" fill="{LC["fg2"]}" style="font-size:12px">Sources</text>')
    cx0, cx, cy = LX + 20, LX + 20, PY + 258
    for src, label in spec["sources"].items():
        cnt = st["by_source"].get(src, 0)
        val = str(cnt) if cnt else "soon"
        w = (len(label) + 1 + len(val)) * 12 * 0.6 + 20
        if cx + w > LX + LW - 16:
            cx, cy = cx0, cy + 30
        A(f'<rect x="{cx:.1f}" y="{cy}" width="{w:.1f}" height="24" rx="12" fill="{LC["head"]}"/>')
        A(tok_text(cx + 10, cy + 16, [(label + " ", LC["fg"] if cnt else LC["fg2"]),
                                      (val, LC["orange"] if cnt else LC["dim"], "b" if cnt else "")],
                   ' style="font-size:12px"'))
        cx += w + 8

    # ── right panel: editor ──
    A(f'<rect x="{RX}" y="{PY}" width="{RW}" height="{PH}" rx="10" fill="{LC["panel"]}"/>')
    defs.append(f'<clipPath id="ph"><rect x="{RX}" y="{PY}" width="{RW}" height="38" rx="10"/></clipPath>')
    A(f'<g clip-path="url(#ph)"><rect x="{RX}" y="{PY}" width="{RW}" height="38" fill="{LC["head"]}"/></g>')
    A(f'<rect x="{RX}" y="{PY + 37}" width="{RW}" height="1" fill="{LC["border"]}"/>')
    A(tok_text(RX + 16, PY + 24, [("</>", LC["green"], "b"), ("  Code", LC["fg"], "b")], ' style="font-size:13px"'))
    A(f'<text x="{RX + 112}" y="{PY + 24}" fill="{LC["dim"]}" style="font-size:13px">Python3</text>')
    # Run / Submit buttons
    A(f'<rect x="{RX + RW - 176}" y="{PY + 7}" width="70" height="24" rx="6" fill="{LC["border"]}"/>'
      f'<text x="{RX + RW - 141}" y="{PY + 23}" fill="{LC["fg"]}" text-anchor="middle" style="font-size:12px">Run</text>')
    press = [(t, LC["green"] if not v else "#1f8a43") for t, v in S["press"]]
    A(f'<rect x="{RX + RW - 98}" y="{PY + 7}" width="84" height="24" rx="6" fill="{LC["green"]}">'
      f'{tl.disc("fill", press)}</rect>'
      f'<text x="{RX + RW - 56}" y="{PY + 23}" fill="#fff" font-weight="700" text-anchor="middle" '
      f'style="font-size:12px">Submit</text>')

    prob_iv = intervals(S["prob"], P)
    for k, p in enumerate(probs):
        o, a = tl.vis(prob_iv.get(k, []))
        dl = DIFF_LABEL[p["difficulty"]]
        title_w = len(f"{k + 1}. {p['name']}") * 14 * 0.6
        pill = (f'<rect x="{RX + 16 + title_w + 12:.1f}" y="{PY + 50}" width="{len(dl) * 7.2 + 18:.1f}" height="20" '
                f'rx="10" fill="{LC[p["difficulty"]]}" fill-opacity=".16"/>'
                f'<text x="{RX + 16 + title_w + 21:.1f}" y="{PY + 64}" fill="{LC[p["difficulty"]]}" '
                f'style="font-size:12px">{dl}</text>')
        A(f'<g opacity="{o}">{a}<text x="{RX + 16}" y="{PY + 65}" fill="{LC["fg"]}" font-weight="700" '
          f'style="font-size:14px">{k + 1}. {esc(p["name"])}</text>{pill}</g>')

    # gutter
    for i in range(n_lines):
        A(f'<text x="{GUT_X}" y="{CODE_Y + i * CLH:.1f}" fill="{LC["dim"]}" text-anchor="end" '
          f'style="font-size:{CFS}px">{i + 1}</text>')
    defs.append(f'<clipPath id="code"><rect x="{CODE_X - 2}" y="{PY + 40}" width="{RX + RW - CODE_X - 12}" '
                f'height="{RES_Y - PY - 44}"/></clipPath>')
    code = []
    for k, p in enumerate(probs):
        start = S["reveal"][k]
        for i, line in enumerate(p["code"]):
            if not line.strip():
                continue
            # the t=0 block is already written; every other one reveals line by line
            ivs = [(a_ if a_ == 0 else start + i * 0.16, P + 1 if b_ is None else b_)
                   for a_, b_ in S["lines"][k]]
            o, a = tl.vis(ivs)
            code.append(f'<g opacity="{o}">{a}{tok_text(CODE_X, CODE_Y + i * CLH, highlight(line), f" style=\"font-size:{CFS}px\"")}</g>')
    A(f'<g clip-path="url(#code)">{"".join(code)}</g>')

    # result strip
    A(f'<rect x="{RX}" y="{RES_Y}" width="{RW}" height="1" fill="{LC["border"]}"/>')
    res = intervals(S["res"], P)
    ry = RES_Y + 38
    o, a = tl.vis(res.get("idle", []))
    A(f'<text x="{RX + 16}" y="{ry}" fill="{LC["dim"]}" opacity="{o}" style="font-size:13px">'
      f'Writing solution…{a}</text>')
    o, a = tl.vis(res.get("pending", []))
    A(f'<text x="{RX + 16}" y="{ry}" fill="{LC["fg2"]}" opacity="{o}" style="font-size:14px">Pending…{a}</text>')
    o, a = tl.vis(res.get("judging", []))
    bar = [(t, f"{200 * v:.0f}") for t, v in S["bar"]]
    A(f'<g opacity="{o}">{a}<text x="{RX + 16}" y="{ry}" fill="{LC["medium"]}" style="font-size:14px">Judging</text>'
      f'<rect x="{RX + 104}" y="{ry - 8}" width="200" height="6" rx="3" fill="{LC["track"]}"/>'
      f'<rect x="{RX + 104}" y="{ry - 8}" width="0" height="6" rx="3" fill="{LC["medium"]}">{tl.disc("width", bar)}</rect></g>')
    acc_iv = res.get("accepted", [])
    o, a = tl.vis(acc_iv)
    A(f'<g opacity="{o}">{a}<text x="{RX + 16}" y="{ry + 1}" fill="{LC["green"]}" font-weight="700" '
      f'style="font-size:18px">Accepted</text></g>')
    # complexity boxes: problem k's note, during its accepted window
    for k, p in enumerate(probs):
        note = p["complexity"] or "O(?) time | O(?) space"
        tm, sp = (s.strip().rsplit(" ", 1)[0] for s in note.split("|")) if "|" in note else (note, "")
        mine = _overlap(acc_iv, prob_iv.get(k, []))
        o, a = tl.vis(mine)
        boxes = []
        for j, (lab, val) in enumerate((("Time", tm), ("Space", sp))):
            x = RX + 196 + j * 182
            boxes.append(f'<rect x="{x}" y="{RES_Y + 14}" width="170" height="36" rx="8" fill="{LC["head"]}"/>'
                         f'<text x="{x + 12}" y="{RES_Y + 37}" fill="{LC["fg2"]}" style="font-size:12px">{lab}</text>'
                         f'<text x="{x + 158}" y="{RES_Y + 38}" fill="{LC["fg"]}" font-weight="700" text-anchor="end" '
                         f'style="font-size:14px">{esc(val)}</text>')
        A(f'<g opacity="{o}">{a}{"".join(boxes)}</g>')

    A(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{LC["border"]}"/>')
    out = "".join(body)
    return svg(W, H, f"{spec['repo']} — {total} solved", body_fonts(out), "".join(defs), out)


def _overlap(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(max(x0, y0), min(x1, y1)) for x0, x1 in a for y0, y1 in b if max(x0, y0) < min(x1, y1)]
