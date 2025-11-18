# CHRONICLES.md - Project Lore & Design Discussions

> **Purpose**: This document captures key discussions, design decisions, and historical context for the Ixpantilia project. Unlike IMPLEMENTATION.md (which tracks *what* to build) or CLAUDE.md (which explains *how* to build), Chronicles explains *why* we're building it this way.

**Created**: 2025-11-18
**Format**: Chronological entries with discussion summaries
**Audience**: Future developers, decision-makers, and your future self

---

## Entry 1: The Central Problem of AI (2025-11-18)

### The Question

> "I have a bunch of documents and I want to know what is in them. The canonical 'query my documents' problem. If there were a silver bullet, I would probably know about it. What is the deal with this problem, and am I reinventing the axle?"

This is **the** question. If you're reading this wondering whether Ixpantilia is necessary, start here.

---

### Why There's No Silver Bullet

The "query my documents" problem is fundamentally hard because it's **not one problem—it's many problems disguised as one**.

#### Different Query Types Need Different Approaches

| Query Type | Example | Best Approach | Why Others Fail |
|------------|---------|---------------|-----------------|
| **Lookup** | "What did I save about React hooks?" | Full-text search (grep) | Semantic search over-complicates, LLMs hallucinate |
| **Conceptual** | "What do I know about state management?" | Semantic search (embeddings) | Full-text misses synonyms, LLMs too slow |
| **Synthesis** | "How do these ideas connect?" | RAG with LLM | Search can't generate, embeddings can't synthesize |
| **Temporal** | "What was I interested in last March?" | Archaeology/analytics | Standard search ignores time dimension |

**No single approach wins at all of these.** That's not a technology gap—it's a fundamental trade-off.

#### The Fundamental Trade-offs

1. **Recall vs. Precision**
   - Cast a wide net → get irrelevant results
   - Be specific → miss important connections
   - No algorithm solves both perfectly

2. **Speed vs. Quality**
   - Fast search → simpler models → misses nuance
   - Deep analysis → slow → unusable on mobile
   - Can't have both without caching/pre-computation

3. **Context Window Limits**
   - LLMs can't hold your entire vault
   - Must retrieve → rank → assemble context
   - Retrieval quality determines output quality
   - Wrong chunks = wrong answers

4. **Exact Match vs. Semantic Match**
   - Keyword search: finds "React" but not "user interface libraries"
   - Semantic search: finds concepts but might miss the exact phrase you saved
   - Both are needed for different tasks

---

### Comparison of Existing Solutions

Why isn't someone else already solving this? **They are, but not for *your* use case.**

| Solution | What It Does Well | Why It Doesn't Solve Ixpantilia's Problem | Cost/Complexity |
|----------|-------------------|------------------------------------------|-----------------|
| **Obsidian Native Search** | Fast keyword search, works offline | Not semantic, doesn't rank by relevance, desktop-only UI, no mobile optimization | Free, built-in |
| **Obsidian Copilot** | Chat with vault, semantic search, good LLM integration | Requires OpenAI API (not local), complex 6000-char chunking, chat-focused not search-focused, heavy dependencies | ~$20/mo for API, plugin setup |
| **Perplexity/ChatGPT** | Great at synthesis, up-to-date info, natural language | Searches the *internet*, not your vault, no access to private notes, hallucination risk | $20/mo, requires internet |
| **Vector DBs (Pinecone, Weaviate)** | Scalable semantic search, production-ready, good for large datasets | Requires restructuring vault into DB, complex setup/maintenance, not Obsidian-aware, overkill for personal use | $70+/mo or self-host complexity |
| **NotebookLM** | Excellent RAG, source citations, audio summaries | Not local (cloud-based), not mobile-optimized, not real-time with vault changes, Google data policies | Free (for now), privacy trade-off |
| **Elasticsearch** | Enterprise search, scales well, good ranking | Massive overkill for personal vault, not semantic by default (need plugins), complex config, resource-heavy | Self-host: high complexity |
| **mem0.ai** | Personal memory layer, good for LLM context | Cloud-based, not Obsidian-native, requires API integration | Freemium, $10+/mo |
| **Recall (recall.wiki)** | Summarizes bookmarks, semantic search of saved links | Cloud storage, browser-focused not note-focused, doesn't integrate with Obsidian workflow | Free tier limited |

