# Gleanings Rethink - February 2026

## Context

Filtering implementation (Phase 1 complete) has surfaced fundamental issues with how gleanings work. Time to step back and rethink the gleaning system before continuing with Phase 2 filtering.

**Date**: 2026-02-06
**Branch**: `filters-and-combs` (current), may need new branch
**Status**: Problem statement phase

---

## The Core Problems

### 1. GitHub Gleaning Template is Broken

**The Issue**: GitHub repos are a major gleaning source, but the current template is awful.

**What's wrong**:
- Redundant information (repo name repeated, "Contribute to..." suffixes)
- Missing the essential info: "What does this repo do? Why did I save it?"
- URL normalization helps with redundancy but doesn't solve the core problem
- The gleaning is supposed to capture "why this was interesting" but GitHub gleanings don't

**Example of current state** (from normalizers.py):
```markdown
Before: user/repo: A great tool for developers. - user/repo
After: user/repo | A great tool for developers.
```

**What we actually want**:
```markdown
Title: user/repo
Description: [Why I saved this - manually written or from my daily note context]
Metadata: stars, language, topics (already added via GitHub enrichment)
```

**Why it matters**: Gleanings exist because something was "interesting but not interesting enough to capture the whole text." For GitHub repos, capturing the whole text is meaningless anyway - we need to capture *why it was interesting*.

---

### 2. Two-Phase Filtering Architecture

**The Insight**: There are fundamentally two different kinds of filtering.

#### Pre-Fetch Filtering (Query Parameters)
**When**: Before search happens
**Where**: Server-side, affects what gets retrieved
**Why**: Efficiency - don't retrieve what you don't want
**Examples**:
- `type:project` - only search Project notes
- `-type:daily` - exclude daily notes from search
- Status filters (active/inactive gleanings)

**Implementation**: Query parameters sent to server
```
/search?q=fastapi&type=project&exclude_types=daily
```

#### Post-Fetch Filtering (Client-Side)
**When**: After search results returned
**Where**: Client-side, filters existing results
**Why**: Exploration - "show me just the project notes from these results"
**Examples**:
- Looking at 50 results about "python testing"
- Want to see which are Project notes vs Gleanings vs regular notes
- Toggle filters to explore different facets

**Implementation**: Current Phase 1 filtering in Explorer view
```
Filter syntax: type:project path:L/Gleanings
(filters displayed results, no server round-trip)
```

**Key Distinction**:
- Pre-fetch: "Search only these types" (affects retrieval)
- Post-fetch: "From these results, show only these types" (affects display)

**Both are valid, both are needed, they serve different purposes**

---

### 3. Some Filters Can Only Work Pre-Fetch

**Examples**:
- Type filtering for semantic search - can't search unindexed notes
- Vault selection - can't post-filter across vaults
- Model selection - can't change embeddings after retrieval

**Examples of Post-Only**:
- Exact path matching - server doesn't know full paths during ranking
- Complex boolean logic - easier client-side
- Dynamic filter combinations - instant feedback without server round-trip

**Examples of Either**:
- Tag filtering - can do both (BM25 boost pre-fetch, display filter post-fetch)
- Status filtering - can do both (exclude inactive pre-fetch, toggle post-fetch)

**Implication**: The UI needs to make this distinction clear
- Some filters should be in "Search Options" (pre-fetch)
- Some filters should be in "Filter Results" (post-fetch)
- Some filters might appear in both (with different semantics)

---

### 4. Type System: Infinite but Conventional

**The Reality**:
- The `type` frontmatter property has no schema
- Users can put anything: `type: project`, `type: gleaning`, `type: daily`, `type: literature-note`, `type: moc`, `type: person`, etc.
- But there ARE conventions in any given vault

**What This Means for Filtering**:
- Can't hardcode type values in UI
- Need to discover types from vault (like tag discovery)
- Need to support "common filters" (e.g., `-type:daily` as a standard exclusion)
- Need to support ad-hoc type filtering for exploration

**Possible Approach**:
- Server endpoint: `GET /types?vault=X` returns all type values in vault
- Config option: `standard_exclusions: [daily, template]`
- UI: Type dropdown populated from vault + common presets
- Save common filter combinations as... profiles? presets? saved searches?

---

### 5. Standard Filters / Search Presets

**The Need**: Some filters should be standard/default.

**Examples**:
- Never show `type:daily` in results (too noisy, rarely useful)
- Never show `type:template` in results
- Always exclude `status:inactive` gleanings (unless explicitly searching)
- Always exclude paths matching `.archive/` or `.templates/`

