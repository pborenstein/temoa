"""Unit tests for the composable search pipeline (src/temoa/pipeline.py).

These exercise the Stage/Pipeline abstraction and the pure post-retrieval
stages with fixture result dicts — no config, vault, index, or model required,
so they run in any environment.
"""

from temoa.pipeline import (
    Pipeline,
    SearchContext,
    ScoreFilterStage,
    StatusFilterStage,
    LimitStage,
    set_score,
    score_view,
    SCORE_FLAT_ALIASES,
)


# --------------------------------------------------------------------------- #
# Score envelope
# --------------------------------------------------------------------------- #

def test_set_score_writes_envelope_and_flat_field():
    r: dict = {}
    set_score(r, "semantic", 0.72)
    set_score(r, "bm25", 12.4)
    # canonical envelope
    assert r["scores"]["semantic"] == 0.72
    assert r["scores"]["bm25"] == 12.4
    # legacy flat fields preserved for existing consumers
    assert r["similarity_score"] == 0.72
    assert r["bm25_score"] == 12.4


def test_set_score_envelope_only_for_unaliased_name():
    r: dict = {}
    set_score(r, "bm25_base", 2.48)
    assert r["scores"]["bm25_base"] == 2.48
    assert "bm25_base" not in r  # no flat alias, lives only in envelope
    assert "bm25_base" not in SCORE_FLAT_ALIASES


def test_score_view_prefers_envelope():
    r = {"scores": {"semantic": 0.5}, "similarity_score": 0.9}
    assert score_view(r)["semantic"] == 0.5


def test_score_view_reconstructs_from_flat_fields():
    r = {"similarity_score": 0.6, "rrf_score": 0.01, "cross_encoder_score": 0.8}
    view = score_view(r)
    assert view["semantic"] == 0.6
    assert view["rrf"] == 0.01
    assert view["cross_encoder"] == 0.8


# --------------------------------------------------------------------------- #
# ScoreFilterStage
# --------------------------------------------------------------------------- #

def _results(*scores):
    return [{"relative_path": f"n{i}.md", "similarity_score": s} for i, s in enumerate(scores)]


def test_score_filter_semantic_mode_drops_below_threshold():
    ctx = SearchContext(query="q", search_mode="semantic", params={"min_score": 0.3})
    ctx.results = _results(0.5, 0.2, 0.31, 0.29)
    ScoreFilterStage().run(ctx)
    assert [r["similarity_score"] for r in ctx.results] == [0.5, 0.31]
    assert ctx.meta["score_removed"] == 2


def test_score_filter_skipped_in_hybrid_mode():
    stage = ScoreFilterStage()
    ctx = SearchContext(query="q", search_mode="hybrid")
    assert stage.applies(ctx) is False


def test_score_filter_uses_param_over_default():
    ctx = SearchContext(query="q", search_mode="semantic", params={"min_score": 0.4})
    ctx.results = _results(0.5, 0.35)
    ScoreFilterStage(min_score=0.1).run(ctx)
    assert len(ctx.results) == 1  # param 0.4 wins over constructor default 0.1


# --------------------------------------------------------------------------- #
# StatusFilterStage
# --------------------------------------------------------------------------- #

def test_status_filter_removes_inactive_and_hidden():
    ctx = SearchContext(query="q")
    ctx.results = [
        {"title": "a", "frontmatter": {"status": "active"}},
        {"title": "b", "frontmatter": {"status": "inactive"}},
        {"title": "c", "frontmatter": {"status": "hidden"}},
        {"title": "d", "frontmatter": {}},          # no status -> active
        {"title": "e"},                              # no frontmatter -> fail open
    ]
    StatusFilterStage().run(ctx)
    assert [r["title"] for r in ctx.results] == ["a", "d", "e"]
    assert ctx.meta["status_removed"] == 2


# --------------------------------------------------------------------------- #
# Pipeline runner + gating + debug
# --------------------------------------------------------------------------- #

def test_pipeline_runs_stages_in_order_and_gates_with_applies():
    ctx = SearchContext(query="q", search_mode="hybrid", limit=2)
    ctx.results = [
        {"title": "a", "similarity_score": 0.9, "frontmatter": {"status": "active"}},
        {"title": "b", "similarity_score": 0.1, "frontmatter": {"status": "inactive"}},
        {"title": "c", "similarity_score": 0.8, "frontmatter": {"status": "active"}},
        {"title": "d", "similarity_score": 0.7, "frontmatter": {"status": "active"}},
    ]
    pipe = Pipeline([ScoreFilterStage(), StatusFilterStage(), LimitStage()])
    pipe.run(ctx)
    # ScoreFilter skipped (hybrid); StatusFilter drops "b"; Limit keeps 2
    assert [r["title"] for r in ctx.results] == ["a", "c"]


def test_pipeline_debug_capture_records_each_applied_stage():
    ctx = SearchContext(query="q", search_mode="semantic", limit=10,
                        params={"min_score": 0.3, "pipeline_debug": True})
    ctx.results = _results(0.5, 0.1)
    Pipeline([ScoreFilterStage(), StatusFilterStage()]).run(ctx)
    names = [s["stage"] for s in ctx.stages_debug]
    assert names == ["score_filter", "status_filter"]
    assert all("elapsed_ms" in s for s in ctx.stages_debug)


def test_context_defaults_original_query_to_query():
    ctx = SearchContext(query="hello")
    assert ctx.original_query == "hello"
