#!/usr/bin/env python3
"""Harvest candidate search judgments from Claude Code transcripts.

Phase 0 of docs/SEARCH-QUALITY-PLAN.md. Read-only: walks the transcript
JSONL files, finds every `temoa search` run through Bash, and looks at what
the agent did next. Each search becomes one JSONL row listing the paths
Temoa returned and the vault paths the agent opened, cited, or saw in grep
output afterwards, with a suggested verdict per path. Rows are written with
`reviewed: false`; they are candidates, not judgments.

Suggested verdicts:
    used       returned by Temoa, then opened or cited
    missed     not returned, but cited, or surfaced by grep/find and then opened
    unopened   returned, never opened or cited (the description may have sufficed)
    context    not returned, opened without grep finding it (likely task context)
    grep_only  not returned, surfaced in grep/find output but never opened

Rows whose output was filtered through grep or python before printing are
marked `parse: loose`: their paths are what survived the filter, in printed
order, so ranks may not be Temoa's ranks.

Usage:
    uv run python scripts/harvest_transcripts.py > candidates.jsonl
    uv run python scripts/harvest_transcripts.py --window 8 -o candidates.jsonl
"""

import argparse
import json
import re
import shlex
import sys
from pathlib import Path

# Invoked, not quoted: preceded by start, whitespace, or a shell operator
SEARCH_RE = re.compile(r"(?:^|(?<=[\s;&|(]))temoa\s+search\b")
HEADER = "Search results for: "
RESULT_RE = re.compile(r"^(\d+)\. .*\n[ \t]+(\S.*?\.md)[ \t]*$", re.MULTILINE)
RELPATH_RE = re.compile(r'"relative_path":\s*("(?:[^"\\]|\\.)*")')
PERSISTED_RE = re.compile(r"Full output saved to: (\S.*?\.txt)")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
SEARCHY_RE = re.compile(r"(^|[\s|;&(])(grep|rg|ag|find|fd|ls)\s")
VALUE_OPTS = {"--limit", "-n", "--min-score", "-s", "--type", "-t",
              "--exclude-type", "-x", "--vault"}
STOP_TOKENS = {"|", "||", ";", "&&", "&", ">", ">>", "<", "2>", ">&", "(", ")"}


class Vault:
    """Known vault paths, for finding them inside arbitrary text."""

    def __init__(self, root):
        self.root = root
        self.paths = set()
        stems = {}
        for p in root.rglob("*.md"):
            rel = p.relative_to(root)
            if any(part.startswith(".") for part in rel.parts):
                continue
            rel = rel.as_posix()
            self.paths.add(rel)
            stems.setdefault(p.stem, []).append(rel)
        self.lengths = sorted({len(p) for p in self.paths}, reverse=True)
        self.by_stem = {s: ps[0] for s, ps in stems.items() if len(ps) == 1}

    def find(self, text):
        """Vault-relative paths mentioned in text, longest match per ending."""
        found = []
        start = 0
        while (i := text.find(".md", start)) != -1:
            end = i + 3
            start = end
            for n in self.lengths:
                if n > end:
                    continue
                cand = text[end - n:end]
                if cand in self.paths:
                    found.append(cand)
                    break
        return found

    def find_links(self, text):
        """Vault paths for [[wikilinks]] whose title is a unique note stem."""
        return [self.by_stem[t.strip()] for t in WIKILINK_RE.findall(text)
                if t.strip() in self.by_stem]


def result_text(block, record):
    """Text of a tool_result, following persisted-output pointers."""
    content = block.get("content")
    if isinstance(content, list):
        content = "\n".join(c.get("text", "") for c in content
                            if isinstance(c, dict))
    text = content or ""
    tur = record.get("toolUseResult")
    persisted = tur.get("persistedOutputPath") if isinstance(tur, dict) else None
    if not persisted and (m := PERSISTED_RE.search(text)):
        persisted = m.group(1)
    if persisted and Path(persisted).exists():
        text = Path(persisted).read_text(errors="replace")
    return text


