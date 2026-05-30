"""Composable, swappable search pipeline.

This module provides the lightweight abstraction that lets search behaviors be
selected and composed. A mutable :class:`SearchContext` flows through an ordered
list of :class:`Stage` objects; the :class:`Pipeline` is just a ``for`` loop with
per-stage gating and optional debug capture.

It is intentionally minimal — no dependency-injection container, no plugin
registry, no class hierarchy — per the project's "avoid over-engineering"
principle (see ``CLAUDE.md``). Stages are plain objects implementing a one-method
``Protocol``.

Status / migration note
------------------------
This abstraction is introduced *alongside* the existing inline pipeline in
``server.search()``. It is not yet wired into the live endpoint. Rewiring
``server.search()`` to build and run a ``Pipeline`` is a follow-up (strangler-fig)
step that must be verified against the live server tests, which require a
configured vault + index + the cross-encoder model. The pure stages and helpers
here are unit-tested in ``tests/test_pipeline.py`` without those dependencies.

Score envelope
--------------
Scores are currently scattered across inconsistent top-level fields
(``similarity_score``, ``bm25_score``, ``rrf_score``, ``cross_encoder_score``,
``time_boost``). :func:`set_score` introduces a canonical ``result["scores"]``
dict **additively** — it writes both the canonical name and the legacy flat
field — so existing consumers (the ``search.html`` Explorer, ``time_scoring``,
``deduplicate_chunks``, the reranker) keep working unchanged while new code can
read the unified envelope via :func:`score_view`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable


# --------------------------------------------------------------------------- #
# Score envelope
# --------------------------------------------------------------------------- #

# Canonical score name -> legacy flat field name. Canonical names that have no
# legacy equivalent (e.g. "bm25_base") simply live in the envelope only.
SCORE_FLAT_ALIASES: dict[str, str] = {
    "semantic": "similarity_score",
    "bm25": "bm25_score",
    "rrf": "rrf_score",
    "cross_encoder": "cross_encoder_score",
    "time_boost": "time_boost",
    "final": "final_score",
}


def set_score(result: dict, name: str, value: Any) -> None:
    """Set a score on ``result`` both in the canonical envelope and, where one
    exists, the legacy flat field.

    Writing both keeps the abstraction strangler-safe: nothing that reads the
    old flat names breaks the day the envelope is introduced.
    """
    scores = result.setdefault("scores", {})
    scores[name] = value
    flat = SCORE_FLAT_ALIASES.get(name)
    if flat is not None:
        result[flat] = value


def score_view(result: dict) -> dict[str, Any]:
    """Return the unified score envelope for ``result``.

    Reads ``result["scores"]`` if present, otherwise reconstructs it from the
    legacy flat fields so callers can rely on canonical names regardless of how
    a result was produced.
    """
    if result.get("scores"):
        return dict(result["scores"])
    view: dict[str, Any] = {}
    for canonical, flat in SCORE_FLAT_ALIASES.items():
        if flat in result:
            view[canonical] = result[flat]
    return view


# --------------------------------------------------------------------------- #
# Context + Stage protocol
# --------------------------------------------------------------------------- #

@dataclass
class SearchContext:
    """Mutable state threaded through the pipeline.

    Inputs are set once before the run; ``results`` and ``meta`` are mutated by
    stages. ``services`` holds the expensive, app-lifetime objects (synthesis
    client, reranker, time scorer, query expander) so stages stay cheap to
    construct per request.
    """

    query: str
    original_query: str = ""
    vault_path: Optional[Path] = None
    vault_name: str = ""
    limit: int = 10
    search_mode: str = "semantic"  # "semantic" | "hybrid" | "bm25"
    params: dict[str, Any] = field(default_factory=dict)
    services: dict[str, Any] = field(default_factory=dict)

    results: list[dict] = field(default_factory=list)
    file_filter: Optional[list[str]] = None

    meta: dict[str, Any] = field(default_factory=dict)
    stages_debug: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.original_query:
            self.original_query = self.query


@runtime_checkable
class Stage(Protocol):
    """A single, swappable pipeline step.

    ``applies`` lets a stage be skipped per-request (e.g. ``rerank=False``,
    ``time_boost=False``) without rebuilding the stage list. ``run`` mutates the
    context in place.
    """

    name: str

    def applies(self, ctx: SearchContext) -> bool: ...

    def run(self, ctx: SearchContext) -> None: ...


class Pipeline:
    """Runs an ordered list of stages over a :class:`SearchContext`."""

    def __init__(self, stages: list[Stage]):
        self.stages = stages

    def run(self, ctx: SearchContext) -> SearchContext:
        debug = bool(ctx.params.get("pipeline_debug"))
        for stage in self.stages:
            if not stage.applies(ctx):
                continue
            before = len(ctx.results)
            t0 = time.time()
            stage.run(ctx)
            if debug:
                ctx.stages_debug.append({
                    "stage": stage.name,
                    "before_count": before,
                    "after_count": len(ctx.results),
                    "elapsed_ms": round((time.time() - t0) * 1000, 2),
                })
        return ctx


# --------------------------------------------------------------------------- #
# Pure post-retrieval stages (no external services required)
#
# These mirror the corresponding inline stages in server.search() and are the
# extraction targets for the strangler-fig migration.
# --------------------------------------------------------------------------- #

class ScoreFilterStage:
    """Mirror of server.search() Stage 3.

    Drops results below the similarity threshold — but only in semantic mode.
    In hybrid mode RRF has already ranked results (and BM25-only results may
    lack a similarity score), so filtering is skipped.
    """

    name = "score_filter"

    def __init__(self, min_score: float = 0.3):
        self.min_score = min_score

    def applies(self, ctx: SearchContext) -> bool:
        return ctx.search_mode == "semantic"

    def run(self, ctx: SearchContext) -> None:
        threshold = ctx.params.get("min_score", self.min_score)
        kept = [r for r in ctx.results if r.get("similarity_score", 0) >= threshold]
        ctx.meta["score_removed"] = len(ctx.results) - len(kept)
        ctx.results = kept


class StatusFilterStage:
    """Mirror of server.search() Stage 4 (filter_inactive_gleanings).

    Removes results whose frontmatter ``status`` is ``inactive`` or ``hidden``.
    Fails open: results without frontmatter are kept.
    """

    name = "status_filter"

    def applies(self, ctx: SearchContext) -> bool:
        return True

    def run(self, ctx: SearchContext) -> None:
        kept = []
        for result in ctx.results:
            frontmatter = result.get("frontmatter")
            if frontmatter is not None:
                if frontmatter.get("status", "active") in ("inactive", "hidden"):
                    continue
            kept.append(result)
        ctx.meta["status_removed"] = len(ctx.results) - len(kept)
        ctx.results = kept


class QueryFilterStage:
    """Mirror of server.search() Stage 5.

    Applies frontmatter property, tag, path, and file filters using the
    existing ``filter_by_*`` helpers from ``server.py``. Filter specs are read
    from ``ctx.params`` at run time so the same stage object is reusable across
    requests with different filter combinations.
    """

    name = "query_filter"

    def applies(self, ctx: SearchContext) -> bool:
        p = ctx.params
        return bool(
            p.get("include_props") or p.get("exclude_props")
            or p.get("include_tags") or p.get("exclude_tags")
            or p.get("include_paths") or p.get("exclude_paths")
            or p.get("include_files") or p.get("exclude_files")
        )

    def run(self, ctx: SearchContext) -> None:
        from temoa.server_filters import (
            filter_by_files,
            filter_by_paths,
            filter_by_properties,
            filter_by_tags,
        )
        p = ctx.params
        results = ctx.results
        total_removed = 0

        if p.get("include_props") or p.get("exclude_props"):
            results, n = filter_by_properties(
                results,
                include_props=p.get("include_props"),
                exclude_props=p.get("exclude_props"),
            )
            total_removed += n

        if p.get("include_tags") or p.get("exclude_tags"):
            results, n = filter_by_tags(
                results,
                include_tags=p.get("include_tags"),
                exclude_tags=p.get("exclude_tags"),
            )
            total_removed += n

        if p.get("include_paths") or p.get("exclude_paths"):
            results, n = filter_by_paths(
                results,
                include_paths=p.get("include_paths"),
                exclude_paths=p.get("exclude_paths"),
            )
            total_removed += n

        if p.get("include_files") or p.get("exclude_files"):
            results, n = filter_by_files(
                results,
                include_files=p.get("include_files"),
                exclude_files=p.get("exclude_files"),
            )
            total_removed += n

        ctx.meta["query_filter_removed"] = total_removed
        ctx.results = results


class RerankStage:
    """Mirror of server.search() Stage 6.

    Runs the cross-encoder reranker held in ``ctx.services["reranker"]``.
    Skipped when ``ctx.params["rerank"]`` is falsy or when there are no results.
    After reranking the limit is already applied by the reranker (``top_k``), so
    the terminal :class:`LimitStage` checks ``rerank`` and skips itself to avoid
    double-truncation.
    """

    name = "rerank"

    def applies(self, ctx: SearchContext) -> bool:
        return bool(ctx.params.get("rerank", True)) and bool(ctx.results)

    def run(self, ctx: SearchContext) -> None:
        reranker = ctx.services.get("reranker")
        if reranker is None:
            return
        rerank_count = min(100, len(ctx.results))
        ctx.results = reranker.rerank(
            query=ctx.query,
            results=ctx.results,
            top_k=ctx.limit,
            rerank_top_n=rerank_count,
        )


class TimeBoostStage:
    """Mirror of server.search() Stage 7.

    Applies time-decay scoring held in ``ctx.services["time_scorer"]``.
    Skipped when ``ctx.params["time_boost"]`` is falsy or results are empty.
    """

    name = "time_boost"

    def applies(self, ctx: SearchContext) -> bool:
        return bool(ctx.params.get("time_boost", True)) and bool(ctx.results)

    def run(self, ctx: SearchContext) -> None:
        scorer = ctx.services.get("time_scorer")
        if scorer is None:
            return
        ctx.results = scorer.apply_boost(ctx.results, ctx.vault_path)


class LimitStage:
    """Terminal limit. Skipped when the reranker has already applied the limit."""

    name = "limit"

    def applies(self, ctx: SearchContext) -> bool:
        return not bool(ctx.params.get("rerank", True))

    def run(self, ctx: SearchContext) -> None:
        ctx.results = ctx.results[: ctx.limit]


# --------------------------------------------------------------------------- #
# Default pipeline factory
# --------------------------------------------------------------------------- #

def default_pipeline() -> Pipeline:
    """Return the standard post-retrieval pipeline mirroring server.search() stages 3–7.

    Retrieval (stages 0–2) is not included here — it still happens in
    ``server.search()`` before this pipeline is invoked.
    """
    return Pipeline([
        ScoreFilterStage(),
        StatusFilterStage(),
        QueryFilterStage(),
        RerankStage(),
        TimeBoostStage(),
        LimitStage(),
    ])
