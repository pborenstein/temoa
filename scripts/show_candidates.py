#!/usr/bin/env python3
"""Print harvested candidate judgments, one block per search.

Usage:
    uv run python scripts/show_candidates.py                 # every search
    uv run python scripts/show_candidates.py Josiah 1095     # queries starting with these
    uv run python scripts/show_candidates.py --all           # include grep_only candidates
    uv run python scripts/show_candidates.py -f other.jsonl
"""

import argparse
import json
from pathlib import Path

DEFAULT = Path("~/Obsidian/amoxtli/.temoa/candidates.jsonl").expanduser()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("prefixes", nargs="*", help="only queries starting with these")
    ap.add_argument("-f", "--file", type=Path, default=DEFAULT)
    ap.add_argument("--all", action="store_true", help="include grep_only candidates")
    args = ap.parse_args()

    prefixes = tuple(args.prefixes)
    for line in args.file.open():
        r = json.loads(line)
        if prefixes and not (r["query"] or "").startswith(prefixes):
            continue
        print(f"== {r['query']}  [{r['timestamp'][:10]} {r['mode']} {r.get('parse', '-')}]")
        if "error" in r:
            print("  (no results parsed)")
        for c in r["candidates"]:
            if c["suggested"] == "grep_only" and not args.all:
                continue
            print(f'  {c["suggested"]:9} {str(c["rank"] or "-"):3} '
                  f'o={int(c["opened"])} c={int(c["cited"])} g={int(c["grep"])} {c["path"]}')


if __name__ == "__main__":
    main()