def load_events(path):
    """Ordered tool calls and assistant text from one transcript."""
    events = []
    calls = {}
    for line in path.open(errors="replace"):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") not in ("assistant", "user"):
            continue
        content = (rec.get("message") or {}).get("content")
        if isinstance(content, str):
            if rec["type"] == "user":
                events.append({"kind": "prompt"})
            continue
        if not isinstance(content, list):
            continue
        for b in content:
            kind = b.get("type")
            if kind == "tool_use" and b.get("id") not in calls:
                call = {"kind": "call", "id": b["id"], "name": b.get("name"),
                        "input": b.get("input") or {}, "result": "",
                        "timestamp": rec.get("timestamp"), "cwd": rec.get("cwd")}
                calls[b["id"]] = call
                events.append(call)
            elif kind == "tool_result" and b.get("tool_use_id") in calls:
                calls[b["tool_use_id"]]["result"] = result_text(b, rec)
            elif kind == "text" and rec["type"] == "assistant":
                events.append({"kind": "text", "text": b.get("text", "")})
            elif kind == "text" and rec["type"] == "user":
                events.append({"kind": "prompt"})
    return events


def command_queries(command):
    """(query, flags) for each `temoa search` in a shell command."""
    out = []
    for m in SEARCH_RE.finditer(command):
        lex = shlex.shlex(command[m.end():], posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        query, flags, skip = None, [], False
        try:
            for tok in lex:
                if tok in STOP_TOKENS:
                    break
                if skip:
                    skip = False
                elif tok.startswith("-"):
                    flags.append(tok)
                    skip = tok in VALUE_OPTS
                elif query is None:
                    query = tok
        except ValueError:
            pass
        out.append((query, flags))
    return out


def parse_text_output(text):
    """Text-mode sections: [(query, mode, [paths])], plus leftover output."""
    sections, leftover = [], []
    parts = text.split(HEADER)
    leftover.append(parts[0])
    for part in parts[1:]:
        header, _, body = part.partition("\n")
        mode = None
        if (m := re.match(r"(.*) \((\w+)\)$", header)):
            header, mode = m.group(1), m.group(2)
        # The result block ends at the first unindented line that isn't "N. title"
        lines = body.split("\n")
        end = len(lines)
        for i, ln in enumerate(lines):
            if ln and not ln[0].isspace() and not re.match(r"\d+\. ", ln) \
                    and ln != "No results found.":
                end = i
                break
        block = "\n".join(lines[:end])
        leftover.append("\n".join(lines[end:]))
        paths = [p for _, p in RESULT_RE.findall(block)]
        sections.append((header.strip(), mode, paths))
    return sections, "\n".join(leftover)


def parse_json_output(text):
    """JSON-mode output: [(query, mode, [paths])], tolerant of truncation."""
    decoder = json.JSONDecoder()
    sections = []
    for m in re.finditer(r"^\{", text, re.MULTILINE):
        try:
            obj, _ = decoder.raw_decode(text, m.start())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "results" in obj:
            sections.append((obj.get("query"), obj.get("search_mode"),
                             [r.get("relative_path") for r in obj["results"]]))
    if not sections and '"relative_path"' in text:
        paths = [json.loads(s) for s in RELPATH_RE.findall(text)]
        sections.append((None, None, paths))
    return sections


def harvest_transcript(path, vault, window):
    events = load_events(path)
    rows = []
    for idx, ev in enumerate(events):
        if ev["kind"] != "call" or ev["name"] != "Bash":
            continue
        command = ev["input"].get("command", "")
        if not SEARCH_RE.search(command):
            continue
        queries = command_queries(command)
        text = ev["result"]
        parse = "full"
        sections, leftover = parse_text_output(text)
        if not sections:
            sections, leftover = parse_json_output(text), ""
        if not sections and len(queries) == 1:
            # Output filtered through grep/python: take what survived
            parse = "loose"
            paths = [p for _, p in RESULT_RE.findall(text)] or vault.find(text)
            if paths:
                sections = [(None, None, list(dict.fromkeys(paths)))]

        # Paths the same command's grep/find printed alongside the search
        same_call_grep = set()
        if SEARCHY_RE.search(command):
            same_call_grep = set(vault.find(leftover))

        # Following tool calls, up to the window or the next search
        opened, cited, surfaced = set(), set(), set(same_call_grep)
        n = 0
        in_turn = True
        for later in events[idx + 1:]:
            if later["kind"] == "prompt":
                in_turn = False
                if n >= window:
                    break
                continue
            if later["kind"] == "text":
                if in_turn:
                    cited.update(vault.find(later["text"]))
                    cited.update(vault.find_links(later["text"]))
                continue
            later_cmd = later["input"].get("command", "")
            if later["name"] == "Bash" and SEARCH_RE.search(later_cmd):
                break
            n += 1
            if n > window:
                if not in_turn:
                    break
                continue
            opened.update(vault.find(json.dumps(later["input"], ensure_ascii=False)))
            if later["name"] in ("Grep", "Glob") or \
                    (later["name"] == "Bash" and SEARCHY_RE.search(later_cmd)):
                surfaced.update(vault.find(later["result"]))

        for i, (query, mode, returned) in enumerate(sections):
            cmd_query, flags = queries[i] if i < len(queries) else (None, [])
            returned = [p for p in returned if p]
            candidates = []
            for rank, p in enumerate(returned, 1):
                hit = p in opened or p in cited
                candidates.append({"path": p, "rank": rank,
                                   "opened": p in opened, "cited": p in cited,
                                   "grep": p in surfaced,
                                   "suggested": "used" if hit else "unopened"})
            for p in sorted((opened | cited | surfaced) - set(returned)):
                if p in cited or (p in opened and p in surfaced):
                    suggested = "missed"
                elif p in opened:
                    suggested = "context"
                else:
                    suggested = "grep_only"
                candidates.append({"path": p, "rank": None,
                                   "opened": p in opened, "cited": p in cited,
                                   "grep": p in surfaced,
                                   "suggested": suggested})
            rows.append({
                "search_id": f"{path.stem}:{ev['id']}:{i}",
                "session": path.stem,
                "transcript": str(path),
                "timestamp": ev["timestamp"],
                "cwd": ev["cwd"],
                "query": query or cmd_query,
                "mode": mode or ("hybrid" if "--hybrid" in flags else
                                 "bm25" if "--bm25-only" in flags else None),
                "flags": flags,
                "command": command,
                "window": window,
                "parse": parse,
                "candidates": candidates,
                "reviewed": False,
            })
        if not sections:
            for query, flags in queries:
                rows.append({
                    "search_id": f"{path.stem}:{ev['id']}:none",
                    "session": path.stem, "transcript": str(path),
                    "timestamp": ev["timestamp"], "cwd": ev["cwd"],
                    "query": query, "mode": None, "flags": flags,
                    "command": command, "window": window,
                    "candidates": [], "error": text[:500], "reviewed": False,
                })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--projects-dir", type=Path,
                    default=Path("~/.claude/projects").expanduser())
    ap.add_argument("--vault", type=Path,
                    default=Path("~/Obsidian/amoxtli").expanduser())
    ap.add_argument("--window", type=int, default=5,
                    help="tool calls after each search to inspect (default: 5)")
    ap.add_argument("-o", "--output", type=Path,
                    help="write JSONL here instead of stdout")
    args = ap.parse_args()

    vault = Vault(args.vault.expanduser())
    transcripts = [p for p in sorted(args.projects_dir.rglob("*.jsonl"))
                   if "tool-results" not in p.parts]

    rows = []
    for t in transcripts:
        # Cheap prefilter: most transcripts never mention temoa
        with t.open(errors="replace") as fh:
            if not any("temoa search" in line for line in fh):
                continue
        rows.extend(harvest_transcript(t, vault, args.window))
    rows.sort(key=lambda r: r["timestamp"] or "")

    out = args.output.open("w") if args.output else sys.stdout
    for r in rows:
        out.write(json.dumps(r, ensure_ascii=False) + "\n")
    if args.output:
        out.close()

    counts = {}
    for r in rows:
        for c in r["candidates"]:
            counts[c["suggested"]] = counts.get(c["suggested"], 0) + 1
    sessions = len({r["session"] for r in rows})
    print(f"{len(rows)} searches in {sessions} transcripts "
          f"({len(transcripts)} scanned); candidates: "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())),
          file=sys.stderr)


if __name__ == "__main__":
    main()
