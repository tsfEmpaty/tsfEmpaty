"""python -m engine build [--only nvim,badges] [--no-readme]"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tomllib
from pathlib import Path

from .cards import badges, nvim

ROOT = Path(__file__).resolve().parent.parent
CARDS = {"badges": badges.render, "nvim": nvim.render}   # order = order in README


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
        alt = cfg["name"] if name == "nvim" else name
        block = (f"<!-- ENGINE:{name.upper()}:START -->\n<p align=\"center\">\n"
                 f"  <img src=\"{src}\" alt=\"{alt}\" width=\"100%\"/>\n</p>\n<!-- ENGINE:{name.upper()}:END -->")
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
    args = ap.parse_args()

    cfg = load_config()
    only = [c for c in args.only.split(",") if c] or list(CARDS)
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    rendered = {}
    for name in only:
        if name not in CARDS:
            print(f"unknown card: {name}  (есть: {', '.join(CARDS)})")
            return 2
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
