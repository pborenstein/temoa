# Temoa Origins: A Chronicle

**Period**: Pre-Temoa (2024) → Present (2026-01-04)
**Status**: Knowledge Archaeology Document
**Purpose**: Trace the evolution from failed gleanings system to full vault semantic search

---

## The Foundation: Synthesis Project

**Before Temoa existed**, there was **Synthesis** (`~/projects/obsidian-projects/synthesis`).

**What it was**:
- Local semantic search engine for Obsidian vaults
- Built with sentence-transformers (local embeddings)
- 5 model support (all-MiniLM-L6-v2, all-mpnet-base-v2, etc.)
- CLI-based: `uv run main.py search "query" --json`
- Already indexing **1,899 vault files** (entire vault, not just gleanings)

**What it provided**:
- Semantic search capability (the hard part already solved)
- Multi-model architecture (quality vs speed tradeoff)
- JSON output (perfect for building on top)
- Interest archaeology (`archaeology` command for temporal analysis)
- Production-ready, battle-tested code

**Key insight**:
> You didn't need to build semantic search. You needed to make it **accessible from mobile** and **useful for research workflows**.

**Synthesis was the engine. Temoa became the interface.**

---

## Timeline of Key Insights

### Pre-Temoa: The Old-Gleanings Failure (2024)

**System**: 2,771 lines of Python
**Approach**: Categorization + Static Index Generation + Web App
**Status**: Abandoned

**Architecture**:
- 15+ categories for organizing gleanings
- Complex state management system
- Static HTML index generation
- Separate workflow outside Obsidian
- Manual script runs to regenerate index

**The Problem It Tried to Solve**:
> "Saved links accumulate but are never surfaced"

**Why It Failed**:
```
Over-engineering kills adoption
  ↓
15 categories created friction ("which category?")
  ↓
Manual regeneration created delay
  ↓
Living outside Obsidian created workflow split
  ↓
User abandonment
```

**Key Quote from PROJECT-PROPOSAL.md (Nov 17, 2025)**:
> "The old-gleanings system (2,771 lines of Python) tried to solve this through categorization and static index generation. It failed because:
> - Over-engineered (15+ categories, state management, web app)
> - Created friction (manual script runs, regenerate index)
> - Lived outside Obsidian (separate workflow)
> - Optimized for browsing, not for research-time discovery"

**The Core Insight That Changed Everything**:
> **"You don't have an organization problem. You have a surfacing problem."**

---

## Phase 0-1: Foundation (Nov 17-18, 2025)

**Shift in Thinking**: From categorization to semantic search

**Key Decisions**:

### DEC-XXX: Individual Files vs Aggregation
- **Old approach**: Aggregate gleanings into categorized index
- **New approach**: Individual markdown files, one per gleaning
- **Rationale**:
  - Cleaner separation of concerns (daily notes = ephemeral, gleanings = permanent)
  - Better for semantic search (each gleaning is a discrete unit)
  - Easier to maintain and update individual gleanings

### DEC-XXX: MD5-Based IDs
- **Problem**: How to uniquely identify gleanings for deduplication?
- **Solution**: MD5 hash of normalized URL
- **Rationale**: Same URL = same gleaning (prevents duplicates)

**Scope Explicitly Out**:
From phase-0-1-foundation.md:
```
| ❌ Categorizing gleanings | old-gleanings proved this fails |
| ❌ Complex state management | Adds friction, kills adoption |
| ❌ Organizing knowledge into categories | 2,771 lines of complexity |
```

**The Lesson**:
> "Over-engineering kills adoption. Keep Temoa simple."

**What Was Preserved From Old-Gleanings**:
- Extraction regex patterns for links
- Understanding of gleaning formats in daily notes
- 505 gleanings in state file (Jan-Aug 2025) to migrate

**The Original Vision** (Nov 17, 2025):

From PROJECT-PROPOSAL.md:
> "Fast semantic search across **entire vault (1899+ files)**"
> "Surfaces gleanings when contextually relevant"

