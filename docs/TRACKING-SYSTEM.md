# TRACKING-SYSTEM.md - Temoa's Hybrid Documentation Approach

> **Purpose**: Explains Temoa's project tracking system, its relationship to the token-efficient standard, and how to maintain documentation across sessions.

**Created**: 2026-02-07
**Last Updated**: 2026-02-07

---

## Overview

Temoa uses a **hybrid documentation system** that adapts the token-efficient standard to fit the project's needs. This document explains our choices and how to work with the system.

### Core Principle

**Token-efficient + pragmatic customizations** = System that works for active experimentation phase

We follow the token-efficient standard's structure but make intentional deviations where they improve usability for this project's specific context.

---

## Document Responsibilities

### CONTEXT.md - Hot State (30-50 lines)

**Purpose**: Current session state, updated every session
**Token-efficient role**: Entry point for session pickup
**Temoa customization**: None (follows standard)

**Contents**:
- Current focus and active tasks
- Blockers
- Recent work context (last 1-2 sessions)
- Next session guidance

**Update frequency**: Every session (via `/session-wrapup` or manual)

**Example**:
```yaml
---
phase: "Experimentation"
phase_name: "Option B - Single LIVE Slider"
updated: 2026-02-07
last_commit: 50b9cad
branch: main
---

## Current Focus
Implemented Option B: Single LIVE slider for instant client-side blending.

## Active Tasks
- [x] Implemented Option B architecture
- [ ] Test full workflow after server restart
```

---

### IMPLEMENTATION.md - Progress Tracking (300+ lines)

**Purpose**: Waterfall plan with phase completion tracking
**Token-efficient role**: Progress dashboard
**Temoa customization**: Extensive phase details, experimentation section

**Contents**:
- Phase overview table (status, duration, dependencies)
- Detailed phase breakdowns with deliverables
- Current phase status (Experimentation)
- Tunable parameters table
- Completed/pending tasks

**Update frequency**: When phases complete, major features ship, or experimentation parameters change

**When to update**:
- Phase completes → mark ✅, update status
- Major feature ships → add to appropriate phase section
- New experimental tool → add to Experimentation section
- Parameter tuning → update tunable parameters table

**Don't update for**: Bug fixes, minor tweaks, documentation updates (use CONTEXT.md instead)

---

### DECISIONS.md - Decision Registry (290+ lines, 97+ decisions)

**Purpose**: Architectural decision records (ADR)
**Token-efficient role**: Decision history
**Temoa customization**: **Hybrid table + heading format** (intentional deviation)

**Format**:
```markdown
## Decision Registry

| Decision | Entry | Summary |
|----------|-------|---------|
| DEC-097: Two-Phase Filtering | 73-74 | Query Filter + Results Filter |

## DEC-097: Two-Phase Filtering Architecture (2026-02-07)

**Status**: ✅ Accepted
[Full details with context, alternatives, consequences]
```

**Why hybrid format?**
- Table: Quick scanning (97 decisions in one view)
- Heading sections: Full context for complex decisions
- Grep-friendly: `grep "DEC-097" docs/DECISIONS.md` finds both
- Best of both worlds

**Update frequency**: When making significant architectural decisions

**When to add decision**:
- Affects system architecture or behavior
- Has alternatives that were explicitly rejected
- Future developers might question ("why did we do it this way?")
- Sets a pattern or precedent for future work

**How to add**:
1. Find next DEC-XXX number (check table)
2. Document in chronicle entry first
3. Add row to table (sorted by number)
4. Add full heading section for complex decisions
5. Commit both chronicle AND DECISIONS.md together

---

### chronicles/ - Detailed History (11 files, organized by phase + topic)

**Purpose**: Deep-dive entries with rationale and implementation details
**Token-efficient role**: Historical context
**Temoa customization**: **Phase + topical organization** (intentional deviation)

**Structure**:
```
chronicles/
├── phase-0-1-foundation.md          # Phase-based
├── phase-2-gleanings.md             # Phase-based
├── phase-3-implementation.md        # Phase-based
├── experimentation-harness.md       # Topical (ongoing)
├── production-hardening.md          # Topical
└── github-gleaning-fix-plan.md      # Topical
```

**Why hybrid organization?**
- Phase files: Historical phases that are complete
- Topical files: Active areas that span multiple sessions
- Prevents phase files from becoming unwieldy (experimentation-harness.md is 890+ lines)

**Topical file requirements**:
- MUST have phase metadata header
- MUST reference phase context in overview
- SHOULD link to phase-specific decisions

**Example topical file header**:
```markdown
---
phase: "Experimentation"
topic: "Search Harness and Query Filtering"
started: 2025-12-15
updated: 2026-02-07
---
```

**Update frequency**: When significant work happens (new features, decisions, architectural changes)

**Entry numbering**: Sequential across ALL chronicles (Entry 76 in experimentation-harness.md follows Entry 40 in entry-40-chunking.md)

---

### CLAUDE.md - Development Guide (700+ lines)

**Purpose**: Onboarding guide for new AI sessions
**Token-efficient role**: Supplement to CONTEXT.md
**Temoa customization**: **Comprehensive guide** (intentional expansion)

**Why comprehensive instead of slim?**
- Different purpose: Persistent knowledge vs. hot state
- Project principles (uv shop, mobile-first, no hardcoded paths)
- Implementation patterns (direct imports, lifespan pattern, LRU caching)
- Quick reference commands
- Session checklist