**Key Insight**: Most solutions optimize for one of:
- **Enterprise scale** (you have 1 vault, not 1000 databases)
- **Cloud convenience** (you want privacy and local processing)
- **Chat interface** (you want search results, not conversations)
- **General web content** (you have curated, structured knowledge)

**None optimize for**: *"Search my personal vault from my phone in <2s while preserving privacy."*

---

### What Ixpantilia Actually Is

**Ixpantilia is NOT a new search algorithm.** It's a **workflow wrapper** that:

1. **Makes existing tech (Synthesis) accessible from mobile** → removes friction
2. **Puts your vault first** → habit formation (check before Googling)
3. **Stays local** → privacy, no API costs, works offline
4. **Obsidian-native** → works with existing notes, no migration

#### Analogy

You're not inventing a new search engine. You're building a **speed dial for your brain's external hard drive**.

#### The Real Problem Being Solved

It's not *"How do I search documents?"*

It's: **"I save things but never see them again. How do I make my past research useful for my present research?"**

This is a **retrieval behavior problem**, not a search technology problem.

---

### Why Gleanings Are Different

Most RAG solutions assume you have **unstructured documents**. You have **pre-structured knowledge artifacts**:

- **Already filtered**: You decided these links were important (curation done)
- **Timestamped**: Temporal context preserved (when you were interested)
- **Atomic**: One link per note (perfect granularity for embeddings)
- **Personal**: Your knowledge graph, not generic web content

**This is a huge advantage.** Gleanings are already in the ideal format for semantic search.

---

### What We're NOT Trying to Solve

These are explicitly **out of scope** (learned from old-gleanings failure):

| Anti-Goal | Why We're Avoiding It | Cost of Attempting |
|-----------|----------------------|-------------------|
| ❌ Answering questions with perfect accuracy | That's AGI-complete | Infinite development time |
| ❌ Replacing Google | Internet search is a different problem space | Wasted effort on wrong problem |
| ❌ Organizing knowledge into categories | old-gleanings proved this fails (2,771 lines of complexity) | User frustration, abandonment |
| ❌ Building a new embedding model | sentence-transformers is fine for personal use | Months of ML training, no ROI |
| ❌ Multi-user collaboration | Personal vault is single-user by design | Auth, sync, conflict resolution complexity |
| ❌ Real-time sync | Batch re-indexing is sufficient | Watcher overhead, race conditions |

**Lesson from old-gleanings**: Over-engineering kills adoption. Keep Ixpantilia simple.

---

### The Ixpantilia Hypothesis

Our core bet:

> **"If I can search my vault from my phone in <2 seconds, I'll check it before Googling. Over time, this habit makes past research compound."**

This is **not** a technology hypothesis. It's a **behavioral hypothesis**.

#### Success Looks Like

- **Week 1**: "This is fast and convenient"
- **Month 1**: "I check my vault before Googling sometimes"
- **Month 3**: "I check my vault *first* most of the time"
- **Month 6**: "I'm rediscovering forgotten gleanings regularly"
- **Year 1**: "My research builds on itself instead of restarting"

#### Failure Looks Like

- Vault search takes >3 seconds → I don't use it → habit never forms
- Results aren't relevant → I lose trust → I stop checking
- Mobile UI is clunky → friction too high → back to Google

**The technology must be invisible.** Speed and relevance are the only metrics that matter for habit formation.

---

### Key Insights for Future Reference

1. **There is no silver bullet** because "query my documents" is 4+ different problems requiring different approaches.

2. **RAG ≠ Search**
   - RAG generates answers (can hallucinate)
   - Search returns what you actually have (trustworthy)
   - Both are needed for different tasks

