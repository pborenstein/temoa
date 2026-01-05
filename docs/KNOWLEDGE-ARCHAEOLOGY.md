# Knowledge Archaeology: The Pattern

**Date**: 2026-01-04
**Status**: Vision Document
**Insight**: Temoa solves the same problem at every scale

---

## The Core Problem

**How do I surface the information I already have at the time that I need it when I didn't know I would need it in the first place?**

This is the fundamental challenge that Temoa addresses - but the pattern appears at multiple scales:

### Lifetime/Bookmarking Level (Current Temoa Usage)
- **Corpus**: 500+ links saved over 2 years
- **Challenge**: Didn't know which one I'd need today
- **Solution**: Semantic search surfaces the relevant gleaning when context emerges

### Repository Level (Meta-Temoa)
- **Corpus**: 50 design decisions over 6 months
- **Challenge**: Didn't know which decision I'd need to revisit
- **Solution**: Same - semantic search surfaces "we rejected X because Y" when Y changes

### Career/Lifetime Level (Future Vision)
- **Corpus**: All project docs across all repositories
- **Challenge**: Accumulated design wisdom scattered across projects
- **Solution**: Index all CHRONICLES.md, DECISIONS.md, design docs from every project

---

## The Pattern: Same Problem, Same Solution

At every scale:
1. **Information captured without knowing future context**
2. **Metadata provides structure** (tags, frontmatter, IDs)
3. **Semantic search surfaces relevance** when context emerges later
4. **Time-aware scoring** (recent work more relevant, but old wisdom still accessible)

---

## The Infohoarder's Dilemma

> "To lose an idea is to lose the world" - paraphrasing the Talmud

The classic fear: What if we tried something that failed, but later learned something that would have made it succeed?

**The trap**: Hoarding everything makes nothing findable.

**The insight**: The answer isn't more documentation, it's better **retrieval mechanisms**.

---

## Meta-Temoa: Indexing Development Knowledge

Temoa's own documentation IS a vault:

```bash
# Add Temoa docs as a searchable vault
temoa vaults add temoa-dev ~/projects/temoa/docs

# Search during development
temoa search "rejected because performance" --vault temoa-dev
temoa search "deferred until we have" --vault temoa-dev
temoa search "why did we choose FastAPI" --vault temoa-dev
temoa search "chunking decision" --vault temoa-dev
```

The docs already have the structure:
- **Frontmatter**: Decision IDs (DEC-XXX), entry numbers, dates, status
- **Tags**: phase, component, type
- **Searchable content**: The narrative of what you tried and why

---

## What This Enables

### 1. Deferred vs Rejected Decisions

**Pattern to adopt in DECISIONS.md**:
- **Rejected**: "Won't work because of fundamental constraint"
- **Deferred**: "Not now, but revisit if X changes"
- **Would reconsider if**: Explicit conditions for revisiting

When conditions change, search for those conditions:
```bash
temoa search "would reconsider if performance" --vault temoa-dev
```

### 2. Knowledge Archaeology During Development

**Before implementing a feature**:
```bash
# Did we already consider this?
temoa search "authentication approaches" --vault temoa-dev

# Why did we reject it?
temoa search "rejected JWT" --vault temoa-dev

# What would change our mind?
temoa search "deferred until" --vault temoa-dev
```

### 3. Near-Miss Recovery

**Example**: You rejected adaptive chunking early (too complex, unclear need). Later, when indexing a 9MB book fails, search:
```bash
temoa search "chunking large files" --vault temoa-dev
```

Surfaces the old decision with context: "Rejected in Phase 1 because complexity, but noted would reconsider if we index books."

### 4. Cross-Project Learning

**Future vision**: Index docs from ALL projects:
```bash
temoa vaults add apantli-dev ~/projects/apantli/docs
temoa vaults add synthesis-dev ~/projects/synthesis/docs

# Later, working on authentication in a new project
temoa search "authentication patterns we've used" --vault apantli-dev
temoa search "JWT vs session decision" --vault temoa-dev
```

Your accumulated design wisdom becomes searchable across your entire development history.

---

## Documentation Patterns That Support This

### 1. Retrospective Links

When you learn something new, grep for related old decisions and add:
```markdown
**Update (2026-01-04)**: See Entry 42 - chunking now makes sense because we're indexing books. Revisiting this decision.
```

### 2. "What Would Change This" Sections

In DECISIONS.md:
```markdown
## DEC-085: Rejected Adaptive Chunking (Phase 1)

**Decision**: Don't implement chunking yet.
**Rationale**: Added complexity, unclear need for 3KB average files.

**Would reconsider if**:
- We start indexing long-form content (books, papers)
- Users report missing content in search results
- Performance improves enough to handle overhead
```

### 3. Chronicle Entries for Near Misses

```markdown
## Entry N: Almost Tried X

**Context**: Considered implementing X but chose Y instead.
**Why Y**: Simpler, met immediate needs, proven pattern.
**Why not X**: Unknown complexity, no clear benefit yet.
**Conditions for X**: Would revisit if we need Z or learn Q.
```

### 4. Explicit "Failed Experiments" Section

In Chronicles:
```markdown
## Failed Experiments (Phase 1)

- **Query expansion via embeddings**: Too slow, unclear benefit over TF-IDF
- **Client-side re-ranking**: Network overhead too high
- **Multiple cross-encoder passes**: Diminishing returns after first pass
```

Searchable later when circumstances change.

---

## The Recursive Nature

**Temoa is built to solve this problem for gleanings.**

**This conversation reveals Temoa should index itself.**

**The pattern: Tools that think should eat their own dog food.**

When your development docs are searchable with the same tool you're building, you create a feedback loop:
1. Build Temoa to search knowledge
2. Use Temoa to search Temoa's development knowledge
3. Improve Temoa based on what works for searching Temoa
4. Repeat

---

## Next Steps (Future)

### Short-term
- Add temoa docs as a vault
- Test searching Chronicles/Decisions during development
- Document what works, what doesn't

### Medium-term
- Establish patterns for "deferred" vs "rejected" decisions
- Add "would reconsider if" sections to key decisions
- Create retrospective links when revisiting old choices

### Long-term
- Index docs from other projects (Apantli, Synthesis, etc.)
- Build career-level knowledge base
- Develop patterns for cross-project learning

---

## Key Insight

**The problem Temoa solves isn't about bookmarks or notes or project docs.**

**It's about surfacing accumulated knowledge when context makes it relevant.**

**That pattern is scale-invariant.**

Whether it's 500 gleanings, 50 design decisions, or a lifetime of development work - the mechanism is the same:

1. Capture structured information
2. Add semantic meaning
3. Search when context emerges
4. Surface what you didn't know you'd need

---

**Author**: Conversation with Claude (Sonnet 4.5)
**Type**: Vision Document
**Related**: CHRONICLES.md, DECISIONS.md, ARCHITECTURE.md
**Status**: Foundational insight, needs validation through use
