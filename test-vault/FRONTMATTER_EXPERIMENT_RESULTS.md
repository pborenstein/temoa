# Frontmatter Weighting Experiment Results

**Date**: 2025-12-14
**Experiment**: Phase 1 - Simple frontmatter concatenation
**Method**: Prepend "Title: {title}. Tags: {tags}." before body content

## Hypothesis

Including frontmatter (title, tags) in embedded text should improve search quality for queries that match tag values or document titles.

## Implementation

Modified `synthesis/src/embeddings/vault_reader.py`:
```python
def _build_embedding_text(self, title: str, tags: List[str], body: str) -> str:
    """Build text for embedding with frontmatter prepended."""
    parts = []
    parts.append(f"Title: {title}.")
    if tags:
        parts.append(f"Tags: {', '.join(tags)}.")
    parts.append(body)
    return " ".join(parts)
```

## Test Queries and Results

### Baseline (No Frontmatter Weighting)

| Query | Expected Match | Found? | Top 3 Results |
|-------|----------------|---------|---------------|
| python tools | Areas/Synthesis.md (tags: [tool, python]) | ❌ | Gleanings only |
| semantic search projects | Projects/Temoa.md (tag: semantic-search) | ✅ | #1 (0.51) |
| productivity systems | Areas/PKM.md (tag: productivity) | ❌ | Gleanings only |
| zettelkasten books | Books/Smart Notes.md (tags: [book, zettelkasten]) | ❌ | Gleanings only |
| smart notes | Books/How to Take Smart Notes.md (title match) | ✅ | #1 (0.70) |
| obsidian plugins | Projects/Temoa.md (tag: obsidian) | ❌ | Gleanings only |
| pkm learning | Areas/PKM.md (tags: [pkm, learning]) | ~ | #2 (0.46) |
| writing books | Books/Smart Notes.md (tags: [book, writing]) | ❌ | Gleanings only |

**Score: 2.5 / 8** (31% success rate)

### Phase 1 (With Frontmatter Concatenation)

| Query | Expected Match | Found? | Top 3 Results |
|-------|----------------|---------|---------------|
| python tools | Areas/Synthesis.md (tags: [tool, python]) | ❌ | Gleanings only |
| semantic search projects | Projects/Temoa.md (tag: semantic-search) | ✅ | #1 (0.54) ↑ |
| productivity systems | Areas/PKM.md (tag: productivity) | ❌ | Gleanings only |
| zettelkasten books | Books/Smart Notes.md (tags: [book, zettelkasten]) | ❌ | Gleanings only |
| smart notes | Books/How to Take Smart Notes.md (title match) | ✅ | #1 (0.72) ↑ |
| obsidian plugins | Projects/Temoa.md (tag: obsidian) | ❌ | Gleanings only |
| pkm learning | Areas/PKM.md (tags: [pkm, learning]) | ~ | #2 (0.45) |
| writing books | Books/Smart Notes.md (tags: [book, writing]) | ❌ | Gleanings only |

**Score: 2.5 / 8** (31% success rate)

### Direct Tag Query Tests

| Query | Expected | Found? | Score |
|-------|----------|--------|-------|
| synthesis semantic search | Areas/Synthesis.md | ✅ | #1 (0.77) - EXCELLENT |
| zettelkasten | Books/Smart Notes.md | ❌ | Not in top 10 |
| book | Books/Smart Notes.md | ❌ | Not in top 5 |

## Key Findings

### 1. Frontmatter IS Being Embedded

Evidence:
- Content length increased from ~1400 chars to 1473 chars for Smart Notes book
- Metadata shows tags: `['zettelkasten', 'writing', 'book']`
- Query "synthesis semantic search" scores 0.77 (excellent)

### 2. But Results Show Minimal Improvement

- Overall success rate: 31% → 31% (unchanged)
- Slight score improvements on queries that already worked (+0.02 to +0.03)
- Still missing most tag-based matches

### 3. The Problem: Semantic Distance

**Key Insight**: Semantic embeddings don't do keyword matching - they measure *conceptual similarity*.

Examples:
- ❌ "python tools" is too generic to match the specific context of Synthesis
- ✅ "synthesis semantic search" is semantically close to the content AND tags
- ❌ "zettelkasten" alone doesn't match because the book talks ABOUT zettelkasten, not just having the tag
- ✅ "smart notes" works because it's in the title AND discussed in the body

## Why Simple Concatenation Isn't Enough

### Problem 1: Tags Are Context-Free

Tags like `[python, tool]` don't carry much semantic weight when embedded. They're just isolated words without context.

**Embedded text:**
```
Title: Synthesis. Tags: tool, semantic-search, python. Local semantic search engine...
```

**Query:** "python tools"
**Why it fails:** The model sees "python" and "tool" as isolated tokens among 1400+ chars of unrelated content about semantic search. The semantic distance is still large.

### Problem 2: Gleanings Dominate

The vault has 563 files, many are gleanings with richer body content. Tags don't carry enough weight to overcome strong body matches.

### Problem 3: No Exact Matching

BM25 (keyword) + semantic (concepts) hybrid search should help, but tags still don't boost enough.

## What We Learned About My Confidence Levels

**I was 85% confident concatenation would help**: Reality showed 0-5% improvement.

**Why I was wrong:**
1. Overestimated how much positional weighting matters in sentence-transformers
2. Underestimated how gleanings' rich body content would dominate
3. Didn't account for semantic vs keyword matching difference

**Where I was right:**
- Frontmatter CAN be embedded (it is)
- Direct title matches work well (0.70-0.77 scores)
- The mechanism works, just not as effectively as predicted

## Recommended Next Steps

### Option A: Stronger Weighting (Repetition)

Repeat tags multiple times to increase their weight:

```python
# Heavy tag weighting
text = f"{title}. {title}. {' '.join(tags * 5)}. {body}"
```

**Pros:** Might push tag importance higher
**Cons:** Crude, may dilute body content importance

### Option B: BM25 Field Boosting

Boost BM25 scores when query terms match tags:

```python
if query_term in tags:
    bm25_score *= 2.0
```

**Pros:** Works for exact keyword matches, no re-indexing
**Cons:** Only helps BM25 side, not semantic

### Option C: Separate Tag Embeddings

Embed tags separately and use weighted fusion:

```python
tag_embedding = model.encode(' '.join(tags))
body_embedding = model.encode(body)
final_sim = 0.4 * tag_sim + 0.6 * body_sim
```

**Pros:** Maximum control, true weighting
**Cons:** 2x indexing cost, complex search logic

### Option D: Accept Current Performance

The system already works well for:
- Title matches (0.70+ scores)
- Full-context queries ("synthesis semantic search")
- Body content semantic similarity

Maybe tags aren't as important as we thought?

## My Recommendation

**Try Option B (BM25 field boosting) first:**

1. Zero re-indexing cost
2. Helps the keyword-match case (where tags excel)
3. Can implement in 20 lines of code
4. If it doesn't help, we learned something

**Then maybe Option A (repetition)** if BM25 boosting helps but isn't enough.

**Save Option C for later** - it's the "nuclear option" with highest cost.

## Conclusion

Simple frontmatter concatenation **does work mechanically** (frontmatter is embedded), but provides **minimal search quality improvement** (<5%) because:

1. Semantic embeddings favor contextual similarity over isolated keywords
2. Tag words don't carry enough semantic weight when mixed with rich body content
3. The test queries were more keyword-focused than the semantic model can handle well

This experiment revealed an important insight: **tags and semantic search are solving different problems**. Tags are for categorization (keyword), semantic search is for conceptual similarity. We need a hybrid approach that respects both.