**Critical realization**: The vision was **never "search gleanings only"**—it was always **"search entire vault, with gleanings as the killer use case"**.

**Why gleanings were special**:
- Already filtered (you decided these were important)
- Timestamped (temporal context preserved)
- Atomic (one link per note, perfect for embeddings)
- Pre-structured knowledge (huge advantage over raw documents)

**The framing**:
- Gleanings were the **justification** for building Temoa
- Vault search was the **actual product**
- Mobile access was the **enabling constraint** (had to build server)

---

## Phase 2: Gleanings Implementation (Nov 18-19, 2025)

**Goal**: Make 505+ historical gleanings searchable, automate extraction

**Major Components Built**:

### 1. Extraction System (`scripts/extract_gleanings.py` - 319 lines)
**Challenge**: Parse gleanings from daily notes

**Format discovered in the wild**:
```markdown
## Gleanings

- [Title](URL) - Brief description
- [Title](URL)  [14:30]
> Description on next line
```

**Implementation**:
- Regex-based parsing of gleanings sections
- MD5-based gleaning IDs from URLs (deduplication)
- Frontmatter generation with title, URL, date, description
- Obsidian URI generation for deep linking

**Result**: Successfully extracted 6 gleanings from test-vault daily notes

### 2. Historical Migration (`scripts/migrate_old_gleanings.py` - 259 lines)
**Challenge**: Migrate 505 gleanings from old-gleanings JSON format

**Approach**:
- Parse old JSON state file
- Convert to individual markdown files
- Preserve dates, titles, descriptions, URLs
- Mark with `migrated_from: old-gleanings` frontmatter

**Result**: All 505 gleanings migrated successfully → **total 516 gleanings** in test-vault

**The Irony**: The old system's state file became its most valuable artifact—not the code, the data.

---

## Phase 2.5: Deployment & Real-World Usage (Nov 19-25, 2025)

**Milestone**: Gleanings in production, searchable from mobile

**Key Learning**: Gleanings work best as part of unified vault search, not as separate feature

**Automation Established**:
- Daily extraction runs (manual or cron)
- Automatic reindexing after extraction
- Seamless integration with Synthesis

**Then came the wake-up call** (Nov 22, 2025)...

---

## The Scope Shift: From Gleanings to Full Vault Search (Nov 22, 2025)

### The Wake-Up Call: Type Filtering (Commit b780e4e)

**User observation**:
> "the temoa web app filters daily notes. the cli search does not. is that right? I'd like to implement a mechanism that filters on the `type:` field."

**The problem discovered**:
- Search results **cluttered with daily notes**
- Daily notes are the **source** of gleanings (where links are saved)
- Gleanings are the **artifacts** (extracted, curated knowledge)
- Searching daily notes = finding fleeting context
- Searching gleanings = finding permanent knowledge

**The realization**:
```
Daily notes: Ephemeral source (excluded)
Gleanings: Permanent artifacts (searched)
```

**DEC-025: Default exclude_types=["daily"]**

**Rationale**:
> "Gleanings extracted from daily notes are the actual findings"

**Implementation** (Phase 2.5):
- Comprehensive type filtering system
- Frontmatter `type:` field parsing (string or YAML array)
- Inclusive (`--type`) and exclusive (`--exclude-type`) modes
- Multi-select UI dropdowns
- Default excludes `type: daily` to reduce noise

**The shift in thinking**:

**Before**: "How do I search my gleanings?"
**After**: "How do I search my vault and exclude the noise?"

### The Scope Explicitly Expands (Dec 2025)

**Entry 40 (chunking analysis)** made it official:

> **Phase 0-1 assumptions** (November 2025):
> - ✓ Temoa designed for **gleanings only**
> - ✓ Gleanings are small (500 chars)
> - ✓ No need to search full vault
>
> **Current reality** (December 2025):
> - ✗ Vault scope expanded to **full vault indexing (all content types)**
> - ✗ New use case: **Large document libraries** (books, articles, reference docs)
> - ✗ Files up to **9MB** in production use
> - ✗ **Daily notes excluded by default**, so indexed content is everything else

