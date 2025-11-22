# Decision: Custom Embeddings System

**Date**: 2025-08-28  
**Decision**: Build a custom embedding system rather than leverage Obsidian Copilot's infrastructure  
**Status**: Approved  

## Context

The Synthesis Project needs semantic embeddings to enable cross-vault connection discovery, similarity search, and concept clustering. We investigated whether to:

**Option A**: Build our own embedding system  
**Option B**: Leverage Obsidian Copilot's existing embedding infrastructure

## Investigation Findings

### Copilot's Embedding System
- **Two systems found**: Legacy v2 (Orama-based, deprecated) and current v3 (MemoryIndexManager with JSONL snapshots)
- **Multiple providers supported**: OpenAI, Ollama, Cohere, Google, Azure, etc.
- **Full infrastructure**: EmbeddingManager, VectorStoreManager, indexing, garbage collection
- **Purpose-built for**: Search and retrieval in chat context

### Technical Challenges with Option B
1. **Architecture coupling**: Copilot's system is optimized for search/retrieval, not synthesis
2. **Changing internals**: v2 deprecated, v3 current but could evolve
3. **Investigation difficulties**: Hit repeated tool errors trying to read their v3 implementation
4. **Different use case**: Their system serves chat queries, ours needs graph analysis, temporal patterns, creative connections

## Decision Rationale

### Why Option A (Custom System)
1. **Purpose-built**: Optimized specifically for synthesis tasks, not general search
2. **Clean architecture**: No coupling to Copilot's changing internals  
3. **Flexibility**: Can optimize for our specific data types and use cases
4. **Control**: Full control over storage format, indexing strategy, and retrieval methods
5. **Simplicity**: Focused implementation without Copilot's complexity

### Trade-offs Accepted
- **Development time**: Building from scratch vs. reusing existing
- **Maintenance**: We own the full stack
- **Feature parity**: Won't have all of Copilot's provider options initially

## Implementation Plan

### Phase 1: Minimal Viable Embeddings
- **Model**: Local sentence-transformers model (privacy-first)
- **Storage**: Simple JSON/numpy arrays or lightweight vector DB
- **Scope**: Embed all vault content (daily notes, references, L/ files)

### Phase 2: Enhanced Features
- **Multiple models**: Support different embedding models
- **Vector DB**: Upgrade to FAISS, Chroma, or similar
- **Chunking strategies**: Optimize for different content types

### Phase 3: Synthesis Integration
- **Graph relationships**: Embed connections between notes
- **Temporal embeddings**: Time-aware similarity
- **Creative clustering**: Non-obvious connection discovery

## Success Criteria
- [ ] Embed all vault content (900+ files)
- [ ] Sub-second similarity search
- [ ] Enable synthesis tool development
- [ ] Maintain privacy (all local processing)

## Alternatives Considered
1. **Hybrid approach**: Use Copilot for some features, custom for others (rejected: complexity)
2. **Cloud embeddings**: Use OpenAI/similar APIs (rejected: privacy concerns)
3. **No embeddings**: Pure lexical/graph analysis (rejected: limits synthesis potential)

## Notes
- Investigation hit technical difficulties reading Copilot's v3 system
- "Product Manager vibes achieved" - user approved Option A approach
- Focus on building foundation before synthesis tools
- Can revisit integration with Copilot in future if beneficial

---
*This decision enables Phase 1 foundation work to proceed with clear technical direction.*