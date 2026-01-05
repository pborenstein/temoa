# Production Hardening Roadmap

> **Created**: 2026-01-05
> **Status**: Planning
> **Goal**: Systematically address code quality, security, and reliability issues identified in 2026-01-05 code review
> **Approach**: Phased implementation minimizing risk to daily operations

---

## Overview

This roadmap organizes 20 findings from the comprehensive code review into 6 phases, prioritized by:
- **Risk to daily use** (start with lowest-risk changes)
- **Dependencies** (logical ordering of related fixes)
- **Impact vs effort** (high-value improvements first)
- **Grouping** (related changes in same phase)

Each phase is designed to be:
- **Independently deployable** - Can ship after each phase
- **Incrementally testable** - Validate before moving forward
- **Low disruption** - Daily searches continue working throughout

---

## Phase 0: Testing Infrastructure (ZERO Risk)

**Goal**: Add comprehensive tests without changing production code
**Risk Level**: ZERO (only adding tests)
**Estimated Duration**: 4-6 hours
**Can ship after**: Immediately (tests don't affect production)

### Tasks

#### 0.1: Edge Case Test Suite
**File**: `tests/test_edge_cases.py` (new)

Add tests for scenarios currently untested:

1. **Cache eviction** - 4th vault added to 3-vault cache
2. **Concurrent operations** - Two reindex requests simultaneously
3. **Malformed frontmatter** - Unterminated YAML blocks
4. **Unicode edge cases** - Emoji, surrogate pairs, null bytes
5. **Path traversal attempts** - Malicious `relative_path` values
6. **Empty vault** - Search when no files indexed
7. **Disk full during reindex** - Storage exhaustion handling
8. **Query extremes** - 10,000 character queries, empty queries
9. **Tag matching edge cases** - Special characters, unicode tags
10. **BM25 corpus edge cases** - Files with no content, title-only files

**Success Criteria**:
- [ ] All 10 edge case categories covered
- [ ] Tests pass (revealing any existing bugs)
- [ ] CI integration working

#### 0.2: Unicode Sanitization Tests
**File**: `tests/test_unicode.py` (new)

Test the `sanitize_unicode()` function comprehensively:

1. **Surrogate pairs** - `\uD800`, `\uDFFF`, various combinations
2. **Emoji sequences** - Multi-codepoint emoji
3. **Nested structures** - Dicts, lists, tuples with unicode issues
4. **Large responses** - Performance with 100+ results
5. **None values** - Handling missing data
6. **Mixed valid/invalid** - Partial corruption

**Success Criteria**:
- [ ] 100% code coverage for `sanitize_unicode()`
- [ ] Performance benchmarks established (< 10ms for 100 results)
- [ ] All edge cases documented

#### 0.3: Normalizer Test Expansion
**File**: `tests/test_normalizers.py` (expand existing)

Current: 21 tests. Add:

1. **Edge cases** - URLs with unusual formats
2. **Multiple normalizers** - Chain normalizers for complex URLs
3. **Performance** - Normalization overhead benchmarks
4. **Emoji edge cases** - Multi-byte emoji, emoji sequences
5. **Whitespace variations** - Tabs, newlines, mixed whitespace

**Success Criteria**:
- [ ] Test count: 21 → 35+
- [ ] Cover all regex edge cases
- [ ] Performance benchmarks (< 5ms per URL)

---

## Phase 1: Low-Risk Simplifications (LOW Risk)

**Goal**: Remove dead code and unnecessary abstractions
**Risk Level**: LOW (simplifications, no behavior changes)
**Estimated Duration**: 3-4 hours
**Depends On**: Phase 0 (tests establish baseline)

### Tasks

#### 1.1: Remove Dead Code in Search Profiles
**Files**: `src/temoa/search_profiles.py`, `src/temoa/server.py`

**Problem**: `metadata_boost` defined but never used

**Fix**:
1. Grep for all references to `metadata_boost`
2. Confirm it's never read in server.py or synthesis.py
3. Remove from all profile definitions
4. Add TODO comment if future feature planned
5. Update profile documentation

**Changes**:
- Remove ~100 lines of unused config
- Simplify profile structure (14 params → 10 params)

**Success Criteria**:
- [ ] No references to `metadata_boost` in codebase
- [ ] All tests still pass
- [ ] Documentation updated
- [ ] Search results unchanged (behavior identical)

#### 1.2: Simplify Config Property Methods
**File**: `src/temoa/config.py`

**Problem**: 10+ property methods that just forward to dict access

**Fix** (two options, choose one):

**Option A** (Minimal): Keep properties, add comment explaining why
```python
# Properties provide IDE autocomplete and type hints for common config keys
@property
def vault_path(self) -> Path:
    return self._config["vault_path"]
```

**Option B** (Simplify): Remove properties, use `__getitem__`
```python
def __getitem__(self, key: str):
    """Access config values via config['key'] syntax."""
    return self._config[key]
```

**Recommendation**: Option A (keep properties for IDE support, just document why)

**Changes**:
- Add docstring explaining rationale
- OR remove ~30 lines of property boilerplate

**Success Criteria**:
- [ ] Decision made on approach
- [ ] Documentation clear on config access pattern
- [ ] No behavior changes

#### 1.3: Extract Duplicate Frontmatter Parsing
**File**: `src/temoa/gleanings.py`

**Problem**: Lines 188-213 and 267-293 have identical parsing logic

**Fix**:
```python
def extract_frontmatter(content: str) -> Optional[str]:
    """Extract raw frontmatter string from markdown.

    Args:
        content: Markdown content potentially with frontmatter

    Returns:
        Frontmatter string without delimiters, or None if not found
    """
    if not content.startswith("---\n"):
        return None
    end_idx = content.find("\n---\n", 4)
    return content[4:end_idx] if end_idx != -1 else None
```

Then replace both duplicates with calls to this helper.

**Changes**:
- +15 lines (new function with docstring)
- -40 lines (two duplicate blocks)
- Net: -25 lines

**Success Criteria**:
- [ ] Helper function tested
- [ ] Both call sites updated
- [ ] gleaning tests still pass
- [ ] No behavior changes

#### 1.4: Limit Gleaning History Size
**File**: `src/temoa/gleanings.py`

**Problem**: History array grows unbounded

**Fix**:
```python
MAX_HISTORY = 100  # At module level

# In update function:
record["history"].append({...})
record["history"] = record["history"][-MAX_HISTORY:]  # Keep last 100
```

**Changes**:
- +3 lines
- Prevents pathological growth

**Success Criteria**:
- [ ] Constant defined
- [ ] Trimming applied after append
- [ ] Test with >100 history entries
- [ ] Old gleanings with >100 entries handled gracefully

---

## Phase 2: Performance Optimizations (LOW-MEDIUM Risk)

**Goal**: Improve search performance without changing results
**Risk Level**: LOW-MEDIUM (optimizations that don't change outputs)
**Estimated Duration**: 4-6 hours
**Depends On**: Phase 0 (perf benchmarks established)

### Tasks

#### 2.1: Fix File I/O in Hot Path (HIGH PRIORITY)
**File**: `src/temoa/server.py:237-255`

**Problem**: `filter_inactive_gleanings()` opens/reads every result file

**Current**:
```python
for result in results:
    file_path = result.get("file_path")
    with open(file_path, "r") as f:  # 🔥 HOT PATH I/O!
        content = f.read()
    status = parse_frontmatter_status(content)
```

**Fix**: Use frontmatter already in results
```python
for result in results:
    frontmatter = result.get("frontmatter", {})
    status = frontmatter.get("status", "active")
    if status in ("inactive", "hidden"):
        continue
    filtered.append(result)
```

**Impact**:
- 50 result files: 50 file reads eliminated
- ~500-1000ms latency reduction on HDD
- ~50-100ms on SSD

**Changes**:
- server.py: -15 lines (remove file I/O logic)
- synthesis.py: Verify frontmatter included in results

**Success Criteria**:
- [ ] No file I/O during filtering
- [ ] Benchmark shows measurable improvement
- [ ] All status filtering tests pass
- [ ] Edge case: frontmatter missing handled

#### 2.2: Optimize Tag Matching (O(N²) → O(N))
**File**: `src/temoa/bm25_index.py:172-176`

**Current** (quadratic):
```python
for query_token in query_tokens:
    for tag in tags_lower:
        if query_token in tag or tag in query_token:
            tags_matched.append(tag)
```

**Fix** (linear with set intersection):
```python
# Exact match first (fast)
query_set = set(query_tokens)
tag_set = set(tags_lower)
exact_matches = list(query_set & tag_set)

# Substring match only if no exact matches (compatibility)
if not exact_matches:
    for query_token in query_tokens:
        for tag in tags_lower:
            if query_token in tag or tag in query_token:
                exact_matches.append(tag)
                break

tags_matched = exact_matches
```

**Impact**:
- 10,000 docs × 10 tags × 5 query tokens: 500k → 150k operations
- ~200-300ms saved on large vaults

**Changes**:
- +10 lines (two-tier matching)
- Maintains backward compatibility (substring matches)

**Success Criteria**:
- [ ] Benchmark shows improvement
- [ ] Tag boosting results identical
- [ ] Test with large vault (3000+ docs)
- [ ] Substring matches still work

#### 2.3: Fix Memory Leak in Hybrid Search
**File**: `src/temoa/synthesis.py:656-677`

**Problem**: Large embedding arrays not explicitly released

**Fix**:
```python
try:
    if query_embedding is None:
        query_embedding = self.pipeline.engine.embed_text(query)
        embeddings_array, metadata_list, _ = self.pipeline.store.load_embeddings()

    # ... use embeddings ...

finally:
    # Explicit cleanup for large arrays
    if 'embeddings_array' in locals():
        del embeddings_array
    if 'metadata_list' in locals():
        del metadata_list
    import gc
    gc.collect()  # Hint to GC to reclaim memory
```

**Impact**:
- Faster memory reclamation in long-running server
- Reduced peak memory usage

**Changes**:
- +8 lines (try/finally cleanup)

**Success Criteria**:
- [ ] Memory profiling shows improvement
- [ ] No performance regression
- [ ] Long-running server test (1000+ searches)

---

## Phase 3: Error Handling & Observability (MEDIUM Risk)

**Goal**: Replace bare exceptions with specific types, improve logging
**Risk Level**: MEDIUM (changes exception handling, could reveal hidden bugs)
**Estimated Duration**: 6-8 hours
**Depends On**: Phase 0 (tests catch any regressions)

### Tasks

#### 3.1: Replace Bare Exceptions Throughout
**Files**: `src/temoa/server.py` (20+ locations), `src/temoa/synthesis.py`, `src/temoa/gleanings.py`

**Problem**: `except Exception as e:` catches everything including `KeyboardInterrupt`

**Strategy**: Define specific exception types
```python
# src/temoa/exceptions.py (new file)
class TemoaError(Exception):
    """Base exception for Temoa errors."""
    pass

class VaultReadError(TemoaError):
    """Error reading vault files."""
    pass

class SearchError(TemoaError):
    """Error during search operation."""
    pass

class IndexError(TemoaError):
    """Error during indexing."""
    pass

class ConfigError(TemoaError):
    """Configuration error."""
    pass
```

**Pattern for replacing**:
```python
# BEFORE (dangerous):
try:
    content = f.read()
except Exception as e:
    logger.warning(f"Error reading {path}: {e}")
    continue

# AFTER (safe):
try:
    content = f.read()
except (IOError, OSError, UnicodeDecodeError) as e:
    logger.warning(f"Error reading {path}: {e}")
    continue
except Exception as e:
    logger.error(f"Unexpected error reading {path}: {e}")
    raise  # Re-raise unexpected errors
```

**Locations** (priority order):
1. `server.py:252-255` (filter_inactive_gleanings - HIGH)
2. `server.py:309-311` (filter_by_type - HIGH)
3. `server.py:364-387` (enhance_results - MEDIUM)
4. `synthesis.py` (search operations - HIGH)
5. `gleanings.py` (file operations - MEDIUM)
6. All other locations (LOW)

**Changes**:
- New file: `src/temoa/exceptions.py` (~50 lines)
- Modified: 20+ exception handlers across 5 files

**Success Criteria**:
- [ ] All bare `except Exception` replaced
- [ ] Specific exception types document<blink>ed
- [ ] Tests for each exception type
- [ ] No regressions in error handling
- [ ] KeyboardInterrupt works correctly

#### 3.2: Document Error Handling Philosophy
**File**: `CLAUDE.md` or `docs/ARCHITECTURE.md`

**Add section**:
```markdown
## Error Handling Philosophy

### Fail-Open vs Fail-Closed

**Fail-Open** (include on error):
- Search result filtering (better to show too much than miss results)
- Frontmatter parsing (include file even if YAML invalid)
- Optional metadata (missing description → empty, not error)

**Fail-Closed** (exclude on error):
- Authentication/authorization (deny access on error)
- Data modification (reject rather than corrupt)
- Security validation (path traversal → reject)
- Critical operations (reindex with errors → abort)

### Exception Types

Use specific exceptions, not bare `except Exception`:
- `VaultReadError` - File I/O failures
- `SearchError` - Search operation failures
- `IndexError` - Indexing failures
- `ConfigError` - Configuration issues

Never catch `KeyboardInterrupt`, `SystemExit`, or `MemoryError`.
```

**Success Criteria**:
- [ ] Philosophy documented
- [ ] Examples provided
- [ ] Guidelines clear for future development

---

## Phase 4: Security Hardening (MEDIUM-HIGH Risk)

**Goal**: Fix security vulnerabilities
**Risk Level**: MEDIUM-HIGH (changes could break valid use cases if too aggressive)
**Estimated Duration**: 4-6 hours
**Depends On**: Phase 3 (error handling in place for security failures)

### Tasks

#### 4.1: Fix CORS Configuration (HIGH PRIORITY)
**File**: `src/temoa/server.py:351-358`

**Current** (insecure):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ DANGEROUS
    allow_credentials=True,
```

**Fix**:
```python
# Read from environment or config
allowed_origins = os.getenv("TEMOA_CORS_ORIGINS", "").split(",")
if not allowed_origins or allowed_origins == [""]:
    # Default: only same-origin
    server_port = config.get("server", {}).get("port", 8080)
    allowed_origins = [
        f"http://localhost:{server_port}",
        f"http://127.0.0.1:{server_port}",
    ]

    # Add Tailscale IP if available
    tailscale_ip = os.getenv("TAILSCALE_IP")
    if tailscale_ip:
        allowed_origins.append(f"http://{tailscale_ip}:{server_port}")

logger.info(f"CORS allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
```

**Configuration**:
- Environment variable: `TEMOA_CORS_ORIGINS="http://localhost:8080,http://192.168.1.100:8080"`
- Config file: `config.json` → `"cors_origins": ["http://..."]`
- Documentation: `docs/DEPLOYMENT.md`

**Changes**:
- server.py: +20 lines
- config.example.json: Add cors_origins example
- DEPLOYMENT.md: Document CORS configuration

**Success Criteria**:
- [ ] Default is restrictive (localhost only)
- [ ] Tailscale IPs can be whitelisted
- [ ] Environment variable override works
- [ ] Documented in deployment guide
- [ ] Warning logged if wildcard used

#### 4.2: Add Rate Limiting for Expensive Operations
**File**: `src/temoa/server.py`

**Add rate limiting for**:
1. `/reindex` (max 5 per hour per IP)
2. `/extract` (max 10 per hour per IP)
3. `/search` (max 1000 per hour per IP - generous)

**Implementation**:
```python
# src/temoa/rate_limiter.py (new file)
from collections import defaultdict
from time import time
from typing import Dict, List

class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self._requests: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

    def check_limit(self, client_id: str, endpoint: str, max_requests: int, window_seconds: int = 3600) -> bool:
        """
        Check if request is within rate limit.

        Args:
            client_id: Client identifier (IP address)
            endpoint: Endpoint name (e.g., "reindex")
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds (default 1 hour)

        Returns:
            True if within limit, False if exceeded
        """
        now = time()
        requests = self._requests[client_id][endpoint]

        # Remove old requests outside window
        requests[:] = [t for t in requests if now - t < window_seconds]

        if len(requests) >= max_requests:
            return False

        requests.append(now)
        return True

# In server.py
from fastapi import HTTPException, Request
from .rate_limiter import RateLimiter

rate_limiter = RateLimiter()

@app.post("/reindex")
async def reindex(request: Request, ...):
    client_ip = request.client.host

    if not rate_limiter.check_limit(client_ip, "reindex", max_requests=5):
        raise HTTPException(
            status_code=429,
            detail="Too many reindex requests. Maximum 5 per hour. Try again later."
        )

    # ... rest of reindex logic
```

**Limits** (tunable via config):
- `/reindex`: 5 per hour
- `/extract`: 10 per hour
- `/search`: 1000 per hour
- `/archaeology`: 20 per hour

**Changes**:
- New file: `src/temoa/rate_limiter.py` (~80 lines)
- Modified: `src/temoa/server.py` (add rate limiting to 4 endpoints)
- Config: Add rate limit settings to config.json

**Success Criteria**:
- [ ] Rate limits configurable
- [ ] 429 responses on limit exceeded
- [ ] Clear error messages
- [ ] Legitimate use not blocked
- [ ] DoS protection working

#### 4.3: Add Path Traversal Validation
**File**: `src/temoa/time_scoring.py:71-84` (already fixed in Entry 41!)

**Status**: ✅ **ALREADY COMPLETE** (2025-12-19, commit 26e20c6)

**Current code**:
```python
file_path_resolved = file_path.resolve()
vault_path_resolved = vault_path.resolve()

if not str(file_path_resolved).startswith(str(vault_path_resolved)):
    logger.warning(f"Path traversal attempt detected: {result['relative_path']}")
    continue
```

**No action needed** - verification only:
- [ ] Confirm fix is deployed
- [ ] Add test for path traversal attempts
- [ ] Document in security guide

---

## Phase 5: Architecture Improvements (LOW Priority, OPTIONAL)

**Goal**: Larger refactors that improve maintainability
**Risk Level**: MEDIUM (significant code changes)
**Estimated Duration**: 8-12 hours
**Depends On**: Phases 0-4 complete
**Optional**: Can defer to Phase 4 or skip entirely

### Tasks

#### 5.1: Abstract Synthesis Coupling (Optional)
**Files**: `src/temoa/synthesis.py:259-330`

**Problem**: Direct `sys.path` manipulation, hard to test without Synthesis

**Fix**: Use `importlib` for isolated imports
```python
import importlib.util
from pathlib import Path

def _import_synthesis_module(self, module_name: str):
    """Import Synthesis module without polluting sys.path."""
    module_path = self.synthesis_path / "src" / f"{module_name}.py"

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Usage:
vault_reader = self._import_synthesis_module("vault_reader")
SearchPipeline = vault_reader.SearchPipeline
```

**Benefits**:
- No global state pollution
- Easier testing (mock Synthesis)
- Cleaner import semantics

**Trade-offs**:
- More complex code
- Same functionality
- Testing benefits may not justify complexity

**Decision Point**: Discuss with user before implementing

**Changes**:
- synthesis.py: +40 lines, -20 lines
- Better testability

**Success Criteria**:
- [ ] No `sys.path` manipulation
- [ ] All imports work
- [ ] Tests pass
- [ ] Performance unchanged

#### 5.2: Simplify Search Profiles (Optional)
**File**: `src/temoa/search_profiles.py`

**Problem**: 14 parameters, many unimplemented

**Options**:

**Option A**: Remove unimplemented features
- Remove: `show_chunk_context`, `max_results_per_file`, `max_age_days`
- Result: 14 → 11 parameters
- Risk: LOW (features never worked anyway)

**Option B**: Implement missing features
- Implement: Chunk context, results per file, age filtering
- Result: Features actually work
- Risk: MEDIUM (new code, new bugs)

**Option C**: Simplify to essentials
- Keep only: `bm25_weight`, `enable_reranker`, `enable_chunking`, `time_decay_days`
- Result: 14 → 4 parameters
- Risk: MEDIUM (breaking change for profiles)

**Recommendation**: Option A (remove dead features) or defer entirely

**Decision Point**: Discuss with user

#### 5.3: Cache Invalidation Locking (Optional but Recommended)
**File**: `src/temoa/client_cache.py:102-118`

**Problem**: Race condition during reindex

**Fix**:
```python
import asyncio
from typing import Dict

class ClientCache:
    def __init__(self, max_size: int = 3):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._locks: Dict[str, asyncio.Lock] = {}

    async def get_or_create(self, vault_path, model, ...):
        """Get client or wait for reindex to complete."""
        key = self._make_key(vault_path, model)

        # Get or create lock for this vault
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            # Check cache under lock
            if key in self._cache:
                return self._cache[key]

            # Create new client (no one else can create for same key)
            client = SynthesisClient(...)
            self._cache[key] = client
            return client

    async def invalidate_and_reindex(self, vault_path, model):
        """Invalidate cache and reindex atomically."""
        key = self._make_key(vault_path, model)

        if key not in self._locks:
            self._locks[key] = asyncio.Lock()

        async with self._locks[key]:
            # Remove old client
            if key in self._cache:
                del self._cache[key]

            # Reindex
            await self._reindex_impl(vault_path, model)

            # Create fresh client with new index
            client = SynthesisClient(...)
            self._cache[key] = client
            return client
```

**Benefits**:
- No stale clients during reindex
- Thread-safe cache operations
- Atomic invalidate-and-reindex

**Trade-offs**:
- More complex code
- Async lock overhead (minimal)

**Changes**:
- client_cache.py: +60 lines
- server.py: Update reindex endpoint to use new method

**Success Criteria**:
- [ ] No stale clients observed
- [ ] Concurrent reindex test passes
- [ ] Performance unchanged

---

## Phase 6: Documentation & Polish (ZERO Risk)

**Goal**: Update documentation to reflect all changes
**Risk Level**: ZERO (docs only)
**Estimated Duration**: 3-4 hours
**Depends On**: Phases 0-5 complete

### Tasks

#### 6.1: Update ARCHITECTURE.md
**File**: `docs/ARCHITECTURE.md`

Add sections:
- Error handling strategy
- Security considerations (CORS, rate limiting, path validation)
- Performance optimizations applied
- Testing coverage

#### 6.2: Update CLAUDE.md
**File**: `CLAUDE.md`

Update:
- Remove references to metadata_boost (if removed in Phase 1)
- Add error handling philosophy (from Phase 3)
- Document security defaults (from Phase 4)
- Update performance characteristics (from Phase 2)

#### 6.3: Create SECURITY.md
**File**: `docs/SECURITY.md` (new)

Document:
- CORS configuration
- Rate limiting
- Path traversal protection
- Unicode sanitization
- Vault isolation
- Threat model (single-user, Tailscale network)

#### 6.4: Update TESTING.md
**File**: `docs/TESTING.md` (new or expand existing)

Document:
- Test structure and coverage
- Running tests
- Adding new tests
- Performance benchmarks
- Edge case testing strategy

---

## Success Criteria (Per Phase)

### Phase 0: Testing
- [ ] 35+ new tests added
- [ ] All tests pass
- [ ] Code coverage > 70%
- [ ] Performance benchmarks established

### Phase 1: Simplifications
- [ ] Dead code removed
- [ ] Duplicate code eliminated
- [ ] No behavior changes
- [ ] All tests pass

### Phase 2: Performance
- [ ] Measurable latency improvements
- [ ] No degraded search quality
- [ ] Memory leak fixed (profiling confirms)
- [ ] Benchmarks show improvements

### Phase 3: Error Handling
- [ ] No bare `except Exception` remains
- [ ] Philosophy documented
- [ ] Specific exceptions defined
- [ ] All error paths tested

### Phase 4: Security
- [ ] CORS properly configured
- [ ] Rate limiting working
- [ ] Path traversal protection verified
- [ ] Security guide written

### Phase 5: Architecture (Optional)
- [ ] User approval for each task
- [ ] Backwards compatibility maintained OR migration path clear
- [ ] Performance unchanged or improved
- [ ] Testing coverage maintained

### Phase 6: Documentation
- [ ] All changes documented
- [ ] Examples provided
- [ ] Security guide complete
- [ ] Testing guide complete

---

## Deployment Strategy

### Between Phases

After each phase:
1. **Run full test suite**
2. **Deploy to development** (`./dev.sh`)
3. **Manual testing** (10-20 searches, validate behavior)
4. **Commit with clear message** (reference phase number)
5. **Monitor for issues** (check logs)
6. **Proceed to next phase** only if stable

### Rollback Plan

If issues discovered:
1. **Identify problematic commit**
2. **Git revert** specific change
3. **Re-test** to confirm issue resolved
4. **Fix properly** before re-attempting
5. **Update plan** with lessons learned

### Production Deployment

After all phases (or after each phase):
1. **Unload launchd service** (`launchctl unload ...`)
2. **Pull changes** (`git pull origin main`)
3. **Install dependencies** (`uv sync`)
4. **Reload service** (`launchctl load ...`)
5. **Check health** (`curl http://localhost:8080/health`)
6. **Monitor logs** (`./view-logs.sh`)

---

## Metrics to Track

### Performance
- Search latency (p50, p95, p99)
- Reindex duration
- Memory usage (peak, average)
- Cache hit rate

### Reliability
- Exception rate (per endpoint)
- Rate limit triggers
- Path traversal attempts detected
- Unicode sanitization invocations

### Testing
- Test count
- Code coverage %
- Test execution time
- Edge cases covered

---

## Open Questions

### For User Decision

1. **Phase 1.2**: Keep config properties or simplify to `__getitem__`?
2. **Phase 4.1**: Default CORS to localhost only? (could break Tailscale access)
3. **Phase 4.2**: Rate limit values too aggressive? too lenient?
4. **Phase 5.1**: Worth abstracting Synthesis coupling? (testability vs complexity)
5. **Phase 5.2**: Simplify profiles or implement missing features?
6. **Phase 5.3**: Add cache locking? (safety vs complexity)

### For Investigation

1. **Chunking default**: CLAUDE.md says enabled, config defaults to False - which is correct?
2. **Metadata boost**: Should we implement or permanently remove?
3. **Search profiles**: Are all 14 parameters needed? Which are used?
4. **Frontend-aware search**: Is description prepending actually used?

---

## Timeline Estimate

| Phase | Duration | Risk | Can Ship After |
|-------|----------|------|----------------|
| Phase 0: Testing | 4-6 hours | ZERO | Immediately |
| Phase 1: Simplifications | 3-4 hours | LOW | Phase 0 |
| Phase 2: Performance | 4-6 hours | LOW-MED | Phase 1 |
| Phase 3: Error Handling | 6-8 hours | MEDIUM | Phase 2 |
| Phase 4: Security | 4-6 hours | MED-HIGH | Phase 3 |
| Phase 5: Architecture | 8-12 hours | MEDIUM | Phase 4 (OPTIONAL) |
| Phase 6: Documentation | 3-4 hours | ZERO | Phase 5 |
| **Total** | **32-46 hours** | | **Can stop after any phase** |

**Recommended approach**:
- Do Phases 0-4 (high value, clear benefits)
- Skip Phase 5 unless specific needs arise
- Always do Phase 6 (documentation hygiene)

**Timeline**: ~25-30 hours for Phases 0-4 + 6

---

## Notes

### Already Complete

Some items from the code review are already fixed:
- ✅ **Path traversal validation** (Entry 41, 2025-12-19, commit 26e20c6)
- ✅ **Query expansion error handling** (Entry 41, 2025-12-19, commit 26e20c6)
- ✅ **Pipeline order fix** (Entry 41, 2025-12-19, commit 26e20c6)
- ✅ **Unicode sanitization** (Entry 35, 2025-12-08, commit 03d3468)

These just need:
- Verification they're deployed
- Tests added (Phase 0)
- Documentation (Phase 6)

### Risk Mitigation

**Why start with testing?**
- Establishes baseline behavior
- Catches regressions immediately
- Zero risk to production
- Enables confident refactoring

**Why security in Phase 4, not earlier?**
- Needs error handling in place (Phase 3)
- Needs performance baseline (Phase 2)
- Single-user + Tailscale reduces urgency
- Can be thorough vs rushed

**Why architecture improvements optional?**
- High effort, moderate benefit
- Works fine as-is
- Refactoring risk > stability value
- Can defer until specific need

---

**Created**: 2026-01-05
**Author**: Claude (Sonnet 4.5)
**Based On**: Comprehensive code review (2026-01-05)
**Status**: Planning (awaiting user approval)
**Next Step**: Review plan, approve phases, begin Phase 0
