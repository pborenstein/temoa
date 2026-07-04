# Temoa Testing Guide

**Last Updated**: 2026-07-04
**Test Baseline**: 156 passed, 0 failed, 0 skipped

---

## Test Status Overview

### Current Baseline (v2.0 Pure Search Engine)

```
Total Tests: 156
Passing: 156 (100%)
Skipped: 0
Failed: 0
```

**Key Metric**: **0 failures is the norm.** Every test either passes or doesn't exist. Tests for removed v1 features (gleanings, normalizers, UI) were deleted with the v2.0 rebuild.

---

## Running Tests

### Full Test Suite

```bash
uv run python -m pytest -v
```

### Quick Summary

```bash
uv run python -m pytest -q
```

### Specific Test File

```bash
uv run python -m pytest tests/test_server.py -v
```

### With Coverage

```bash
uv run python -m pytest --cov=src/temoa --cov-report=html
```

---

## Test Organization

### By Feature

| Feature | Test File | Tests |
|---------|-----------|-------|
| Chunking | `test_chunking.py` | 19 |
| Configuration | `test_config.py` | 8 |
| Edge Cases | `test_edge_cases.py` | 21 |
| Pipeline | `test_pipeline.py` | 23 |
| Reranker | `test_reranker.py` | 9 |
| Search Log | `test_search_log.py` | 8 |
| Server | `test_server.py` | 14 |
| Storage | `test_storage.py` | 13 |
| Unicode | `test_unicode.py` | 41 |

---

## Adding New Tests

### Guidelines

1. **Every test must pass.** No aspirational specs, no "known failures."
2. **Test behavior, not internals.** Call the same interfaces real code calls.
3. **Skip for infrastructure, not laziness.** `@pytest.mark.skip` is for tests that genuinely need a real vault; currently none.

### Unit Tests

```python
# tests/test_myfeature.py
import pytest
from temoa.myfeature import my_function

def test_my_function_basic_case():
    """Test basic functionality."""
    result = my_function("input")
    assert result == "expected"
```

### Edge Case Tests

Add to `tests/test_edge_cases.py` with descriptive class:

```python
class TestMyFeatureEdgeCases:
    """Test edge cases for my feature."""

    def test_handles_empty_input(self, tmp_path):
        """Should handle empty input gracefully."""
        # BM25Index requires storage_dir=tmp_path
        # ClientCache.get() takes (vault_path, model, storage_dir)
```

---

## Performance Benchmarks

### Search Latency (3,000 file vault)

| Operation | Latency | Target |
|-----------|---------|--------|
| Semantic search | ~400ms | < 2s |
| Hybrid search | ~450ms | < 2s |
| With cross-encoder | ~600ms | < 2s |
| With expansion + rerank | ~800-1000ms | < 2s |

### Reindexing (3,059 file vault)

| Mode | Duration | Notes |
|------|----------|-------|
| Full reindex | ~159s | Build all embeddings |
| Incremental (no changes) | ~5s | 30x faster |
| Incremental (5 new files) | ~6-8s | Only process changed |
| Incremental (50 changed) | ~15-20s | Still much faster |

---

## Debugging Failed Tests

```bash
# Verbose output for one test
uv run python -m pytest tests/test_edge_cases.py::TestPathTraversalProtection -vv

# Full traceback
uv run python -m pytest --tb=long

# Drop into debugger on failure
uv run python -m pytest --pdb

# Run only failed tests from last run
uv run python -m pytest --lf
```

---

## Success Criteria

- **0 test failures** (no exceptions)
- No regressions when adding features
- Core paths covered: search, index, pipeline, filtering
- Security tests passing: CORS, rate limiting, path validation
- Performance within targets (< 2s mobile)

---

**Created**: 2026-01-09
**Last Updated**: 2026-07-04
**Context**: v2.0 pure search engine baseline (v1 feature tests deleted with the rebuild)
