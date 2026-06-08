"""Persistent search query log backed by SQLite.

Logs every search request: query, mode, params, timing, and top results
(path + score only — no content). Used to compare result quality before
and after algorithm changes.
"""

from __future__ import annotations

import json
import logging
import statistics
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS searches (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp     TEXT NOT NULL,
  query         TEXT NOT NULL,
  vault         TEXT,
  mode          TEXT,
  "limit"       INTEGER,
  rerank        INTEGER,
  expand_query  INTEGER,
  retrieval_ms  INTEGER,
  total_ms      INTEGER,
  result_count  INTEGER,
  top_score     REAL,
  score_p50     REAL,
  results       TEXT,
  pipeline_stages TEXT,
  error         TEXT
);
CREATE INDEX IF NOT EXISTS idx_timestamp ON searches(timestamp);
CREATE INDEX IF NOT EXISTS idx_vault     ON searches(vault, timestamp);
"""


def _final_score(result: dict) -> Optional[float]:
    """Pick the most-derived score available for a result."""
    for key in ("cross_encoder_score", "rrf_score", "similarity_score", "bm25_score"):
        v = result.get(key)
        if v is not None:
            return float(v)
    return None


class SearchLog:
    def __init__(self, path: Path):
        self.path = path

    @asynccontextmanager
    async def _conn(self):
        async with aiosqlite.connect(self.path) as conn:
            conn.row_factory = aiosqlite.Row
            yield conn
            await conn.commit()

    async def init(self) -> None:
        async with self._conn() as conn:
            await conn.executescript(_SCHEMA)
        logger.info(f"Search log initialized: {self.path}")

    async def log_search(
        self,
        *,
        query: str,
        vault: Optional[str] = None,
        mode: Optional[str] = None,
        limit: Optional[int] = None,
        rerank: bool = False,
        expand_query: bool = False,
        retrieval_ms: Optional[int] = None,
        total_ms: Optional[int] = None,
        results: list[dict] = (),
        pipeline_stages: Optional[list[dict]] = None,
        error: Optional[str] = None,
    ) -> None:
        scores = [s for r in results if (s := _final_score(r)) is not None]
        top_score = max(scores) if scores else None
        score_p50 = statistics.median(scores) if len(scores) >= 2 else None

        results_json = json.dumps([
            {"path": r.get("relative_path"), "score": _final_score(r)}
            for r in results
        ])

        async with self._conn() as conn:
            await conn.execute(
                """
                INSERT INTO searches
                  (timestamp, query, vault, mode, "limit", rerank, expand_query,
                   retrieval_ms, total_ms, result_count, top_score, score_p50,
                   results, pipeline_stages, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    query,
                    vault,
                    mode,
                    limit,
                    int(rerank),
                    int(expand_query),
                    retrieval_ms,
                    total_ms,
                    len(results),
                    top_score,
                    score_p50,
                    results_json,
                    json.dumps(pipeline_stages) if pipeline_stages else None,
                    error,
                ),
            )

    async def get_stats(self) -> dict[str, Any]:
        async with self._conn() as conn:
            row = await (await conn.execute(
                "SELECT COUNT(*) as total, MIN(timestamp) as first, MAX(timestamp) as last FROM searches WHERE error IS NULL"
            )).fetchone()
            total = row["total"]
            first = row["first"]
            last = row["last"]

            by_mode = {}
            async with conn.execute(
                "SELECT mode, COUNT(*) as n FROM searches WHERE error IS NULL GROUP BY mode"
            ) as cur:
                async for r in cur:
                    by_mode[r["mode"] or "unknown"] = r["n"]

            timing = {}
            t_row = await (await conn.execute(
                """SELECT
                     AVG(retrieval_ms) as avg_retrieval,
                     AVG(total_ms)     as avg_total
                   FROM searches WHERE error IS NULL AND total_ms IS NOT NULL"""
            )).fetchone()
            if t_row:
                timing = {
                    "avg_retrieval_ms": round(t_row["avg_retrieval"] or 0),
                    "avg_total_ms": round(t_row["avg_total"] or 0),
                }

        return {
            "total_searches": total,
            "date_range": {"first": first, "last": last},
            "by_mode": by_mode,
            "timing": timing,
        }

    async def recent(self, n: int = 20) -> list[dict[str, Any]]:
        """Return the n most recent searches as plain dicts."""
        async with self._conn() as conn:
            rows = await (await conn.execute(
                "SELECT * FROM searches ORDER BY id DESC LIMIT ?", (n,)
            )).fetchall()
        return [dict(r) for r in rows]
