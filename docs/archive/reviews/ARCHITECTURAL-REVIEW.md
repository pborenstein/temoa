# Temoa Architectural Review

## Executive Summary

Temoa is a **well-architected FastAPI server** that successfully achieves its core goal: providing fast (<500ms) semantic search for Obsidian vaults via mobile devices. The architecture is **simple, pragmatic, and performance-focused**, with clear layering and well-documented design decisions.

**Overall Assessment**: ✅ **Architecturally sound** with some **maintenance and scalability concerns** that should be addressed before future phases.

**Key Metrics**:
- 2,499 lines of production code across 6 modules
- 24 passing tests with comprehensive coverage
- ~400ms search performance (5x better than 2s target)
- Clear separation into server → wrapper → engine layers

---

## 1. Strengths

### 1.1 Core Architectural Decisions ⭐⭐⭐⭐⭐

**DEC-009: Direct Imports Over Subprocess**
- **Documented**: docs/ARCHITECTURE.md lines 786-807
- **Impact**: 10x performance improvement (400ms vs 2-3s)
- **Implementation**: Clean wrapper in `synthesis.py` that imports Synthesis modules directly
- **Assessment**: ✅ Excellent decision, well-executed

**DEC-013: Modern FastAPI Lifespan Pattern**
- **Location**: `server.py` lines 62-77
- **Pattern**: Uses `@asynccontextmanager` for startup/shutdown
- **Assessment**: ✅ Best practice, clean resource management

### 1.2 Layered Architecture ⭐⭐⭐⭐

The code exhibits **clear separation of concerns**:

```
┌─────────────────────────────────────────┐
│ HTTP Layer (server.py)                  │  ← Endpoints, validation, filtering
├─────────────────────────────────────────┤
│ Wrapper Layer (synthesis.py)            │  ← Abstraction, URI generation
├─────────────────────────────────────────┤
│ Engine Layer (synthesis/)               │  ← Core search logic (external)
├─────────────────────────────────────────┤
│ Storage Layer (vault + .temoa/)         │  ← Files, embeddings, state
└─────────────────────────────────────────┘
```

**Evidence**:
- `server.py`: HTTP endpoints, request validation, response formatting
- `synthesis.py`: Wrapper with clean interface (`search()`, `archaeology()`, `reindex()`)
- `config.py`: Centralized configuration with path expansion
- `gleanings.py`: Status management (single responsibility)

### 1.3 Configuration Management ⭐⭐⭐⭐⭐

**File**: `config.py` (198 lines)

**Strengths**:
- Standard locations hierarchy (XDG → home → cwd)
- Path expansion with `~` support
- Validation at load time
- Helpful error messages with setup instructions (lines 65-82)
- Clean property-based access

**Code Quality**:
```python
@property
def vault_path(self) -> Path:
    """Path to Obsidian vault"""
    return self._config["vault_path"]
```
Clean, type-safe, self-documenting.

### 1.4 Error Handling ⭐⭐⭐⭐

**Custom Exceptions**:
- `ConfigError` (config.py)
- `SynthesisError` (synthesis.py)

**Consistent Pattern**:
```python
try:
    result = synthesis.search(query, limit)
except SynthesisError as e:
    logger.error(f"Search failed: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

Good use of logging, exception translation, and HTTP status codes.

### 1.5 Documentation ⭐⭐⭐⭐⭐

**Exceptional documentation**:
- `docs/ARCHITECTURE.md`: 1,015 lines explaining system design, embeddings, data flow
- `CLAUDE.md`: 847 lines of development guide
- `docs/CHRONICLES.md`: Design decision history
- Inline docstrings with type hints
- OpenAPI docs auto-generated at `/docs`

---

## 2. Concerns

### 2.1 Module-Level Initialization ⚠️ **CRITICAL**

**Location**: `server.py` lines 36-58

**Problem**:
```python
# Lines 36-41: Module-level config initialization
try:
    config = Config()
    logger.info(f"Configuration loaded: {config}")
except ConfigError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Lines 44-55: Module-level Synthesis initialization
try:
    logger.info("Initializing Synthesis client...")
    synthesis = SynthesisClient(...)
    logger.info("✓ Synthesis client ready")
except SynthesisError as e:
    logger.error(f"Failed to initialize Synthesis: {e}")
    raise
```

**Issues**:
1. **Import-time side effects**: Simply importing `server.py` loads model (15s delay)
2. **Testing nightmare**: Can't mock these for unit tests
3. **Circular dependency risk**: If other modules import from server
4. **Startup failure**: Config error prevents module import entirely
5. **Violates lifespan pattern**: You have a lifespan manager (lines 62-77) but don't use it for initialization

**Impact**: 🔴 High - Makes testing difficult, violates best practices

**Recommended Fix**:
Move initialization into lifespan context:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    config = Config()  # ← Move here
    synthesis = SynthesisClient(...)  # ← Move here

    # Share via app.state
    app.state.config = config
    app.state.synthesis = synthesis

    yield

    # Shutdown cleanup
    await synthesis.cleanup()  # if needed
```

