# Temoa Documentation

> **Navigation guide** for all documentation in this directory.

**Last Updated**: 2026-01-04

---

## User Guides

Documentation for deploying and using Temoa.

| Document | Purpose | Audience |
|----------|---------|----------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | How to deploy and run Temoa server | Users, DevOps |
| [GLEANINGS.md](GLEANINGS.md) | How to use the gleanings extraction system | Users |

---

## Technical Reference

Deep dives into how Temoa works internally.

| Document | Purpose | Audience |
|----------|---------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, embeddings explanation, data flow | Developers, Contributors |
| [SEARCH-MECHANISMS.md](SEARCH-MECHANISMS.md) | Complete guide to search algorithms (semantic, BM25, hybrid, re-ranking, etc.) | Developers, Researchers |

---

## Planning & Progress

Living documents tracking implementation progress and decisions.

| Document | Purpose | Audience |
|----------|---------|----------|
| [CONTEXT.md](CONTEXT.md) | Current project status and session context | Everyone |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Master progress tracker across all phases (current phase detailed) | Everyone |
| [DECISIONS.md](DECISIONS.md) | Architectural decision registry (DEC-001+) with governance process | Developers, Contributors, LLMs |
| [CHRONICLES.md](CHRONICLES.md) | Design discussions and historical context (links to decisions) | Developers, Future maintainers |

**Note**: Session workflows (pick-up/wrap-up) are now managed by the plinth plugin (`/session-wrapup` command).

---

## Historical Records

Detailed session notes and completed implementation plans.

### Subdirectories

| Directory | Contents |
|-----------|----------|
| **[chronicles/](chronicles/)** | Detailed session-by-session implementation notes organized by phase |
| **[archive/](archive/)** | Historical documents (original planning docs, completed plans, research notes) |
| **[assets/](assets/)** | Images, diagrams, and other resources |

### Chronicles Organization

Session notes with detailed implementation decisions:

- `phase-0-1-foundation.md` - Phase 0 (Discovery) and Phase 1 (MVP) sessions
- `phase-2-gleanings.md` - Phase 2 (Gleanings) sessions
- `phase-2.5-deployment.md` - Phase 2.5 (Mobile validation, UI refinement) sessions
- `phase-3-implementation.md` - Phase 3 (Enhanced features) sessions
- `phase-3.5-specialized-search.md` - Phase 3.5 (Search profiles, chunking, QoL) sessions
- `production-hardening.md` - Production fixes and enhancements

### Chronicle Reading Guide

**If you're new to Temoa**, start with:
1. Entry 1 (The Central Problem) in phase-0-1-foundation.md - understand the "why"
2. Entry 6 (Phase 1 Complete) in phase-0-1-foundation.md - see what we built
3. Entry 11 (Mid-Course Assessment) in phase-2.5-deployment.md - understand current status

**If you're debugging**, look for:
- Performance issues → Entry 4 (phase-0-1-foundation.md)
- Architecture questions → Entry 2 (phase-0-1-foundation.md)
- Path/config problems → Entry 3 (phase-0-1-foundation.md)
- Gleanings bugs → Entries 9, 10, 12 (phase-2-gleanings.md, phase-2.5-deployment.md)

**If you're continuing development**, check:
- CONTEXT.md for current session state and active tasks
- IMPLEMENTATION.md for Phase 3.5 status (profiles, chunking, QoL complete)
- Latest chronicle file (phase-3.5-specialized-search.md) for recent work

---

## Document Lifecycle

**Active Documents** (top-level `docs/`):
- User guides (DEPLOYMENT, GLEANINGS)
- Technical reference (ARCHITECTURE, SEARCH-MECHANISMS)
- Living planning docs (IMPLEMENTATION, CHRONICLES, PHASE-3-READY)

**Historical Documents** (`docs/archive/`):
- Completed implementation plans (moved after phase completion)
- QoL improvements (archived 2026-01-04 - all phases complete)
- Research notes (e.g., copilot-learnings.md)
- Superseded plans

**Session Notes** (`docs/chronicles/`):
- Detailed session-by-session implementation logs
- Never archived (permanent historical record)

---

## Quick Reference

### I want to...

**Deploy Temoa**: Start with [DEPLOYMENT.md](DEPLOYMENT.md)

**Understand how search works**: Read [SEARCH-MECHANISMS.md](SEARCH-MECHANISMS.md)

**Understand system architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md) (updated for Phase 3.5)

**See current project status**: Check [CONTEXT.md](CONTEXT.md) for active tasks and session state

**See current progress**: Check [IMPLEMENTATION.md](IMPLEMENTATION.md) for Phase 3.5 status

**Look up a design decision**: Search [DECISIONS.md](DECISIONS.md) for quick reference, or read [CHRONICLES.md](CHRONICLES.md) for full context

**Understand why we made a choice**: Read the decision in [DECISIONS.md](DECISIONS.md), then follow the Entry link to [CHRONICLES.md](CHRONICLES.md) for discussion

**Extract gleanings from daily notes**: Read [GLEANINGS.md](GLEANINGS.md)

**Start a new session**: Use `/session-pickup` command (plinth plugin)

---

## Contributing to Documentation

When adding new documentation:

1. **User guides** → Top-level `docs/` (e.g., `FEATURE-NAME.md`)
2. **Technical reference** → Top-level `docs/` (e.g., `SUBSYSTEM-INTERNALS.md`)
3. **Implementation plans** → Top-level `docs/` while active, move to `archive/` when complete
4. **Session notes** → Add to appropriate file in `chronicles/` (never archive)
5. **Assets** → `docs/assets/` directory

Update this README when adding significant new documentation.

---

**Maintained by**: pborenstein + Claude
**Project**: Temoa - Vault-First Research Workflow
