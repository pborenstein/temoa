---
title: "Project Temoa"
description: "Local semantic search server for Obsidian vault - vault-first research workflow"
created: 2025-11-17
status: planning
tags: [project, semantic-search, obsidian, apantli, synthesis]
---

# Project Temoa

> [Temoa](https://nahuatl.wired-humanities.org/content/temoa) (Nahuatl): To find out something about a friend; for something to present or manifest itself

A local semantic search server that enables vault-first research workflows, making your personal knowledge base the first stop before searching the broader internet.

---

## The Problem

### Current Research Workflow (Broken)
```
Question → Perplexity/Claude/GPT → Save link to daily note → Never see it again
```

**Pain Points**:
- Saved links (gleanings) accumulate but are never surfaced
- No way to check "what do I already know about X?" before searching externally
- Obsidian Copilot semantic search is slow and unusable on mobile
- Mobile is primary research environment
- Native Obsidian search works only if you know exact keywords

### Desired Research Workflow
```
Question → Vault Search (semantic) → [if relevant found: build on it]
                                   → [if not: external search → save → connect to vault]
```

**Requirements**:
- Fast semantic search across entire vault (1899+ files)
- Works on mobile (server does heavy lifting)
- Private (runs locally, inside Tailscale)
- Surfaces gleanings when contextually relevant
- Low friction (must be faster than just googling)

---

## The Insight

**You don't have an organization problem. You have a surfacing problem.**

The old-gleanings system (2,771 lines of Python) tried to solve this through categorization and static index generation. It failed because:
- Over-engineered (15+ categories, state management, web app)
- Created friction (manual script runs, regenerate index)
- Lived outside Obsidian (separate workflow)
- Optimized for browsing, not for research-time discovery

**What's actually needed**:
- Gleanings as individual, searchable notes
- Semantic search that surfaces them when relevant
- Integration with existing research tools (Apantli)
- Mobile-first design

---

## Existing Infrastructure

### Synthesis Project
**Location**: `.tools/synthesis/` (in main vault, not in toy-vault)
**Tech**: Python, sentence-transformers, local embeddings
**Status**: Production-ready, multi-model support

**Capabilities**:
```bash
# Semantic search with JSON output
uv run main.py search "query" --json

# Returns:
{
  "query": "AI",
  "results": [
    {
      "relative_path": "Daily/2024/2024-03-15.md",
      "title": "Daily Note - March 15",
      "similarity_score": 0.847,
      "obsidian_uri": "obsidian://vault/amoxtli/Daily/2024/2024-03-15",
      "wiki_link": "[[Daily Note - March 15]]",
      "file_path": "~/Obsidian/amoxtli/Daily/2024/2024-03-15.md"
    }
  ]
}

# Interest archaeology (temporal analysis)
uv run main.py archaeology "topic" --json

# Statistics
uv run main.py stats
```

**Models**: 5 sentence-transformer models
- `all-MiniLM-L6-v2` (384d, fast, default)
- `all-mpnet-base-v2` (768d, better quality)
- `multi-qa-mpnet-base-cos-v1` (768d, Q&A optimized)
- Others...

**Current Coverage**: 1899 vault files (excludes dot directories, utilities)

**Question**: Does synthesis currently index daily notes where gleanings live?

### Apantli
**Location**: https://github.com/pborenstein/apantli
**Tech**: Python, Alpine (HTTP), RESTish API
**Status**: Production (running locally via Tailscale)

**Purpose**: LLM proxy - provider-agnostic, usage tracking
**Current Capabilities**:
- Proxies requests to OpenAI, Anthropic, etc.
- Tracks req/res for debugging
- No vault awareness (pure proxy)

**Tech Stack**: Alpine for HTTP handling

**Question**: What's the current API surface? Easy to add new endpoints?

### Old-Gleanings
**Location**: `old-gleanings/`
**Status**: Abandoned (over-engineered, see GLEANINGS_ANALYSIS.md)
**Useful Parts**:
- Extraction regex patterns for links
- Understanding of gleaning formats in daily notes
- 505 gleanings in state file (Jan-Aug 2025) could be migrated

**Skip**: Categorization, state management, web app (all too complex)

---

## Proposed Architecture

### High-Level Flow
```
┌─────────────────────────────────────────────────────┐
│ Mobile (Obsidian / Browser / API client)           │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP Request: /search?q=semantic+search
                  ↓
┌─────────────────────────────────────────────────────┐
│ Temoa Server (or Apantli + /search endpoint)    │
│ - Receives query                                    │
│ - Calls synthesis                                   │
│ - Returns formatted results                         │
└─────────────────┬───────────────────────────────────┘
                  │ Subprocess call
                  ↓
┌─────────────────────────────────────────────────────┐
│ Synthesis (existing)                                │
│ - Loads embeddings                                  │
│ - Semantic search                                   │
│ - Returns JSON with obsidian:// URIs                │
└─────────────────────────────────────────────────────┘
```

### Decision Point: Integration or Standalone?

**Option A: Integrate into Apantli**
```
Apantli becomes:
  - LLM proxy (existing)
  - Vault search (new /search endpoint)

Pros:
  - Single service to manage
  - Already has usage tracking infrastructure
  - Same Tailscale access

Cons:
  - Mixes concerns (LLM proxy + search)
  - Apantli changes affect both workflows
```

**Option B: Separate Temoa Service**
```
Temoa:
  - Dedicated vault search service
  - Could be called BY Apantli (before external LLM)
  - Could be called directly from mobile

Pros:
  - Separation of concerns
  - Can evolve independently
  - Apantli could use it to enhance LLM context

Cons:
  - Another service to deploy/maintain
  - Need to figure out coordination
```

**Option C: Hybrid - Apantli Orchestrates**
```
Apantli becomes intelligent proxy:
  - GET /search → calls Temoa → returns results
  - POST /chat → calls Temoa first → includes vault context → calls LLM

This is the "vault-first LLM" architecture
```

**Recommendation**: Start with Option A (integrate into Apantli), migrate to Option C if complexity grows

---

## Core Components

### 1. Gleanings Extraction

**Problem**: Gleanings currently live scattered in daily notes under `## Gleanings` sections

**Solution**: Extract to individual notes that synthesis can index

**Format**:
```
L/Gleanings/
  2025-11-11-valyu-pricing.md
  2025-11-11-agent-fusion.md
  2025-11-11-fortran-backus.md
```

**Each note structure**:
```markdown
---
gleaned: 2025-11-11
url: https://www.valyu.ai/pricing
tags: [gleaning, api, llm-tool]
source: "[[2025-11-11-Tu]]"
---

# Valyu DeepSearch Pricing

> First 1,000 queries free. Usage starts at $0.50 per 1k. Access full text Open Research, Web Search, Finance APIs, and Scientific Content-try for free.

[Link](https://www.valyu.ai/pricing)
```

**Extraction Script** (~50 lines of Python):
```python
# glean.py - Simple extraction, no state management
# 1. Scan Daily/**/*.md for "## Gleanings" sections
# 2. Extract links (markdown format, naked URLs)
# 3. Create individual notes in L/Gleanings/
# 4. Tag with #gleaning + inferred tags
# 5. No categorization, no complex state
```

**Run periodically or on-demand**:
```bash
cd old-gleanings/  # or new location
uv run glean.py    # extracts new gleanings since last run
```

**Then synthesis re-indexes**:
```bash
cd .tools/synthesis/
uv run main.py process  # incremental, only new/changed files
```

**Alternative**: Could Temoa trigger synthesis re-indexing automatically?

### 2. Temoa Server

**Tech Stack Options**:
- **Option A**: Alpine (like Apantli) - familiar, lightweight
- **Option B**: FastAPI - more features, OpenAPI docs, async
- **Option C**: Flask - simple, widely known

**Recommendation**: FastAPI (modern, async, good for calling subprocesses)

**Core Endpoints**:

```python
GET /search?q=<query>&model=<model>&limit=<n>
  → Returns: JSON with search results

GET /archaeology?q=<query>&threshold=<n>
  → Returns: Temporal timeline of interest

GET /stats
  → Returns: Vault statistics

GET /health
  → Returns: Service health, synthesis availability
```

**Implementation Sketch**:
```python
from fastapi import FastAPI
import subprocess
import json

app = FastAPI()

@app.get("/search")
async def search_vault(q: str, model: str = None, limit: int = 10):
    """
    Semantic search across vault using synthesis
    """
    # Build command
    cmd = ["uv", "run", "main.py", "search", q, "--json"]
    if model:
        cmd.extend(["--model", model])

    # Run synthesis (assumes synthesis is at known path)
    result = subprocess.run(
        cmd,
        cwd="/path/to/.tools/synthesis",
        capture_output=True,
        text=True
    )

    # Parse and return
    data = json.loads(result.stdout)
    return {
        "query": q,
        "results": data["results"][:limit],
        "model": model or "default"
    }

@app.get("/archaeology")
async def archaeology(q: str, threshold: float = 0.2):
    """
    Temporal interest archaeology
    """
    cmd = ["uv", "run", "main.py", "archaeology", q, "--json", "--threshold", str(threshold)]

    result = subprocess.run(
        cmd,
        cwd="/path/to/.tools/synthesis",
        capture_output=True,
        text=True
    )

    return json.loads(result.stdout)
```

**Questions**:
- Should this cache results? (probably not initially)
- Should this track usage like Apantli? (nice to have)
- Should this have auth? (Tailscale provides network auth, probably fine)

### 3. Mobile Interface

**Option A: Simple Web UI**
```html
<!-- Served by Temoa at / -->
<html>
  <body>
    <input id="query" placeholder="Search vault..." />
    <button onclick="search()">Search</button>
    <div id="results"></div>

    <script>
      async function search() {
        const q = document.getElementById('query').value;
        const res = await fetch(`/search?q=${q}`);
        const data = await res.json();

        // Display results with obsidian:// links
        document.getElementById('results').innerHTML =
          data.results.map(r =>
            `<div>
               <a href="${r.obsidian_uri}">${r.title}</a>
               <span>${r.similarity_score.toFixed(3)}</span>
             </div>`
          ).join('');
      }
    </script>
  </body>
</html>
```

**Option B: Obsidian Plugin**
- More complex, requires TypeScript
- Better UX (native to Obsidian)
- Works offline if Temoa is down
- Could show results in sidebar

**Option C: Shortcuts/Scriptable (iOS)**
- Quick shortcut to open Safari with search
- Or launch query and copy results to clipboard

**Recommendation**: Start with Option A (web UI), graduate to Option B if valuable

### 4. Vault-First LLM (Future)

**The Vision**: When you ask an LLM a question, it checks your vault first

**Implementation**:
```python
# In Apantli or Temoa
@app.post("/chat")
async def chat_with_context(message: str, provider: str = "anthropic"):
    # 1. Search vault semantically
    vault_results = await search_vault(message, limit=5)

    # 2. Build context from vault
    context = "Relevant notes from your vault:\n\n"
    for r in vault_results["results"]:
        context += f"- {r['title']} (similarity: {r['similarity_score']})\n"

    # 3. Prepend to user message
    enhanced_message = f"{context}\n\nUser question: {message}"

    # 4. Call LLM with vault context
    response = call_llm(provider, enhanced_message)

    return {
        "vault_context": vault_results,
        "response": response
    }
```

**This solves**: "I want LLMs to know what I already know before answering"

---

## Gleanings in This Architecture

### The Role of Gleanings
Once extracted to individual notes and indexed by synthesis:

**When researching "local LLM tools"**:
1. Query Temoa: `/search?q=local LLM tools`
2. Results include:
   - Your notes about local LLMs
   - MOCs you've created
   - **Gleanings** (GitHub projects you saved)
   - Daily notes where you discussed this

**Gleanings surface naturally** when semantically relevant, solving the "I saved this but forgot" problem.

### Migration from Old System
505 gleanings exist in `old-gleanings/gleanings_state.json` (Jan-Aug 2025).

**One-time migration script**:
```python
# migrate_gleanings.py
# Read old state file
# For each gleaning:
#   Create L/Gleanings/{date}-{slug}.md
#   With frontmatter: gleaned, url, tags, source
#   Body: title, description, link
```

**Then**: Re-run synthesis to index them all.

### Going Forward
**Simple capture**:
1. Continue adding links to daily notes (habit is working)
2. Periodically run `glean.py` to extract
3. Synthesis re-indexes (automatic or manual)
4. Search finds them when relevant

**Or**: Create gleanings directly as individual notes (bypassing daily notes entirely)

---

## Technical Considerations

### Path Resolution
- **Synthesis location**: `.tools/synthesis/` (in main vault)
- **Temoa location**: TBD - could be:
  - Integrated into Apantli repo
  - Separate repo/service
  - Inside vault (like synthesis)?

**Question**: Where should this live?

### Vault Path Configuration
Synthesis needs to know where the vault is. Currently hardcoded?

**Options**:
- Environment variable: `VAULT_PATH=/path/to/vault`
- Config file: `Temoa_config.json`
- Command-line arg when starting server

### Model Selection
Synthesis supports 5 models. Which should Temoa use?

**Default**: `all-MiniLM-L6-v2` (fast)
**Production**: `all-mpnet-base-v2` (better quality)
**Specialized**: `multi-qa-mpnet-base-cos-v1` (Q&A optimized)

Should this be:
- Configurable per request? (`/search?q=foo&model=all-mpnet-base-v2`)
- System-wide default? (set once in config)
- Automatic based on query type?

### Performance
- **Synthesis search**: How fast is it currently? (need to measure)
- **Cold start**: Loading embeddings on first query
- **Subprocess overhead**: Calling `uv run main.py` each time
  - Alternative: Keep synthesis running as service?
  - Or: Import synthesis as Python module?

### Deployment
**Where does Temoa run?**
- Same server as Apantli (local machine, always on?)
- Raspberry Pi / home server?
- Docker container?

**How to start**:
```bash
# Option A: systemd service
sudo systemctl start Temoa

# Option B: Docker
docker run -d -p 8080:8080 Temoa

# Option C: Simple script
cd /path/to/Temoa
uv run server.py
```

**Tailscale access**: Already configured for Apantli, same setup?

---

## Implementation Plan

### Phase 0: Discovery & Validation
**Goal**: Answer open questions before building

**Tasks**:
1. **Test synthesis performance**
   - Run `main.py search` with various queries
   - Measure response time (cold start vs warm)
   - Check if daily notes are indexed (where gleanings live now)

2. **Review Apantli codebase**
   - How easy to add new endpoint?
   - Current API patterns?
   - Alpine usage - can we add another route?

3. **Prototype subprocess call**
   - Write simple Python script that calls synthesis
   - Parse JSON output
   - Measure overhead

4. **Design mobile UX**
   - Mockup simple search interface
   - Test obsidian:// URI handling on mobile
   - Decide on web UI vs plugin

5. **Extract sample gleanings**
   - Write minimal extraction script
   - Extract 10-20 gleanings from daily notes
   - See if synthesis finds them

**Output**: Decision on architecture (integrate vs standalone), tech stack, deployment

### Phase 1: Minimal Viable Search
**Goal**: Basic semantic search working on mobile

**Tasks**:
1. **Create Temoa server** (or add to Apantli)
   - Single endpoint: `GET /search?q=query`
   - Calls synthesis, returns JSON
   - Simple error handling

2. **Simple web UI**
   - Single page: search box + results
   - Obsidian:// links clickable
   - Shows similarity scores
   - Hosted by Temoa at `/`

3. **Deploy to local server**
   - Configure Tailscale access
   - Test from mobile
   - Verify obsidian:// links work

4. **Usage testing**
   - Search 20+ queries
   - Measure response time
   - Validate results quality
   - Gather feedback (personal use)

**Success Criteria**:
- Can search vault from phone in < 2 seconds
- Results are relevant
- Clicking result opens Obsidian mobile
- Faster than opening Obsidian + manual search

### Phase 2: Gleanings Integration
**Goal**: Gleanings are findable via semantic search

**Tasks**:
1. **Write extraction script** (`glean.py`)
   - Parse daily notes for `## Gleanings`
   - Extract links (markdown + naked URLs)
   - Create individual notes in `L/Gleanings/`
   - Track last extraction (simple timestamp file)

2. **Migrate existing gleanings**
   - One-time script: read `old-gleanings/gleanings_state.json`
   - Create 505 individual notes
   - Preserve dates, descriptions, URLs

3. **Re-index with synthesis**
   - Run `main.py process`
   - Verify gleanings appear in search
   - Test queries like "local LLM tools"

4. **Automated extraction**
   - Cron job or manual workflow
   - Could trigger from Temoa? (`POST /reindex`)

**Success Criteria**:
- All 505 historical gleanings are searchable
- New gleanings are extracted regularly
- Searching "semantic search" returns relevant gleanings
- Gleanings include GitHub projects, articles, etc.

### Phase 3: Enhanced Features
**Goal**: Make this indispensable

**Tasks**:
1. **Archaeology endpoint**
   - Add `GET /archaeology?q=topic`
   - Returns temporal timeline
   - "When was I interested in X?"

2. **Statistics & insights**
   - Add `GET /stats`
   - Vault coverage, model info
   - Recent searches (usage tracking?)

3. **Better UI**
   - Filters: date range, file type
   - Grouping: by folder, by tag
   - Preview: show snippet of note
   - Model selection dropdown

4. **Mobile optimization**
   - PWA (installable web app)
   - Offline capability?
   - Search history
   - Favorites/bookmarks

**Success Criteria**:
- Using this daily instead of Obsidian native search
- Can answer "when did I learn about X?" with archaeology
- UI is pleasant on phone

### Phase 4: Vault-First LLM (Future)
**Goal**: LLMs search your vault before the internet

**Tasks**:
1. **Chat endpoint with context**
   - POST /chat with message
   - Search vault first
   - Include top 5 results as context
   - Call LLM via Apantli (or directly)

2. **Context optimization**
   - How much vault context to include?
   - Summarize long notes?
   - Rank by relevance

3. **Multi-turn conversations**
   - Track conversation history
   - Re-search vault for each turn?
   - Or maintain context throughout?

4. **Provider integration**
   - Works with OpenAI, Anthropic, etc.
   - Respects Apantli usage tracking
   - Falls back gracefully if vault search fails

**Success Criteria**:
- "Ask my vault first" becomes default research mode
- LLM responses reference your own notes
- Builds on existing knowledge instead of reinventing

---

## Open Questions

### Architecture
- [ ] Integrate into Apantli or separate service?
- [ ] Where should Temoa code live? (repo location)
- [ ] How to coordinate synthesis + server? (subprocess vs module import)

### Technical
- [ ] Does synthesis currently index daily notes?
- [ ] How fast is synthesis search? (measure cold start, warm)
- [ ] Should we cache search results?
- [ ] How to handle synthesis updates/re-indexing?

### Gleanings
- [ ] Should gleanings stay in daily notes + get extracted?
- [ ] Or create gleanings directly as individual notes?
- [ ] What metadata is essential vs nice-to-have?
- [ ] How to handle updates (link changes, descriptions)?

### UX
- [ ] Web UI vs Obsidian plugin - which first?
- [ ] How to display results on mobile (small screen)?
- [ ] Should search history be tracked?
- [ ] How to handle no results / poor matches?

### Integration
- [ ] Can Temoa trigger synthesis re-indexing?
- [ ] Should Apantli use Temoa for vault context?
- [ ] How to coordinate between services?

### Deployment
- [ ] Same server as Apantli or separate?
- [ ] Systemd vs Docker vs simple script?
- [ ] How to handle updates/restarts?
- [ ] Backup strategy for gleanings?

---

## Success Metrics

### Quantitative
- **Response time**: < 2s from mobile search to results
- **Relevance**: Top 3 results useful for 80%+ queries
- **Coverage**: All gleanings (505+) searchable
- **Usage**: Using this 5+ times per day

### Qualitative
- **Lower friction than**: Opening Obsidian + manual search
- **More useful than**: Obsidian Copilot on mobile
- **Vault-first habit**: Check vault before googling
- **Rediscovery**: Finding forgotten gleanings regularly

### Behavioral
- **Reduced external searches**: Less reliance on Perplexity/Claude for known topics
- **More connections**: Linking new findings to existing notes
- **Gleaning value**: Actually using saved links instead of hoarding
- **Research quality**: Building on past knowledge instead of starting from scratch

---

## Related Projects & Context

### Old-Gleanings (Abandoned)
**Location**: `old-gleanings/`
**Analysis**: See `GLEANINGS_ANALYSIS.md`
**Key Lesson**: Over-engineering kills adoption. Keep it simple.

**Reusable**:
- Extraction regex patterns
- Understanding of gleaning formats
- 505 gleanings in state file (migration source)

**Avoid**:
- Complex categorization (15+ categories)
- State management systems
- Web application (Obsidian is the UI)
- Manual script runs with regeneration

### Synthesis
**Location**: `.tools/synthesis/` (main vault)
**Repo**: https://github.com/pborenstein/synthesis
**Status**: Production-ready
**Purpose**: Semantic search and knowledge graph generation

**Integration Point**: Temoa calls synthesis for actual search

### Apantli
**Repo**: https://github.com/pborenstein/apantli
**Status**: Production (local server)
**Purpose**: LLM proxy with usage tracking

**Integration Point**: Temoa could be integrated, or called by Apantli

### Obsidian Bases
**Feature**: Native Obsidian database/filtering (launched Aug 2025)
**Docs**: https://help.obsidian.md/bases

**Note**: Prefer Bases over Dataview where possible, but neither replaces semantic search

---

## Next Steps

1. **Read this document thoroughly**
2. **Answer open questions** (especially in Phase 0)
3. **Run Phase 0 discovery tasks** to validate approach
4. **Make architecture decision**: Integrate into Apantli vs standalone
5. **Build Phase 1**: Minimal viable search (one weekend?)
6. **Test on mobile**: Validate UX and performance
7. **Iterate**: Add features based on actual usage

---

## References

- **Gleanings Analysis**: `GLEANINGS_ANALYSIS.md`
- **Synthesis README**: `.tools/synthesis/README.md` (main vault)
- **Apantli Repo**: https://github.com/pborenstein/apantli
- **Obsidian Bases**: https://help.obsidian.md/bases
- **This Session**: (capture key insights as you go)

---

## Appendix: Example Queries

### What should work well:
- "local LLM inference" → gleanings about GitHub projects
- "semantic search tools" → gleanings + your notes
- "obsidian plugins" → gleanings + daily mentions
- "AI agents" → comprehensive results across vault

### What might not work:
- Very specific filenames (use Obsidian native search)
- Exact quotes or code snippets (use grep/search)
- Recent content not yet indexed

### Test suite for Phase 1:
```
# Gleanings-focused
- "GitHub LLM projects"
- "semantic search implementations"
- "obsidian copilot alternatives"

# General vault
- "writing about trust"
- "notes on retirement"
- "daily note 2024-11-11"

# MOC discovery
- "knowledge management"
- "personal knowledge base"

# Edge cases
- Single word: "AI"
- Very specific: "all-mpnet-base-v2"
- No results: "quantum chromodynamics"
```

---

*End of Plan*

**Status**: Planning
**Next Action**: Phase 0 Discovery
**Owner**: TBD
**Created**: 2025-11-17
**Updated**: 2025-11-17
