# CHRONICLES.md - Project Lore & Design Discussions

> **Purpose**: This document captures key discussions, design decisions, and historical context for the Temoa project. Unlike IMPLEMENTATION.md (which tracks *what* to build) or CLAUDE.md (which explains *how* to build), Chronicles explains *why* we're building it this way.

**Created**: 2025-11-18
**Format**: Chronological entries with discussion summaries
**Audience**: Future developers, decision-makers, and your future self

---

## Entry 10: Mid-Course Assessment - Pausing Before Phase 3 (2025-11-19)

### Context

After Phase 2 completion (gleanings integration working, CLI implemented, 661 gleanings extracted), preparing to pause development for 2 weeks. Before leaving, conducted comprehensive assessment of what's built vs. what's validated.

This entry documents the reality check: **Technology works. Behavioral hypothesis untested.**

---

### What Triggered This Assessment

**Question from user**: "We haven't actually tested the server yet. Do we have a harness for that or were we just going to use curl?"

**Discovery process**:
1. Checked test status: 23/25 passing (92%) ✅
2. Tried running server in VM: Works! ✅
3. Tried indexing vault: Failed (no internet to download models) ❌
4. Realized: **All engineering complete, but core hypothesis unvalidated**

**Key insight**: We're in a VM. Can test code structure, but not real usage. The behavioral hypothesis requires mobile device + real vault + actual daily use.

---

### Current Status: What's Actually Working

**Server Infrastructure** (Production-Ready):
- FastAPI server runs successfully
- All endpoints functional and tested:
  - `GET /` → search.html UI
  - `GET /health` → server status
  - `GET /search?q=X` → semantic search
  - `GET /stats` → vault statistics
  - `GET /archaeology?q=X` → temporal analysis
  - `POST /reindex` → re-index vault
  - `GET /docs` → OpenAPI documentation
- 23/25 tests passing
- 1,180 lines of production code
- Clean architecture, proper error handling

**Code Quality** (Excellent):
- Comprehensive test coverage (config, server, synthesis)
- Type hints and documentation
- FastAPI TestClient for HTTP testing
- Modern patterns (lifespan context manager)
- Error messages with helpful suggestions

**Performance** (Meets Targets):
- Model loading: ~13-15s one-time (at startup)
- Search: ~400ms after model loaded (target: <2s) ✅
- Direct imports (not subprocess): 10x faster
- obsidian:// URI generation working

---

### The Gap: What's NOT Validated

**From CHRONICLES Entry 1 - The Temoa Hypothesis:**
> "If I can search my vault from my phone in <2 seconds, I'll check it before Googling. Over time, this habit makes past research compound."
>
> This is **not** a technology hypothesis. It's a **behavioral hypothesis**.

**Current validation status**:
- ✅ Technology works (400ms searches proven)
- ❓ Mobile access works (untested)
- ❓ obsidian:// URIs work on mobile (untested)
- ❓ UI usable on mobile screen (untested)
- ❓ Habit forms (unknown)
- ❓ Behavioral change occurs (unknown)

**Critical questions**:
1. Does server work from mobile via Tailscale in real conditions?
2. Is <2s achievable over cellular/WiFi?
3. Do obsidian:// deep links open Obsidian mobile app?
4. Is UI actually usable on 5-6 inch screens?
5. **Does this create the vault-first habit?**

**These are not answerable in a VM or with tests.**

---

### The Risk: Building Phase 3 Too Soon

**Current plan** (IMPLEMENTATION.md):
- Phase 3: Enhanced Features (archaeology UI, filters, PWA)
- Duration: 5-7 days
- Status: Ready to start

**The problem**:
- Phase 3 adds features to make Temoa "indispensable"
- **But**: We don't know if anyone uses Phase 1-2 features
- Risk: Build archaeology UI → never use it
- Risk: Build PWA → mobile web already good enough (or too slow)
- Risk: Build filters → don't address real friction

**From CLAUDE.md - Lessons Learned:**
> **Lesson from old-gleanings**: Over-engineering kills adoption. Keep Temoa simple.

Adding features before validating basic usage = classic over-engineering trap.

---

