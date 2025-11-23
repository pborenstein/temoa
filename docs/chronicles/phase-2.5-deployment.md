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

## Entry 13: Archaeology Shakedown & Feature Discovery (2025-11-21)

### Context

After fixing search quality issues (min_score filtering, model upgrade to all-mpnet-base-v2, dark mode UI), user tested the `/archaeology` endpoint for the first time.

**Initial result**: AttributeError - method called `trace_interest`, not `analyze_topic`.

**This kicked off two discoveries:**
1. Archaeology endpoint was broken (wrong method name)
2. Archaeology answered the wrong question (led to feature insight)

---

### Bug: Wrong Method Name

**Error:**
```python
AttributeError: 'TemporalArchaeologist' object has no attribute 'analyze_topic'
```

**Root cause:**
- synthesis.py called `self.archaeologist.analyze_topic()`
- Actual method in Synthesis: `trace_interest(query, threshold, exclude_daily)`
- Also passed `top_k` parameter that doesn't exist (hardcoded to 50 in Synthesis)

**Fix:**
1. Changed method call to `trace_interest()`
2. Replaced `top_k` parameter with `exclude_daily` (filter daily notes if needed)
3. Properly serialized `InterestTimeline` NamedTuple to JSON dict

**Commit:** c4ffe53 "fix: correct archaeology method call from analyze_topic to trace_interest"

**Response structure now:**
```json
{
  "query": "topic",
  "threshold": 0.2,
  "entries": [{"date": "2024-01-01", "content": "...", "similarity_score": 0.8}],
  "intensity_by_month": {"2024-01": 0.75},
  "activity_by_month": {"2024-01": 5},
  "peak_periods": [{"month": "2024-01", "intensity": 0.75}],
  "dormant_periods": ["2024-02"],
  "model": "all-mpnet-base-v2"
}
```

---

### Discovery: What Archaeology Actually Does

**User tested:** `/archaeology?q=a+time+for+monsters`

**Result:**
- 5 entries over 12 months (Nov 2024 → Nov 2025)
- Sporadic interest (9 months dormant)
- Peak in Aug 2025 (0.48 similarity)
- Recent resurrection (Nov 2025)

**User's question:** "Now, a better question about archaeology: what is it good for. what is it telling us?"

**Analysis revealed:**

**What archaeology IS:**
- **Topic → Time mapping**: "Given a topic, when was I interested in it?"
- Shows lifecycle: birth, growth, dormancy, resurrection
- Good for: "Have I explored this before?"

**Patterns it reveals:**
- **Sporadic interest** (low activity, gaps) → passing references
- **Deep dive** (high activity + intensity) → research phase
- **Resurrection** (dormancy → activity) → renewed relevance

**User's insight:** "this is actually interesting: What was I obsessed with in 2023"

**Problem:** Archaeology can't answer this! It requires **Time → Topics mapping** (the inverse).

---

### Feature Discovery: "Themes by Period"

**The missing capability:**
```
Current: archaeology("semantic search") → when did I care about this?
Missing: themes(year=2023) → what did I care about?
```

**User request:** "how would I search for that I don't think archaeology can do it"

**Correct!** Archaeology does **topic → time**. What's needed is **time → themes**.

**Conceptual algorithm:**
```python
def discover_themes_by_period(
    year: int,
    min_cluster_size: int = 5
) -> List[Theme]:
    """Find dominant themes in a time period"""

    # 1. Get all files from time period
    files = filter_by_date(vault, year=year)

    # 2. Get embeddings for all files
    embeddings = [get_embedding(f) for f in files]

    # 3. Cluster similar content
    clusters = cluster_embeddings(embeddings, min_size)

    # 4. Extract representative topic for each cluster
    themes = []
    for cluster in clusters:
        representative_docs = get_cluster_centers(cluster)
        theme = extract_theme_name(representative_docs)
        themes.append({
            "theme": theme,
            "file_count": len(cluster),
            "intensity": avg_similarity(cluster),
            "sample_files": representative_docs[:5]
        })

    return sorted(themes, key=lambda t: t["file_count"], reverse=True)
```

**API endpoint concept:**
```
GET /themes?year=2023
GET /themes?start=2023-01-01&end=2023-12-31
GET /themes?period=2023-Q3
```

**Response:**
```json
{
  "period": "2023",
  "themes": [
    {
      "theme": "semantic search and embeddings",
      "file_count": 45,
      "avg_intensity": 0.68,
      "peak_month": "2023-07",
      "sample_files": ["...", "...", "..."]
    },
    {
      "theme": "obsidian plugins and workflows",
      "file_count": 32,
      "avg_intensity": 0.55,
      "peak_month": "2023-03",
      "sample_files": ["...", "..."]
    }
  ]
}
```

---

### Implementation Considerations

**Complexity:**
- **Clustering**: Need sklearn/HDBSCAN for semantic clustering
- **Theme extraction**: Tricky - how to name clusters?
  - Option 1: Most frequent keywords (simple, may be generic)
  - Option 2: LLM summary of cluster (accurate, requires API)
  - Option 3: Representative document titles (simple, works often)
- **Performance**: Clustering all vault embeddings could be slow
- **Accuracy**: Small clusters may not have clear themes

**Why it's valuable:**
- Answers "what was I obsessed with?" question directly
- Complements archaeology (topic → time vs time → topics)
- Helps rediscover forgotten research threads
- Shows evolution of interests over years

**Workarounds until implemented:**
1. Multiple archaeology queries with broad topics
2. Manual review of files by date
3. Daily notes as timeline proxy

---

### Decision: Document as Future Enhancement

**DEC-022: Themes by Period - Future Enhancement**

**Date**: 2025-11-21
**Context**: User asked "What was I obsessed with in 2023?" - archaeology can't answer
**Decision**: Document as potential Phase 3+ feature, continue Phase 2.5 validation
**Rationale:**
- Valuable capability discovered through real usage
- Requires clustering infrastructure not yet built
- Phase 2.5 focus: validate existing features before adding new ones
- Behavior validation first, feature expansion second

**Where documented:**
- CHRONICLES.md Entry 13 (this entry) - discovery and analysis
- IMPLEMENTATION.md Phase 4+ - added to future enhancements backlog
- For now: Manual workarounds documented

**When to revisit:**
- After Phase 2.5 validation complete
- If "time → themes" need surfaces repeatedly in usage
- When clustering infrastructure justified by other needs

