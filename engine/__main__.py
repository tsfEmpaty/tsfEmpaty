"""python -m engine build [--only nvim,badges] [--no-readme] [--offline]"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tomllib
from functools import partial
from pathlib import Path

from . import stats
from .cards import algorithms, aura, badges, divider, nvim

ROOT = Path(__file__).resolve().parent.parent
CARDS = {                                                 # order = order in README
    "div_profile": partial(divider.render, num=1, title="profile"),
    "badges": badges.render,
    "nvim": nvim.render,
    "div_projects": partial(divider.render, num=2, title="projects"),
    "algorithms": algorithms.render,
    "aura": aura.render,
}
NEEDS_STATS = {"algorithms", "aura"}


def load_config() -> dict:
    with open(ROOT / "config" / "profile.toml", "rb") as f:
        return tomllib.load(f)


def refresh_readme(cfg: dict, rendered: dict[str, str]) -> None:
    """Replace what sits between <!-- ENGINE:NAME:START/END --> markers; prose stays untouched."""
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    user = cfg.get("github_user", "").strip()
    for name, content in rendered.items():
        h = hashlib.sha1(content.encode()).hexdigest()[:10]
        src = (f"https://raw.githubusercontent.com/{user}/{user}/main/assets/{name}.svg?v={h}"
               if user else f"./assets/{name}.svg")
        alt = (cfg["name"] if name == "nvim" else cfg[name]["repo"] if name in NEEDS_STATS
               else name.removeprefix("div_"))
        img = f"<img src=\"{src}\" alt=\"{alt}\" width=\"100%\"/>"
        if name in NEEDS_STATS:                       # project cards open their repo
            img = f"<a href=\"https://github.com/{cfg[name]['repo']}\">{img}</a>"
        block = (f"<!-- ENGINE:{name.upper()}:START -->\n<p align=\"center\">\n"
                 f"  {img}\n</p>\n<!-- ENGINE:{name.upper()}:END -->")
        pat = re.compile(rf"<!-- ENGINE:{name.upper()}:START -->.*?<!-- ENGINE:{name.upper()}:END -->", re.S)
        if pat.search(text):
            text = pat.sub(lambda _: block, text)
        else:
            print(f"  ! в README нет меток ENGINE:{name.upper()} — блок пропущен")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(prog="engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="render cards and refresh README")
    b.add_argument("--only", default="", help="comma list of cards, e.g. nvim")
    b.add_argument("--no-readme", action="store_true")
    b.add_argument("--offline", action="store_true", help="no GitHub API: use assets/stats.json")
    args = ap.parse_args()

    cfg = load_config()
    only = [c for c in args.only.split(",") if c] or list(CARDS)
    unknown = [c for c in only if c not in CARDS]
    if unknown:
        print(f"unknown card: {', '.join(unknown)}  (есть: {', '.join(CARDS)})")
        return 2
    if NEEDS_STATS & set(only):
        cfg["stats"] = stats.load(cfg, offline=args.offline)
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    rendered = {}
    for name in only:
        svg = CARDS[name](cfg)
        (out / f"{name}.svg").write_text(svg, encoding="utf-8")
        rendered[name] = svg
        print(f"  ✓ assets/{name}.svg  {len(svg)//1024} KB")
    if not args.no_readme:
        refresh_readme(cfg, rendered)
        print("  ✓ README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