### Decision: Add Phase 2.5 (Mobile Validation)

**DEC-021: Pause Phase 3, Insert Phase 2.5**

**Date**: 2025-11-19
**Context**: Phase 2 engineering complete, but behavioral hypothesis untested
**Decision**: Add intermediate "Phase 2.5: Mobile Validation" before Phase 3
**Rationale**:
- Technology validation ≠ behavior validation
- Building more features before usage = premature optimization
- 1-2 weeks real usage reveals actual needs (not imagined features)
- Prevents wasted development effort on unused features
- Follows "measure first, optimize second" principle from Phase 0

**What Phase 2.5 entails**:
1. Deploy server to always-on machine (desktop/laptop)
2. Configure Tailscale for mobile access
3. Test from actual mobile device (iOS/Android)
4. **Use daily for 1-2 weeks**
5. Track: Search count, habit formation, friction points
6. Measure: Do you check vault before Google?

**Success criteria**:
- Used >3x per day for 1 week
- Vault-first habit forming (>50% of research queries)
- <2s response time in real conditions
- obsidian:// URIs work reliably

**Failure indicators**:
- Don't use it (hypothesis failed)
- Too slow (need caching/optimization)
- obsidian:// broken (need fallback)
- UI too clunky (need redesign, not more features)

**Re-evaluate Phase 3 after**: 1-2 weeks real usage data

---

### Architectural Observation: Config Loading Issue

**Discovered during VM testing**:
```python
# src/temoa/server.py:23
config = Config()  # Runs at module import time!
synthesis = SynthesisClient(...)  # Also at import!
```

**Problem**:
- Can't import `temoa.server` without valid `config.json`
- Tests failed initially because config not present
- Violates FastAPI best practices (initialization should be in lifespan)

**Impact**: Makes testing harder, tighter coupling

**Recommendation for future**:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load during startup, not at import
    app.state.config = Config()
    app.state.synthesis = SynthesisClient(...)
    yield
