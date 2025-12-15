# Documentation Guide - How Temoa Documentation Works

> **Purpose**: Complete guide to Temoa's documentation structure, session workflows, and maintenance processes
>
> **Audience**: Contributors, LLMs working on Temoa, future maintainers

**Created**: 2025-12-14
**Status**: Living document

---

## Documentation Philosophy

**Core Principle**: Separate concerns for fast session pickup

- **IMPLEMENTATION.md** = "What we're doing now" (living todo for current phase)
- **CHRONICLES.md** = "What happened and why" (historical narrative navigation)
- **DECISIONS.md** = "What we decided" (quick decision lookup)
- **chronicles/** = "The detailed story" (session-by-session implementation notes)

**Goal**: New session starts in <5 minutes by reading IMPLEMENTATION.md current phase section (~200 lines)

---

## Documentation Structure

### Top-Level Documents

```
docs/
├── IMPLEMENTATION.md          # Progress tracker (914 lines)
├── CHRONICLES.md              # Historical navigation (118 lines)
├── DECISIONS.md               # Decision registry (227 lines)
├── README.md                  # Documentation index (121 lines)
├── ARCHITECTURE.md            # System architecture
├── SEARCH-MECHANISMS.md       # Search algorithms deep dive
├── DEPLOYMENT.md              # Deployment guide
└── GLEANINGS.md              # Gleanings system guide
```

### Directory Structure

```
docs/
├── chronicles/                # Detailed implementation notes by phase
│   ├── phase-0-1-foundation.md      (1,308 lines | Entries 1-6)
│   ├── phase-2-gleanings.md         (965 lines   | Entries 7-10)
│   ├── phase-2.5-deployment.md      (3,762 lines | Entries 11-19)
│   ├── phase-3-implementation.md    (2,919 lines | Entries 20-32)
│   └── production-hardening.md      (1,286 lines | Entries 33-38+)
│
├── archive/                   # Historical documents
│   └── original-planning/     # Waterfall plans from before implementation
│       ├── README.md          (explains these are historical)
│       ├── phase-0-discovery.md
│       ├── phase-1-mvp.md
│       ├── phase-2-gleanings.md
│       ├── phase-3-enhanced.md
│       └── phase-4-llm.md
│
└── assets/                    # Images, diagrams, etc.
```

---

## File Purposes & When to Update

### IMPLEMENTATION.md (Progress Tracker)

**Purpose**: Living todo list for current phase

**Structure**:
- Phase Overview table (all phases summary)
- Completed phases: 80-120 line summaries
- **Current phase: DETAILED** (200-300 lines) ← the active todo
- Future phases: High-level plans

**When to update**:
- ✅ Start of phase: Add detailed task breakdown for new current phase
- ✅ During phase: Update task status, add notes
- ✅ End of phase: Compress completed phase to summary, link to chronicles/

**What goes here**:
- Task lists with checkboxes
- High-level achievements
- Performance metrics
- Links to chronicles/ for details

**What DOESN'T go here**:
- Detailed bug analysis (goes in chronicles/)
- Implementation code examples (goes in chronicles/)
- Design discussions (goes in chronicles/)

**Size target**: Keep IMPLEMENTATION.md at ~800-1000 lines total

---

### CHRONICLES.md (Historical Navigation)

**Purpose**: Index and navigation for all chronicle entries

**Structure**:
- Chronicle organization (links to chapter files)
- Entry list by phase (1-line summary per entry)
- Link to DECISIONS.md
- Reading guide for newcomers

**When to update**:
- ✅ End of session: Add new entry to appropriate phase section
- ✅ New phase starts: Add new phase section header

**What goes here**:
- Entry numbers and titles
- One-line summaries
- Links to chronicle chapter files
- Navigation hints ("If you're debugging..." → Entry X)

**What DOESN'T go here**:
- Full entry content (goes in chronicles/phase-X.md)
- Decision details (goes in DECISIONS.md)

**Size target**: Keep CHRONICLES.md at ~150-200 lines (just navigation)

---

### chronicles/phase-X.md (Detailed Implementation Notes)

**Purpose**: Session-by-session implementation journal for each phase

**Structure per entry**:
```markdown
## Entry XX: Title - Brief Description (YYYY-MM-DD)

**Context**: Why this work was needed

### The Problem
[What we were trying to solve]

### The Solution
[What we built/fixed]

### Implementation Details
[Code changes, file changes, approaches tried]

### Testing
[How we validated it works]

### Key Decisions
**DEC-XXX: Decision Title**
- Rationale: Why
- Alternative: What we didn't choose
- Impact: What this affects

### Interesting Episodes
[Bugs, surprises, lessons learned]

### What's Next
[Follow-up work, future enhancements]

---
**Entry created**: YYYY-MM-DD
**Author**: Claude (model-name)
**Type**: [Feature/Bug Fix/Refactor/etc.]
**Impact**: [HIGH/MEDIUM/LOW]
**Duration**: ~X hours
**Branch**: branch-name
**Commits**: commit-hash
**Files changed**: N files
**Decision IDs**: DEC-XXX, DEC-YYY
```

**When to update**:
- ✅ End of session: Add new entry to current phase chronicle file
- ✅ During long sessions: Can add multiple entries

**What goes here**:
- Detailed implementation notes
- Code examples and snippets
- Bug analysis and fixes
- Design discussions
- Performance metrics
- Test results
- File lists and commit hashes
- Lessons learned

**Size**: No limit - these are the permanent detailed record

---

### DECISIONS.md (Decision Registry)

**Purpose**: Centralized registry of all architectural decisions

**Structure**:
- Decision Governance Process (at top)
- Decision Registry table (DEC-001 through DEC-N)
- Deprecated decisions
- Historical notes

**When to update**:
- ✅ When making significant architectural choice
- ✅ MUST update when documenting decision in chronicles/

**Process**:
1. Check DECISIONS.md for last decision number
2. Increment by 1 (e.g., DEC-084 → DEC-085)
3. Document in chronicle entry (detailed)
4. Add row to DECISIONS.md table (one-line summary)
5. **Commit both files together**

**What goes here**:
- Decision number (DEC-XXX)
- Short title
- Entry reference (where documented)
- One-line summary

**What DOESN'T go here**:
- Detailed rationale (goes in chronicles/ entry)
- Code examples (goes in chronicles/)
- Full discussion (goes in chronicles/)

**Size target**: One row per decision, ~300-400 lines for 100+ decisions

---

## Session Workflows

### Session Pick-Up Process

**Command**: `/session-pick-up` (in .claude/commands/)

**What it does**:
1. Reads IMPLEMENTATION.md (current phase section)
2. Reads latest CHRONICLES.md entries
3. Summarizes what to work on next

**Manual process** (if command not available):

```bash
# 1. Read current phase in IMPLEMENTATION.md
#    Find the phase marked with 🔵 (current)
#    Read the detailed task list (~200-300 lines)

# 2. Check latest chronicle entries (optional for context)
#    CHRONICLES.md → find latest entry numbers
#    Read latest 1-2 entries in chronicles/phase-X.md

# 3. Check DECISIONS.md (if working on architecture)
#    Search for relevant decisions

# Time: ~5 minutes
```

**Example**:
```
User: /session-pick-up

Claude reads:
1. IMPLEMENTATION.md lines 500-700 (Production Hardening section)
   - Sees Entry 33-38 completed
   - Identifies next task: "Validate frontmatter search on production vault"

2. CHRONICLES.md → Latest is Entry 38

3. Ready to work in ~2 minutes
```

---

### Session Wrap-Up Process

**Command**: `/session-wrap-up` (planned, not yet implemented)

**Manual process** (current):

#### 1. Update IMPLEMENTATION.md (if phase status changed)

```bash
# Only if completing tasks or changing phase status
# Update checkbox status, add notes

# If phase completes:
# - Mark phase as ✅ COMPLETE
# - Update next phase to 🔵 (current)
```

#### 2. Document Session in chronicles/

**Create new entry** in appropriate phase file:

```bash
# Example: Working on Production Hardening
# Edit: docs/chronicles/production-hardening.md

# Add new entry at bottom:
## Entry 39: Feature Name - Brief Description (2025-12-14)

**Context**: [Why this work]

### The Problem
[...]

### The Solution
[...]

[... rest of entry template ...]

---
**Entry created**: 2025-12-14
**Author**: Claude (Sonnet 4.5)
**Commits**: abc1234
**Decision IDs**: DEC-085 (if any)
```

#### 3. Add Decisions (if any)

If you made architectural decisions:

```bash
# 1. Check last decision number in DECISIONS.md
grep "^| DEC-" docs/DECISIONS.md | tail -1
# Example output: | DEC-084: Two-phase approach | 37 | ...

# 2. Next number is DEC-085

# 3. Document in chronicle entry (detailed)
**DEC-085: Smart query suggestions**
- Rationale: Real-world usage shows names vs topics distinction
- Alternative: Always expand (rejected, adds noise for names)
- Impact: Better UX, opt-in expansion

# 4. Add to DECISIONS.md table
| DEC-085: Smart query suggestions | 39 | Detect person names, suggest search modes |

# 5. Commit both files together
git add docs/chronicles/production-hardening.md docs/DECISIONS.md
git commit -m "docs: add Entry 39 - smart query suggestions"
```

#### 4. Update CHRONICLES.md

Add entry to phase section:

```bash
# Edit docs/CHRONICLES.md
# Find current phase section (e.g., "Production Hardening")
# Add new entry line:

- Entry 39: Smart Query Suggestions - Detect Names vs Topics
```

#### 5. Commit Documentation

```bash
git add docs/CHRONICLES.md docs/chronicles/production-hardening.md
# (and docs/DECISIONS.md if applicable)

git commit -m "docs: add Entry 39 - smart query suggestions (DEC-085)"
```

**Time**: ~10-15 minutes for thorough documentation

---

## Governance Rules

### Rule 1: One Source of Truth

**Never duplicate content between files**

- ✅ Detail in chronicles/ → Summary in IMPLEMENTATION.md
- ✅ Decision detail in chronicles/ → One-line in DECISIONS.md
- ❌ Same bug analysis in both IMPLEMENTATION.md AND chronicles/

### Rule 2: Compress Completed Phases

**When phase completes**:

1. **Trim IMPLEMENTATION.md** section from 500 lines → ~100 lines:
   - Keep: High-level summary, key achievements
   - Remove: Detailed task lists, bug analysis, code examples
   - Add: Link to chronicles/phase-X.md

2. **Mark phase ✅ COMPLETE** in Phase Overview table

3. **Move to next phase** (mark 🔵 current)

### Rule 3: Current Phase Gets Detail

**The active phase section in IMPLEMENTATION.md**:
- ✅ Detailed task lists (200-300 lines)
- ✅ Status updates during work
- ✅ Bullet points, code snippets, metrics
- ✅ This is the living todo list

**All other phases**:
- ❌ No detailed task lists
- ✅ Only summaries and links

### Rule 4: Decisions Need Two Commits

**When documenting decision**:

1. **First**: Detailed decision in chronicles/ entry
2. **Second**: Add to DECISIONS.md table
3. **Commit**: Both files together

**Never**: Decision in DECISIONS.md without chronicle entry

### Rule 5: Entry Numbers Are Sequential

**Chronicle entries**:
- Sequential across all phases (Entry 1, 2, 3... 38, 39, 40...)
- Never reuse entry numbers
- Never skip entry numbers

**Decision numbers**:
- Sequential (DEC-001, DEC-002... DEC-084, DEC-085...)
- Gaps are OK (historical reasons documented)
- Check DECISIONS.md for last number before adding new

---

## File Size Targets

| File | Target Size | Why |
|------|-------------|-----|
| IMPLEMENTATION.md | 800-1000 lines | Fast session pickup |
| CHRONICLES.md | 150-200 lines | Navigation only |
| DECISIONS.md | Grows with decisions | One row per decision |
| chronicles/phase-X.md | No limit | Permanent detailed record |

**If IMPLEMENTATION.md grows > 1200 lines**: Time to compress a completed phase

---

## Common Workflows

### Starting a New Phase

1. **Update IMPLEMENTATION.md**:
   - Mark previous phase ✅ COMPLETE
   - Compress previous phase to summary
   - Add detailed section for new phase
   - Mark new phase 🔵 (current)

2. **Update CHRONICLES.md**:
   - Add new phase section header

3. **Create new chronicle file** (if needed):
   - `docs/chronicles/phase-X-name.md`
   - Add to CHRONICLES.md navigation

### Completing a Phase

1. **Create final chronicle entry**:
   - "Phase X Complete" entry
   - Summary of achievements
   - Link to IMPLEMENTATION.md for details

2. **Update IMPLEMENTATION.md**:
   - Mark phase ✅ COMPLETE
   - Compress phase section to ~100 lines
   - Add "See chronicles/phase-X.md for details"

3. **Update CHRONICLES.md**:
   - Update phase status to ✅ COMPLETE

### Fixing a Production Bug

1. **Document in current phase chronicle**:
   - Entry title: "Bug Fix - [Description]"
   - Full analysis in chronicles/

2. **Update IMPLEMENTATION.md** (optional):
   - If significant, add bullet to current phase section
   - Keep brief, link to chronicle entry

3. **Decision** (if architectural):
   - Add to chronicle entry
   - Add to DECISIONS.md

---

## Quick Reference

### Session Pickup (5 min)
1. Read IMPLEMENTATION.md current phase section
2. Optionally check latest chronicle entries
3. Start working

### Session Wrap-Up (15 min)
1. Update IMPLEMENTATION.md (task status)
2. Create chronicle entry in phase-X.md
3. Add decisions to DECISIONS.md (if any)
4. Update CHRONICLES.md (add entry line)
5. Commit all docs together

### Adding a Decision
1. Check DECISIONS.md for last number
2. Document detailed in chronicle entry
3. Add row to DECISIONS.md
4. Commit both files together

---

## File Templates

### Chronicle Entry Template

```markdown
## Entry XX: Title - Brief Description (YYYY-MM-DD)

**Context**: [Why this work was needed]

### The Problem
[What we were trying to solve]

### The Solution
[What we built/fixed]

### Implementation Details
[Code changes, approaches tried]

### Testing
[How we validated]

### Key Decisions (if any)

**DEC-XXX: Decision Title**
- **Rationale**: Why this decision
- **Alternative**: What we didn't choose
- **Impact**: What this affects

### What's Next
[Follow-up work, future enhancements]

---
**Entry created**: YYYY-MM-DD
**Author**: Claude (model-name)
**Type**: [Feature/Bug Fix/Refactor/etc.]
**Impact**: [HIGH/MEDIUM/LOW]
**Branch**: branch-name
**Commits**: commit-hash
**Files changed**: N files
**Decision IDs**: DEC-XXX (if any)
```

### Decision Template (in chronicle entry)

```markdown
**DEC-XXX: Short Title**
- **Rationale**: Why we made this decision
- **Alternative**: What we considered but didn't choose
- **Impact**: What this affects (code, UX, performance, etc.)
- **Trade-offs**: What we gain vs. what we lose (optional)
```

### DECISIONS.md Table Row

```markdown
| DEC-XXX: Short title | Entry# | One-line summary of decision |
```

---

## Anti-Patterns to Avoid

### ❌ Don't Duplicate Content

**Bad**:
```
IMPLEMENTATION.md: [500 lines of detailed bug analysis]
chronicles/: [same 500 lines of bug analysis]
```

**Good**:
```
IMPLEMENTATION.md: "Fixed incremental extraction bug. See Entry 24."
chronicles/: [detailed bug analysis]
```

### ❌ Don't Let IMPLEMENTATION.md Bloat

**Bad**: IMPLEMENTATION.md reaches 2,000+ lines because completed phases are still detailed

**Good**: Trim completed phases to summaries, keep current phase detailed

### ❌ Don't Skip Decision Registry

**Bad**: Decision documented in chronicle but not added to DECISIONS.md

**Good**: Add to both (chronicle = detail, DECISIONS.md = registry)

### ❌ Don't Create Orphan Entries

**Bad**: Entry in chronicles/phase-X.md but not listed in CHRONICLES.md

**Good**: Update both files together

---

## Troubleshooting

### "IMPLEMENTATION.md is too long"

**Solution**: Compress completed phases to summaries

### "Can't find a decision"

**Solution**: Search DECISIONS.md table, follow Entry link for details

### "Session pickup takes too long"

**Solution**: Only read IMPLEMENTATION.md current phase section (~200 lines)

### "Don't know where to document something"

**Decision tree**:
- Architectural decision? → Chronicle entry + DECISIONS.md
- Implementation detail? → Chronicle entry only
- Task status update? → IMPLEMENTATION.md only
- Bug fix? → Chronicle entry + brief mention in IMPLEMENTATION.md

---

## Version History

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-14 | Created DOCUMENTATION-GUIDE.md | Document the structure we built |
| 2025-12-14 | Created DECISIONS.md | Separate decision registry from CHRONICLES.md |
| 2025-12-14 | Trimmed IMPLEMENTATION.md | Completed phases to summaries (57% reduction) |
| 2025-11-18 | Split CHRONICLES into chapters | Original CHRONICLES.md became too long |

---

**Maintained by**: Contributors and LLMs working on Temoa
**Questions?**: See examples in docs/CHRONICLES.md or docs/DECISIONS.md
**Project**: Temoa - Vault-First Research Workflow