3. **Ixpantilia's niche is underserved**: Mobile-first, local, Obsidian-native semantic search with <2s response time.

4. **Behavioral change is the hard part**, not the technology. Synthesis already works. Making it accessible and habitual is the innovation.

5. **Pre-structured knowledge (gleanings) is an advantage** over generic RAG, which must chunk arbitrary documents.

6. **Phase 0 validation is critical**: If Synthesis is slow, if obsidian:// URIs don't work on mobile, if subprocess overhead is high → the hypothesis fails. Measure first.

---

## Decision Log

### DEC-001: Why Subprocess Instead of Library Import?

**Date**: 2025-11-18
**Context**: How should Ixpantilia call Synthesis?
**Options Considered**:
1. Import Synthesis as Python module → tight coupling
2. Keep Synthesis as separate service → deployment complexity
3. **Subprocess call via CLI** → clean separation ✓

**Decision**: Subprocess call
**Rationale**:
- Clean interface via JSON (well-defined contract)
- Synthesis changes don't break Ixpantilia (loose coupling)
- Overhead ~50-100ms acceptable for non-interactive use
- Simpler deployment (one codebase, one process)

**Trade-offs Accepted**: Slightly higher latency, but worth it for maintainability

---

### DEC-002: Why No Chunking?

**Date**: 2025-11-18
**Context**: Obsidian Copilot uses 6000-char chunks. Should Ixpantilia chunk documents?
**Decision**: No chunking initially
**Rationale**:
- Gleanings are already small (<500 chars typically)
- Atomic units (one link per note)
- Synthesis handles short documents well
- Reduces implementation complexity

**Re-evaluate if**: Gleanings grow to include long summaries (>2000 chars)

---

### DEC-003: Why No Caching Initially?

**Date**: 2025-11-18
**Context**: Should we cache Synthesis search results?
**Decision**: No caching in Phase 1
**Rationale**:
- Measure Synthesis performance first (Phase 0)
- Avoid premature optimization
- Cache invalidation adds complexity
- Server has more RAM than mobile (less constrained)

**Add caching if**: Search takes >500ms consistently AND same queries repeat often

**Caching strategy if needed**: Simple in-memory LRU cache with 15-minute TTL

---

## Entry 2: Architectural Constraints & Deployment Model (2025-11-18)

### The Context

Before implementation begins, we need to establish key architectural constraints that will shape how Ixpantilia is built and deployed. These aren't nice-to-haves—they're fundamental assumptions about the environment.

---

### Constraint 1: Vault Format Agnosticism

**Principle**: Ixpantilia is a neutral backend service.

- **Optimized for**: Obsidian vault structure (markdown files, frontmatter, wikilinks)
- **Should degrade gracefully to**: Plain text files in directories
- **Must not require**: Obsidian-specific features to function

**Why This Matters**:
- Future-proofs against Obsidian abandonment/pivots
- Allows use with other markdown-based tools (Logseq, Foam, plain text)
- Synthesis already works with plain markdown—don't add Obsidian dependencies

**Implications**:
- Don't parse Obsidian config files (`.obsidian/`)
- Don't assume plugins are available
- obsidian:// URIs are UI enhancement, not core functionality
- File discovery should work on any directory tree

**Test**: If I point Ixpantilia at a folder of .txt files, search should still work (even if less optimized).

---

### Constraint 2: Vector Database Location

**Question**: Where should the embedding index/vector DB live?

**Current thinking**: Store with the vault (probably in `.ixpantilia/` or similar)

**Rationale**:
- Co-location with data (vault moves → index moves)
- Simpler backup story (vault backup includes index)
- Clear ownership (index belongs to vault, not server)
- Allows multiple vaults with separate indices

**BUT** (important flexibility):
- We don't know yet if this is best
- Index might be large (test in Phase 0)
- Might want to exclude from Obsidian Sync (see next section)
- **Don't paint ourselves into a corner**

**Decision for Phase 1**: Store index with vault in `.ixpantilia/` directory, but make path configurable in `config.json` so we can move it later if needed.

