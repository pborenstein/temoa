"""Tests for scripts/harvest_transcripts.py — Phase 0 transcript harvester."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "scripts" / "harvest_transcripts.py"
spec = importlib.util.spec_from_file_location("harvest_transcripts", SCRIPT)
harvest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harvest)


@pytest.fixture
def vault(tmp_path):
    root = tmp_path / "vault"
    for rel in ["Reference/Josiah seal.md", "Reference/Temple Scroll.md",
                "L/altar to siddur.md", "L/unrelated.md", "L/TIMELINE.md",
                ".obsidian/hidden.md"]:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("x")
    return harvest.Vault(root)


def call(tid, name, inp):
    return {"type": "assistant", "timestamp": "2026-10-22T00:00:00Z",
            "cwd": "/vault", "message": {"content": [
                {"type": "tool_use", "id": tid, "name": name, "input": inp}]}}


def result(tid, text):
    return {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": tid, "content": text}]}}


def text(t):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}


SEARCH_OUTPUT = """
Search results for: Josiah reform (hybrid)

1. The Temple Scroll
   Reference/Temple Scroll.md
   Semantic: 0.604 | BM25: 163.825
   Tags: second-temple

2. Josiah seal
   Reference/Josiah seal.md
   Semantic: 0.509 | BM25: 0.000
"""


def write_transcript(tmp_path, records):
    path = tmp_path / "session-1.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records))
    return path


def test_vault_skips_dot_dirs(vault):
    assert ".obsidian/hidden.md" not in vault.paths
    assert "L/altar to siddur.md" in vault.paths


def test_vault_find_prefers_longest_and_strips_prefix(vault):
    found = vault.find('cat "/Users/x/vault/L/altar to siddur.md"; ls Reference/Josiah seal.md')
    assert found == ["L/altar to siddur.md", "Reference/Josiah seal.md"]


def test_command_queries_skips_option_values():
    q = harvest.command_queries(
        'temoa search --limit 5 "Josiah reform" --vault ~/v --hybrid | head; grep x')
    assert q == [("Josiah reform", ["--limit", "--vault", "--hybrid"])]


def test_quoted_mention_is_not_a_search():
    assert not harvest.SEARCH_RE.search("grep -c 'temoa search' f.jsonl")
    assert harvest.SEARCH_RE.search("cd v && uv run temoa search q")


def test_harvest_labels_candidates(tmp_path, vault):
    records = [
        call("t1", "Bash", {"command": 'temoa search "Josiah reform" --hybrid'}),
        result("t1", SEARCH_OUTPUT),
        call("t2", "Bash", {"command": "grep -ril josiah L Reference"}),
        result("t2", "L/altar to siddur.md\nL/unrelated.md\nReference/Josiah seal.md"),
        call("t3", "Read", {"file_path": "/vault/Reference/Josiah seal.md"}),
        result("t3", "..."),
        call("t4", "Read", {"file_path": "/vault/L/altar to siddur.md"}),
        result("t4", "..."),
        call("t5", "Read", {"file_path": "/vault/L/TIMELINE.md"}),
        result("t5", "..."),
    ]
    rows = harvest.harvest_transcript(write_transcript(tmp_path, records), vault, 5)
    assert len(rows) == 1
    row = rows[0]
    assert row["query"] == "Josiah reform"
    assert row["mode"] == "hybrid"
    assert row["parse"] == "full"
    verdicts = {c["path"]: (c["rank"], c["suggested"]) for c in row["candidates"]}
    assert verdicts == {
        "Reference/Temple Scroll.md": (1, "unopened"),
        "Reference/Josiah seal.md": (2, "used"),
        "L/altar to siddur.md": (None, "missed"),
        "L/TIMELINE.md": (None, "context"),
        "L/unrelated.md": (None, "grep_only"),
    }


def test_window_stops_at_next_search(tmp_path, vault):
    records = [
        call("t1", "Bash", {"command": 'temoa search "a"'}),
        result("t1", SEARCH_OUTPUT),
        call("t2", "Bash", {"command": 'temoa search "b"'}),
        result("t2", SEARCH_OUTPUT),
        call("t3", "Read", {"file_path": "/vault/Reference/Josiah seal.md"}),
        result("t3", "..."),
    ]
    rows = harvest.harvest_transcript(write_transcript(tmp_path, records), vault, 5)
    first = {c["path"]: c["suggested"] for c in rows[0]["candidates"]}
    second = {c["path"]: c["suggested"] for c in rows[1]["candidates"]}
    assert first["Reference/Josiah seal.md"] == "unopened"
    assert second["Reference/Josiah seal.md"] == "used"


def test_citation_in_answer_counts(tmp_path, vault):
    records = [
        call("t1", "Bash", {"command": 'temoa search "a"'}),
        result("t1", SEARCH_OUTPUT),
        text("See [[Temple Scroll]] and [[altar to siddur]]."),
    ]
    rows = harvest.harvest_transcript(write_transcript(tmp_path, records), vault, 5)
    verdicts = {c["path"]: c["suggested"] for c in rows[0]["candidates"]}
    assert verdicts["Reference/Temple Scroll.md"] == "used"
    assert verdicts["L/altar to siddur.md"] == "missed"


def test_filtered_output_parses_loose(tmp_path, vault):
    records = [
        call("t1", "Bash", {"command": 'temoa search "a" --json | python3 -c "..."'}),
        result("t1", "0.5 Reference/Josiah seal.md | desc\n0.4 L/unrelated.md | desc"),
    ]
    rows = harvest.harvest_transcript(write_transcript(tmp_path, records), vault, 5)
    assert rows[0]["parse"] == "loose"
    assert [c["path"] for c in rows[0]["candidates"]] == [
        "Reference/Josiah seal.md", "L/unrelated.md"]