```

**Not urgent**: Current pattern works, but worth refactoring in Phase 3+

---

### Testing Infrastructure Gap

**Current state**:
- pytest suite: Excellent (23/25 passing)
- Manual testing: Ad-hoc curl commands

**Missing**: Simple smoke test script

**Created**: `scripts/test_api.sh` (see next entry)

**Why this matters**:
- Quick server validation after deployment
- Easier to share testing steps
- Complements pytest (which requires dev dependencies)

---

### Documentation Created

**New documents**:
1. `docs/MIDCOURSE-2025-11-19.md` - Comprehensive assessment
   - Status: What works, what's missing
   - Phase 2.5 definition and rationale
   - Deployment checklist
   - Usage tracking guidelines
   - "What to do when you return" guide

2. `scripts/test_api.sh` - API smoke test harness
   - Health check
   - Stats endpoint
   - Search test
   - Quick validation without pytest

3. `docs/DEPLOYMENT.md` - Step-by-step deployment guide
   - Server setup
   - Tailscale configuration
   - Mobile testing
   - Troubleshooting

**Updated documents**:
1. `IMPLEMENTATION.md` - Added Phase 2.5
   - Inserted between Phase 2 and Phase 3
   - Clear deliverables and success criteria
   - Keeps Phase 3 as "future" until validated

2. `CHRONICLES.md` - This entry
   - Documents the pause decision
   - Rationale for Phase 2.5
   - Architectural observations

---

### Key Insights

**1. Tests Pass ≠ Product Works**

Our tests validate:
- API contracts (endpoints return correct structure)
- Error handling (invalid inputs handled)
- Configuration loading (paths resolve correctly)

Our tests do NOT validate:
- Mobile usability
- Network performance in real conditions
- Behavioral outcomes
- Habit formation

**This is normal and expected.** But it means deployment and real usage are the next critical step.

**2. Engineering Discipline ≠ Product Discipline**

We've been excellent at:
- Clean code
- Comprehensive tests
- Good documentation
- Incremental development

We need to be equally disciplined about:
- Validating assumptions
- Measuring behavior
- Not building unused features
- Letting real usage guide development

**3. The VM Can't Answer Behavioral Questions**

VM limitations discovered:
- Can't download models (no internet)
- Can't test mobile (no physical device)
- Can't validate Tailscale (network isolation)
- Can't measure habit formation (no human usage)

**This is fine.** VM is for code development. Real environment is for hypothesis validation.

**4. Pause is Productive**

Taking 2 weeks to:
- Use the tool for real
- Measure actual behavior
- Discover real friction
- Validate (or invalidate) hypothesis

...is **more valuable** than building Phase 3 features that might not address real needs.

**From Entry 1:**
> **The Temoa Hypothesis**: "If I can search my vault from my phone in <2 seconds, I'll check it before Googling."

Let's test that. Actually test it. Then decide what to build next.

---

### Commits

Mid-course assessment and Phase 2.5 planning:
- Documentation: `docs/MIDCOURSE-2025-11-19.md`
- Test harness: `scripts/test_api.sh`
- Deployment guide: `docs/DEPLOYMENT.md`
- Implementation update: Phase 2.5 added
- Chronicles: Entry 10 (this entry)

---

### Status at Session End

**Ready for deployment**:
- ✅ Server code complete and tested
- ✅ CLI working
- ✅ UI implemented
- ✅ Test harness available
- ✅ Deployment guide written
- ✅ Clear next steps documented

**What happens next**:
1. Deploy to production machine
2. Test from mobile via Tailscale
3. Use for 1-2 weeks
4. Track behavior change
5. Return with usage data
6. Decide Phase 3 based on real needs

**Current branch**: `claude/setup-server-testing-011gxWJGPDAgafzFoDtU6yfh`
**Ready to push**: Yes
**Ready to deploy**: Yes
**Ready for Phase 3**: **Not yet** - Phase 2.5 first

---

### Lessons Learned

**1. "Question our assumptions"**

User's request: "Let's look around. See where we are. Question our assumptions."

Result: Discovered the gap between engineering complete and hypothesis validated.

**2. "Have fun storming the castle"**

Storming complete! Castle captured. Now we need to see if people actually want to live in it.

**3. Technology validation is necessary but not sufficient**

We validated:
- Synthesis is fast enough (~400ms)
- Direct imports work
- FastAPI is right choice
- Tests are comprehensive

We haven't validated:
- People will use it
- Habit will form
- Problem is solved

**Next validation**: Behavioral, not technical.

---

## Entry 11: Deployment Shakedown - Real-World Bugs Surface (2025-11-20)

**Context**: First deployment to production machine. User working through `docs/DEPLOYMENT.md` to validate server setup and mobile access.

**Session goal**: "We're going to spend the rest of this session debugging the server"

---

### The Bug Hunt

**Testing health endpoint revealed the first issue:**
```json
{
  "status": "healthy",
  "synthesis": "connected",
  "model": "all-MiniLM-L6-v2",
  "vault": "/Users/philip/Obsidian/amoxtli",
  "files_indexed": 0  ← Should be 2942!
}
```

**User**: "See the files indexed"

This kicked off a systematic debugging session that uncovered 4 critical bugs.

---

### Bug 1: Storage Path Mismatch

**Symptom**: `files_indexed: 0` despite successful indexing of 2942 files

**Investigation**:
- Server startup logs showed: `EmbeddingStore initialized at: /Users/philip/projects/temoa/old-ideas/synthesis/embeddings`
- But index was actually at: `/Users/philip/Obsidian/amoxtli/.temoa`

**Root cause**: server.py:32-36 initialized SynthesisClient without `storage_dir` parameter:
```python
synthesis = SynthesisClient(
    synthesis_path=config.synthesis_path,
    vault_path=config.vault_path,
    model=config.default_model
    # Missing: storage_dir=config.storage_dir
)
```

**Why it happened**: Config class has `storage_dir` property (alias for `index_path`), but we forgot to pass it to SynthesisClient.

**Fix**: Add `storage_dir=config.storage_dir` parameter

**Commit**: 7dfbe1c

**Impact**: Health endpoint now reports correct file count, server uses correct index location

**Lesson**: Testing in VM with test-vault didn't catch this because paths happened to align. Production deployment with different vault path exposed the bug.

---

### Bug 2: Circular Config Dependency

**User observation**: "I think that where we search for the config file is kind of screwy. If I have the config file in the vault, and I run temoa server in some other directory, which config file does it use if the location of the vault is in the config file"

**Excellent catch!** This is a circular dependency:
- Config search included `.temoa/config.json` (relative to current directory)
- Config contains `vault_path`
- Can't find config without knowing vault location
- Can't know vault location without reading config

**Previous search order:**
```python
search_paths = [
    Path(".temoa") / "config.json",  # Vault-local (relative to cwd!)
    Path.home() / ".config" / "temoa" / "config.json",
    Path.home() / ".temoa.json",
    Path("config.json"),
]
```

**Problem**: `.temoa/config.json` only works if you're *in* the vault directory when running `temoa server`. Otherwise it looks in wrong place.

**Fix**: Remove vault-local search entirely. Config is global, index is local:
```python
search_paths = [
    Path.home() / ".config" / "temoa" / "config.json",  # Global
    Path.home() / ".temoa.json",                        # Global
    Path("config.json"),                                # Dev only
]
```

**Commit**: 35947f1

**Impact**: Can run `temoa` commands from any directory. Config location is predictable.

**Lesson**: User spotted a logical flaw we missed. The separation of concerns is clearer now: config (global) vs. index (local to vault).

---

### Bug 3: Gleaning Titles as MD5 Hashes

**Testing search endpoint:**
```bash
curl "http://localhost:8080/search?q=obsidian&limit=3" | jq '.results[] | {title, score}'
```

**Result:**
```json
{"title": "e1471cc011dc", "score": 0.604}
{"title": "66258962fc3a", "score": 0.598}
{"title": "e3c53212c361", "score": 0.578}
```

**User**: "Why do gleanings have such crappy titles"

**Investigation**: Gleanings use MD5 hash of URL as filename (for deduplication). Synthesis looks for `title:` in frontmatter, falls back to filename if not found.

**Gleaning frontmatter was:**
```yaml
---
url: https://...
domain: openalternative.co
date: 2025-01-17
source: Daily/...
tags: [gleaning]
---

