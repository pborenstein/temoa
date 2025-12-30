# Phase 3.5: Specialized Search Modes - Chronicles

> **Timeline**: 2025-12-30 onwards
> **Status**: In Progress
> **Goal**: Enable search profiles optimized for different content types, adaptive chunking for large documents, and metadata-aware ranking

---

## Entry 1: Search Profile System Implementation (2025-12-30)

**Context**: After completing Production Hardening, user requested a new phase to improve search strategy by specializing for different content types. Current one-size-fits-all approach doesn't optimize for different use cases (repos vs recent work vs deep reading).

### The Vision

**User's request**: "I'd like to have a way to tune for different kinds of searches"

**Specific use cases identified**:
1. **Searching for repos**: Keyword-heavy, metadata-driven (stars, topics, language)
2. **Recent daily notes**: Temporal focus, aggressive time-decay
3. **Long-form reading**: Semantic-heavy, need chunking for >2,500 char docs
4. **Technical/keyword search**: Exact matching, minimal semantic interpretation

**Key insight**: Different searches need different weightings (semantic vs BM25), different time curves, different features (chunking, cross-encoder, expansion).

### The Design: Search Profiles

**Core concept**: Pre-configured search parameter bundles optimized for specific use cases.

**5 Built-in Profiles**:

1. **repos** (GitHub/tech focus):
   - 30% semantic, 70% BM25
   - 2x BM25 boost
   - Metadata boosting: stars (log scale), topics (3x), language (1.5x)
   - No time decay (recency doesn't matter for repos)
   - No cross-encoder (speed over precision)
   - Only searches gleanings by default
   - No chunking (gleanings are small)

2. **recent** (temporal focus):
   - 50/50 hybrid
   - 7-day half-life (aggressive - prefer this week!)
   - 90-day hard cutoff (ignore older content)
   - 50% max boost for today
   - Searches daily notes + notes + writering
   - Chunking enabled (daily notes can be long)

3. **deep** (long-form semantic):
   - 80% semantic, 20% BM25
   - Cross-encoder enabled (precision matters)
   - Chunking enabled: 2,000 char chunks, 400 char overlap
   - Shows chunk context
   - Up to 3 chunks per file
   - Excludes daily/gleaning (focuses on articles/books)

4. **keywords** (exact matching):
   - 20% semantic, 80% BM25
   - 1.5x BM25 boost
   - No cross-encoder (speed)
   - No query expansion
   - Chunking enabled

5. **default** (balanced - current behavior):
   - 50/50 hybrid
   - Standard time decay (90-day half-life, 20% boost)
   - All features enabled
   - Excludes daily notes by default

### Implementation

**Architecture**:
- `SearchProfile` dataclass with all search configuration
- `SEARCH_PROFILES` registry with built-in profiles
- Profile loading in server lifespan (supports custom profiles from config)
- Profile parameter in API/CLI with override support

**Files created**:
- `src/temoa/search_profiles.py` (224 lines)
  - SearchProfile dataclass
  - 5 built-in profile definitions
  - get_profile(), list_profiles(), load_custom_profiles()
- `tests/test_search_profiles.py` (10 comprehensive tests)
- `docs/phases/phase-3.5-specialized-search.md` (complete 6-phase plan)

**API changes**:
- `/search?profile=<name>` - New profile parameter (default: "default")
- `/profiles` - New endpoint listing all profiles
- Profile defaults apply, individual parameters can override

**CLI changes**:
- `temoa search --profile <name>` - Profile flag (default: "default")
- `temoa profiles` - List all available profiles with descriptions

**Configuration support**:
- Custom profiles can be defined in config.json
- Custom profiles cannot override built-in names (safety)
- Loaded at server startup

### Testing & Validation

**Unit tests** (10 tests, all passing):
- Built-in profiles exist and are valid
- get_profile() works correctly
- Each profile has correct configuration
- list_profiles() returns all profiles
- Custom profile loading works
- Cannot override built-in profiles

**Manual testing**:
```bash
temoa profiles  # ✓ Lists 5 profiles with descriptions
temoa search "python library" --profile repos --limit 3  # ✓ Works, applies gleaning filter
uv run python -c "from src.temoa.server import app; ..."  # ✓ Server imports successfully
```

### Design Decisions

**Why user-selectable instead of auto-detect?**
- User knows their intent better than we can guess
- Different queries to same content may want different modes
- Recommendation system can suggest (Phase 3.5.4) but user decides
- Explicit > implicit for search behavior

**Why 5 profiles?**
- Covers identified use cases
- Not overwhelming (2-4 is ideal, 5 is acceptable)
- Easy to remember and explain
- Can add custom profiles if needed

**Why profiles apply defaults that parameters can override?**
- Best of both worlds: convenience + control
- `--profile repos` gives you repo search instantly
- `--profile repos --rerank` enables cross-encoder if you want precision
- Power users can fine-tune, casual users get good defaults

**Profile state**: Stateless (no persistence)
- Profile chosen per-query, not session-wide
- Simpler implementation
- UI can persist selected profile in localStorage
- Each search is independent

### Interesting Episodes

**The parameter override dance**: Initially confused about when profile defaults apply vs when user parameters take precedence. Solution: Profile sets defaults BEFORE parsing user parameters, so user always wins. This feels natural.

**Metadata boosting structure**: Profiles define `metadata_boost` config but implementation deferred to Phase 3.5.3. This works because repos profile can specify the config even if backend doesn't use it yet. When Phase 3.5.3 implements it, repos profile "just works".

**Chunking readiness**: All profiles specify chunking settings even though chunking isn't implemented yet (Phase 3.5.2). This is intentional - when chunking lands, profiles will automatically benefit from correct settings.

### What's Next

**Phase 3.5.2: Adaptive Chunking** (4-5 days)
- The BIG ONE - solves 2,500 char limit
- Makes 9MB books fully searchable
- Chunk overlap prevents context loss
- See Entry 40 (chunking analysis) for full context

**Remaining sub-phases**:
- 3.5.3: Metadata Boosting (implement what repos profile defines)
- 3.5.4: Profile Recommendation (auto-suggest best profile)
- 3.5.5: UI Updates (profile dropdown in web UI)
- 3.5.6: Documentation & Testing

### Lessons Learned

**Planning pays off**: The 31KB phase plan document (phase-3.5-specialized-search.md) made implementation straightforward. Knew exactly what to build and why.

**Test-driven confidence**: Writing 10 unit tests before manual testing caught several edge cases early. Tests give confidence to refactor later.

**Split documentation works**: Phase plan in docs/phases/, chronicle entry here, decision table in CHRONICLES.md. Each serves different purpose, no duplication.

**User-driven design**: User's specific examples ("searching for repos", "recent daily notes") led to concrete profiles instead of abstract configuration.

---

**Entry created**: 2025-12-30
**Author**: Claude (Sonnet 4.5)
**Type**: Feature Implementation - Search Profiles
**Impact**: HIGH - Enables specialized search experiences
**Duration**: ~2.5 hours (planning 30min, implementation 1.5h, testing 30min)
**Branch**: `phase-3.5-search-modes`
**Commits**:
- `e68f724` - "feat: add search profile system (Phase 3.5.1)"

**Files created**:
- `src/temoa/search_profiles.py` (224 lines)
- `tests/test_search_profiles.py` (10 tests)
- `docs/phases/phase-3.5-specialized-search.md` (31KB plan)

**Files modified**:
- `src/temoa/server.py` (+82 lines) - Profile integration, /profiles endpoint
- `src/temoa/cli.py` (+70 lines) - --profile flag, profiles command

**Lines changed**: +378/-2 (net +376 lines)

**Tests**: 10/10 passing ✓
