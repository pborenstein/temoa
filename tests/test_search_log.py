"""Tests for SearchLog — SQLite-backed query log."""

import asyncio
import json
from pathlib import Path

import pytest

from temoa.search_log import SearchLog


@pytest.fixture
def log_path(tmp_path):
    return tmp_path / "search_log.db"


@pytest.fixture
def search_log(log_path):
    return SearchLog(log_path)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_init_creates_db(log_path, search_log):
    run(search_log.init())
    assert log_path.exists()


def test_log_search_basic(search_log):
    run(search_log.init())
    run(search_log.log_search(
        query="semantic search",
        vault="amoxtli",
        mode="hybrid",
        limit=10,
        rerank=True,
        expand_query=False,
        retrieval_ms=250,
        total_ms=310,
        results=[
            {"relative_path": "Reference/article.md", "rrf_score": 0.82},
            {"relative_path": "L/note.md", "rrf_score": 0.71},
        ],
    ))
    rows = run(search_log.recent(10))
    assert len(rows) == 1
    row = rows[0]
    assert row["query"] == "semantic search"
    assert row["vault"] == "amoxtli"
    assert row["mode"] == "hybrid"
    assert row["result_count"] == 2
    assert abs(row["top_score"] - 0.82) < 0.001
    assert row["retrieval_ms"] == 250
    assert row["rerank"] == 1
    assert row["expand_query"] == 0


def test_results_json_stored(search_log):
    run(search_log.init())
    run(search_log.log_search(
        query="test",
        results=[{"relative_path": "foo.md", "similarity_score": 0.5}],
    ))
    rows = run(search_log.recent(1))
    stored = json.loads(rows[0]["results"])
    assert stored == [{"path": "foo.md", "score": 0.5}]


def test_get_stats_empty(search_log):
    run(search_log.init())
    stats = run(search_log.get_stats())
    assert stats["total_searches"] == 0
    assert stats["by_mode"] == {}


def test_get_stats_with_data(search_log):
    run(search_log.init())
    run(search_log.log_search(query="q1", mode="semantic", total_ms=100, retrieval_ms=80))
    run(search_log.log_search(query="q2", mode="hybrid", total_ms=200, retrieval_ms=150))
    stats = run(search_log.get_stats())
    assert stats["total_searches"] == 2
    assert stats["by_mode"]["semantic"] == 1
    assert stats["by_mode"]["hybrid"] == 1
    assert stats["timing"]["avg_total_ms"] == 150


def test_pipeline_stages_stored(search_log):
    run(search_log.init())
    stages = [{"stage": "rerank", "before_count": 30, "after_count": 10, "elapsed_ms": 45.2}]
    run(search_log.log_search(query="q", pipeline_stages=stages))
    rows = run(search_log.recent(1))
    stored = json.loads(rows[0]["pipeline_stages"])
    assert stored[0]["stage"] == "rerank"


def test_error_logged(search_log):
    run(search_log.init())
    run(search_log.log_search(query="bad", error="timeout"))
    rows = run(search_log.recent(1))
    assert rows[0]["error"] == "timeout"


def test_init_idempotent(log_path, search_log):
    run(search_log.init())
    run(search_log.init())  # second init must not fail
    assert log_path.exists()