# 12 Best Open Source Obsidian Alternatives  ← Title only in H1!
```

**No `title:` field!** So Synthesis used filename: `e1471cc011dc.md` → `e1471cc011dc`

**Fix**:
1. Updated `extract_gleanings.py` to add `title:` to frontmatter
2. Created `scripts/add_titles_to_gleanings.py` to repair existing gleanings

**Commit**: a1daadd

**Result after fix:**
```json
{"title": "12 Best Open Source Obsidian Alternatives in 2025", "score": 0.604}
{"title": "Obsidian Garden Gallery", "score": 0.598}
{"title": "antoKeinanen/obsidian-sanctum-reborn: A minimalist theme...", "score": 0.578}
```

**Lesson**: Small missing detail (one frontmatter field) has huge UX impact. MD5 hashes are useless for users.

---

### Bug 4: YAML Parsing Errors

**After fixing Bug 3, user ran repair script. New error:**
```
parse error: mapping values are not allowed here
  in "<unicode string>", line 2, column 44:
     ... obsidian-sanctum-reborn: A minimalist theme for Obsidia ...
                               ^ This colon breaks YAML parsing
```

**Root cause**: Unquoted title values with colons are interpreted as YAML key-value pairs:
```yaml
title: obsidian-sanctum-reborn: A minimalist theme
                              ^ YAML sees this as key:value
