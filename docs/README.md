# Temoa Documentation

> Navigation guide for all documentation in this directory.

**Last Updated**: 2026-07-04

---

## User Guides

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deploy and run the server (launchd, Tailscale, config) |
| [ZEITGEIST-INTEGRATION.md](ZEITGEIST-INTEGRATION.md) | Design notes: zeitgeist snapshots as high-density search signal |

---

## Technical Reference

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, components, pipeline, security, performance |
| [SEARCH-MECHANISMS.md](SEARCH-MECHANISMS.md) | Search algorithms: semantic, BM25, hybrid, reranking, chunking, etc. |

---

## Planning & Progress

| Document | Purpose |
|----------|---------|
| [CONTEXT.md](CONTEXT.md) | Current session state and active tasks |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Phase progress tracker |
| [DECISIONS.md](DECISIONS.md) | Architectural decision registry (DEC-001+) |
| [chronicles/](chronicles/) | Session-by-session notes for the current (v2 pure search) era |

---

## Historical Records

| Directory | Contents |
|-----------|----------|
| [archive/chronicles-v1/](archive/chronicles-v1/) | v1-era chronicles (UI, gleanings, phases 0–3.5, hardening) |
| [archive/](archive/) | Completed plans, superseded docs, research notes |

---

## Quick Reference

**Deploy Temoa** → [DEPLOYMENT.md](DEPLOYMENT.md)

**Understand search algorithms** → [SEARCH-MECHANISMS.md](SEARCH-MECHANISMS.md)

**Understand the architecture** → [ARCHITECTURE.md](ARCHITECTURE.md)

**Current project status** → [CONTEXT.md](CONTEXT.md)

**Phase progress** → [IMPLEMENTATION.md](IMPLEMENTATION.md)

**Design decision lookup** → [DECISIONS.md](DECISIONS.md)

**Start a new session** → `/handoff:session-pickup`

---

**Maintained by**: pborenstein + Claude
**Project**: Temoa v2.0.0 — Local Semantic Search Server
