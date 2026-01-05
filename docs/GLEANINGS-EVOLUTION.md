# The Evolution of Gleanings

**Period**: Pre-Temoa (2024) → Present (2026-01-04)
**Status**: Knowledge Archaeology Document
**Purpose**: Trace how our thinking about gleanings evolved from failed complexity to elegant simplicity

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

**The evolution of gleanings mirrors the evolution of Temoa**:

```
Start: Complex system trying to impose order
  ↓
Failure: Over-engineering kills adoption
  ↓
Insight: "You don't have an organization problem"
  ↓
Pivot: Semantic search surfaces what's relevant
  ↓
Success: Simple files + smart search
  ↓
Refinement: Add value based on real usage
  ↓
Present: 900+ gleanings, searchable, enriched, useful
```

**The pattern that works**:
1. **Start simple**: Individual files, basic extraction
2. **Use in production**: Discover real patterns
3. **Add intelligence**: Normalize, enrich, enhance
4. **Stay flexible**: No rigid structure, organic growth

**The pattern that fails**:
1. **Design upfront**: 15 categories, complex state
2. **Build infrastructure**: Web app, regeneration scripts
3. **Impose structure**: Force gleanings into categories
4. **Abandon**: Friction > value

---

## Current State (2026-01-04)

**Gleanings in production**: 900+
**Format support**: 5 input formats recognized
**Normalization**: GitHub domain-specific
**Enrichment**: GitHub API metadata (266 repos)
**Integration**: Unified vault search (semantic + BM25 + tags)
**Maintenance**: Automated extraction, link checking, status tracking
**Mobile**: Fast search from phone (<2s)

**What's working**:
- Vault-first research workflow adopted
- Forgotten gleanings resurfacing regularly
- Low friction (faster than googling)
- No categories, no complexity, no manual indexing

**What's evolved**:
- From 2,771 lines of abandoned Python
- To ~500 lines of focused extraction + maintenance
- From "where does this belong?"
- To "what's related to this?"

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

**1. Organization is not the problem**
- Old-gleanings spent 2,771 lines organizing
- Temoa spends ~500 lines surfacing
- Surfacing > organizing

**2. Complexity kills adoption**
- 15 categories = friction
- Simple files + smart search = adoption

**3. Real usage reveals true needs**
- GitHub is 91% of gleanings (discovered after deployment)
- Normalization became critical (not designed upfront)
- Enrichment added value (based on real usage patterns)

**4. Start simple, add intelligence**
- Phase 2: Extract → save
- Normalization: Clean → save
- Enrichment: Fetch → enhance
- Each step additive, not revolutionary

**5. The code you don't write is the code you don't maintain**
- No categories, no state, no indexes
- Just files, frontmatter, and semantic search
- Simplicity scales

---

**Created**: 2026-01-04
**Author**: Traced from git history, chronicles, and documentation
**Type**: Knowledge Archaeology
**Purpose**: Preserve thinking evolution for future reference
**Related**: KNOWLEDGE-ARCHAEOLOGY.md, GLEANINGS.md, CHRONICLES (all phases)