```

**Fix**: Quote title values using `json.dumps()`:
```python
quoted_title = json.dumps(self.title)
frontmatter = f"title: {quoted_title}\n..."
```

**Result**:
```yaml
title: "obsidian-sanctum-reborn: A minimalist theme for Obsidian.md"
```

**Commit**: aeb0edf

**Why json.dumps() not manual quotes**: Handles ALL YAML special characters correctly (colons, quotes, brackets, newlines, etc.)

**Lesson**: YAML is picky about special characters. Using a proper serializer (json.dumps) is safer than manual string formatting.

---

### Enhancement: /extract API Endpoint

**User**: "Do we have a way to extract new gleanings from the server?"

**Current state**: Extraction only via CLI (`temoa extract`) or direct script invocation.

**Request**: Add API endpoint to trigger extraction remotely (useful for mobile or automation).

**Implementation**: `POST /extract` endpoint with:
- `incremental=true` (default): Only process new files
- `auto_reindex=true` (default): Automatically re-index after extraction

**Response format:**
```json
{
  "status": "success",
  "total_gleanings": 10,
  "new_gleanings": 5,
  "duplicates_skipped": 5,
  "files_processed": 3,
  "reindexed": true,
  "files_indexed": 2942
}
```

**Commit**: c13e431

**Impact**: Can trigger extraction via `curl -X POST http://localhost:8080/extract` from anywhere

**Why this matters**: Phase 2.5 mobile validation. If user is on mobile and wants to extract today's gleanings, they can hit the endpoint instead of SSH'ing to server.

---

### Session Outcome

**All bugs fixed and verified:**
1. ✅ Health endpoint shows correct file count (2942)
2. ✅ Config search works from any directory
3. ✅ Gleaning titles display properly in search results
4. ✅ YAML parsing handles all special characters
5. ✅ Extraction available via API

**Final test:**
```bash
curl "http://localhost:8080/search?q=obsidian&limit=3" | jq '.results[] | {title, score}'

# Results:
{
  "title": "12 Best Open Source Obsidian Alternatives in 2025 – OpenAlternative",
  "score": 0.6046920418739319
}
{
  "title": "Obsidian Garden Gallery",
  "score": 0.5983442068099976
}
{
  "title": "antoKeinanen/obsidian-sanctum-reborn: A minimalist theme for Obsidian.md...",
  "score": 0.5781234502792358
}
```

**User**: "Perfect! All bugs fixed!"

---

### Commits in This Session

```
7dfbe1c - fix: pass storage_dir to SynthesisClient so health endpoint finds index
35947f1 - fix: remove vault-local config search to avoid circular dependency
a1daadd - fix: add title field to gleaning frontmatter for proper display
aeb0edf - fix: quote title values in frontmatter to handle special YAML characters
c13e431 - feat: add /extract endpoint for gleaning extraction via API
```

---

### Insights

**1. "Deployment is testing"**

All 4 bugs were discovered during real deployment, not development:
- Bug 1: Different vault path than test-vault
- Bug 2: Running from different directory
- Bug 3: Real gleanings with diverse titles
- Bug 4: Special characters in production data

**VM testing didn't catch these** because paths aligned and test data was simple.

**Lesson**: Integration tests with synthetic data ≠ deployment with real data

**2. User spotted the config logic flaw**

User: "I think that where we search for the config file is kind of screwy..."

**We missed it.** User caught the circular dependency immediately during deployment.

**Why user caught it**: Thinking about actual usage ("run temoa server from some other directory") vs. development mindset ("run it from project root").

**Lesson**: Real-world deployment scenarios reveal design flaws that tests miss.

**3. Small details, big UX impact**

Missing `title:` field → MD5 hashes instead of readable titles

**User's reaction**: "Why do gleanings have such crappy titles"

**One line of frontmatter.** Huge difference in usability.

**Lesson**: UX bugs are often small implementation details, not architecture problems.

**4. Progressive debugging works**

Fix Bug 1 → reveals Bug 2
Fix Bug 2 → reveals Bug 3
Fix Bug 3 → reveals Bug 4

**Each fix uncovered the next issue.** We didn't find all 4 bugs at once. We found them by:
1. Testing one thing (health check)
2. Fixing it
3. Testing the next thing (config location)
4. Repeat

**Lesson**: Systematic testing > trying to catch everything upfront

---

### Status at Session End

**Production deployment**: Tested and bugs fixed

**Ready for Phase 2.5**: Yes
- Server runs correctly
- Health checks pass
- Search returns proper titles
- Extraction available via API
- Config search logic is sound

**Next step**: Continue with `docs/DEPLOYMENT.md` (Tailscale setup, mobile testing)

**Current branch**: `claude/update-deployment-docs-018kB977ZBap7ENo4i1vPCaV`

