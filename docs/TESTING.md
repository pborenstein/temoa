# Temoa Testing Guide

**Last Updated**: 2026-02-21
**Test Baseline**: 196 passed, 0 failed, 15 skipped

---

## Test Status Overview

### Current Baseline (Test Hygiene Phase Complete)

```
Total Tests: 211
Passing: 196 (92.9%)
Skipped: 15 (7.1%)
Failed: 0
```

**Key Metric**: **0 failures is the norm.** Every test either passes or doesn't exist. Skipped tests require real infrastructure (Obsidian vault, Synthesis engine) that isn't available in CI.

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

## Skipped Tests (15 tests)

All skips require infrastructure not available in CI. Each has a reason string.

**Disk full scenarios** (2 tests) - `test_edge_cases.py`:

- `test_reindex_with_no_disk_space`: Requires disk full simulation
- `test_gleaning_write_with_no_space`: Requires disk full simulation

**Multi-vault integration** (5 tests) - `test_multi_vault_integration.py`:

- Require real vault paths and Synthesis engine

**Synthesis integration** (8 tests) - `test_synthesis.py`, `test_storage.py`:

- Require Synthesis engine and vault configuration

---

## Test Organization

### By Feature

| Feature | Test File | Tests |
|---------|-----------|-------|
| Chunking | `test_chunking.py` | 19 passing |
| Configuration | `test_config.py` | 7 passing |
| Edge Cases | `test_edge_cases.py` | 32 passing, 2 skipped |
| Gleanings | `test_gleanings.py` | 19 passing |
| Multi-vault | `test_multi_vault_integration.py` | 5 skipped |
| Normalizers | `test_normalizers.py` | 44 passing |
| Reranker | `test_reranker.py` | 8 passing |
| Server | `test_server.py` | 53 passing |
| Storage | `test_storage.py` | 8 passing (4 need vault, skipped) |
| Synthesis | `test_synthesis.py` | 1 passing, 7 skipped |
| Unicode | `test_unicode.py` | 4 passing |

---

## Adding New Tests

### Guidelines

1. **Every test must pass.** No aspirational specs, no "known failures."
2. **Test behavior, not internals.** Call the same interfaces real code calls.
3. **Skip for infrastructure, not laziness.** `@pytest.mark.skip` is for real vault / Synthesis dependencies only.

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
        # ClientCache.get() takes (vault_path, synthesis_path, model, storage_dir)
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
- Core paths covered: search, index, extract, normalize
- Security tests passing: CORS, rate limiting, path validation
- Performance within targets (< 2s mobile)

---

**Created**: 2026-01-09
**Last Updated**: 2026-02-21
**Context**: Test Hygiene Phase - cleaned 33 failures to 0
