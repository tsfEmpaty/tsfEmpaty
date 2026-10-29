"""Live numbers for the project cards, pulled from the GitHub API at build time.

The last good snapshot lives in assets/stats.json (committed): an offline build,
or an API hiccup in CI, falls back to it instead of failing or drawing zeros.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
CACHE = Path(__file__).resolve().parent.parent / "assets" / "stats.json"
DIFFICULTIES = ("easy", "medium", "hard")
CODE_LINES = 12          # how much of a solution the card can show


def _get(url: str):
    headers = {"User-Agent": "profile-engine", "Accept": "application/vnd.github+json"}
    if tok := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {tok}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
        data = r.read().decode()
    return data if url.startswith(RAW) else json.loads(data)


def _repo(repo: str) -> dict:
    m = _get(f"{API}/repos/{repo}")
    return dict(stars=m["stargazers_count"], forks=m["forks_count"], language=m["language"] or "",
                license=(m.get("license") or {}).get("spdx_id") or "", branch=m["default_branch"])


def _title(dirname: str) -> str:
    """LongestPeak → Longest Peak, Depth-firstSearch → Depth-first Search."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", dirname)


def _solution(repo: str, branch: str, path: str) -> tuple[str, list[str]]:
    """(complexity note, code lines) — leading comments/blank lines dropped, `# O(...)` kept as the note."""
    lines = _get(f"{RAW}/{repo}/{branch}/{path}").expandtabs(4).splitlines()
    note = ""
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("#")):
        head = lines.pop(0).strip()
        if not note and head.startswith("# O("):
            note = head[2:].split(" - ")[0]
    return note, lines[:CODE_LINES]


def _algorithms(spec: dict, meta: dict) -> dict:
    repo, branch = spec["repo"], meta["branch"]
    tree = _get(f"{API}/repos/{repo}/git/trees/{branch}?recursive=1")["tree"]
    # a problem = a folder <source>/.../<Problem>/ that holds at least one .py file
    problems: dict[str, list[str]] = {}
    for e in tree:
        parts = e["path"].split("/")
        if e["type"] == "blob" and parts[-1].endswith(".py") and len(parts) >= 3:
            problems.setdefault("/".join(parts[:-1]), []).append(e["path"])
    by_diff = dict.fromkeys(DIFFICULTIES, 0)
    by_source = dict.fromkeys(spec["sources"], 0)
    for p in problems:
        parts = p.split("/")
        diff = next((d for d in parts if d in DIFFICULTIES), None)
        if diff:
            by_diff[diff] += 1
        by_source[parts[0]] = by_source.get(parts[0], 0) + 1
    showcase = []
    for p in spec["showcase"]:
        if p not in problems:
            print(f"  ! showcase: в {repo} нет {p} — пропущено")
            continue
        note, code = _solution(repo, branch, sorted(problems[p])[0])
        diff = next((d for d in p.split("/") if d in DIFFICULTIES), "easy")
        showcase.append(dict(path=p, name=_title(p.rsplit("/", 1)[-1]), difficulty=diff,
                             complexity=note, code=code))
    return dict(total=len(problems), by_diff=by_diff, by_source=by_source, showcase=showcase)


def fetch(cfg: dict) -> dict:
    repos = {cfg[k]["repo"]: _repo(cfg[k]["repo"]) for k in ("algorithms", "aura")}
    algo = cfg["algorithms"]
    return dict(repos=repos, algorithms=_algorithms(algo, repos[algo["repo"]]))


def load(cfg: dict, offline: bool = False) -> dict:
    """Fresh stats (and refresh the cache), or the cached snapshot when offline / the API fails."""
    if not offline:
        try:
            stats = fetch(cfg)
            CACHE.parent.mkdir(exist_ok=True)
            CACHE.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return stats
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
            print(f"  ! GitHub API: {e} — беру {CACHE.name}")
    if not CACHE.exists():
        raise SystemExit(f"нет {CACHE} — первую сборку нужно сделать с доступом к GitHub API")
    return json.loads(CACHE.read_text(encoding="utf-8"))