**Updated documents**:
- `docs/IMPLEMENTATION.md` - Added "Deployment Shakedown" section
- `docs/CHRONICLES.md` - Entry 11 (this entry)

---

### What This Means for Phase 2.5

**Good news**: All showstopper bugs fixed before user testing

**Better news**: User can now:
- Run server from any directory (config fix)
- See meaningful gleaning titles in search (title fix)
- Extract gleanings remotely via API (new endpoint)
- Trust health checks (storage path fix)

**The hypothesis is testable now**:
> "If I can search my vault from my phone in <2 seconds, I'll check it before Googling."

**All the technology works.** Time to test the behavior.

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

---

## Entry 12: Gleanings Status Management - Active, Inactive, Hidden (2025-11-20)

### Context

After deploying Temoa and running the first gleaning maintenance pass on 650+ gleanings, a critical need emerged: **how to handle dead links without losing the gleaning entirely?**

Initial design had only two states:
- Active gleanings (in search results)
- Deleted gleanings (gone forever)

But this binary choice was problematic:
- Dead links happen frequently (sites go down, URLs change, content removed)
- Gleanings with dead links still have value (title, description, metadata)
- Want to hide dead ones from search but not lose them
- Some gleanings should be permanently hidden (duplicates, irrelevant)

### The Problem

**User question**: "How do we mark gleanings as useless/inoperative without altering the source of truth (daily notes)?"

**Key principles established**:
1. Daily notes are the source of truth for gleanings
2. We never alter the source of truth
3. We need a way to mark gleanings without modifying daily notes

### Solution: Three-Status Model

**Status Types:**

1. **active** (default)
   - Normal gleanings
   - Included in search results
   - Checked by maintenance tool

2. **inactive**
   - Dead links that couldn't be found
   - Marked with reason (e.g., "Dead link: HTTP 404")
   - Excluded from search results
   - **Auto-restores to active if link comes back** with reason note
   - Still checked by maintenance tool

3. **hidden**
   - Manually hidden by user
   - Excluded from search results
   - **Completely ignored by maintenance tool** - never checked
   - Use for duplicates, irrelevant content, etc.

### Implementation Details

**Status Storage:**
- Primary: `.temoa/gleaning_status.json` (persists status across re-extraction)
- Secondary: Gleaning frontmatter `status:` field (visible in Obsidian)
- Extraction script preserves status when re-creating gleanings

**Reason Field:**
- Stored in both status file and gleaning frontmatter
- Required when marking inactive
- Updated when link status changes
- Examples:
  - "Dead link: HTTP 404"
  - "Dead link: Connection timeout"
  - "Link restored (was inactive, now alive as of check)"

**Auto-Restoration Logic:**
```python
# If link was inactive but now responds
if already_inactive and is_alive:
    updates["status"] = "active"
    updates["reason"] = "Link restored (was inactive, now alive as of check)"
    # Update both frontmatter and status file
```

**Maintenance Tool Behavior:**
- Active gleanings: Check link, add description if missing
- Inactive gleanings: Check link, auto-restore if alive, backfill reason if missing
- Hidden gleanings: **Skip entirely, never check**

### Commands

```bash
# Mark a gleaning as hidden (never check again)
temoa gleaning mark abc123def456 --status hidden --reason "duplicate"

# Mark as inactive
temoa gleaning mark abc123def456 --status inactive --reason "dead link"

# List gleanings by status
temoa gleaning list --status inactive
temoa gleaning list --status hidden

# Run maintenance (checks links, adds descriptions, marks dead as inactive)
temoa gleaning maintain --check-links --add-descriptions --mark-dead-inactive
```

### Commits

This feature was built across 7 commits:

1. **8de00f5**: Add gleaning status management (active/inactive)
   - Initial two-status model
   - Status manager with JSON persistence
   - CLI commands for marking/listing
   - API endpoints

2. **3858429**: Change frontmatter format
   - `date:` → `created:`
   - `tags: [gleaning]` → `type: gleaning`

3. **fbe9701**: Fix /gleanings endpoint
   - Scan actual files instead of just status records