**Anti-duplication strategy**:
- Don't repeat IMPLEMENTATION.md's detailed progress
- Don't repeat CONTEXT.md's current session state
- Use cross-references: "See CONTEXT.md for recent work"
- Focus on: principles, patterns, commands, resources

**Update frequency**: When structure/principles change, not for every feature

**When to update**:
- New project principle added
- New implementation pattern established
- Commands change
- Resources added
- Major phase shift

**Don't update for**: Feature completion, bug fixes, parameter tuning (use IMPLEMENTATION.md/CONTEXT.md)

---

## Session Workflows

### Session Pickup (5 minutes)

1. **Read CONTEXT.md** (1 min) - Current focus, blockers, active tasks
2. **Skim IMPLEMENTATION.md** (2 min) - Verify current phase status
3. **Check recent decisions** (2 min) - Last 3-5 in DECISIONS.md
4. **Optional**: Read relevant chronicle entries if unfamiliar with recent work

**Tools**: Use `/session-pickup` skill if available (automates this workflow)

---

### Session Wrapup (10 minutes)

1. **Update CONTEXT.md** - Current focus, next session guidance, latest commit hash
2. **Update IMPLEMENTATION.md** (if major progress) - Mark completed tasks, update phase status
3. **Add decisions** (if architectural choices made) - Chronicle entry first, then DECISIONS.md
4. **Add chronicle entry** (if significant feature/decision) - Document what/why/how
5. **Commit changes** - Include tracking docs in commit

**Tools**: Use `/session-wrapup` skill if available (automates steps 1-2)

---

## Deviations from Token-Efficient Standard

| Aspect | Token-Efficient Standard | Temoa Customization | Rationale |
|--------|--------------------------|---------------------|-----------|
| DECISIONS.md format | Heading-only | Hybrid table + heading | Quick scanning (97 decisions) + detail for complex choices |
| Chronicle organization | Phase-only | Phase + topical | Experimentation phase ongoing, topical files prevent bloat |
| CLAUDE.md size | Slim supplement | Comprehensive guide | Different purpose (persistent knowledge vs. hot state) |
| Archive directory | Not specified | Keep with README | Preserves historical context, low cost |

All deviations are **intentional** and serve specific needs of an active experimentation phase.

---

## Update Triggers

### Update CONTEXT.md when:
- ✅ Starting a session (update focus/tasks)
- ✅ Ending a session (update context, next steps)
- ✅ Hitting a blocker
- ✅ Completing active tasks

### Update IMPLEMENTATION.md when:
- ✅ Phase completes
- ✅ Major feature ships
- ✅ Experimental tool added
- ✅ Parameter tuning completed
- ❌ NOT for: Bug fixes, minor tweaks

### Update DECISIONS.md when:
- ✅ Making architectural choice
- ✅ Rejecting an alternative approach
- ✅ Setting a pattern/precedent
- ❌ NOT for: Implementation details, obvious choices

### Update chronicles/ when:
- ✅ Significant feature work
- ✅ Architectural decision with context
- ✅ Performance optimization with measurement
- ✅ User feedback that changes direction
- ❌ NOT for: Bug fixes, typos, minor tweaks

### Update CLAUDE.md when:
- ✅ New project principle
- ✅ New implementation pattern
- ✅ Commands/tools change
- ✅ Major phase shift
- ❌ NOT for: Feature completion, parameter tuning

---

## Cross-References

Documents reference each other to avoid duplication:

```
CONTEXT.md
  ↓ "See IMPLEMENTATION.md for phase details"
IMPLEMENTATION.md
  ↓ "See DECISIONS.md for architectural choices"
DECISIONS.md
  ↓ "See Chronicle Entry XX"
chronicles/
  ↓ "See DEC-XXX"
```

**Golden rule**: Write details once, reference elsewhere

---

## Tools

**Plinth Skills** (if available):
- `/session-pickup` - Reads CONTEXT.md, displays current state
- `/session-wrapup` - Updates CONTEXT.md, commits changes
- `/project-tracking` - Establishes tracking files for new projects

**Manual workflow**: Follow session workflows above if skills unavailable

---

## FAQ

**Q: Why not strict token-efficient compliance?**
A: Token-efficient is a framework, not a religion. Temoa's experimentation phase benefits from hybrid approach (table scanning, topical chronicles, comprehensive guide).

**Q: When should we switch to pure token-efficient?**
A: If documentation becomes unwieldy (>2000 lines per file) or session pickup takes >10 minutes. Currently working well.

**Q: How do I know which file to update?**
A: Use the "Update Triggers" section above. When in doubt: CONTEXT.md for session state, chronicles for details.

**Q: What if I forget to update tracking docs?**
A: Not catastrophic. Next session will be harder (need to read commits), but system is resilient. Just update when you notice.

**Q: Can I change the system?**
A: Yes! Document your changes in this file. Tracking systems should evolve with project needs.

---

## Related Documents

- [Token-Efficient Standard](https://github.com/your-org/token-efficient-docs) - Inspiration for this system
- [CONTEXT.md](CONTEXT.md) - Current session state
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Progress tracking
- [DECISIONS.md](DECISIONS.md) - Decision registry
- [CLAUDE.md](../CLAUDE.md) - Development guide

---

**Maintained by**: Project contributors
**Review frequency**: Every major phase shift or when session pickup becomes slow