---

### Constraint 3: Obsidian Sync Considerations

**Current setup**:
- Main vault lives on local machine (desktop/laptop)
- Uses Obsidian Sync to sync to mobile devices (iOS/Android)
- Currently only syncing to mobile (read-mostly access)

**Problem**: Should the vector DB sync via Obsidian Sync?

**Probably not**, because:
- Index could be large (hundreds of MB for 2000+ files)
- Mobile devices don't run Ixpantilia server (yet?)
- Wasted bandwidth syncing binary index files
- Index format might be platform-specific

**But maybe yes**, if:
- We eventually run Ixpantilia on mobile (future possibility?)
- Index is small enough (need to measure)
- Having local index enables offline search on mobile

**Decision for Phase 1**:
- Store index in `.ixpantilia/` directory within vault
- Document how to exclude from Obsidian Sync (`.obsidian/sync-config.json` or similar)
- Keep the option open to change this later

**Don't paint ourselves into a corner**: Make index location configurable. Allow index to live either:
1. Inside vault (`.ixpantilia/`)
2. Outside vault (e.g., `~/.local/share/ixpantilia/<vault-name>/`)
3. Wherever user specifies in config

**Actual Obsidian Sync exclusion**: Add `.ixpantilia/` to the vault's `.gitignore` equivalent for Obsidian Sync. (Obsidian Sync has its own exclusion patterns—document this in setup guide.)

---

### Constraint 4: Network Architecture

**Assumption**: We're running on a local machine behind NAT, not internet-accessible.

**Current setup**:
- Ixpantilia server runs on desktop/laptop (local network)
- NOT exposed to public internet (no port forwarding, no VPS)
- Using **Tailscale** to create "fake local network" across devices
- Very naive Tailscale usage (no special config, just "everything on same VPN")

**Why Tailscale**:
- Devices appear to be on same local network (100.x.x.x addresses)
- Mobile can access desktop as if on WiFi (e.g., `http://100.85.23.42:8080`)
- Encrypted by default (Wireguard under the hood)
- No certificates, no DNS, no SSL complexity (for now)

**What this means for Ixpantilia**:
- No authentication needed initially (Tailscale network is trusted)
- No HTTPS required (Tailscale encrypts transport)
- Simple `http://` endpoints are fine
- Focus on speed, not security theater