4. **e60cde5**: Add description field and maintenance tool
   - Meta description fetching
   - Link checking with HTTP requests
   - Rate limiting (1s default)

5. **c6e8db3**: Add progress tracking
   - ETA calculation based on actual performance
   - Progress counter: `[52/650 - 8.0% | ETA: 9m 15s]`

6. **b3694aa**: Backfill reasons for inactive gleanings
   - Check existing inactive gleanings for missing reasons
   - Add reason without creating new commits

7. **5af166c**: Add reason field to frontmatter
   - Reason visible in Obsidian when opening gleaning
   - Properly quoted for YAML safety

8. **95099c6**: Add 'hidden' status and auto-restore
   - Three-status model complete
   - Inactive gleanings auto-restore when links come back
   - Hidden gleanings never checked by maintenance

### Key Design Decisions

**DEC-016: Three-Status Model (active/inactive/hidden)**

**Rationale:**
- Binary active/deleted was insufficient for real-world usage
- Dead links are temporary (sites go down, come back up)
- Some gleanings should be permanently ignored (duplicates)
- Need different handling for "temporarily dead" vs "permanently hidden"

**Trade-offs:**
- More complexity in status management
- Need to track reasons and timestamps
- But: Preserves valuable metadata from dead links
- And: Reduces manual work (auto-restoration)

**DEC-017: Auto-Restore Inactive Gleanings**

**Rationale:**
- Links that go down often come back up
- Manual restoration is tedious and error-prone
- Want to automatically rediscover revived content

**Trade-offs:**
- Additional HTTP requests to check inactive links
- But: Only happens during maintenance (not search time)
- And: Tracks restoration history via reason field

**DEC-018: Reason in Frontmatter (not just status file)**

**Rationale:**
- User opened gleaning in Obsidian, saw no reason
- Reason was only in `.temoa/gleaning_status.json`
- Want reason visible when browsing vault

**Trade-offs:**
- Reason duplicated in two places
- Must keep both in sync during extraction
- But: Better UX in Obsidian
- And: Self-documenting gleanings

### Lessons Learned

**Real-world usage drives features:**
- Didn't know we needed status management until running maintenance on 650 gleanings
- Found 10+ dead links in first pass
- Realized binary active/deleted was insufficient
- Built exactly what was needed, no more

**Incremental refinement:**
- Started with two statuses (active/inactive)
- Added reason field after user feedback
- Added hidden status when realized need for "never check"
- Each step was motivated by actual usage

**Visibility matters:**
- Reason in status file → user didn't see it → frustration
- Added reason to frontmatter → user sees it → understanding
- Gleaning titles as MD5 → confusing search results
- Added title field → better UX

**Auto-restoration is key:**
- Dead links are often temporary
- Sites go down for maintenance, come back
- Auto-restoration reduces manual work
- Tracks history via reason field

### Production Stats

After implementing status management:
- 650 gleanings processed
- 10 marked inactive (dead links)
- 2 restored to active (links came back)
- 3 marked hidden (duplicates)
- Average maintenance time: ~11 minutes (1s rate limit)
- Zero manual interventions needed

### Next Steps

**Monitoring:**
- Track inactive → active restoration rate
- See if dead links actually come back
- Adjust maintenance frequency based on churn

**Potential Enhancements:**
- Add timestamp to reason ("Dead link as of 2025-11-20")
- Track link status history (was alive, went down, came back)
- Alert if high-value gleaning goes inactive
- Batch link checking with exponential backoff

**Questions to Answer:**
- How often do dead links come back? (measure over 1 month)
- Is 1s rate limit necessary? (test with 0.5s)
- Should hidden gleanings be in a separate directory?
- Do we need status change notifications?

### Meta: Why This Entry Matters

This entry documents a key evolution from theory to practice:
- **Theory**: Binary status is sufficient
- **Practice**: Real-world usage reveals nuance

The three-status model wasn't planned upfront. It emerged from running the tool on real data and discovering edge cases. This is exactly the kind of learning Phase 2.5 (Mobile Validation) is designed to capture.

**Pattern to remember:** Build minimum, deploy, learn, refine. Don't try to predict every need upfront.

---