**Three vaults, three different use cases**:

| Vault | Indexed Content (daily excluded) | File Size Range | Primary Use |
|-------|----------------------------------|-----------------|-------------|
| **amoxtli** | Gleanings + writering/llmering | 500-10,000 bytes | Research + writing |
| **rodeo** | Work notes (type varies) | 1,000-10,000 bytes | Project notes |
| **1002** | Project Gutenberg books | 100KB-**9.1MB** | Reading library |

**Content type breakdown discovered**:
- **gleaning**: Extracted links (~500 chars) - ✅ Fully searchable
- **daily**: Daily notes, excluded by default - N/A
- **story**: Books, novels (100KB-9MB) - Required chunking
- **writering/llmering/article/reference**: Varies (500-50,000+ chars) - Mixed
- **note**: General notes - Mixed

**The evolution**:
```
Nov 17: "Search entire vault, surface gleanings"
    ↓
    Gleanings are the justification

Nov 22: "Daily notes clutter results, add type filtering"
    ↓
    Need to exclude SOURCE to find ARTIFACTS

Dec 2025: "Vault scope includes books, articles, all content types"
    ↓
    Full vault search with metadata-based filtering
```

**Gleanings' role transformed**:

From: **The product** (what you search for)
To: **One content type** (among story, article, writering, note, etc.)

**The pattern**:
> Real-world usage reveals true needs. You thought you were building gleaning search. You were actually building **vault search with metadata-based content filtering**. Gleanings were the gateway drug.

---

## Production Hardening: Gleanings Get Smarter (Dec 2025)

### Entry 34: URL Normalization (Dec 6-7, 2025)

**Problem Discovered During Real Usage**:
> GitHub gleanings had verbose, repetitive titles and descriptions

**Observed Pattern**:
```
Before normalization:
  title: "user/repo: A great tool for developers"
  description: "A great tool for developers. - user/repo"

After normalization:
  title: "user/repo"
  description: "A great tool for developers."
```

**Scale**: 776 GitHub gleanings out of 852 total (91% are GitHub!)

**Design Decision**:
- Normalization happens during extraction (new gleanings)
- Backfill script for existing gleanings
- Domain-specific normalizers (GitHub first, extensible for others)
- Backward compatible (non-GitHub gleanings unchanged)

**Key Architectural Choice**:
> Don't break non-GitHub gleanings. 637 gleanings unchanged (intentional).

**Result**:
- Production vault normalized (214 gleanings)
- GitHub repos: cleaner titles, no emojis, no redundant descriptions
- Other domains: backward compatible (unchanged)

### Entry 37: GitHub Enrichment (Dec 13-14, 2025)

**Problem Discovered**:
> GitHub gleanings were minimally useful—just scraped HTML titles with no visibility into repo language, popularity, topics, or archived status.

**Current State**: 266 GitHub gleanings that could be much more informative

**Solution**: Extend `maintain_gleanings.py` to fetch GitHub API metadata

**Architecture Decision**:
> Maintenance tool, not extraction pipeline. Enrichment is retroactive enhancement, not core extraction.

**Enrichment Added**:
```yaml
---
title: "pborenstein/temoa"
url: "https://github.com/pborenstein/temoa"
gleaning_id: "abc123..."
date: 2025-12-13
description: "Local semantic search server for Obsidian - vault-first research"
github:
  language: "Python"
  stars: 42
  topics: ["obsidian", "semantic-search", "fastapi"]
  archived: false
  fork: false
  pushed_at: "2025-12-13T15:30:00Z"
---

# pborenstein/temoa

Local semantic search server for Obsidian - vault-first research workflow

**Language**: Python | **Stars**: 42 | **Topics**: obsidian, semantic-search, fastapi

Last updated: 2025-12-13
```

**Impact**:
- 266 GitHub gleanings can be enriched (~18 minutes for all)
- Search results show language, popularity, and topics
- Archived/unmaintained repos are visible
- Last update timestamp helps judge freshness