**Future considerations** (out of scope for Phase 1):
- Multi-user access (if family/team wants to use)
- API keys (if exposing beyond Tailscale network)
- Rate limiting (if needed to prevent abuse)
- HTTPS (if Tailscale isn't sufficient)

**For now**: Design for single-user, trusted network. Don't over-engineer security.

---

### Constraint 5: Flexibility Over Optimization

**Meta-principle**: Don't paint ourselves into a corner.

Throughout these decisions, the theme is: **Make it work, keep it simple, leave options open.**

**Specific examples**:
- Index location is configurable (can move later)
- Vault format agnostic (can use with non-Obsidian tools)
- No hard-coded paths (use config file)
- No assumptions about Synthesis location (could swap for other search engine)

**Why this matters**:
- We're in Phase 0 (don't know what we don't know)
- Requirements will change as we use it
- Over-optimization now = regret later

**The old-gleanings lesson**: Rigid structure (15 categories, complex state) killed adoption. Ixpantilia stays flexible.

---

## Decision Log (Continued)

### DEC-004: Vault Format Agnosticism

**Date**: 2025-11-18
**Decision**: Optimize for Obsidian but support plain text files
**Rationale**:
- Future-proofs against tool changes
- Synthesis already works with any markdown
- Obsidian-specific features are UI enhancements, not core functionality
**Trade-offs**: May not leverage all Obsidian features (graph view, plugins, etc.)
**Test**: Point Ixpantilia at a directory of .txt files—search should work

---

### DEC-005: Vector Database Storage Location

**Date**: 2025-11-18
**Decision**: Store in `.ixpantilia/` within vault, but make path configurable
**Rationale**:
- Co-location with data (vault moves → index moves)
- Simpler backup story
- Allows multiple vaults with separate indices
- Configuration allows flexibility to change later
**Trade-offs**: May need to exclude from Obsidian Sync (requires user config)
**Re-evaluate if**: Index size becomes problematic, or we want cross-vault search

---

### DEC-006: Obsidian Sync Exclusion

**Date**: 2025-11-18
**Decision**: Document how to exclude `.ixpantilia/` from Obsidian Sync, but keep option open
**Rationale**:
- Index could be large (hundreds of MB)
- Mobile doesn't run server (yet)
- Wasted bandwidth for binary files
- But maybe useful if we run search on mobile in future
**Trade-offs**: Users must manually configure sync exclusion
**Re-evaluate if**: We build mobile-native search, or index is tiny

---

### DEC-007: Network Security Model

**Date**: 2025-11-18
**Decision**: Trust Tailscale network, no auth/HTTPS in Phase 1
**Rationale**:
- Single-user use case
- Tailscale already provides encryption and access control
- Premature security complexity slows development
- Can add auth later if multi-user needed
**Trade-offs**: Not suitable for public internet exposure (but that's not the use case)
**Re-evaluate if**: Multi-user access needed, or exposing beyond Tailscale

---

### DEC-008: Configuration Over Convention

**Date**: 2025-11-18
**Decision**: Make paths/locations configurable, avoid hard-coded assumptions
**Rationale**:
- We don't know optimal setup yet
- Different users have different needs
- Easy to change via config.json
- "Don't paint ourselves into a corner"
**Trade-offs**: Slightly more complex config file
**Implementation**: All paths in `config.json`, expanded at runtime

---

## Future Topics to Chronicle

Questions to answer in future entries:

- How did Phase 0 performance testing go?
- Did obsidian:// URIs work reliably on mobile?
- What gleaning formats were found in the wild?
- How many gleanings were actually extracted?
- Did the <2s response time hypothesis hold?
- What was the actual adoption curve?
- Which features got used vs. ignored?

---

## Entry 3: The Hardcoded Paths Saga (2025-11-18)

### The Problem

During Phase 0 validation testing in a VM environment, we discovered multiple instances of hardcoded absolute paths that broke portability:

1. **Setup script**: `cd /home/user/ixpantilia/old-ideas/synthesis`
2. **Config resolution**: `.resolve()` converting relative paths to absolute
3. **Relative path calculation**: Hacky string replacement using `file_path.parents[2]`
4. **Embeddings in git**: 1,981 files from Mac vault committed to repo

These issues manifested as:
- Scripts failing in VM: `No such file or directory: /System/Volumes/Data/home/user/...`
- Search results with Mac paths: `/Users/philip/projects/ixpantilia/...`
- Duplicate path segments: `test-vault/test-vault/Areas/...`
- Old embeddings polluting test results

### Why This Matters

**Portability is non-negotiable** for this project:
- Development happens across multiple environments (Mac, VM, future contributors)
- Testing requires clean, reproducible environments
- Documentation assumes paths work for anyone
- The project itself is about *local* workflows—hardcoded paths violate that principle

### The Golden Rule

**GOLDEN RULE #4: No Hardcoded Paths**

All paths must be:
- ✅ **Relative** where possible (configs, scripts)
- ✅ **Expandable** via `~` or environment variables
- ✅ **Calculated** using proper pathlib methods (`relative_to()`)
- ❌ **Never** contain absolute paths like `/Users/`, `/home/`, `/System/`

### What We Fixed

#### 1. Setup Script Portability
**Before**:
```bash
cd /home/user/ixpantilia/old-ideas/synthesis
```

**After**:
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/old-ideas/synthesis"
```

**Why**: Script now works from any location, on any machine.

#### 2. Config Path Resolution
**Before**:
```python
def get_vault_path(self) -> Optional[Path]:
    vault_path = self.get("vault_path")
    if vault_path:
        return Path(vault_path).expanduser().resolve()  # <- .resolve() makes absolute
    return None
```

**After**:
```python
def get_vault_path(self) -> Optional[Path]:
    vault_path = self.get("vault_path")
    if vault_path:
        return Path(vault_path).expanduser()  # Keep relative
    return None
```

**Why**: `.resolve()` converts `../../test-vault` to `/Users/philip/projects/ixpantilia/test-vault`. Removing it preserves relative paths that work across environments.

#### 3. Relative Path Calculation
**Before**:
```python
self.relative_path = str(file_path).replace(str(file_path.parents[2]), "").lstrip("/")
```

**After**:
```python
self.relative_path = str(file_path.relative_to(vault_root))
```

**Why**: Proper pathlib method instead of string hacks. `parents[2]` assumed directory depth and created bugs like `test-vault/test-vault/Areas/...`

#### 4. Embeddings in .gitignore
**Before**: Embeddings committed to repo (4.1MB, 40,288 deletions)

**After**:
```gitignore
embeddings/
```

**Why**: Generated artifacts shouldn't be in version control. They're environment-specific and bloat the repo.

### Lessons Learned

1. **Test in clean environments early** - VM testing caught these issues before they became production problems
2. **Pathlib is your friend** - Use `relative_to()`, not string manipulation
3. **`.resolve()` is dangerous** - It seems helpful but breaks portability
4. **Generated files don't belong in git** - Embeddings, caches, build artifacts
5. **Scripts should be location-agnostic** - Use `$SCRIPT_DIR` patterns

### Test Results

After fixes:
```bash
# Clean relative paths ✅
"file_path": "../../test-vault/Daily/2025/2025-11-15-Fr.md"

# Correct file count ✅
Files processed: 13

# No file read errors ✅
All paths resolve correctly

# Portable config ✅
"vault_path": "../../test-vault"
```

### Decision Log Updates

**DEC-004**: All scripts must use relative paths or `$SCRIPT_DIR` pattern
- **Context**: VM testing revealed hardcoded paths break portability
- **Decision**: Ban absolute paths in configs and scripts
- **Trade-off**: Slightly more complex path logic, but works everywhere

**DEC-005**: Use pathlib methods, not string manipulation for paths
- **Context**: `file_path.parents[2]` hack created duplicate path segments
- **Decision**: Always use `.relative_to()` for path calculations
- **Trade-off**: None—pathlib is clearer and more correct

**DEC-006**: Generated artifacts go in .gitignore
- **Context**: 1,981 embeddings from Mac committed (4.1MB)
- **Decision**: `embeddings/` added to .gitignore
- **Trade-off**: Each environment generates its own (correct behavior)

### Commits

- `1c5db13`: fix: use relative paths instead of hardcoded absolute paths
- `4caee60`: fix: remove .resolve() to preserve relative paths in config
- `92169b8`: chore: remove embeddings and add to .gitignore
- `80782f3`: fix: use pathlib relative_to() for proper relative path calculation

### Phase 0 Progress

This work partially validates **Task 0.1: Test Synthesis Performance**:
- ✅ Verified Synthesis processes files correctly (13 in test-vault)
- ✅ Confirmed JSON output format
- ✅ Validated relative path handling
- ⚠️ Performance testing blocked by VM internet access (can't download models)
- 📝 Need Mac testing for full performance baseline

---

## Meta: How to Use This Document

**When starting a new session:**
1. Read the latest entry to understand recent discussions
2. Check Decision Log before proposing architectural changes
3. Add new entries when major design questions arise

**When making a design decision:**
1. Summarize the context and options
2. Document the decision and rationale
3. Note trade-offs accepted
4. Add to Decision Log with unique ID (DEC-XXX)

**When questioning a decision:**
1. Read the original rationale in Decision Log
2. Check if context has changed
3. If reversing decision, document why in new entry

---

**Remember**: This document explains *why*. IMPLEMENTATION.md explains *what*. CLAUDE.md explains *how*.

If you're wondering "why are we doing it this way?", the answer should be here.
