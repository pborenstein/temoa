# DECISIONS.md - Architectural Decision Registry

> **Purpose**: Centralized registry of all significant architectural and design decisions made during Temoa development.
>
> **Format**: Each decision has a unique number (DEC-XXX), title, summary, and link to the chronicle entry where it was discussed.
>
> **For LLMs/Contributors**: Follow the governance process below when adding new decisions.

**Last Updated**: 2026-02-07
**Total Decisions**: 97 (DEC-001 through DEC-102, with historical gaps documented)

---

## Decision Governance Process

### When to Record a Decision

Record a decision when you make a choice that:
- Affects system architecture or behavior
- Has alternatives that were explicitly rejected
- Future developers might question ("why did we do it this way?")
- Sets a pattern or precedent for future work
- Involves a trade-off between competing concerns

### How to Add a New Decision

**Step 1: Find the next decision number**
- Check the table below for the last DEC-XXX number
- Increment by 1 (e.g., if last is DEC-100, use DEC-101)

**Step 2: Document in chronicle entry**
```markdown
### Key Decisions

**DEC-XXX: Short Title**
- **Rationale**: Why this decision was made
- **Alternative**: What we didn't choose and why
- **Impact**: What this affects (code, UX, performance, etc.)
- **Trade-offs**: What we gain vs. what we lose
```

**Step 3: Add to this table**
- Add row to the table below with format: `| DEC-XXX: Title | Entry# | One-line summary |`
- Keep table sorted by decision number
- Commit both chronicle file AND this DECISIONS.md file together

**Step 4: Reference in code (optional)**
```python
# DEC-042: Search is primary, vault is infrequent
# Vault selector moved to bottom of page for mobile UX
vault_selector_position = "bottom"
```

### Validation

Before committing, run:
```bash
# Future: Add validation script
./scripts/validate_decisions.sh
```

This checks for:
- Duplicate decision numbers
- Decisions in chronicles but not in this table
- Gaps in numbering sequence

---

## Historical Notes

**Decision number gaps exist** (particularly DEC-002 through DEC-012):
- Early development didn't use formal decision tracking
- Some decisions were documented in chronicle entries but not added to the table
- Duplicates were resolved by assigning new numbers (DEC-085+)
- This is intentional and preserved for historical continuity

**Format evolved over time**:
- Early: Decisions embedded in entries without formal numbers
- Phase 2+: Formal DEC-XXX numbering introduced
- Phase 3: Decision table created in CHRONICLES.md
- Production: Moved to dedicated DECISIONS.md (this file)

---

## Decision Registry

