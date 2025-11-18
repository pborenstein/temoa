---
created: 2025-11-18
tags: [project, semantic-search, obsidian]
status: planning
---

# Temoa

Local semantic search server for Obsidian vault. Makes saved links and notes searchable from mobile.

## Problem

I save hundreds of links and notes but never resurface them when I need them. Native Obsidian search is keyword-only, doesn't work semantically.

## Solution

FastAPI server wrapping [[Synthesis]] semantic search engine. Access from phone via [[Tailscale]], results open in Obsidian mobile.

## Key Principles

1. **Mobile-first**: If it doesn't work on phone, it doesn't work
2. **Sub-2-second response time**: Speed is essential for habit formation
3. **Local processing**: No external APIs for embeddings
4. **Privacy**: Everything on local network via Tailscale

## Architecture

- Server: FastAPI (async Python)
- Search: Synthesis subprocess (sentence-transformers)
- Embeddings: all-MiniLM-L6-v2 (384d, fast)
- Network: Tailscale VPN
- Storage: Index in `.temoa/` within vault

See [[docs/CHRONICLES.md]] for architectural decisions.

## Phases

- Phase 0: Discovery & validation (current)
- Phase 1: Minimal viable search
- Phase 2: Gleanings integration
- Phase 3: Enhanced features
- Phase 4: Vault-first LLM

## Related

- [[Synthesis]] - The underlying search engine
- [[Mobile-First Design]]
- [[Personal Knowledge Management]]