**The Evolution**:
```
Old-gleanings: Category-based organization
    ↓
Phase 2: Individual files + semantic search
    ↓
Normalization: Clean up noisy metadata
    ↓
Enrichment: Add value through external APIs
```

---

## Key Evolution Patterns

### 1. From Static to Dynamic

**Old approach**: Pre-generate index, browse by category
**Current approach**: Search when needed, surface by relevance

### 2. From Organization to Discovery

**Old approach**: "Where should this go?" (categorization friction)
**Current approach**: "What's related to this?" (semantic similarity)

### 3. From Standalone to Integrated

**Old approach**: Separate gleanings system, separate workflow
**Current approach**: Gleanings are vault files, unified search

### 4. From Manual to Automated

**Old approach**: Manual script runs, regenerate index
**Current approach**: Automatic extraction, automatic reindexing, maintenance tools

### 5. From Simple to Smart (But Still Simple)

**Phase 2**: Extract title, URL, description → save as markdown
**Normalization**: Clean up domain-specific noise (GitHub)
**Enrichment**: Fetch external metadata (GitHub API)

**But**: Still just markdown files with frontmatter. No complex state, no database, no categories.

---

## Format Evolution

### In Daily Notes (Input)

**Original format** (discovered in Phase 0):
```markdown
## Gleanings

- [Title](URL) - Brief description
```

**Formats added** (discovered during real usage):
```markdown
# Format 2: Timestamp
- [Title](URL)  [14:30]
> Description on next line

# Format 3: Naked URL
- https://example.com/article

# Format 4: Bare URL
https://example.com/article

# Format 5: Multi-line descriptions
- [Title](URL)  [15:54]
> First paragraph
> - Bullet point 1
> - Bullet point 2
>
> Second paragraph
```

**The Pattern**: Discover formats in the wild → support them

### As Individual Files (Output)

**Phase 2** (basic):
```yaml
---
title: "Article Title"
url: "https://example.com/article"
gleaning_id: "abc123..."
date: 2025-11-19
description: "Brief description"
type: gleaning
---
```

**Normalization** (GitHub):
```yaml
---
title: "user/repo"  # Cleaned
description: "No emoji, no redundant repo name"  # Normalized
---
```

**Enrichment** (GitHub):
```yaml
---
title: "user/repo"
description: "Repo description"
github:
  language: "Python"
  stars: 42
  topics: ["tag1", "tag2"]
  archived: false
---
```

**The Pattern**: Start simple → add value based on usage

---

## Failed Experiments (What Didn't Work)

### 1. Categories (Old-Gleanings)
**Why it failed**:
- Friction ("which category?")
- Rigid structure doesn't match organic discovery
- Maintenance burden (categories drift over time)

**What replaced it**: Semantic search + tags in frontmatter (organic, flexible)

### 2. Static Index Generation (Old-Gleanings)
**Why it failed**:
- Manual regeneration = delay = friction
- Index is stale the moment it's generated

**What replaced it**: Real-time search with always-current embeddings

### 3. Separate Web App (Old-Gleanings)
**Why it failed**:
- Workflow split (Obsidian vs gleanings app)
- Duplicate effort (two systems to maintain)

**What replaced it**: Unified search UI, gleanings are just vault files

---

## Successful Patterns (What Worked)

### 1. Individual Files
- Each gleaning is a discrete unit
- Easy to edit, update, delete
- Semantic search works naturally
- No complex state to manage

### 2. MD5-Based IDs
- Deterministic from URL
- Deduplication is automatic
- No central registry needed

### 3. Frontmatter for Metadata
- Structured data (title, URL, date, description)
- Searchable content in body
- Obsidian-native format
- Easy to extend (github metadata, etc.)