### 2.2 sys.path Manipulation ⚠️ **MODERATE**

**Locations**:
- `server.py` lines 24-27 (scripts path)
- `synthesis.py` lines 140-143 (synthesis path)
- `cli.py` line 663 (scripts path again)

**Problem**:
```python
# server.py
scripts_path = Path(__file__).parent.parent.parent / "scripts"
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))
```

**Issues**:
1. **Path pollution**: Modifies global Python import system
2. **Order-dependent**: First import wins
3. **Fragile**: Breaks if directory structure changes
4. **Hard to debug**: Import errors become mysterious
5. **Not portable**: Assumes specific directory layout

**Impact**: 🟡 Moderate - Works but fragile, hard to maintain

**Recommended Fix**:
1. **Make scripts a proper package**: Add `scripts/__init__.py`
2. **Use relative imports**: `from ..scripts import extract_gleanings`
3. **Or use entry points**: Define in `pyproject.toml`

### 2.3 Business Logic in HTTP Layer ⚠️ **MODERATE**

**Location**: `server.py`

**Problem**: Filtering logic mixed with HTTP endpoint code

**Examples**:
- `filter_inactive_gleanings()` (lines 80-120)
- `filter_daily_notes()` (lines 123-148)
- Complex filtering logic in `/search` endpoint (lines 256-315)

**Issues**:
1. **Hard to test**: Need HTTP client to test filtering
2. **Not reusable**: CLI duplicates this logic (cli.py lines 111-126)
3. **Violates SRP**: Server should route, not filter
4. **Coupling**: Changes to filtering require server changes

**Impact**: 🟡 Moderate - Reduces maintainability, increases duplication

**Recommended Fix**:
Create a service layer:

```python
# src/temoa/search_service.py
class SearchService:
    def __init__(self, synthesis_client, gleaning_manager):
        self.synthesis = synthesis_client
        self.gleaning_manager = gleaning_manager

    def search(self, query, filters=None):
        results = self.synthesis.search(query)
        return self._apply_filters(results, filters)

    def _apply_filters(self, results, filters):
        # Filtering logic here
        ...
```

Then use in both server and CLI.

### 2.4 Tight Coupling to Synthesis Internals ⚠️ **MODERATE**

**Location**: `synthesis.py` lines 146-160

**Problem**:
```python
from src.embeddings import EmbeddingPipeline
from src.embeddings.models import ModelRegistry
from src.temporal_archaeology import TemporalArchaeologist
```

Direct imports of Synthesis internal modules.

**Issues**:
1. **Breaking changes**: If Synthesis refactors, Temoa breaks
2. **No abstraction**: Wrapper tightly coupled to implementation
3. **Hard to swap**: Can't easily replace Synthesis with alternative
4. **Testing difficulty**: Need full Synthesis environment

**Impact**: 🟡 Moderate - Acceptable for Phase 1, risky long-term

**Mitigation Options**:
1. **Pin Synthesis version**: Prevent unexpected breaks
2. **Add integration tests**: Detect breaking changes early
3. **Document dependency**: Clear in docs (already done ✓)
4. **Future**: Consider Synthesis as a service (Phase 4)

### 2.5 Gleaning Status Management Split ⚠️ **LOW**

**Locations**:
- Frontmatter status: `gleanings.py` lines 188-213
- JSON status file: `.temoa/gleaning_status.json`

**Problem**: Two sources of truth for gleaning status

**Current Design**:
1. Extraction writes status to frontmatter
2. API writes status to JSON file
3. Search reads from frontmatter (server.py lines 100-106)
4. Status API reads from JSON file

**Issues**:
1. **Inconsistency risk**: Frontmatter and JSON can diverge
2. **Complexity**: Need to check both sources
3. **Performance**: Reading files for every search result

**Impact**: 🟢 Low - Works, but could be simpler

**Recommended Fix**:
Choose one source of truth:
- **Option A**: Frontmatter only (simpler, self-contained)
- **Option B**: JSON only (faster, no file parsing)

Document the choice clearly.

### 2.6 No Dependency Injection ⚠️ **LOW**

**Problem**: Hard to test components in isolation

**Example**:
```python
# server.py - synthesis is global
synthesis = SynthesisClient(...)

@app.get("/search")
async def search(q: str):
    return synthesis.search(q)  # ← Can't mock this
```

**Impact**: 🟢 Low - Tests exist and pass, but could be better

**Future Enhancement**:
Use FastAPI's dependency injection:

