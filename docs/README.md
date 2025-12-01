# Temoa Documentation

> **Navigation guide** for all documentation in this directory.

**Last Updated**: 2025-12-01

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
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Master progress tracker across all phases | Everyone |
| [CHRONICLES.md](CHRONICLES.md) | High-level decision log and design discussions | Developers, Future maintainers |
| [PHASE-3-READY.md](PHASE-3-READY.md) | Phase 3 overview and remaining work | Developers |

---

## Historical Records

Detailed session notes and completed implementation plans.

### Subdirectories

| Directory | Contents |
|-----------|----------|
| **[chronicles/](chronicles/)** | Detailed session-by-session notes organized by phase |
| **[phases/](phases/)** | Original waterfall-style phase planning documents |
| **[archive/](archive/)** | Completed implementation plans and historical research |
| **[assets/](assets/)** | Images, diagrams, and other resources |

### Chronicles Organization

Session notes with detailed implementation decisions:

- `phase-0-1-foundation.md` - Phase 0 (Discovery) and Phase 1 (MVP) sessions
- `phase-2-gleanings.md` - Phase 2 (Gleanings) sessions
- `phase-2.5-deployment.md` - Phase 2.5 (Mobile validation, UI refinement) sessions
- `phase-3-enhanced-features.md` - Phase 3 (Enhanced features) sessions

---

## Document Lifecycle

**Active Documents** (top-level `docs/`):
- User guides (DEPLOYMENT, GLEANINGS)
- Technical reference (ARCHITECTURE, SEARCH-MECHANISMS)
- Living planning docs (IMPLEMENTATION, CHRONICLES, PHASE-3-READY)

**Historical Documents** (`docs/archive/`):
- Completed implementation plans (moved after phase completion)
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

**Understand system architecture**: Read [ARCHITECTURE.md](ARCHITECTURE.md)

**See current progress**: Check [IMPLEMENTATION.md](IMPLEMENTATION.md)

**Understand a design decision**: Search [CHRONICLES.md](CHRONICLES.md) or dig into `chronicles/` for detailed session notes

**Extract gleanings from daily notes**: Read [GLEANINGS.md](GLEANINGS.md)

**See what's next**: Check [PHASE-3-READY.md](PHASE-3-READY.md) or [IMPLEMENTATION.md](IMPLEMENTATION.md)

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