---

### Current Status: Archaeology Working

**Fixed issues:**
- ✅ Method name corrected (trace_interest)
- ✅ Parameters aligned with Synthesis API
- ✅ Response properly serialized to JSON
- ✅ Endpoint documented with example output

**Tested query:** "a time for monsters"
- Shows sporadic interest pattern (5 entries, 12 months)
- Peak in Aug 2025, dormant periods identified
- Recent resurrection in Nov 2025

**User's next step:** "let's continue shaking down the api/ui"

---

### Lessons Learned

**1. Breaking features reveal missing features**

Fixing archaeology bug led to trying it for first time → revealed what archaeology doesn't do → discovered "themes by period" gap.

**Pattern:** Use → discover limits → identify complementary features

**2. Real questions > imagined use cases**

"What was I obsessed with in 2023?" is a **real question** from actual usage.

Much more valuable than imagining features upfront. Phase 2.5 validation philosophy: let real usage reveal real needs.

**3. Topic → Time vs Time → Topics**

Archaeology is fundamentally **unidirectional**:
- You already know the topic, find the timeline
- Can't go the other way: find topics in a timeline

**Inverse operations need different algorithms.** Can't just "reverse" archaeology.

**4. Document for future, focus on present**

Good idea doesn't mean implement now. Document clearly, add to backlog, continue Phase 2.5 validation.

**Prevents:**
- Feature creep during validation phase
- Building before validating existing features work
- Repeating old-gleanings over-engineering mistake

---

### Commits

Search quality improvements (prior session):
- 15dba1d: Narrow layout, remove blue border, remove emojis
- ef4fb96: Dark mode with better card separation
- c195cc7: Add New England flag footer
- 9a7f1cf: Restore API docs and Status links to footer

Archaeology fix (this session):
- c4ffe53: Correct archaeology method call from analyze_topic to trace_interest

---

### Updated Documents

- `docs/chronicles/phase-2.5-deployment.md` - Entry 13 (this entry)
- `docs/IMPLEMENTATION.md` - Added "Themes by Period" to Phase 4+ backlog

---

### Next: Continue API/UI Shakedown

User directive: "let's continue shaking down the api/ui"

**Remaining endpoints to test:**
- `/stats` - vault statistics
- `/reindex` - force re-indexing
- Search with various min_score thresholds
- Mobile UI testing (responsive design)

**Phase 2.5 goal:** Validate all features work before deciding what to build next.

---

## Entry 14: Architecture Documentation - Explaining the Machine (2025-11-22)

### Context

User requested comprehensive architecture documentation:
- "Write up the architecture of this thing. I love ascii diagrams."
- "Explain how the embeddings work"
- "Update IMPLEMENTATION and CHRONICLE"

**Why this matters:** Temoa has grown from concept to working system (1,800+ lines of code, 2,281 indexed files, 766 gleanings). Time to document **how it all works** for future developers and contributors.

---

### What Was Created

**New Document:** `docs/ARCHITECTURE.md` (500+ lines)

**Contents:**
1. High-level system architecture (ASCII diagrams)
2. How embeddings work (semantic search explanation)
3. Request flow (mobile → server → Synthesis → results)
4. Storage architecture (file system layout, index structure)
5. Component details (each module explained)
6. Deployment model (Tailscale VPN, server lifecycle)
7. Performance characteristics (scalability, memory, disk)
8. Troubleshooting guide

---

### Key Architecture Diagrams

**High-Level System:**
```
Mobile Device
    ↓ (Tailscale VPN)
FastAPI Server
    ↓ (Direct imports)
Synthesis Engine
    ↓ (sentence-transformers)
Obsidian Vault + .temoa/embeddings.pkl
```

**Embeddings Process:**
```
Indexing (one-time):
  Vault files → Transformer model → 384D vectors → Store in .temoa/

Search (per query):
  Query → Embedding → Cosine similarity → Ranked results
  ~400ms total
```

**Request Flow:**
```
User types query → HTTP GET /search
  → FastAPI endpoint
  → SynthesisClient wrapper
  → Synthesis engine (generate query embedding)
  → Compare with stored embeddings (cosine similarity)
  → Rank results
  → Return JSON
  → Render in UI
  → Click obsidian:// link
  → Open in Obsidian app

Total: ~400ms
```

---

### How Embeddings Work (Explained)

**The core technology behind Temoa's semantic search:**

**What are embeddings?**
- Text → high-dimensional vectors (lists of 384 numbers)
- Similar text → similar vectors
- Enables semantic search (meaning, not just keywords)

**Example:**
```
Query: "machine learning"
Embedding: [0.42, -0.13, 0.87, ..., 0.21]

Finds semantically similar:
- "neural networks" (similar vector)
- "deep learning" (similar vector)
- "AI models" (similar vector)

Doesn't require exact keyword match!
```

**Process:**
1. **Indexing** (one-time): Transformer model converts all vault files → vectors → store
2. **Searching** (per query): Convert query → vector, compare with all stored vectors
3. **Ranking**: Cosine similarity (angle between vectors) → higher score = more similar

**Why it works:**
- Pre-trained transformer models learned semantic meaning from billions of texts
- Context-aware: "bank" (river) vs "bank" (finance) get different embeddings
- Language agnostic: works across topics, styles, domains

**Model used:** `all-MiniLM-L6-v2`
- 384 dimensions (good balance)
- ~80 MB model size
- Fast on mobile
- Good quality results

---

### Storage Architecture Explained

**File system layout:**
```
vault/
├── Daily/2025-11-22.md        (source of gleanings)
├── L/Gleanings/abc123.md      (extracted gleanings)
└── .temoa/
    ├── embeddings.pkl         (vector index, ~10MB for 2000 files)
    ├── config.json            (vault-local config)
    ├── extraction_state.json  (gleaning tracking)
    └── gleaning_status.json   (active/inactive/hidden)
```

**Gleaning file format:**
```markdown
---
title: "Article Title"
url: "https://..."
date: "2025-11-22"
timestamp: "14:30"
tags: [obsidian, plugins]
status: active
---

Description of the gleaning.
```

**Index structure (.temoa/embeddings.pkl):**
```python
{
  "embeddings": [
    {
      "file_path": "L/Gleanings/abc123.md",
      "embedding": [0.42, -0.13, ..., 0.21],  # 384 floats
      "metadata": {"title": "...", "tags": [...]}
    },
    # ... 2000+ more
  ],
  "model_name": "all-MiniLM-L6-v2",
  "total_files": 2281
}
```