```python
def get_synthesis():
    return synthesis

@app.get("/search")
async def search(
    q: str,
    synthesis: SynthesisClient = Depends(get_synthesis)
):
    return synthesis.search(q)
```

Easier to mock for testing.

---

## 3. Code Organization Assessment

### 3.1 Module Structure ⭐⭐⭐⭐

**Current Structure**:
```
src/temoa/
├── __init__.py        (empty - good)
├── __main__.py        (20 lines - entry point)
├── cli.py             (733 lines - comprehensive CLI)
├── config.py          (198 lines - config management)
├── gleanings.py       (303 lines - status management)
├── server.py          (774 lines - HTTP layer)
├── synthesis.py       (471 lines - wrapper)
└── ui/
    └── search.html    (411 lines - web UI)
```

**Assessment**: ✅ **Well-organized**

**Strengths**:
- Clear module boundaries
- Single responsibility per file
- Logical grouping (UI in subfolder)
- Reasonable file sizes (no god objects)

**Potential Split**:
- `server.py` (774 lines) could be split:
  - `server.py`: Core endpoints
  - `filters.py`: Filtering logic
  - `endpoints/`: Separate files per endpoint group

### 3.2 Abstraction Levels ⭐⭐⭐

**Good**:
- Config abstraction (clean properties)
- Synthesis wrapper (hides complexity)
- Error types (domain-specific)

**Missing**:
- Service layer (business logic)
- Repository pattern (data access)
- Domain models (Result, Gleaning classes)

**Impact**: Not critical for Phase 1, but will help scalability.

### 3.3 Dependency Graph

```
cli.py ─────┐
            ├──→ config.py
server.py ──┤   synthesis.py ──→ Synthesis (external)
            ├──→ gleanings.py
scripts/ ───┘
```

**Assessment**: ✅ **Acyclic, clean**

No circular dependencies detected.

---

## 4. Scalability & Maintainability

### 4.1 Performance Scalability ⭐⭐⭐⭐⭐

**Current Performance** (from docs):
- 100 files: 380ms
- 1,000 files: 400ms
- 2,000 files: 410ms
- 5,000 files: 450ms (estimated)
- 10,000 files: 550ms (estimated)

**Assessment**: ✅ **Excellent** - Linear scaling, well within targets

**Bottlenecks Identified**:
1. **Similarity calculation**: 38% of time (necessary)
2. **Index loading**: 25% of time (could cache in RAM)
3. **Filtering**: Reads files for status (could optimize)

**Recommended Optimizations** (if needed):
1. Cache index in RAM (currently loads from disk each search)
2. Cache gleaning statuses (avoid file reads)
3. Use async file I/O for filtering

### 4.2 Code Scalability ⭐⭐⭐

**Current State**: Good for Phase 1-2, needs attention for Phase 3-4

**Will Scale Well**:
- ✅ Adding endpoints (FastAPI pattern clear)
- ✅ Adding CLI commands (Click structure good)
- ✅ Adding config options (properties pattern)

**Will Need Refactoring**:
- ⚠️ Adding complex business logic (needs service layer)
- ⚠️ Adding alternative backends (tight Synthesis coupling)
- ⚠️ Adding authentication (module-level init blocks this)

**Recommended Before Phase 3**:
1. Introduce service layer
2. Move to dependency injection
3. Split large modules
4. Add domain models

### 4.3 Maintainability ⭐⭐⭐⭐

**Strengths**:
- ✅ Excellent documentation
- ✅ Type hints throughout
- ✅ Consistent error handling
- ✅ Good logging
- ✅ Test coverage

**Weaknesses**:
- ⚠️ sys.path manipulation (fragile)
- ⚠️ Module-level initialization (hard to test)
- ⚠️ Some logic duplication (server.py and cli.py)

**Technical Debt**: Low overall, but address concerns 2.1 and 2.2 soon.

---

## 5. Future Phase Readiness

### 5.1 Phase 2.5 (Mobile Validation) ✅ **READY**

Current architecture supports:
- ✅ Mobile access (Tailscale networking)
- ✅ Fast response times (<500ms)
- ✅ obsidian:// URI generation
- ✅ Simple, mobile-first UI

**No blockers**.

### 5.2 Phase 3 (Enhanced Features) ⚠️ **NEEDS REFACTORING**

Planned features:
- PWA support
- Caching layer
- Advanced UI

**Recommended Before Phase 3**:
1. ✅ Fix module-level initialization (Concern 2.1)
2. ✅ Add service layer (Concern 2.3)
3. ⚠️ Add domain models (Results, Gleanings as classes)
4. ⚠️ Improve test coverage for business logic

### 5.3 Phase 4 (LLM Integration) ⚠️ **ARCHITECTURE REVIEW NEEDED**

Planned features:
- `/chat` endpoint with vault context
- Integration with Apantli LLM proxy
- Citation system