### 4. Domain-Specific Intelligence
- GitHub normalization (91% of gleanings!)
- Extensible pattern for other domains
- Backward compatible (don't break existing)

### 5. Maintenance Tools
- Backfill scripts for retroactive improvements
- Status tracking (active/inactive/hidden)
- Link checking (dead link detection)
- Enrichment (fetch external metadata)

---

## The Meta-Lesson

**The complete arc from Synthesis to Temoa**:

```
2024: Synthesis built (vault semantic search engine)
  ↓
  Local embeddings, 1,899 files indexed, CLI-based

2024: Old-gleanings failed (2,771 lines, abandoned)
  ↓
  Over-engineering kills adoption

Nov 17, 2025: "You don't have an organization problem"
  ↓
  Insight: Surfacing > organizing

Nov 17, 2025: Temoa proposed
  ↓
  "Make Synthesis accessible from mobile"
  ↓
  Gleanings are the justification (killer use case)
  ↓
  Vault search is the actual product

Nov 18-19, 2025: Phase 1-2 implementation
  ↓
  FastAPI server wrapping Synthesis
  ↓
  Extract 505 gleanings, make searchable

Nov 22, 2025: Type filtering wake-up call
  ↓
  "Daily notes clutter results"
  ↓
  Realization: Need metadata-based filtering
  ↓
  Gleanings are ONE type among many

Dec 2025: Scope explicitly expands
  ↓
  Books (9MB files), articles, all content types
  ↓
  Full vault search with smart filtering

Present: Three vaults, multiple content types
  ↓
  900+ gleanings (just one part of the system)
  ↓
  Full semantic vault search from mobile (<2s)
```

**The pattern that works**:
1. **Build on existing foundations**: Synthesis already worked
2. **Start simple**: FastAPI wrapper, individual files, basic extraction
3. **Use in production**: Discover real patterns (type filtering, normalization)
4. **Add intelligence**: Normalize, enrich, enhance based on usage
5. **Stay flexible**: No rigid structure, organic growth
6. **Let scope emerge**: Gleanings → full vault search

**The pattern that fails**:
1. **Build from scratch**: Ignore existing tools (Synthesis was already there!)
2. **Design upfront**: 15 categories, complex state
3. **Build infrastructure**: Web app, regeneration scripts
4. **Impose structure**: Force content into predefined categories
5. **Resist change**: "This is a gleanings tool" (scope rigidity)
6. **Abandon**: Friction > value

---

## Current State (2026-01-04)

**System Architecture**:
- **Foundation**: Synthesis (local semantic search engine)
- **Interface**: Temoa (FastAPI server + web UI)
- **Integration**: Direct Python imports (10x faster than subprocess)
- **Deployment**: macOS launchd service, Tailscale network access

**Content Scope**:
- **Three vaults**: amoxtli (research), rodeo (work), 1002 (books)
- **Multiple content types**: gleaning, story, article, writering, llmering, note
- **Daily notes excluded** by default (type filtering)
- **900+ gleanings** (one content type among many)
- **Adaptive chunking** for large files (9MB books fully searchable)

**Gleanings Specifically**:
- **Format support**: 5 input formats recognized
- **Normalization**: GitHub domain-specific (91% of gleanings)
- **Enrichment**: GitHub API metadata (266 repos with stars, language, topics)
- **Maintenance**: Automated extraction, link checking, status tracking
- **Integration**: Part of unified vault search (not standalone system)

**Search Quality**:
- Hybrid search (BM25 + semantic with RRF fusion)
- Tag boosting (5x multiplier for frontmatter tags)
- Cross-encoder re-ranking (20-30% precision improvement)
- Time-aware scoring (recent work boosted)
- Type filtering (exclude daily, include specific types)
- Search profiles (repos, recent, deep, keywords, default)

**Performance**:
- **Mobile**: <2s response time from phone
- **Incremental reindexing**: 30x faster (5s vs 159s)
- **Multi-vault**: LRU cache (3 vaults, ~1.5GB RAM)

**What's working**:
- Vault-first research workflow adopted
- Gleanings surfacing when relevant (not as separate feature)
- Books, articles, notes all searchable
- Low friction (faster than googling)
- No categories, no complexity, no manual indexing

**What's evolved**:
- From: 2,771 lines of abandoned Python (old-gleanings)
- To: ~500 lines of extraction + maintenance + FastAPI wrapper
- From: "Search my gleanings"
- To: "Search my vault, filter by metadata"
- From: "Gleanings are the product"
- To: "Gleanings are one content type in full vault search"

---

## Future Directions

### Short-term
- More domain-specific normalizers (YouTube, arXiv, etc.)
- Smart enrichment (fetch metadata for high-value domains)
- Dead link detection and cleanup

### Medium-term
- Temporal analysis (interest archaeology via `synthesis archaeology`)
- Citation graphs (which gleanings reference each other)
- Automatic topic clustering (no categories, but emergent themes)

### Long-term (Phase 4+)
- LLM-generated summaries for long articles
- Automatic tagging based on content analysis
- Cross-vault gleaning discovery (find related across projects)

---

## Key Documents

**Original vision**: `docs/archive/original-planning/PROJECT-PROPOSAL.md`
**Phase 2 implementation**: `docs/chronicles/phase-2-gleanings.md`
**Normalization**: `docs/chronicles/production-hardening.md` (Entry 34)
**Enrichment**: `docs/chronicles/production-hardening.md` (Entry 37)
**Current workflow**: `docs/GLEANINGS.md`

---

## Lessons for Future Projects

**1. Build on existing foundations**
- Synthesis already worked (1,899 files indexed)
- Don't rebuild what exists—wrap it, extend it, make it accessible
- "Make Synthesis mobile-accessible" > "Build semantic search from scratch"

**2. Let the justification evolve into the product**
- Started: "Build this for gleanings" (justification)
- Became: "Full vault search with filtering" (actual product)
- Gleanings were the gateway drug, not the endgame

**3. Organization is not the problem**
- Old-gleanings: 2,771 lines organizing
- Temoa: ~500 lines surfacing
- Surfacing > organizing

**4. Complexity kills adoption**
- 15 categories = friction
- Simple files + smart search = adoption
- Metadata-based filtering > rigid structure

**5. Real usage reveals true needs**
- Type filtering: Discovered daily notes were noise (not predicted)
- GitHub normalization: 91% of gleanings (scale surprise)
- Scope expansion: Books, articles (use cases emerged)
- You can't design this upfront—you discover it

**6. Start simple, add intelligence**
- Phase 1: FastAPI wrapper around Synthesis
- Phase 2: Extract gleanings → save as files
- Phase 2.5: Type filtering (exclude daily)
- Production: Normalization → enrichment → chunking
- Each step additive, based on real usage

**7. The code you don't write is the code you don't maintain**
- No categories, no state management, no custom indexes
- Just files, frontmatter, and Synthesis
- Wrapper code < 2,000 lines total
- Simplicity scales

**8. Scope rigidity kills evolution**
- If Temoa stayed "gleanings only": Books wouldn't work
- If no type filtering: Daily notes would clutter results
- If no normalization: GitHub gleanings stay noisy
- Flexibility to evolve > adherence to original vision

---

**Created**: 2026-01-04
**Author**: Traced from git history, chronicles, and documentation
**Type**: Knowledge Archaeology - Origins Chronicle
**Purpose**: Preserve the complete arc from Synthesis → Old-Gleanings failure → Temoa → Full vault search

**The complete story**:
- How Synthesis provided the foundation
- How old-gleanings' failure taught "surfacing > organizing"
- How gleanings justified building Temoa
- How real usage revealed the true need (full vault search with metadata filtering)
- How scope flexibility enabled evolution

**Related Documents**:
- KNOWLEDGE-ARCHAEOLOGY.md - The pattern at multiple scales
- GLEANINGS.md - Current workflow
- CHRONICLES (all phases) - Implementation timeline
- docs/archive/original-planning/PROJECT-PROPOSAL.md - First vision
- ~/projects/obsidian-projects/synthesis - The foundation
