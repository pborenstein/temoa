# Phase 4: Vault-First LLM

**Goal**: LLMs check vault before internet

**Duration**: 7-10 days
**Status**: Future
**Dependencies**: Phase 3 complete, Apantli integration

## Tasks

### 4.1: Chat Endpoint with Context

**Actions**:
1. Add `POST /chat` endpoint
2. Search vault before calling LLM
3. Format results as XML context (Copilot pattern)
4. Call LLM via Apantli with vault context

**Acceptance Criteria**:
- [ ] Chat endpoint works
- [ ] Vault context included in prompts
- [ ] LLM responses reference vault

---

### 4.2: Citation System

**Actions**:
1. Implement citation extraction
2. Add source attribution to responses
3. Link citations back to vault notes

**Acceptance Criteria**:
- [ ] LLM cites vault sources
- [ ] Citations are clickable
- [ ] Attribution is accurate

---

## Phase 4 Deliverables

- [ ] `/chat` endpoint
- [ ] Apantli integration
- [ ] Citation system
- [ ] Vault-first chat UI

## Phase 4 Success Criteria

- [ ] Vault-first becomes default research mode
- [ ] LLM responses build on existing knowledge
- [ ] Citations work reliably