**Architectural Questions**:
1. Should Temoa integrate into Apantli, or remain separate?
2. How to handle LLM context (RAG pattern)?
3. Should Synthesis become a service?

**Recommendation**: Revisit architecture in Phase 3, consider microservices pattern.

---

## 6. Specific Recommendations (Prioritized)

### 6.1 Critical (Fix Before Phase 3) 🔴

**1. Fix Module-Level Initialization**
- **File**: `server.py` lines 36-58
- **Action**: Move config and synthesis init into lifespan context
- **Impact**: Enables testing, follows best practices
- **Effort**: 2-3 hours

**2. Remove sys.path Manipulation**
- **Files**: `server.py`, `cli.py`, `synthesis.py`
- **Action**: Make scripts a proper package, use relative imports
- **Impact**: More robust, portable imports
- **Effort**: 1-2 hours

### 6.2 High (Improves Maintainability) 🟡

**3. Introduce Service Layer**
- **Action**: Create `SearchService` class with business logic
- **Impact**: Reusable, testable, follows SOLID principles
- **Effort**: 4-6 hours

**4. Add Domain Models**
- **Action**: Create `SearchResult`, `Gleaning` dataclasses
- **Impact**: Type safety, clear contracts, easier to change
- **Effort**: 2-3 hours

**5. Unify Gleaning Status Management**
- **Action**: Choose frontmatter OR JSON as single source of truth
- **Impact**: Simpler, less error-prone
- **Effort**: 3-4 hours

### 6.3 Medium (Nice to Have) 🟢

**6. Use Dependency Injection**
- **Action**: FastAPI `Depends()` for synthesis, config
- **Impact**: Better testability
- **Effort**: 2-3 hours

**7. Split Large Modules**
- **Action**: Split `server.py` into server + filters + endpoints
- **Impact**: Better organization
- **Effort**: 2-3 hours

**8. Add Integration Tests**
- **Action**: End-to-end tests with real Synthesis
- **Impact**: Catch breaking changes early
- **Effort**: 4-6 hours

### 6.4 Low (Future Enhancements) ⚪

**9. Add Caching Layer**
- **When**: If performance degrades with >5k files
- **Impact**: Faster repeat searches
- **Effort**: 6-8 hours

**10. Consider Repository Pattern**
- **When**: If adding multiple storage backends
- **Impact**: Abstraction for data access
- **Effort**: 8-10 hours

---

## 7. Summary & Verdict

### Overall Assessment: ✅ **ARCHITECTURALLY SOUND**

**Grade**: **B+** (Very Good)

**What's Working Well** ⭐:
- Core architecture is simple, pragmatic, and effective
- Performance exceeds targets by 5x
- Documentation is exceptional
- Clean layering and separation of concerns
- Key decision (direct imports) was brilliant

**What Needs Attention** ⚠️:
- Module-level initialization anti-pattern
- sys.path manipulation fragility
- Business logic in HTTP layer
- Tight coupling to Synthesis internals (acceptable for now)

**Bottom Line**:
The architecture successfully achieves Phase 1-2 goals and will support Phase 2.5 (mobile validation) without changes. However, **address Concerns 2.1 and 2.2 before Phase 3** to avoid technical debt and testing difficulties.

### Recommended Action Plan

**Immediate** (Before Phase 2.5):
- ✅ Document current concerns (this review)
- ✅ Add TODO comments in code for known issues

**Before Phase 3** (1-2 weeks):
1. Fix module-level initialization (2-3 hours)
2. Remove sys.path manipulation (1-2 hours)
3. Introduce service layer (4-6 hours)
4. Add domain models (2-3 hours)

**Before Phase 4** (1-2 months):
1. Architectural review (microservices vs monolith)
2. Consider Synthesis as separate service
3. Design LLM integration pattern

---

## 8. Files Referenced

**Architecture Documentation**:
- `/home/user/temoa/docs/ARCHITECTURE.md` (1,015 lines)
- `/home/user/temoa/CLAUDE.md` (847 lines)
- `/home/user/temoa/docs/IMPLEMENTATION.md`

**Implementation**:
- `/home/user/temoa/src/temoa/server.py` (774 lines)
- `/home/user/temoa/src/temoa/synthesis.py` (471 lines)
- `/home/user/temoa/src/temoa/config.py` (198 lines)
- `/home/user/temoa/src/temoa/gleanings.py` (303 lines)
- `/home/user/temoa/src/temoa/cli.py` (733 lines)

**Project Files**:
- `/home/user/temoa/pyproject.toml`
- `/home/user/temoa/README.md`

---

**Review Date**: 2025-11-22
**Reviewer**: Claude (Sonnet 4.5)
**Project Phase**: Phase 2.5 (Mobile Validation)
**Next Review**: Before Phase 3 implementation