| Decision | Entry | Summary |
|----------|-------|---------|
| DEC-001: Project name (Temoa) | 6 | Named after Nahuatl "to seek" |
| DEC-002: Why No Chunking? (Phase 0-1) | 5 | Gleanings are small (<500 chars), no chunking needed [superseded by DEC-085 for large docs] |
| DEC-003: Why No Caching Initially? | 5 | Synthesis fast enough without caching, avoid premature optimization |
| DEC-004: Vault Format Agnosticism | 2 | Scripts use relative paths or `$SCRIPT_DIR`, no hardcoded paths |
| DEC-005: Vector Database Storage Location | 2 | Use pathlib methods, not string manipulation for paths |
| DEC-006: Obsidian Sync Exclusion | 2 | Generated artifacts go in .gitignore, don't sync to mobile |
| DEC-007: Network Security Model | 2 | Trust Tailscale network, no auth/HTTPS in Phase 1 |
| DEC-008: Configuration Over Convention | 2 | All paths/locations in config.json, easy to change decisions |
| DEC-009: Direct imports over subprocess | 4, 6 | 10x faster searches, model loaded once at startup |
| DEC-010: Gleanings output location | 9 | Individual files in L/Gleanings/ directory |
| DEC-011: Reindex force default | 9 | Reindex defaults to incremental (force=False) |
| DEC-012: Keep Synthesis for Phase 1-2 | 5 | Synthesis is production-ready, don't modify, evaluate for Phase 3 |
| DEC-013: Modern FastAPI lifespan | 6 | Better resource management, replaces deprecated event handlers |
| DEC-014: Rename from Ixpantilia | 6 | Simpler, more memorable name |
| DEC-015: Split implementation docs | 6 | Clearer phase tracking, separate files per phase |
| DEC-016: Three-status model | 13 | active/inactive/hidden for gleanings |
| DEC-017: Auto-restore inactive gleanings | 13 | Links that come back to life are restored automatically |
| DEC-018: Reason in frontmatter | 13 | Store status change reason in both frontmatter and status file |
| DEC-019: Click CLI over custom parsing | 8 | Familiar UX pattern, comprehensive help text |
| DEC-020: Separate `index` vs `reindex` | 8 | Clear intent, index=full rebuild, reindex=incremental |
| DEC-021: Postel's Law for Gleanings | 10 | Be liberal in input, conservative in output |
| DEC-022: Title fetching for naked URLs | 10 | Fetch web titles for completeness when URL has no markdown title |
| DEC-023: Case-sensitive pattern matching | 10 | Only search Daily/Journal (capital-case), not daily/journal |
| DEC-024: Themes by Period feature | 14 | Document for future, focus on present search quality |
| DEC-025: Default exclude daily type | 15 | Reduce noise in search results, daily notes rarely relevant |
| DEC-026: Hybrid search for daily notes | 15 | Daily notes work better with BM25+semantic than pure semantic |
| DEC-027: Compact collapsible results | 17 | Default collapsed, expand on demand to save mobile space |
| DEC-028: Centralized state management | 17 | Versioned localStorage, race condition prevention |
| DEC-029: Safe DOM manipulation | 17 | Replace innerHTML with createElement (XSS protection) |
| DEC-030: Barber pole progress indicator | 18 | Classic macOS-style indeterminate progress for long operations |
| DEC-031: Confirmation dialog for reindex | 18 | Prevent accidental expensive operations |
| DEC-032: Checkboxes below button | 18 | Action first, options second (natural visual hierarchy) |
| DEC-033: Modification time for change detection | 19 | Fast, already tracked (vs content hash which requires I/O) |
| DEC-034: Rebuild BM25 fully (not incremental) | 19 | BM25 fast (<5s), merging adds complexity |
| DEC-035: DELETE→UPDATE→APPEND merge order | 19 | Immutable order to avoid index corruption |
| DEC-036: Multi-vault storage strategy | 20 | Auto-derive as vault/.temoa/ (co-location with data) |
| DEC-037: Validation before operations | 20 | Fail early with clear error, require --force override |
| DEC-038: Auto-migration of old indexes | 20 | Seamless upgrade, no user action required |
| DEC-039: Clean dropdown, info in badges | 21 | Vault selector clean (just names), metadata in badges |
| DEC-040: State priority | 21 | URL param > localStorage > default vault |
| DEC-041: Removed Status link from footer | 21 | Footer clutter, /health endpoint rarely needed by users |
| DEC-042: Search is primary, vault is infrequent | 22 | Move vault selector to bottom (search is primary action) |
| DEC-043: Common settings above the fold | 22 | Move hybrid checkbox outside Options (frequent use) |
| DEC-044: Inline search button for mobile | 22 | Button inside search box (visible with keyboard up) |
| DEC-045: Actions first on management page | 22 | Reorder sections (actions > stats, most important first) |
| DEC-046: Replace gear icon with text | 22 | "Manage" text aligned right (clearer navigation intent) |
| DEC-047: Lifespan over module-level init | 23 | Use FastAPI lifespan for initialization (testability, best practice) |
| DEC-048: Keep Synthesis sys.path usage | 23 | Isolate to helper method (bundled dependency, simpler than importlib) |
| DEC-049: App state pattern for dependencies | 23 | Store in app.state, extract in endpoints (simpler than Depends()) |
| DEC-050: Scripts as package | 23 | Move to src/temoa/scripts/ (proper structure, no sys.path hacks) |
| DEC-051: Modification time for incremental extraction | 24 | Use st_mtime for change detection (fast, already tracked) |
| DEC-052: Incremental by default for auto-reindex | 24 | Auto-reindex uses force=False (30x speedup, 5s vs 2min) |
| DEC-053: Use uvicorn.config.LOGGING_CONFIG | 25 | Modify uvicorn's config, don't replace it (proven pattern from apantli) |
| DEC-054: Enable re-ranking by default | 26 | Re-ranking on by default (significant quality gain for 200ms cost) |
| DEC-055: Re-rank top 100 candidates | 26 | Balance between recall and speed (100 pairs @ 2ms = 200ms) |
| DEC-056: Use ms-marco-MiniLM-L-6-v2 model | 26 | Fast (~2ms/pair), accurate (MS MARCO trained), proven in production |
| DEC-057: TF-IDF over LLM-based expansion | 27 | Fast (~50ms), no external APIs, deterministic, proven technique |
| DEC-058: Expand only short queries (<3 words) | 27 | Short queries benefit most, saves latency, simple rule |
| DEC-059: Show expanded query to user | 27 | Transparency builds trust, educational, allows refinement |
| DEC-060: Exponential decay (not linear) | 27 | Natural, intuitive half-life parameter, smooth gradient |
| DEC-061: Default half-life of 90 days | 27 | Matches common vault patterns, configurable per-user |
| DEC-062: Apply boost before re-ranking | 27 | Combines recency with relevance, clean separation of concerns |
| DEC-063: Comprehensive search documentation | 28 | Document all mechanisms, rationale, and performance (SEARCH-MECHANISMS.md) |
| DEC-064: Archive completed implementation plans | 28 | Clean docs/ after phase completion, preserve in archive/ |
| DEC-065: Navigation README for docs/ | 28 | Index all documentation (docs/README.md for discovery) |
| DEC-066: Cache-first for UI, network-first for API | 29 | Service worker uses different strategies per resource type |
| DEC-067: rsvg-convert over ImageMagick | 29 | Proper Unicode emoji rendering in PNG icons |
| DEC-068: Standalone display mode for PWA | 29 | Launches without browser chrome (native app feel) |
| DEC-069: Version 0.4.0 → 0.5.0 | 29 | Minor bump for PWA (significant new capability) |
| DEC-070: Checkbox organization by frequency | 30 | Hybrid at top, quality toggles in Options (2x2 grid) |
| DEC-071: Search history max 10 items | 31 | Balance utility and UI clutter (browser pattern) |
| DEC-072: Show history only when input empty | 31 | Don't interfere with typing/autocomplete |
| DEC-073: GitHub-style `/` shortcut | 31 | Familiar pattern, selects text for replacement |
| DEC-074: Query persists after search | 31 | User feedback - query disappearing was annoying |
| DEC-075: Query expansion opt-in | 33 | Real-world usage: short queries often names, not topics |
| DEC-076: JavaScript state is single source of truth | 34 | Per-vault filter preferences, eliminate HTML/JS sync bugs |
| DEC-077: Sanitize at endpoint level | 35 | Vault data unchanged on disk, only JSON output affected |
| DEC-078: Use replacement character | 35 | Preserves text length/structure (� instead of drop/skip) |
| DEC-079: Recursive sanitization | 35 | Catches surrogates in all nested structures |
| DEC-080: Follow proven patterns exactly | 36 | When modeling on existing pattern, copy exactly unless blocking issue |
| DEC-081: Registry pattern for URL normalization | 37 | Extensible, testable, single responsibility |
| DEC-082: Comprehensive emoji removal | 37 | Clean text for search, Unicode regex all ranges |
| DEC-083: Backward compatible pass-through | 37 | Don't break non-GitHub gleanings |
| DEC-084: Two-phase approach (extract + backfill) | 37 | Don't require re-extraction of all gleanings |
| DEC-085: Chunking required for large documents | 40 | Adaptive chunking for files >4K chars (deferred to Phase 4) |
| DEC-086: Enrich via maintenance, not extraction | 44 | Keep extraction fast, enrichment optional |
| DEC-087: Require GITHUB_TOKEN | 44 | 5000 req/hour authenticated vs 60 unauthenticated |
| DEC-088: Preserve "user/repo: Description" format | 44 | More informative than bare user/repo |
| DEC-089: Topics as JSON array/YAML list | 44 | Structured data for filtering |
| DEC-090: Only enrich missing data | 44 | Idempotent, skip if github_stars exists |
| DEC-091: README excerpt max 500 chars | 44 | ~2-3 sentences, fits search preview |
| DEC-092: obsidiantools for graph analysis | 58 | Production-ready (502 stars), NetworkX integration, lazy loading |
| DEC-093: Two layers of relatedness | 57-58 | Explicit links (wikilinks) + Implicit similarity (embeddings) |
| DEC-094: Lazy graph loading per vault | 58 | ~90s load time, cache on first request not startup |
| DEC-095: Remove search profiles feature | 64 | Unused abstraction; direct query params sufficient |
| DEC-096: Obsidian-compatible filter parser | 70 | Lexer+parser with AST for property syntax, boolean operators, grouping |
| DEC-097: Two-phase filtering architecture | 73-74 | Query Filter (server pre-filtering) + Results Filter (client post-filtering) |