---

### Component Responsibilities

**1. FastAPI Server** (`src/temoa/server.py`):
- HTTP routing and request handling
- Response formatting (JSON, obsidian:// URIs)
- CORS headers for browser access
- Error handling and logging

**2. SynthesisClient** (`src/temoa/synthesis.py`):
- Wrapper around Synthesis engine
- Direct Python imports (not subprocess)
- Model loading and caching (one-time at startup)
- Search method delegation

**3. Synthesis Engine** (`old-ideas/synthesis/`):
- Core semantic search (sentence-transformers)
- Embedding generation and storage
- Cosine similarity calculations
- Temporal analysis (archaeology)
- **External dependency** (we don't modify it)

**4. Configuration** (`src/temoa/config.py`):
- Centralized config management
- Path expansion (~/, $HOME)
- Validation and defaults
- Override mechanism

**5. Web UI** (`src/temoa/ui/search.html`):
- Mobile-first search interface
- Vanilla HTML/CSS/JS (no frameworks)
- Real-time search (debounced input)
- obsidian:// URI links

**6. Gleaning Extraction** (`scripts/extract_gleanings.py`):
- Parse daily notes for gleanings
- Multiple format support
- MD5-based deduplication
- State tracking for incremental extraction

---

### Performance Characteristics

**Search Performance:**
```
Files         Search Time
100           380ms
1000          400ms
2000          410ms  ← current production
5000          450ms  (estimated)
10000         550ms  (estimated)

Why it scales well:
- Cosine similarity is O(n)
- NumPy vector ops highly optimized (C)
- Most time in query embedding, not comparison
```

**Memory Usage:**
```
Transformer model:  ~500 MB  (loaded at startup)
Embedding index:    ~10 MB   (2000 files × 384d)
FastAPI runtime:    ~50 MB
Python interpreter: ~30 MB
─────────────────────────────
Total:              ~600 MB  (constant)

Scales linearly: 5000 files ≈ 650 MB, 10000 files ≈ 700 MB
```

**Disk Usage:**
```
Per-file: ~2 KB (1.5 KB embedding + 0.5 KB metadata)

Vault sizes:
1000 files:   ~2 MB index
2000 files:   ~4 MB index
5000 files:   ~10 MB index
10000 files:  ~20 MB index
```

**Startup:**
- First run: Download model (~80 MB, one-time, 30-60s)
- Subsequent: Load cached model (~15s)
- Searches after startup: ~400ms ✓

---

### Key Design Decision: Direct Imports vs Subprocess

**DEC-009 revisited:**

**Problem:** Subprocess calls to Synthesis were slow (2-3s per search)

**Solution:** Import Synthesis code directly, load model once at startup

**Impact:** 10x faster searches (400ms vs 2-3s)

**Before (subprocess):**
```python
# Each search loads model (2-3s)
result = subprocess.run(["uv", "run", "main.py", "search", query])
```

**After (direct import):**
```python
# Startup (once): Load model (15s)
from synthesis import Searcher
searcher = Searcher(model="all-MiniLM-L6-v2")

# Each search: Direct function call (400ms)
results = searcher.search(query)
```

**Why this matters:**
- Makes mobile usage feasible (<2s target met)
- Model loaded in RAM, searches instant
- Core enabler of behavioral hypothesis testing

---

### Deployment Model Explained

**Tailscale VPN Network:**
```
Mobile Device (100.x.x.y)
    ↕ (encrypted WireGuard tunnel)
Desktop/Laptop (100.x.x.x)
    ← Both on same "tailnet" (virtual LAN)

Security:
- Tailscale encrypts all traffic
- No port forwarding needed
- No public IP exposure
- No HTTPS needed (encrypted by VPN)
- Only devices on your tailnet can access
```

**Server Lifecycle Options:**

1. **Manual** (development):
   ```bash
   uv run temoa server
   ```

2. **Background** (long-running):
   ```bash
   nohup uv run temoa server > temoa.log 2>&1 &
   ```

3. **Systemd** (production):
   ```bash
   sudo systemctl start temoa
   sudo systemctl enable temoa  # Start on boot
   ```

**Daily automation:**
- Cron job: Extract gleanings daily at 11 PM
- Auto-reindex after extraction
- Weekly maintenance (check dead links)

---

### Documentation Updates

**1. ARCHITECTURE.md** (new):
- Comprehensive system architecture reference
- ASCII diagrams for all major components
- Embeddings explained in detail
- Performance characteristics documented
- Troubleshooting guide included

**2. IMPLEMENTATION.md** (updated):
- Added "Core Documentation" section
- Links to ARCHITECTURE.md, CHRONICLES.md, CLAUDE.md
- Clear navigation for different doc purposes

**3. CHRONICLES.md** (updated):
- Entry 14 (this entry) added to phase-2.5-deployment.md
- Explains why architecture documentation matters now
- Documents the "explaining the machine" moment

---

### Why This Documentation Matters

**For future developers:**
- Understand system design without reading all code
- Visual diagrams show component relationships
- Embeddings explained (not assumed knowledge)
- Troubleshooting guide for common issues

**For current development:**
- Reference for architectural decisions
- Performance baselines documented
- Clear component responsibilities
- Deployment options catalogued

**For Phase 2.5 validation:**
- Users can understand what they're testing
- Clear explanation of how search works
- Performance expectations set
- Troubleshooting guide if issues arise

---

### What Makes This Architecture Work

**1. Simplicity:**
- Minimal layers (mobile → server → Synthesis → vault)
- No caching yet (not needed, search is fast enough)
- Direct imports (not subprocess complexity)
- Vanilla HTML/CSS/JS (no framework overhead)

**2. Performance:**
- Model loaded once (not per-search)
- Vector operations optimized (NumPy/sklearn)
- Scales to 10,000+ files without degradation
- <2s response time target easily met

**3. Privacy:**
- All local processing (no cloud APIs)
- Tailscale VPN encryption
- No data leaves your network
- Full control over embeddings model

**4. Mobile-First:**
- Responsive UI design
- Fast search (<500ms avg)
- obsidian:// deep links
- Simple, focused interface

**5. Maintainability:**
- Clean separation of concerns
- External dependency (Synthesis) isolated
- Configuration centralized
- Comprehensive tests (24 passing)

---

### Lessons from Architecture Documentation

**1. ASCII diagrams >> prose**

Visual representation clarifies in ways text can't. A simple diagram:
```
Mobile → Server → Synthesis → Vault
```
...is clearer than paragraphs explaining the flow.

**2. Explain the "why" of embeddings**

Don't assume readers know what embeddings are or how semantic search works. The explanation:
- What are embeddings? (vectors capturing meaning)
- How do they work? (transformer models, cosine similarity)
- Why do they work? (pre-trained on billions of texts)

**3. Performance numbers matter**

Concrete measurements anchor expectations:
- 400ms search time (not "fast")
- 600 MB memory (not "reasonable")
- 10 MB index (not "small")

**4. Troubleshooting = empathy**

"Search is slow (>2s)" section anticipates real problems:
- Is model loaded?
- Is index too large?
- Network latency?
- Server resources?

**5. Document deployment options**

Not everyone uses the same workflow:
- Manual (development)
- Background (personal use)
- Systemd (always-on)

All are valid, all documented.

---

### Meta: When to Write Architecture Docs

**Too early:**
- System not stable yet
- Components still changing rapidly
- Patterns not emerged
- Documenting churn, not design

**Too late:**
- Knowledge lost (why decisions made)
- New contributors confused
- Assumptions undocumented
- Troubleshooting tribal knowledge

**Right time (Temoa now):**
- ✓ System working and tested
- ✓ Architecture stable (post-Phase 2)
- ✓ Patterns clear (direct imports, etc.)
- ✓ Before validation phase (users need context)
- ✓ Before forgetting why choices were made

**Pattern:** Write architecture docs **after proving it works, before scaling usage**.

---

### Commits

- (pending): docs: add comprehensive ARCHITECTURE.md with ASCII diagrams
- (pending): docs: update IMPLEMENTATION.md with core documentation links
- (pending): docs: add Entry 14 to chronicles about architecture documentation

---

### Updated Documents

- `docs/ARCHITECTURE.md` - New comprehensive architecture reference (500+ lines)
- `docs/IMPLEMENTATION.md` - Added core documentation section with links
- `docs/chronicles/phase-2.5-deployment.md` - Entry 14 (this entry)

---

### Next Steps

**Immediate:**
- Commit architecture documentation
- Continue Phase 2.5 shakedown (remaining API endpoints)

**For contributors:**
- ARCHITECTURE.md is now the starting point for understanding Temoa
- Read alongside CLAUDE.md (development guide) and IMPLEMENTATION.md (progress)

**For future sessions:**
- Reference architecture doc when making changes
- Update diagrams if component interactions change
- Add troubleshooting entries as new issues discovered

---

## Entry 15: Type Filtering - From Noise to Signal (2025-11-23)

### Context

After deploying Temoa and using it for real searches, user identified a critical usability issue:

**User observation:** "the temoa web app filters daily notes. the cli search does not. is that right? I'd like to implement a mechanism that filters on the `type:` field."

**The problem:**
- Search results cluttered with daily notes (which are source of gleanings, not findings themselves)
- Daily notes have `type: daily` in frontmatter but CLI doesn't filter them out
- Web UI had path-based filtering (`Daily/` directory exclusion) but not type-based
- Need consistent type-based filtering across both CLI and Web UI

**Requirements identified:**
1. Filter on frontmatter `type:` field (not just file path)
2. Support both single string and YAML array formats
3. Provide inclusive (--type) and exclusive (--exclude-type) modes
4. OR matching for arrays (document with multiple types)
5. Default should exclude daily notes to reduce noise
6. Implement in both CLI and Web UI

---

### Implementation Overview

**Core Components Built:**

1. **Frontmatter Type Field Parser** (`gleanings.py:216`):
   ```python
   def parse_type_field(frontmatter: dict) -> list[str]:
       """Extract type(s) from frontmatter, normalize to list"""
       # Handles: type: gleaning
       # Handles: type: [writering, article]
       # Handles: type:\n  - writering\n  - article
   ```

2. **Type Filter Function** (`server.py:152`):
   ```python
   def filter_by_type(results, include_types=None, exclude_types=None):
       """Filter results by type with OR matching"""
       # Uses cached frontmatter (no file I/O!)
       # Returns (filtered_results, num_filtered)
   ```

3. **CLI Integration** (`cli.py`):
   - Added `--type/-t` and `--exclude-type/-x` flags
   - Logging configuration to suppress noisy synthesis logs
   - Filter statistics display in results

4. **Web UI Controls** (`search.html`):
   - Multi-select dropdowns for include/exclude types
   - Type badge display in search results
   - Updated stats panel showing filter counts
   - CSS styling for type controls

5. **API Endpoint Updates**:
   - `/search` endpoint accepts `include_types` and `exclude_types` params
   - Response includes `filtered_count` statistics
   - Filter chain: score → status → type → daily notes → limit

---

### The Debug Journey: Three Critical Issues

**Issue 1: Missing Frontmatter Dependency**

**Symptom:**
```bash
$ temoa search "obsidian"
Traceback (most recent call last):
  ...
ModuleNotFoundError: No module named 'frontmatter'
```

**Root cause:** Added `parse_type_field()` using `frontmatter` module, but forgot to add dependency to `pyproject.toml`

**Fix:** Added `python-frontmatter>=1.0.0` to dependencies

**Commit:** 13bef34 "fix: add missing python-frontmatter dependency"

**Lesson:** Always update pyproject.toml when adding new imports

---

**Issue 2: Excessive Logging Spam**

**User complaint:** "wtf is this crud?"

**Symptom:**
```bash
$ temoa search "obsidian"
[VaultReader] Initialized for vault: /Users/.../amoxtli
[VaultReader] Initialized for vault: /Users/.../amoxtli
[VaultReader] Initialized for vault: /Users/.../amoxtli
... (hundreds of lines)
```

**Root cause:** Initial `filter_by_type()` implementation read files for every result, triggering VaultReader initialization logs from synthesis modules

**Fix 1 (quick):** Added logging configuration to CLI:
```python
logging.basicConfig(level=logging.WARNING, format="%(message)s")
logging.getLogger("temoa.synthesis").setLevel(logging.WARNING)
logging.getLogger("src.embeddings").setLevel(logging.WARNING)
```

**Commit:** 3cb340a "fix: reduce noisy logging output in CLI"

**But this revealed a deeper issue...**

---

**Issue 3: Performance Degradation from File I/O**

**User observation:** "but this didn't happen before?"

**Investigation:** User was right - this logging noise was new, caused by the type filtering implementation

**Root cause:**
```python
# Bad: Read file for EVERY result
for result in results:
    with open(result_path) as f:
        post = frontmatter.load(f)  # File I/O!
        types = parse_type_field(post.metadata)
```

**Impact:**
- File I/O for every search result (dozens of file reads per search)
- Triggered VaultReader initialization in synthesis modules
- Performance degradation (not measured but noticeable)
- Excessive logging even with suppression

**User directive:** "we already cache? whatever. make it better"

**Better fix:** Use cached frontmatter from Synthesis results:
```python
# Good: Use cached frontmatter (NO file I/O!)
for result in results:
    frontmatter_data = result.get("frontmatter")  # Already in memory!
    if frontmatter_data is not None:
        types = parse_type_field(frontmatter_data)  # <1ms
```

**Commit:** 68ac23a "perf: use cached frontmatter for type filtering"

**Result:**
- Zero file I/O during type filtering
- <1ms overhead per search
- No VaultReader initialization logs
- Clean output

**Lesson:** Always prefer cached data over file reads. Synthesis already caches frontmatter during indexing - use it!

---

### Architecture Decision: Where Frontmatter is Cached

**Question discovered:** "ok so `temoa index` and `temoa reindex` rebuild the cache?"

**Answer:** Yes! Frontmatter is cached during index/reindex operations by Synthesis:

**Indexing flow:**
```
1. Scan vault files
2. Read each file (parse markdown + frontmatter)
3. Generate embedding from content
4. Store embedding + frontmatter in .temoa/embeddings.pkl
   ↑ Frontmatter cached here!
```

**Search flow:**
```
1. Load embeddings.pkl (includes cached frontmatter)
2. Generate query embedding
3. Calculate similarities
4. Return results with cached frontmatter
   ↑ No file I/O needed!
```

**Why this matters:**
- Type filtering is essentially free (<1ms overhead)
- No file system access during search
- Scales to thousands of results without performance hit
- Cached frontmatter includes ALL fields (type, tags, dates, etc.)

**User question:** "what is the difference between `temoa index` and `temoa reindex --force`"

**Answer:** They're identical! Both rebuild the entire index from scratch. The distinction exists for clarity of intent:
- `temoa index` - "I'm building the index for the first time"
- `temoa reindex --force` - "I know an index exists, rebuild it anyway"

**User response:** "nope it's fine" (accepted current design)

---

### Supported Document Types

**Current types in use:**
- `gleaning` - Extracted links/articles from daily notes
- `writering` - Writing-related content
- `llmering` - LLM/AI-related content
- `article` - General articles
- `reference` - Reference material
- `note` - General notes
- `daily` - Daily notes (excluded by default)

**Extensible:** Users can define any type values in frontmatter, not limited to these

---

### Default Behavior: Exclude Daily Notes

**DEC-025: Default exclude_types=["daily"]**

**Date:** 2025-11-23
**Context:** Search results cluttered with daily notes that are source of gleanings, not findings
**Decision:** Default to excluding documents with `type: daily` in both CLI and Web UI
**Rationale:**
- Daily notes are containers, not content to surface in search
- Gleanings extracted from daily notes are the actual findings
- Reduces noise in search results significantly
- Users can still include daily notes explicitly with `--type daily` or `--exclude-type ""` in CLI, or clearing exclude filter in UI

**Trade-offs:**
- Hides daily notes by default (some users might want them)
- But: Easy to override with flags or UI controls
- And: Dramatically improves signal-to-noise ratio

---

### Migration Support

> **Note**: Migration completed 2025-11-23. Scripts referenced below (`add_type_to_daily_notes.py`, `add_titles_to_gleanings.py`, `analyze_gleaning_formats.py`) have been removed as they were one-time use tools. This section preserved for historical reference.

**Created:** `scripts/add_type_to_daily_notes.py`

**Purpose:** Add `type: daily` to all existing daily note files

**Features:**
- Scans Daily/ directory for markdown files
- Adds `type: daily` to frontmatter if missing
- Skips files that already have a type field
- Warns if existing type conflicts with "daily"
- Includes `--dry-run` mode for safe preview
- Provides detailed summary of changes

**Usage:**
```bash
# Preview changes
uv run scripts/add_type_to_daily_notes.py --dry-run

# Apply changes
uv run scripts/add_type_to_daily_notes.py

# Specify vault path
uv run scripts/add_type_to_daily_notes.py --vault-path ~/Obsidian/vault
```

**Example output:**
```
Scanning daily notes in: /Users/.../vault/Daily
Found 742 markdown files in Daily/

  UPDATED: 2025-01-15.md
  UPDATED: 2025-01-16.md
  SKIPPED: 2025-01-17.md (already has type: daily)

Summary:
  Updated: 740
  Skipped: 2
```

---

### Filter Chain Architecture

**Complete filtering pipeline:**

```
Raw Search Results (2000 files)
    ↓
Score Filter (min_score >= 0.3)
    ↓ (800 results)
Status Filter (exclude inactive/hidden gleanings)
    ↓ (750 results)
Type Filter (exclude_types=["daily"])
    ↓ (500 results)
Daily Path Filter (backward compat: exclude Daily/)
    ↓ (500 results, no change since type filter already excluded)
Limit Filter (top 10)
    ↓
Final Results (10 results)

Filtered count stats returned:
{
  "by_score": 1200,
  "by_status": 50,
  "by_type": 250,
  "by_daily_path": 0,
  "total_filtered": 1500,
  "total_before_limit": 500
}
```

**Why two daily filters?**
- Type filter: New, preferred method (works on `type: daily` field)
- Path filter: Backward compatibility (works on `Daily/` directory)
- Both coexist: Type filter catches typed dailies, path filter catches untyped ones
- Eventually: Migrate all daily notes to have `type: daily`, deprecate path filter

---

### Issue 4: Daily Notes and Semantic Search Mismatch

**User observation:** "semantic search was the problem"

**Context:** After removing path-based filtering, user tested searching for "workout" which appears in 42 daily notes (verified with grep). Semantic-only search found 0 daily notes, but hybrid search found them easily.

**Investigation:**

Semantic-only search:
```bash
$ temoa search "workout" --exclude-type ""
# Result: 1 result (gym article), 29 filtered by score
```

Hybrid search:
```bash
$ temoa search "workout" --exclude-type "" --hybrid --limit 3
# Results: 3 daily notes found!
# Scores:
# - Semantic: 0.266, BM25: 6.981
# - Semantic: 0.239, BM25: 7.267
# - Semantic: 0.213, BM25: 7.437
```

**Root cause:** Daily notes have **low semantic similarity** but **high BM25 keyword match**

Daily note content is typically short and context-poor:
- "- workout good walking is best part"
- "- no workout"
- "- missed workout"

**Why this happens:**

1. **Semantic embeddings need context**: Short phrases like "workout good" don't provide enough context for meaningful semantic similarity. The transformer model can't capture much meaning from 3-4 words.

2. **BM25 excels at keyword matching**: Exact word "workout" → high BM25 score (6-7 range)

3. **Default min_score threshold**: Semantic-only mode filters results with similarity < 0.3, which excludes all daily notes (0.21-0.27 range)

4. **Hybrid mode doesn't apply score filter**: By design, hybrid search doesn't filter by similarity score because BM25-only results may not have semantic scores

**The fix:**

For daily notes, use either:
```bash
# Lower the score threshold
temoa search "workout" --type daily --min-score 0.0

# Or use hybrid (recommended!)
temoa search "workout" --type daily --hybrid
```

**Architectural insight:**

Daily notes are **keyword-rich but context-poor**, making them fundamentally better suited for BM25/hybrid search than pure semantic search.

This has broader implications:
- Maybe hybrid should be the **default search mode**?
- Or at least document that daily note searches work better with `--hybrid`
- Consider different min_score thresholds for different document types?

**The debugging journey:**

1. User: "grep finds 42 daily notes with 'workout' but temoa finds 0"
2. Me: "Daily notes aren't indexed!" ❌ Wrong assumption
3. User: "no, I think semantic search was the problem" ✓ Correct!
4. Testing with `--hybrid` revealed the issue
5. Root cause: min_score threshold filtering out low-similarity daily notes

**Lesson:** Short-form content (daily notes, tweets, chat logs) has different search characteristics than long-form content (articles, documents). Semantic search optimizes for long-form content with rich context. Hybrid search bridges both worlds.

**DEC-026: Hybrid Search Recommendation for Daily Notes**

**Date:** 2025-11-23
**Context:** Daily notes have low semantic scores but high BM25 scores
**Decision:** Document that daily note searches work best with `--hybrid` flag
**Rationale:**
- Daily notes are short and context-poor (3-20 word bullets typically)
- Semantic similarity scores fall below default min_score threshold
- BM25 keyword matching works perfectly for daily notes
- Hybrid combines both → best of both worlds

**Recommendation for users:**
- Default search: Semantic-only (good for finding similar concepts)
- Searching daily notes: Use `--hybrid` flag (good for finding exact keywords)
- Or: Lower `--min-score` threshold when searching dailies

**Future consideration:** Auto-detect when searching for `type: daily` and suggest/enable hybrid mode automatically?

---

### Commits in This Session

```
2c1cfe6 - feat: implement type-based filtering for search results
13bef34 - fix: add missing python-frontmatter dependency
3cb340a - fix: reduce noisy logging output in CLI
68ac23a - perf: use cached frontmatter for type filtering
c7984fe - fix: remove path-based daily filtering, use only type filtering
38ddf45 - refactor: remove unused filter_daily_notes function
```

**Progression:** Feature → Bug fix → Another bug fix → Performance optimization

**Pattern:** Each commit revealed the next issue, systematic debugging approach

---

### Lessons Learned

**1. Real-world deployment reveals performance issues tests miss**

Tests passed with filter_by_type() reading files because:
- Test vault is small (few files)
- File I/O overhead not noticeable
- No logging to spot the problem

Production deployment with 2,281 files:
- Hundreds of file reads per search
- VaultReader initialization spam
- User immediately noticed: "wtf is this crud?"

**Lesson:** Performance issues only visible at scale with real data

---

**2. User feedback drives optimization**

Initial approach: "Just read the files, it's fine"

User complaint about logging noise → investigation → discovered file I/O bottleneck

User question "but this didn't happen before?" → realization this was NEW performance issue

User directive "make it better" → optimization using cached frontmatter

**Lesson:** User observations often reveal architectural flaws we missed

---

**3. Check if data is already cached before fetching**

Synthesis already caches frontmatter during indexing. We could have used it from the start, but didn't check.

**Question to always ask:** "Is this data already in memory somewhere?"

**In this case:**
- Frontmatter cached in embeddings.pkl
- Loaded into memory during search
- Available in search results
- Just needed to access it!

**Lesson:** Know your data flow. Understand what's cached and when.

---

**4. Default exclude behavior improves UX dramatically**

Before: Search results mixed gleanings with daily notes (noisy)
After: Default excludes daily notes (signal!)

**User can still access daily notes** via:
- CLI: `--type daily` or `--exclude-type ""`
- Web UI: Clear exclude filter
- API: `exclude_types=[]` parameter

**Pattern:** Optimize for common case (exclude dailies), allow override for edge cases

---

**5. Migration scripts reduce friction**

Adding `type: daily` to 742 files manually = tedious, error-prone

`add_type_to_daily_notes.py` script:
- Automated, safe (dry-run mode)
- Handles edge cases (existing types)
- Provides clear summary
- Reduces adoption friction

**Lesson:** When introducing new metadata requirements, provide migration tooling

---

### Updated Deliverables

**Code:**
- [x] `parse_type_field()` function in `src/temoa/gleanings.py`
- [x] `filter_by_type()` function in `src/temoa/server.py` (optimized)
- [x] CLI flags: `--type` and `--exclude-type` in `src/temoa/cli.py`
- [x] Web UI type controls in `src/temoa/ui/search.html`
- [x] Logging configuration to suppress synthesis module noise

**Scripts:**
- [x] `scripts/add_type_to_daily_notes.py` - Migration tool

**Documentation:**
- [x] `docs/ARCHITECTURE.md` - Updated with type filtering flow and diagram
- [x] `docs/IMPLEMENTATION.md` - Added "Type Filtering Implementation" section
- [x] `docs/chronicles/phase-2.5-deployment.md` - Entry 15 (this entry)

**Dependencies:**
- [x] `python-frontmatter>=1.0.0` added to `pyproject.toml`

---

### Type Field Format Specification

**Frontmatter type field supports multiple formats:**

**Single string:**
```yaml
type: gleaning
```

**Inline array:**
```yaml
type: [writering, article]
```

**Block array:**
```yaml
type:
  - writering
  - article
```

**OR matching:** If document has multiple types, matches if ANY type in filter
- Document: `type: [gleaning, article]`
- Filter: `--type gleaning` → Matches!
- Filter: `--type note` → No match

**Missing type field:** Treated as empty list `[]`
- Doesn't match include filters
- Doesn't match exclude filters (not excluded if type is missing)

---

### Production Impact

**Before type filtering:**
```
Search: "obsidian"
Results: 50 (mixed daily notes + gleanings + other)
Signal-to-noise: Low (daily notes dominate results)
```

**After type filtering (default exclude daily):**
```
Search: "obsidian"
Results: 10 gleanings (dailies filtered out)
Signal-to-noise: High (only relevant findings)
Filtered out: 40 daily notes
```

**Performance:**
- Filter overhead: <1ms (cached frontmatter)
- No file I/O during search
- Scales to thousands of results

**User experience:**
- Cleaner search results
- Consistent filtering across CLI and Web UI
- Easy to override defaults when needed

---

### Next Steps

**Immediate:**
- Commit all documentation updates
- Continue Phase 2.5 validation with type filtering in production use

**Future enhancements:**
- Track which types are most commonly used
- Add type analytics to /stats endpoint
- Consider auto-detecting types from file content/location
- UI improvements: type autocomplete, recent types

**Questions to answer during Phase 2.5:**
- Is default exclude daily sufficient or too aggressive?
- Do users need more granular type taxonomies?
- Should types be hierarchical (e.g., `gleaning/article`)?
- Is OR matching intuitive or should we support AND?

---

### Meta: The Value of Incremental Optimization

**This feature went through 4 iterations:**

1. **Initial implementation** (2c1cfe6): Basic type filtering with file reads
2. **Dependency fix** (13bef34): Added missing frontmatter library
3. **Logging suppression** (3cb340a): Quick fix for noise
4. **Performance optimization** (68ac23a): Cached frontmatter (proper fix)

**Pattern:**
- Ship basic version → Deploy → User feedback → Optimize → Perfect

Not:
- Predict all issues upfront → Build perfect version → Ship

**Why incremental works:**
- Issues only visible in production (logging spam, performance)
- User feedback guided optimization (user spotted the performance regression)
- Each fix taught us something (file I/O bottleneck, cached frontmatter)

**Lesson:** Perfect is the enemy of shipped. Ship, learn, optimize.

---

### Status at Session End

**Type filtering: COMPLETE**
- ✅ CLI and Web UI both support type filtering
- ✅ Default excludes daily notes for cleaner results
- ✅ Performance optimized using cached frontmatter (<1ms overhead)
- ✅ Migration script available for adding type: daily
- ✅ Documentation updated (ARCHITECTURE, IMPLEMENTATION, CHRONICLES)

**Ready for Phase 2.5 validation:**
- Type filtering working in production
- Can now focus mobile validation on signal, not noise
- User can search without daily notes cluttering results

**Current branch:** `claude/plan-type-filtering-01RdHnhwX7CNC5WkNa4z1Fxb`

**Next:** Commit documentation updates and continue Phase 2.5 mobile validation

---

## Entry 16: UI Refinement - Polish Through Real Usage (2025-11-23)

### Context

After implementing type filtering and using the web UI in production, user identified several UX improvements to make the interface cleaner and more usable:

**User's observations:**
- "Score badge should be on the right, not left"
- "Project-to badge should be next to score"
- "Stats panel takes up too much space, should be collapsible"
- "Type badge placement feels wrong"
- "Need proper error handling for validation errors"

This session focused on UI refinement based on actual usage patterns - part of the Phase 2.5 shakedown process.

---

### The Improvements

**1. Score Badge Repositioning**

**Before:**
```
[0.654] Title of document
        type: gleaning | project-to: phase3
```

**After:**
```
Title of document                           [0.654]
type: gleaning | project-to: phase3
```

**Why:** Score is metadata, not the primary identifier. Title should be leftmost and most prominent. Score on the right creates clean visual hierarchy.

**Commit:** abb74e5 "feat: move score badge to rightmost position in result header"

---

**2. Project-To Badge Repositioned**

**Before:**
```
Title of document                           [0.654]
type: gleaning | project-to: phase3
```

**After:**
```
Title of document              project-to: phase3 [0.654]
type: gleaning
```

**Why:** Project-to and score are both metadata about the document's status/relevance. Grouping them together on the right creates logical association. Type badge stays with other document attributes on the second line.

**Commit:** d02ee39 "feat: move project-to badge next to score in result header"

---

**3. Validation Error Handling**

**Problem:** When API returns validation errors (e.g., missing required parameters), the UI showed generic "Search failed" messages without details about what went wrong.

**Example error:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["query", "q"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

**Solution:** Enhanced error handling in UI to:
- Detect validation error structure (array of detail objects)
- Extract readable error messages
- Display helpful feedback to user
- Handle both single and multiple validation errors

**Display:**
```
❌ Validation error: String should have at least 1 character (query → q)
```

**Commit:** 1a18714 "fix: handle validation errors properly in UI"

---

**4. Compact and Collapsible Stats Panel**

**Problem:** Stats panel showed 8 lines of information that took up significant screen space, especially on mobile:

```
Files indexed: 2,942
Results shown: 10
Filtered by score: 15
Filtered by type: 8
Filtered by status: 2
Model: all-mpnet-base-v2
Response time: 0.4s
Last indexed: 2025-11-23
```

**Solution:** Made stats collapsible with compact summary:

**Collapsed (default):**
```
📊 Stats (2,942 files, 10 results) [click to expand]
```

**Expanded (on click):**
```
📊 Stats (click to collapse)
Files indexed: 2,942
Results shown: 10
... (full details)
```

**Benefits:**
- Saves vertical space (8 lines → 1 line when collapsed)
- Still shows key metrics in summary (total files, result count)
- Easy to expand when detailed stats needed
- Better mobile UX (less scrolling to see results)
- Remembers state in session (localStorage)

**Commit:** 36d895e "feat: compact and collapsible stats panel"

---

**5. Type Badge Repositioned (Final Layout)**

**Problem:** With project-to badge moved to the right, type badge placement needed adjustment for visual balance.

**Final layout:**
```
Title of document              project-to: phase3 [0.654]
type: gleaning
```

**Why:**
- Title is primary (leftmost, bold)
- Metadata on right (project-to, score)
- Attributes on second line (type, tags, etc.)
- Clean visual hierarchy

**Commit:** 94cb4f4 "feat: reposition type badge next to score badge in result header"

---

### Visual Design Principles Emerged

**Information Hierarchy:**
1. **Primary:** Document title (bold, leftmost)
2. **Relevance:** Score + project-to (right side, metadata)
3. **Classification:** Type, tags (second line, attributes)
4. **Context:** Source, date (tertiary info)

**Space Optimization:**
- Collapsible sections for optional information
- Compact summary states that expand on demand
- Mobile-first: minimize scrolling, maximize content

**Error Communication:**
- Specific error messages, not generic failures
- Show what went wrong and where
- Help users fix the issue themselves

---

### Lessons Learned

**1. Real usage reveals UI friction**

None of these issues were apparent during initial development. They only became obvious after:
- Using the search repeatedly
- Looking at actual result layouts
- Noticing what information you look for first
- Experiencing the scroll fatigue on mobile

**Pattern:** Build → Use → Notice friction → Refine

---

**2. Visual hierarchy matters more than you think**

Moving the score badge from left to right seems minor, but impact was significant:
- Title now clearly the primary identifier
- Score feels like metadata, not a label
- Eyes naturally scan left → right: title → relevance

**Lesson:** Even small layout changes affect information processing

---

**3. Collapsible UI saves mobile real estate**

Stats panel went from:
- Always visible (8 lines)
- To: Collapsed by default (1 line)

**Impact:**
- 7 lines saved = 1-2 more results visible without scrolling
- Still accessible when needed (click to expand)
- Remembers preference (localStorage)

**Pattern:** Default to minimal, expand on demand

---

**4. Error messages should teach, not just inform**

**Bad error message:**
```
Search failed
```

**Good error message:**
```
Validation error: String should have at least 1 character (query → q)
```

**Why good is better:**
- Tells user what went wrong
- Shows which field is the problem
- Suggests how to fix it (add characters)
- Respects user's time (no guessing)

**Lesson:** Error messages are teaching moments

---

### Testing Validation

**Tested scenarios:**

1. **Empty query:**
   - Input: `""` (empty string)
   - Expected: Validation error
   - Result: ✓ Proper error message displayed

2. **Score badge positioning:**
   - Desktop: ✓ Right-aligned, clean
   - Mobile: ✓ Wraps properly on small screens

3. **Stats panel collapse:**
   - Default state: ✓ Collapsed
   - Click to expand: ✓ Shows full details
   - Click to collapse: ✓ Returns to summary
   - Refresh page: ✓ Remembers state

4. **Project-to + score grouping:**
   - Visual: ✓ Grouped together logically
   - Alignment: ✓ Right-aligned as metadata
   - Spacing: ✓ Clear separation from title

---

### Commits in This Session

All part of UI refinement shakedown:

```
abb74e5 - feat: move score badge to rightmost position in result header
d02ee39 - feat: move project-to badge next to score in result header
1a18714 - fix: handle validation errors properly in UI
36d895e - feat: compact and collapsible stats panel
94cb4f4 - feat: reposition type badge next to score badge in result header
```

**Pattern:** Each commit is a focused improvement based on real usage observation

---

### Updated Deliverables

**UI Components:**
- [x] Redesigned result header layout (title left, metadata right)
- [x] Collapsible stats panel with compact summary
- [x] Enhanced error handling for validation errors
- [x] Visual hierarchy improvements (typography, spacing)

**State Management:**
- [x] Stats panel collapse state persisted in localStorage
- [x] Graceful fallback if localStorage unavailable

**Error Handling:**
- [x] Validation error detection and parsing
- [x] User-friendly error message formatting
- [x] Field-level error reporting (query → q)

---

### Meta: The Shakedown Philosophy

**What is a shakedown?**

Shakedown = Use the thing you built, find rough edges, smooth them out

**Not the same as:**
- Feature development (building new capabilities)
- Bug fixing (fixing broken functionality)
- Testing (validation that it works)

**Shakedown is:** Refinement through real usage

**Examples from this session:**
- Score badge position: Works, but feels wrong → move it
- Stats panel: Works, but too verbose → collapse it
- Error messages: Works, but too generic → make specific

**All features worked correctly.** Shakedown made them work *well*.

---

### The Value of Polish

**Before this session:**
- Search: ✓ Works
- Type filtering: ✓ Works
- Stats display: ✓ Works
- Error handling: ✓ Works

**After this session:**
- Search: ✓ Works *and feels good to use*
- Type filtering: ✓ Works *and results are easy to scan*
- Stats display: ✓ Works *and doesn't waste space*
- Error handling: ✓ Works *and teaches users what to fix*

**Difference:** Polish = usability × delight

---

### Status at Session End

**UI Refinement: COMPLETE**
- ✅ Result header layout optimized (title left, metadata right)
- ✅ Stats panel compact and collapsible
- ✅ Error messages helpful and specific
- ✅ Visual hierarchy clear and consistent
- ✅ Mobile-first space optimization

**Phase 2.5 Shakedown Progress:**
- ✅ Type filtering (Entry 15)
- ✅ UI refinement (Entry 16 - this entry)
- ⏭️ Next: Continue mobile validation with polished interface

**Current branch:** `claude/update-webapp-ui-01KXciQKmygZoXJvJqJtvuEv`

**Next:** Document this session in chronicles and implementation, continue Phase 2.5 validation

---

### What This Means for Phase 2.5

**Good news:** UI is now polished enough for serious mobile validation

**Better news:** Each refinement makes the behavioral hypothesis easier to test:
- Cleaner results → easier to scan on mobile
- Collapsible stats → less scrolling on small screens
- Better errors → less frustration when things go wrong
- Visual hierarchy → faster information processing

**The hypothesis:**
> "If I can search my vault from my phone in <2 seconds, I'll check it before Googling."

**Now we can test it properly** because the UI is no longer getting in the way.

---