**Obsidian Parallel**: Obsidian has search operators and saved searches
- Less cognitive load (standard syntax)
- Easier to store in config files
- Can share searches across tools/scripts

**Naming Question**: How to describe this?
- "Filter-on-search" vs "filter-on-results"?
- "Pre-fetch filters" vs "post-fetch filters"?
- "Query filters" vs "display filters"?
- "Search filters" vs "result filters"?

**pborenstein's question**: "I need to come up with a way to say this: filter-on-search filter-on-results"

---

## Gleanings Purpose Statement

**What is a gleaning?**

> A gleaning is something that was interesting enough to save, but either:
> 1. Not interesting enough to capture the whole text, OR
> 2. Capturing the whole text is meaningless (e.g., GitHub repos, which change over time)

**The gleaning should capture**:
1. What it is (title, URL)
2. Why it was interesting (description from context)
3. When you found it (temporal context)
4. How to find it again (semantic searchability)

**Current gap**: GitHub gleanings capture #1, #3, #4 but not #2 (the "why").

---

## The Meta Question: How to Approach This Work

**pborenstein's concern**: "I'm not in the mood to do three experiments (gleanings, filtering, and branch tracking) all at once."

**Current state**:
- On branch: `filters-and-combs`
- Phase 1 filtering complete (client-side post-fetch filtering)
- Need to: fix gleanings + add pre-fetch filtering + figure out standard filters

**Options**:

### Option A: Continue on `filters-and-combs`
**Pro**: Everything in one place, easier to test integration
**Con**: Mixing gleaning template fixes with filtering architecture changes

### Option B: New branch for gleanings, merge back
**Pro**: Separate concerns, can iterate on gleanings without touching filtering
**Con**: Merge conflicts likely, project-tracker not set up for multi-branch

### Option C: Go back to main, new branch from there
**Pro**: Clean slate, filtering work stays separate
**Con**: Filtering progress might inform gleaning fixes (they're related)

### Recommendation: Option A (stay on current branch)
**Rationale**:
- Gleanings and filtering are deeply intertwined (types, status, standard filters)
- Phase 1 filtering provides foundation for testing gleaning improvements
- Can commit gleanings work separately even on same branch
- Avoid branch-tracking complexity for now

---

## Next Steps (Proposed)

**Phase 1: Document the problems** ✓ (this document)

**Phase 2: Define the solutions** (next conversation)
- What should the GitHub gleaning template look like?
- How should pre-fetch vs post-fetch filtering work in the UI?
- How should type discovery work?
- What should standard filters look like in config?

**Phase 3: Implement gleanings fixes** (code changes)
- Update extraction script for better GitHub handling
- Update maintenance script to enrich descriptions better
- Test on existing gleanings (migration script?)

**Phase 4: Implement two-phase filtering** (code changes)
- Add pre-fetch filter query parameters
- Separate UI sections for "Search Options" vs "Filter Results"
- Add type discovery endpoint
- Add standard filters to config

**Phase 5: Test and iterate** (validation)
- Test with real gleanings
- Validate that GitHub repos are now useful
- Validate that filtering feels natural

---

## Open Questions

1. **GitHub gleaning descriptions**: Should we require manual descriptions? Extract from daily note context? Use README first paragraph?

2. **Type discovery**: Should `/types` endpoint be lazy (only check indexed files) or eager (scan all files)?

3. **Standard filters config**: Should this be per-vault or global? Where does it live?

4. **Filter naming**: What do we call pre-fetch vs post-fetch filters? (needs to be intuitive)

5. **Saved searches**: Do we need a way to save common filter combinations? (e.g., "project notes only", "recent gleanings", "active literature notes")

6. **Gleaning value**: "I think they have a lot of value (maybe not?)" - is the gleaning system worth investing in? Or should we simplify/rethink more radically?

---

## Terminology Brainstorm (for "filter-on-search" vs "filter-on-results")

Options for naming the two phases:

| Pre-Fetch (Server) | Post-Fetch (Client) | Notes |
|-------------------|---------------------|-------|
| Search filters | Display filters | Clear but generic |
| Query filters | Result filters | Technical but accurate |
| Scope filters | View filters | Implies breadth vs selection |
| Retrieval filters | Presentation filters | Wordy but precise |
| Index filters | List filters | Too implementation-focused |
| Before filters | After filters | Simple but vague |
| Fetch filters | Sort filters | "Sort" is misleading (not just sorting) |

**Current thinking**: "Query filters" vs "Result filters" feels most accurate and least confusing.