---

## Deprecated/Superseded Decisions

These decisions were made during development but later superseded by refined approaches:

| Old Number | New Number | Reason |
|------------|------------|--------|
| DEC-010 (No Caching) | DEC-003 | Duplicate with different meaning, consolidated |
| DEC-011 (FastAPI) | DEC-013 | Superseded by lifespan pattern decision |
| DEC-012 (Synthesis Through Phase 2) | - | Decision revisited and extended, original preserved |
| DEC-016 (Individual Files) | DEC-016 (Three-Status) | Number reused, original less significant |
| DEC-017 (MD5 IDs) | DEC-017 (Auto-Restore) | Number reused, original implementation detail |
| DEC-018 (State Tracking) | DEC-018 (Reason in Frontmatter) | Evolved, both preserved |
| DEC-021 (Pause Phase 3) | DEC-021 (Postel's Law) | Number reused, Postel's Law more enduring |
| DEC-022 (Title Fetching) | DEC-024 (Themes by Period) | Number conflict resolved |
| DEC-030 (Error Boundaries) | DEC-030 (Barber Pole) | Number reused, consolidated UI decisions |
| DEC-031 (Consolidated Options) | DEC-031 (Confirmation Dialog) | Number reused, both UI decisions |

---

## Missing Decision Numbers (Historical Gaps)

**DEC-002 through DEC-012**: Early development decisions were documented in entries but not formally numbered until Phase 2. These have been backfilled above.

**Why gaps exist**: The formal DEC-XXX numbering system was introduced mid-project. Early entries discussed decisions without assigning numbers. During Phase 3, a decision table was created, but not all historical decisions were backfilled. This reconciliation (2025-12-14) filled most gaps.

---

## How to Use This Document

**As a contributor**:
- Check this table before making significant architectural choices
- See if a similar decision was already made
- Follow established patterns unless there's a compelling reason to diverge
- Add new decisions following the governance process above

**As a reviewer**:
- Verify that significant PRs include decision documentation
- Check that decision numbers are unique and sequential
- Ensure decisions are added to both chronicle entry AND this table

**As an LLM**:
- Reference decision numbers in code comments when relevant
- When making architectural choices, check if a similar decision exists
- Always add new decisions following the governance process
- Commit chronicle entry and DECISIONS.md together

---

**Created**: 2025-12-14
**Governance Process**: Established 2025-12-14
**Reconciliation**: Added 19 historical decisions (DEC-002 through DEC-041 gaps)
**Format**: Inspired by Architecture Decision Records (ADR) pattern, adapted for chronicle-based documentation

---

## DEC-102: Option B - Single LIVE Slider (2026-02-07)

**Status**: ✅ Accepted

**Context**:
- Users reported confusion between FETCH and LIVE sliders - both seemed to control semantic/BM25 blending
- FETCH slider actually controlled which searches ran (semantic-only, BM25-only, or both)
- When both searches ran, RRF merged them with fixed weights regardless of slider position
- User expectation: Slider at 0% = semantic only, 100% = BM25 only, with gradual blending in between
- RRF's fixed formula meant slider positions between 0.1-0.9 all gave the same results

**Decision**:
Implement Option B architecture:
- **Server**: Always run both semantic + BM25 searches, merge with RRF, return raw scores
- **Client**: Single LIVE slider instantly re-blends scores without server call
- **Remove**: FETCH hybrid slider (redundant, confusing)
- **Keep**: LIVE slider for instant experimentation (0%=semantic, 100%=BM25)

**Alternatives Considered**:

1. **Option A: Make FETCH slider do weighted blending**
   - Replace RRF with weighted average on server
   - Both FETCH and LIVE would do same thing (redundant)
   - Rejected: Two sliders doing identical work is confusing

2. **Option C: Different roles for each slider**
   - FETCH: Controls retrieval strategy (which searches run)
   - LIVE: Controls final display ranking
   - Rejected: Too complex, users wouldn't understand the difference

**Consequences**:
- ✅ **Simpler**: One slider, one mental model
- ✅ **Instant feedback**: Client remix ~5ms vs server call ~450ms
- ✅ **Experimentation**: Can try 10 blends in 2 seconds
- ✅ **Always get both**: Server runs both searches, user chooses blend
- ⚠️ **Always pays cost**: Both searches always run (~50ms overhead vs single search)
- ⚠️ **RRF smoothing**: Semantic/BM25 differences may be subtle due to RRF's conservative merging

**Implementation**:
- Removed `hybrid_weight` parameter from server
- Server always passes `hybrid=true` to synthesis
- UI always sends `hybrid: 'true'` parameter
- LIVE slider blends: `final = (1-w)*semantic + w*bm25`
- Inspector optimized: Only scores section updates, no graph/similar re-fetch

**See Also**: Chronicle Entry 76

**Commits**: 50b9cad

---

## DEC-097: Two-Phase Filtering Architecture (2026-02-07)

**Status**: ✅ Accepted

**Context**:
- Users wanted flexible filtering: by property (`[type:gleaning]`), tag (`#python`), path (`folder/subfolder`), file name
- Need both pre-filtering (reduce search scope) and post-filtering (refine cached results)
- Performance critical: Searching 3,000 files takes 30+ seconds if filter is too inclusive

**Decision**:
Implement two-phase filtering architecture:

1. **Query Filter** (Server-side, pre-fetch)
   - Generic property/tag/path/file filtering BEFORE semantic search
   - JSON query params: `include_props`, `exclude_props`, `include_tags`, etc.
   - Properties format: `[{prop: "type", value: "gleaning"}]`
   - Filters applied at Stage 5 of pipeline (after search, before re-ranking)
   - Config option: `search.default_query_filter` for automatic exclusions

2. **Results Filter** (Client-side, post-fetch)
   - Obsidian-compatible syntax parser (lexer + AST)
   - Filters cached results without server call
   - Boolean operators: AND (space), OR (`OR`), NOT (`-`)
   - Grouping with parentheses
   - Clear button, persists to localStorage

**Architectural Limitation**:
- Cannot filter BEFORE semantic search (Synthesis limitation)
- Query Filter applied at Stage 5 (after entire vault searched)
- **Inclusive filters slow**: `[type:daily]` searches 3,059 files → 30+ seconds
- **Exclude filters fast**: `-[type:gleaning]` limits results → 6 seconds
- Workaround: Cancel button (AbortController) for long queries

**Performance Impact**:
- Exclude filters: 15-20x speedup (e.g., `-[type:daily]` reduces results from 3,059 to ~3,000)
- Include filters: No speedup (must search all, then filter)
- Default filter (`-[type:daily]`) improves most queries

**Alternatives Considered**:

1. **Single-phase filtering** (only client-side)
   - Rejected: Always fetches full result set, slow for targeted queries

2. **Pre-filtering at Synthesis level**
   - Rejected: Requires modifying Synthesis internals, breaks encapsulation

3. **Type-specific filters only**
   - Rejected: User wanted arbitrary property filtering

**Consequences**:
- ✅ **Flexible**: Any property/tag/path/file can be filtered
- ✅ **Fast for exclude filters**: Common case (exclude daily notes) is fast
- ✅ **Cacheable**: Client-side Results Filter avoids re-fetching
- ⚠️ **Slow for inclusive filters**: Use guidance/cancel button to mitigate
- ⚠️ **Duplicate filter logic**: Property filtering exists in both client/server

**Implementation**:
- Query Filter: `extractServerFilters()` parses AST → JSON params → server applies
- Results Filter: `parseFilter()` → AST → `evaluateFilter()` on cached results
- Cancel support: AbortController passed to fetch, checked in filter loops
- Default filter: Applied automatically unless overridden

**See Also**: Chronicle Entries 73-74

**Commits**: 6911066 (Query Filter), 876ff8d (15-20x speedup)

---
