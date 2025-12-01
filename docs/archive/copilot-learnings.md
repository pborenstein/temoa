# Temoa: Key Learnings from Obsidian Copilot

> **Purpose**: Extract practical implementation insights from Copilot's RAG/semantic search to guide Temoa development

**Created**: 2025-11-18
**Status**: Analysis Complete

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Chunking Strategy](#chunking-strategy)
3. [Dual Search Architecture](#dual-search-architecture)
4. [Mobile-First Performance](#mobile-first-performance)
5. [Context Preparation for LLMs](#context-preparation-for-llms)
6. [Vector Store Implementation](#vector-store-implementation)
7. [Practical Recommendations for Temoa](#practical-recommendations-for-Temoa)

---

## Executive Summary

### What Copilot Got Right (Learn From This)

1. **Dual search modes**: Lexical (fast, no pre-indexing) + Semantic (embeddings-based)
2. **Chunk-based retrieval**: Not full notes, but 6000-char chunks with stable IDs
3. **Mobile-optimized**: < 20MB memory, ephemeral indexing, grep-first recall
4. **XML context format**: Structured `<retrieved_document>` blocks for LLMs
5. **Progressive refinement**: Cheap operations first (grep), expensive later (full-text)

### What's Relevant to Temoa

- **Synthesis already has embeddings** → Start with semantic-only (simpler)
- **Chunking may help gleanings** → Each gleaning is small, probably doesn't need chunking
- **Context formatting** → Adopt XML structure for LLM consumption (future vault-first chat)
- **Performance patterns** → Grep-first recall applicable to file scanning
- **Mobile considerations** → Server-based, so less critical, but inform API design

---

## Chunking Strategy

### How Copilot Chunks Documents

**File**: `src/search/v3/chunks.ts`

```typescript
// Chunk ID format: "note_path#chunk_index"
// Examples:
//   "Daily/2024-11-17.md#0"
//   "Daily/2024-11-17.md#1"
//   "Projects/Temoa.md#0"

interface Chunk {
  id: string;              // note_path#chunk_index
  notePath: string;        // original note path
  chunkIndex: number;      // 0-based position
  content: string;         // chunk text with headers
  contentHash: string;     // integrity validation
  title: string;           // note title
  heading: string;         // section heading
  mtime: number;           // modification time
}
```

### Chunking Algorithm: Heading-First

**Source**: `src/search/v3/chunks.ts:246-308`

```
1. Read note content
2. Get headings from metadata cache (sorted by position)
3. If no headings → treat entire note as one chunk
4. If has headings:
   a. For each heading section:
      - Extract content from heading to next heading (or EOF)
      - If section ≤ 6000 chars → single chunk
      - If section > 6000 chars → split by paragraphs using RecursiveCharacterTextSplitter
   b. Assign sequential chunk indices across entire note
```

### Chunk Content Format

Each chunk includes a **header** for context:

```markdown
NOTE TITLE: [[Project Temoa]]

NOTE BLOCK CONTENT:

## Architecture

[actual section content here...]
```

**Why this matters**:
- LLM sees note title even when receiving middle chunks
- Provides context for standalone chunk understanding
- Enables citation by note title

### Key Parameters

```typescript
const CHUNK_SIZE = 6000;  // characters per chunk
const overlap = 0;        // no overlap (simpler)
const maxBytesTotal = 10 * 1024 * 1024;  // 10MB cache limit
```

**Splitter separators** (in order of preference):
```
["\n\n", "\n", ". ", " ", ""]
```

### Memory Management

**Cache architecture** (`src/search/v3/chunks.ts:99-116`):

```typescript
// Simple Map-based cache (no LRU eviction)
private cache: Map<string, Chunk[]> = new Map();
private memoryUsage: number = 0;

// Budget check before caching
if (this.memoryUsage + chunkBytes <= options.maxBytesTotal) {
  this.cache.set(notePath, chunks);
  this.memoryUsage += chunkBytes;
} else {
  logWarn("Skipping cache, would exceed memory budget");
}
```

**Memory split** (from v3 README):
- 35% → Chunk cache
- 65% → FlexSearch index

### Auto-Regeneration on File Changes

**Source**: `src/search/v3/chunks.ts:156-181`

```typescript
// Validates cache on access
if (file.stat.mtime > chunks[0].mtime) {
  logInfo("File modified, regenerating chunks");
  chunks = await this.regenerateChunks(notePath);
}
```

**Temoa Insight**: Synthesis could track mtimes and re-embed only changed notes.

---

## Dual Search Architecture

### Two Retrieval Modes

Copilot v3 offers **lexical** OR **semantic** OR **merged** search:

```
┌─────────────────────────────────────────────────────┐
│ User Query: "semantic search implementations"       │
└───────────────┬─────────────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐   ┌──────────────┐
│ LEXICAL      │   │ SEMANTIC     │
│ (v3 Search)  │   │ (Orama)      │
└──────┬───────┘   └──────┬───────┘
       │                  │
       ▼                  ▼
   Grep Scan         Vector Search
       ↓                  ↓
   Chunking          Embedding Match
       ↓                  ↓
   FlexSearch        Similarity Rank
       ↓                  ↓
   Boosting          Score Normalize
       │                  │
       └────────┬─────────┘
                ▼
        ┌──────────────────┐
        │ MergedRetriever  │
        │ - Dedupe by ID   │
        │ - Blend scores   │
        │ - Sort & limit   │
        └──────────────────┘
```

### Lexical Search Pipeline

**File**: `src/search/v3/README.md`

**Flow**:
```
User Query
  → QueryExpander (LLM generates variants + extracts salient terms)
  → Grep Scan (recall up to 200 file paths)
  → ChunkManager (heading-first chunks, 800-2000 chars each)
  → FullTextEngine (ephemeral FlexSearch index)
  → Boosting (folder/graph/tag bonuses)
  → Score Normalization (0.02-0.98 range)
  → Final Results
```

**Performance**:
- Grep scan: < 50ms for 1k files
- Chunking: < 50ms for 500 candidates → ~1000 chunks
- Full-text build: < 100ms for 1000 chunks
- **Total latency: < 200ms P95**
- **Memory peak: < 20MB mobile**

### Semantic Search (Orama)

**File**: `src/search/dbOperations.ts`

**Index format**: Orama vector database
**Storage**: `.obsidian/copilot-index/` (with sync) or `.copilot/` (vault root)
**Embeddings**: OpenAI, Anthropic, Google, Ollama, etc.

**Build process**:
1. Extract note content
2. Chunk documents (same chunking algorithm as lexical)
3. Generate embeddings for each chunk
4. Store in Orama DB with metadata
5. Persist to disk

**Query process**:
1. Generate embedding for query
2. Vector similarity search in Orama
3. Return top K chunks with scores
4. Convert to Document format

### Merged Retriever (Fusion)

**File**: `src/search/v3/MergedSemanticRetriever.ts`

```typescript
// Runs both engines in parallel
const [lexicalDocs, semanticDocs] = await Promise.all([
  lexicalRetriever.getRelevantDocuments(query),
  semanticRetriever.getRelevantDocuments(query)
]);

// Dedupe by chunk ID, preferring lexical results
const merged = deduplicateByChunkId(lexicalDocs, semanticDocs);

// Blend scores (lexical ×1.0, semantic ×0.7)
const scored = blendScores(merged);

// Sort and limit
return scored.sort(byScore).slice(0, maxK);
```

**Why prefer lexical on collision?**
- Lexical = deliberate keyword/tag matching (user intent)
- Semantic = paraphrase recall (broader)
- When both match, lexical is more precise

### Field Weights (Lexical Search)

From `src/search/v3/README.md:108`:

```
Title:   3.0x
Heading: 2.5x
Path:    2.0x
Tags:    4.0x   ← Highest weight!
Body:    1.0x
```

**Temoa Insight**: Tags are CRITICAL. Your gleanings should have good tags!

---

## Mobile-First Performance

### Design Principles

From `src/search/v3/README.md`:

1. **Memory-bounded**: < 20MB on mobile
2. **Ephemeral indexes**: No persistent full-text index
3. **Progressive refinement**: Fast grep → full-text search
4. **No pre-indexing required**: Works out-of-the-box

### Grep-First Recall Strategy

**Why grep first?**

- Native OS operation (very fast)
- Reduces candidate set BEFORE heavy processing
- Limits memory usage (max 200 candidates)

**Implementation pattern** (`src/search/v3/README.md:80-87`):

```
Query: "semantic search tools"

Grep Stage:
  → Searches for: ["semantic", "search", "tools"]
  → Finds: 200 candidate file paths (capped)
  → Time: < 50ms

Chunking Stage:
  → Only process those 200 files
  → Generate chunks: ~1000 chunks
  → Time: < 50ms

Full-Text Stage:
  → Index only those 1000 chunks (not entire vault)
  → FlexSearch ephemeral index
  → Time: < 100ms
```

**Total pipeline: < 200ms** instead of seconds

### Memory Budget Split

From v3 architecture:

```
Total RAM: 20MB mobile / 100MB desktop

Split:
  35% → Chunk text cache
  65% → FlexSearch index metadata
```

**Why this matters for Temoa**:
- Server-side, so less critical
- But informs how much to cache in RAM vs re-fetch
- Synthesis could adopt similar budget strategy

### Mobile Detection Pattern

**File**: `src/search/dbOperations.ts:49-55`

```typescript
if (Platform.isMobile && settings.disableIndexOnMobile) {
  this.isIndexLoaded = false;
  this.oramaDb = undefined;
} else if (Platform.isMobile && !settings.disableIndexOnMobile) {
  // Re-initialize DB if mobile setting enabled
  await this.initializeDB(embeddings);
}
```

**Temoa doesn't need this** (server-based), but shows how to optimize for device constraints.

---

## Context Preparation for LLMs

### XML Document Format

**File**: `src/LLMProviders/chainRunner/VaultQAChainRunner.ts:131-137`

```typescript
const context = retrievedDocs
  .map((doc: any) => {
    const title = doc.metadata?.title || "Untitled";
    const path = doc.metadata?.path || title;
    return `<retrieved_document>
<title>${title}</title>
<path>${path}</path>
<content>
${sanitizeContentForCitations(doc.pageContent)}
</content>
</retrieved_document>`;
  })
  .join("\n\n");
```

**Why XML tags?**
- Structured format LLMs understand well
- Clear boundaries between documents
- Enables citation extraction
- Path/title metadata preserved

### Full Example Context

```xml
<retrieved_document>
<title>Semantic Search Tools</title>
<path>L/Gleanings/2025-11-11-semantic-search.md</path>
<content>
# Valyu DeepSearch

First 1,000 queries free. Usage starts at $0.50 per 1k...
</content>
</retrieved_document>

<retrieved_document>
<title>Daily Note - November 11</title>
<path>Daily/2025/2025-11-11-Tu.md</path>
<content>
## Research

Looking into semantic search for vault...
</content>
</retrieved_document>
```

### Citation System

**Files**: `src/LLMProviders/chainRunner/utils/citationUtils.ts`

**Source catalog format**:

```typescript
const sourceEntries = retrievedDocs
  .slice(0, Math.min(20, retrievedDocs.length))
  .map((d: any) => ({
    title: d.metadata?.title || "Untitled",
    path: d.metadata?.path || ""
  }));

const sourceCatalog = sourceEntries
  .map((entry, i) => `${i + 1}. ${entry.title}`)
  .join("\n");
```

**Citation instructions to LLM**:

```
Available sources:
1. Semantic Search Tools
2. Daily Note - November 11
3. Project Temoa Plan

Insert [#] inline citations as you reference sources.
Append a ## Sources section listing all cited sources.
```

**LLM response pattern**:

```markdown
Based on your gleanings [1] and your planning document [3],
semantic search can help surface related notes when needed.

## Sources
1. Semantic Search Tools (L/Gleanings/2025-11-11-semantic-search.md)
3. Project Temoa Plan (Projects/Temoa.md)
```

### Sanitization Before LLM

**File**: `src/LLMProviders/chainRunner/utils/citationUtils.ts`

```typescript
function sanitizeContentForCitations(content: string): string {
  // Remove pre-existing [#] markers to prevent confusion
  return content.replace(/\[\d+\]/g, "");
}
```

### Fallback Sources

If LLM doesn't cite all sources, append them:

```typescript
function addFallbackSources(
  response: string,
  sources: SourceEntry[],
  enableInlineCitations: boolean
): string {
  if (hasInlineCitations(response)) {
    return response; // LLM already added sources
  }

  // Append sources section
  const sourcesSection = "\n\n## Sources\n" +
    sources.map((s, i) => `${i+1}. ${s.title}`).join("\n");

  return response + sourcesSection;
}
```

---

## Vector Store Implementation

### Orama Database

**What is Orama?**
- In-memory vector database
- JavaScript/TypeScript native
- Supports embeddings + full-text search
- Serializable to disk

**File**: `src/search/dbOperations.ts`

### Index Structure

```typescript
interface OramaDocument {
  id: string;           // chunk ID (note_path#index)
  path: string;         // note path
  title: string;        // note title
  content: string;      // chunk content
  embedding: number[];  // vector (384d, 768d, etc)
  tags: string[];       // note tags
  score?: number;       // search score
}
```

### Embedding Models

From analysis notes, Copilot supports:

**OpenAI**:
- `text-embedding-3-small` (1536d)
- `text-embedding-3-large` (3072d)
- `text-embedding-ada-002` (1536d)

**Anthropic**: Via API
**Google**: Gecko embeddings
**Ollama**: Local embeddings (various models)

### Query Process

```typescript
async function searchVault(query: string, k: number) {
  // 1. Generate query embedding
  const queryEmbedding = await embeddings.embedQuery(query);

  // 2. Vector search in Orama
  const results = await oramaDb.search({
    mode: "vector",
    vector: {
      value: queryEmbedding,
      property: "embedding"
    },
    limit: k
  });

  // 3. Convert to Document format
  return results.hits.map(hit => ({
    pageContent: hit.document.content,
    metadata: {
      path: hit.document.path,
      title: hit.document.title,
      score: hit.score
    }
  }));
}
```

### Desktop Build + Mobile Sync Strategy

From `mobile-qa-search.md` analysis:

**Desktop**:
1. Build index with semantic embeddings
2. Enable "Obsidian Sync for Copilot index"
3. Index stored in `.obsidian/copilot-index/`

**Mobile**:
1. Uncheck "Disable index loading on mobile"
2. Wait for index sync via Obsidian Sync
3. Load index from disk (no re-indexing needed)

**Temoa parallel**: Build index on server, make available via API

---

## Practical Recommendations for Temoa

### Phase 0: Answer Key Questions

Based on Copilot learnings, here are informed answers to your Temoa.md questions:

#### 1. "Does synthesis currently index daily notes?"

**Action**: Run this to check:

```bash
cd /path/to/.tools/synthesis
uv run main.py stats
# Look for Daily/ files in output
```

**If not indexed**: Add Daily/ to synthesis scan paths
**If indexed**: Gleanings already findable (scattered in daily notes)

#### 2. "Should gleanings be chunked?"

**Recommendation**: **NO, probably not needed**

**Why**:
- Each gleaning is small (< 500 chars typically)
- Already atomic units (one link per note)
- Chunking adds complexity for minimal gain
- Synthesis sentence-transformers work well on short documents

**But consider**:
- If gleanings have long descriptions/notes → chunk
- CHUNK_SIZE = 6000 is generous, most gleanings won't hit it

#### 3. "Should Temoa cache results?"

**Recommendation**: **Not initially, add later if needed**

**Why start without caching**:
- Synthesis already fast (measure first!)
- Server has more RAM than mobile
- Avoid cache invalidation complexity
- Simpler to debug

**When to add caching**:
- If search takes > 500ms consistently
- If same queries repeated frequently
- Use Redis or simple in-memory LRU

#### 4. "How to format results for LLM consumption?"

**Recommendation**: **Adopt Copilot's XML format**

```python
# In Temoa server
def format_for_llm(results):
    """Format search results for LLM context"""
    docs = []
    for r in results:
        doc = f"""<retrieved_document>
<title>{r['title']}</title>
<path>{r['relative_path']}</path>
<similarity>{r['similarity_score']:.3f}</similarity>
<content>
{r['content']}
</content>
</retrieved_document>"""
        docs.append(doc)

    return "\n\n".join(docs)
```

**Usage in vault-first chat** (Phase 4):

```python
@app.post("/chat")
async def chat_with_vault(message: str):
    # Search vault first
    results = await search_vault(message, limit=5)

    # Format as LLM context
    context = format_for_llm(results)

    # Prepend to user message
    enhanced = f"""Answer based on the user's vault:

{context}

User question: {message}"""

    # Call LLM
    response = await call_llm(enhanced)
    return {"response": response, "sources": results}
```

### Phase 1: Minimal Implementation

Based on Copilot architecture, here's the simplest path:

**Server**: FastAPI (Python)

```python
# Temoa/server.py
from fastapi import FastAPI
import subprocess
import json
from pathlib import Path

app = FastAPI()

SYNTHESIS_PATH = Path("~/.obsidian/vaults/main/.tools/synthesis").expanduser()

@app.get("/search")
async def search_vault(q: str, limit: int = 10, model: str = None):
    """Semantic search via synthesis"""

    # Build command
    cmd = ["uv", "run", "main.py", "search", q, "--json"]
    if model:
        cmd.extend(["--model", model])

    # Run synthesis (subprocess)
    result = subprocess.run(
        cmd,
        cwd=SYNTHESIS_PATH,
        capture_output=True,
        text=True,
        timeout=10  # 10s timeout
    )

    if result.returncode != 0:
        return {"error": "Search failed", "stderr": result.stderr}

    # Parse JSON output
    data = json.loads(result.stdout)

    return {
        "query": q,
        "results": data["results"][:limit],
        "total": len(data["results"]),
        "model": model or "default"
    }

@app.get("/")
async def index():
    """Simple search UI"""
    return HTMLResponse(SEARCH_UI_HTML)
```

**No chunking needed**: Synthesis handles documents as-is
**No vector store**: Synthesis manages embeddings
**No caching**: Direct subprocess call each time

### Phase 2: Gleanings Extraction

**Pattern from Copilot**: Individual note per item, not complex state management

**Extraction script** (`old-gleanings/glean.py`):

```python
#!/usr/bin/env python3
"""
Simple gleaning extraction - no categories, no state files, just notes
"""
import re
from pathlib import Path
from datetime import datetime

VAULT = Path.home() / "Obsidian" / "amoxtli"
DAILY = VAULT / "Daily"
GLEANINGS = VAULT / "L" / "Gleanings"

def extract_gleanings():
    """Extract gleanings from daily notes"""

    # Scan all daily notes
    for daily_note in DAILY.rglob("*.md"):
        content = daily_note.read_text()

        # Find ## Gleanings section
        match = re.search(r"## Gleanings\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
        if not match:
            continue

        section = match.group(1)

        # Extract markdown links: [text](url)
        for link_match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', section):
            text = link_match.group(1)
            url = link_match.group(2)

            # Create gleaning note
            date = daily_note.stem  # e.g., "2025-11-17-Th"
            slug = text[:50].lower().replace(" ", "-")
            filename = f"{date}-{slug}.md"

            gleaning_note = GLEANINGS / filename
            if gleaning_note.exists():
                continue  # Skip duplicates

            # Write note
            gleaning_note.write_text(f"""---
gleaned: {date}
url: {url}
tags: [gleaning]
source: "[[{daily_note.stem}]]"
---

# {text}

[Link]({url})
""")

            print(f"Created: {filename}")

if __name__ == "__main__":
    GLEANINGS.mkdir(parents=True, exist_ok=True)
    extract_gleanings()
```

**After extraction**: Run synthesis to index new gleanings

```bash
cd .tools/synthesis
uv run main.py process  # Re-index
```

### Phase 3: Performance Optimization

**If search is slow**, adopt Copilot patterns:

#### 1. Grep-First Recall

```python
# Add to Temoa if synthesis is slow
import subprocess

def grep_filter(query: str, vault_path: Path) -> list[Path]:
    """Fast grep to filter candidate files before synthesis"""

    # Extract keywords from query
    keywords = query.lower().split()

    # Grep vault for any keyword
    grep_pattern = "|".join(keywords)
    result = subprocess.run(
        ["grep", "-ril", "-E", grep_pattern, str(vault_path)],
        capture_output=True,
        text=True
    )

    # Return paths
    paths = [Path(p) for p in result.stdout.strip().split("\n") if p]
    return paths[:200]  # Limit like Copilot

# Then only run synthesis on filtered files
```

#### 2. Result Caching

```python
from functools import lru_cache
from hashlib import md5

@lru_cache(maxsize=100)
def search_vault_cached(query: str, limit: int):
    """Cache search results"""
    return search_vault(query, limit)

# Or use Redis for persistence across restarts
```

#### 3. Async Synthesis Calls

```python
import asyncio

async def search_vault_async(q: str, limit: int):
    """Async subprocess for synthesis"""

    proc = await asyncio.create_subprocess_exec(
        "uv", "run", "main.py", "search", q, "--json",
        cwd=SYNTHESIS_PATH,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        raise RuntimeError(f"Search failed: {stderr.decode()}")

    return json.loads(stdout.decode())
```

### Phase 4: Vault-First LLM

**Adopt Copilot's RAG pattern**:

```python
@app.post("/chat")
async def vault_first_chat(
    message: str,
    provider: str = "anthropic",
    include_vault: bool = True
):
    """Chat with vault-first RAG"""

    vault_context = ""
    sources = []

    if include_vault:
        # Search vault first
        results = await search_vault_async(message, limit=5)
        sources = results["results"]

        # Format as XML context
        vault_context = format_for_llm(sources)

    # Build enhanced message
    if vault_context:
        enhanced = f"""Relevant notes from user's vault:

{vault_context}

User question: {message}

Instructions:
- Answer based on vault content when relevant
- Cite sources using [1], [2], etc.
- If vault doesn't have answer, say so and provide general knowledge
"""
    else:
        enhanced = message

    # Call LLM via Apantli
    response = await call_apantli(provider, enhanced)

    return {
        "response": response,
        "vault_sources": sources,
        "used_vault": bool(vault_context)
    }
```

---

## Key Differences: Copilot vs Temoa

| Aspect | Copilot | Temoa |
|--------|---------|-----------|
| **Environment** | Obsidian plugin (client-side) | Server-side API |
| **Memory constraints** | 20MB mobile, 100MB desktop | Server RAM (GB available) |
| **Indexing** | Ephemeral (lexical) or Orama (semantic) | Synthesis (pre-built embeddings) |
| **Chunking** | 6000-char chunks for large notes | Probably not needed (small gleanings) |
| **Search modes** | Lexical + Semantic fusion | Semantic-only (simpler) |
| **Performance target** | < 200ms mobile | < 500ms acceptable |
| **Caching** | Aggressive (memory-bounded) | Optional (measure first) |
| **Context format** | XML for LLM consumption | Adopt same pattern |
| **Citation tracking** | Built-in with [#] markers | Future enhancement |

---

## Action Items for Phase 0 Discovery

### 1. Test Synthesis Performance

```bash
cd ~/.obsidian/vaults/main/.tools/synthesis

# Measure search speed
time uv run main.py search "semantic search" --json

# Check stats
uv run main.py stats

# Test different models
time uv run main.py search "gleanings" --model all-mpnet-base-v2 --json
```

**Questions to answer**:
- How fast is search? (< 500ms = good)
- Are Daily/ notes indexed?
- How many gleanings can synthesis find now?

### 2. Prototype Subprocess Call

```python
# test_synthesis.py
import subprocess
import json
import time

def test_search(query):
    start = time.time()

    result = subprocess.run(
        ["uv", "run", "main.py", "search", query, "--json"],
        cwd="/path/to/.tools/synthesis",
        capture_output=True,
        text=True,
        timeout=10
    )

    elapsed = time.time() - start

    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"Query: {query}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Results: {len(data['results'])}")
        print(f"Top result: {data['results'][0]['title']}")
    else:
        print(f"Error: {result.stderr}")

# Test
test_search("semantic search tools")
test_search("local LLM projects")
test_search("obsidian plugins")
```

### 3. Extract Sample Gleanings

```bash
cd old-gleanings

# Extract 10 gleanings as test
uv run glean.py --limit 10

# Check if synthesis finds them
cd ../.tools/synthesis
uv run main.py process  # Re-index
uv run main.py search "semantic search" --json
```

### 4. Design Mobile UX

**Simple HTML search interface**:

```html
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: system-ui; padding: 20px; }
    input { width: 100%; padding: 12px; font-size: 16px; }
    button { width: 100%; padding: 12px; margin-top: 10px; }
    .result {
      border: 1px solid #ddd;
      padding: 10px;
      margin: 10px 0;
      border-radius: 4px;
    }
    .score { color: #666; font-size: 0.9em; }
  </style>
</head>
<body>
  <h1>Vault Search</h1>
  <input id="query" type="text" placeholder="Search your vault..." />
  <button onclick="search()">Search</button>
  <div id="results"></div>

  <script>
    async function search() {
      const q = document.getElementById('query').value;
      const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
      const data = await res.json();

      const html = data.results.map(r => `
        <div class="result">
          <a href="${r.obsidian_uri}">${r.title}</a>
          <div class="score">Similarity: ${r.similarity_score.toFixed(3)}</div>
          <div>${r.relative_path}</div>
        </div>
      `).join('');

      document.getElementById('results').innerHTML = html;
    }

    // Search on Enter key
    document.getElementById('query').addEventListener('keypress', e => {
      if (e.key === 'Enter') search();
    });
  </script>
</body>
</html>
```

**Test on mobile**:
1. Start Temoa server
2. Access via Tailscale: `http://server-ip:8000`
3. Search and click obsidian:// links
4. Verify Obsidian app opens to correct note

---

## Summary: What to Adopt, What to Skip

### ✅ Adopt These Patterns

1. **XML context format** for LLM consumption
2. **Citation system** with source catalogs
3. **Progressive refinement** (fast ops first, expensive later)
4. **Simple caching** (measure first, optimize later)
5. **Chunk-based results** (only if gleanings get long)

### ❌ Skip These (Not Needed for Temoa)

1. **Dual search mode** (semantic-only is simpler)
2. **Mobile memory optimization** (server has plenty of RAM)
3. **Ephemeral indexing** (Synthesis pre-builds embeddings)
4. **Complex boosting** (folder/graph not relevant to gleanings)
5. **LangChain abstractions** (Python has simpler options)

### 🤔 Decide Later (Phase 3+)

1. **Result caching** (measure performance first)
2. **Chunking gleanings** (only if they get long)
3. **Grep-first recall** (only if synthesis is slow)
4. **Multiple embedding models** (start with one)
5. **Usage tracking** (nice-to-have, not critical)

---

## Next Steps

1. **Run Phase 0 discovery tasks** to validate Synthesis performance
2. **Prototype simple Temoa server** with `/search` endpoint
3. **Extract 10-20 gleanings** to test end-to-end flow
4. **Measure performance**: How fast is subprocess + Synthesis?
5. **Test mobile UX**: Does obsidian:// URI work from phone?
6. **Iterate**: Add features based on actual usage patterns

---

## References

- **Copilot v3 Search README**: `src/search/v3/README.md`
- **Chunking Implementation**: `src/search/v3/chunks.ts`
- **Retriever Implementations**: `src/search/v3/TieredLexicalRetriever.ts`, `MergedSemanticRetriever.ts`
- **Context Preparation**: `src/LLMProviders/chainRunner/VaultQAChainRunner.ts`
- **Citation Utilities**: `src/LLMProviders/chainRunner/utils/citationUtils.ts`
- **Your Analysis Notes**: `mobile-qa-search.md`, `chain-runner-architecture.md`, `PB-LEARNINGS.md`

---

*End of Analysis*

**Created**: 2025-11-18
**Status**: Complete
**Next**: Run Phase 0 discovery and decide on architecture
