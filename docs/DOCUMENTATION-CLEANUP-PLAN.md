# Documentation Cleanup Plan

**Created**: 2026-01-02
**Purpose**: Inventory outdated docs and plan cleanup after Phase 3.5 + QoL completion
**Status**: Ready for review

---

## Executive Summary

Recent work (Phase 3.5.1, 3.5.2, QoL Phases 1-5) added significant new features but some core docs haven't been updated since December. This plan identifies what needs updating, what can be archived, and proposes a cleanup strategy.

---

## Current Documentation Inventory

### Core Technical Docs

| Document | Last Updated | Status | Notes |
|----------|-------------|--------|-------|
| **ARCHITECTURE.md** | 2025-12-18 | ⚠️ OUTDATED | Missing: 8 new endpoints, search profiles, chunking, multi-vault details |
| **SEARCH-MECHANISMS.md** | 2025-12-31 | ✅ CURRENT | Has profiles and chunking sections, up to date |
| **DECISIONS.md** | 2025-12-30 | ✅ CURRENT | Has DEC-085 (chunking), up to date |
| **GLEANINGS.md** | 2025-12-30 | ✅ CURRENT | Recently updated |
| **DEPLOYMENT.md** | 2025-12-13 | ⚠️ NEEDS REVIEW | Pre-dates Phase 3.5, may need updates |
| **README.md** (docs/) | 2025-12-14 | ✅ MOSTLY CURRENT | Navigation guide, adequate |

### Planning & Progress Docs

| Document | Last Updated | Status | Notes |
|----------|-------------|--------|-------|
| **CONTEXT.md** | 2026-01-02 | ✅ CURRENT | Just updated in session wrap-up |
| **IMPLEMENTATION.md** | 2026-01-02 | ✅ CURRENT | Just updated in session wrap-up |
| **DOCUMENTATION-GUIDE.md** | 2025-12-14 | ✅ CURRENT | Guides session workflows, adequate |

### Chronicles (Session Notes)

| File | Last Updated | Status | Notes |
|------|-------------|--------|-------|
| phase-0-1-foundation.md | Historical | ✅ ARCHIVED | Complete, no changes needed |
| phase-2-gleanings.md | Historical | ✅ ARCHIVED | Complete, no changes needed |
| phase-2.5-deployment.md | Historical | ✅ ARCHIVED | Complete, no changes needed |
| phase-3-implementation.md | Historical | ✅ ARCHIVED | Complete, no changes needed |
| **phase-3.5-specialized-search.md** | 2026-01-02 | ✅ CURRENT | Has Entry 8 (QoL merge), active |
| production-hardening.md | 2025-12-19 | ✅ CURRENT | Historical fixes, adequate |

### Subdirectories

| Directory | Contents | Status | Notes |
|-----------|----------|--------|-------|
| **QoL-improvements/** | QoL planning docs (PLAN.md) + 3 screenshots | ⚠️ ARCHIVE CANDIDATE | Work complete, can move to archive/ |
| **phases/** | phase-3.5-specialized-search.md | ✅ CURRENT | Active planning doc |
| **chronicles/** | Session notes by phase | ✅ CURRENT | Historical + active (phase-3.5) |
| **archive/** | Completed plans, old planning | ✅ CURRENT | Already archived material |

---

## What's Missing from ARCHITECTURE.md

**API Endpoints Added Since Dec 18** (not documented):

1. `GET /config` - Returns vault configuration (chunking settings, model)
2. `GET /profiles` - Lists available search profiles
3. `GET /vaults` - Lists configured vaults
4. `POST /gleanings/{gleaning_id}/status` - Update gleaning status
5. `GET /gleanings` - List gleanings with filters
6. `GET /gleanings/{gleaning_id}` - Get single gleaning
7. `GET /gleaning/stats` - Gleaning counts by status
8. `GET /models` - List available embedding models
9. `GET /stats/advanced` - Extended vault statistics

**Features Added Since Dec 18** (not documented):

1. **Search Profiles** (Phase 3.5.1):
   - 5 built-in profiles (repos, recent, deep, keywords, default)
   - Custom profile loading from config
   - Profile-based search parameter configuration

2. **Adaptive Chunking** (Phase 3.5.2):
   - Large file splitting (>4000 chars)
   - Chunk deduplication (best-scoring per file)
   - Configurable chunk size/overlap/threshold
   - Per-vault model selection

3. **QoL Improvements** (Web UI enhancements):
   - Content-first search results layout
   - Profile selector dropdown in UI
   - Enhanced management page (gleaning stats, advanced stats, model selector)
   - Mobile-optimized UX (collapsible results, keyboard shortcuts)

4. **Multi-Vault Enhancements**:
   - LRU cache (max 3 vaults)
   - Per-vault chunking configuration
   - Per-vault model selection
   - Vault validation on index operations

---

## Proposed Actions

### 1. Update ARCHITECTURE.md ⚠️ HIGH PRIORITY

**What to add**:

- **Section: API Endpoints** - Comprehensive list of all 22 endpoints with descriptions
  - Core search/stats endpoints
  - Vault management endpoints
  - Gleaning management endpoints
  - PWA/UI endpoints
  - Profile/model endpoints

- **Section: Search Profiles** - Brief explanation linking to SEARCH-MECHANISMS.md
  - What profiles are
  - 5 built-in profiles overview
  - How they configure search parameters

- **Section: Adaptive Chunking** - Brief explanation linking to SEARCH-MECHANISMS.md
  - Why chunking is needed (512 token limit)
  - How chunking works (sliding window)
  - Impact on search coverage

- **Update: Multi-Vault Architecture** - Expand existing section
  - LRU cache details (max 3 vaults)
  - Per-vault configuration (model, chunking)
  - Vault validation

- **Update: Request Flow** - Add chunking and profile steps
  - Query → Profile application → Retrieval → Deduplication → Ranking

**Estimated effort**: 30-45 minutes

---

### 2. Review DEPLOYMENT.md ⚠️ MEDIUM PRIORITY

**Check for**:

- Does it mention all new endpoints?
- Does it explain how to configure profiles?
- Does it explain chunking configuration?
- Is the launchd setup still accurate?

**Estimated effort**: 10-15 minutes

---

### 3. Archive QoL Planning Materials ✅ CLEANUP

**Move to archive/**:

```
docs/QoL-improvements/ → docs/archive/QoL-improvements/
```

**Rationale**:
- QoL work is complete (all 5 phases)
- Squash merged to phase-3.5-search-modes
- Planning doc (PLAN.md) is historical now
- Screenshots are useful for reference but not active

**Create archive README**:
- Add entry to `docs/archive/README.md` explaining what QoL was

**Estimated effort**: 5 minutes

---

### 4. Update docs/README.md ✅ LOW PRIORITY

**What to add**:

- Mention QoL improvements are archived
- Update "If you're continuing development" section to mention Phase 3.5

**Estimated effort**: 5 minutes

---

### 5. Consider Archiving Old Plans 🤔 OPTIONAL

**Candidates in archive/** (already archived, but review):

- `GLEANING-NORMALIZATION-PLAN.md` - Complete, can stay
- `INCREMENTAL-INDEXING-PLAN.md` - Complete, can stay
- `INCREMENTAL-INDEXING-STATUS.md` - Complete, can stay
- `PHASE-3-PART-2-SEARCH-QUALITY.md` - Complete, can stay
- `SEARCH-QUALITY-REVIEW.md` - Complete, can stay
- `UI-CLEANUP-PLAN.md` - Complete, can stay

**Assessment**: Archive is well-organized. No action needed.

---

## Proposed Order of Work

### Session 1: Critical Updates (45-60 minutes)

1. ✅ **Update ARCHITECTURE.md**
   - Add new API endpoints section
   - Add search profiles section
   - Add adaptive chunking section
   - Update multi-vault architecture
   - Update request flow diagram

2. ✅ **Review DEPLOYMENT.md**
   - Check accuracy
   - Add any missing configuration notes

3. ✅ **Archive QoL materials**
   - Move `docs/QoL-improvements/` → `docs/archive/QoL-improvements/`
   - Update `docs/archive/README.md`

4. ✅ **Update docs/README.md**
   - Note QoL archived
   - Update navigation

5. ✅ **Commit all changes**
   - `docs: update ARCHITECTURE.md for Phase 3.5 and QoL features`

---

## Files to Modify Summary

### High Priority (Must Update)

1. **docs/ARCHITECTURE.md** (~200 lines added)
   - New sections: API Endpoints, Search Profiles, Adaptive Chunking
   - Updated sections: Multi-Vault Architecture, Request Flow

### Medium Priority (Should Review)

2. **docs/DEPLOYMENT.md** (~20-50 lines changed?)
   - Configuration sections
   - New endpoint documentation

### Low Priority (Nice to Have)

3. **docs/README.md** (~10 lines changed)
   - Archive notes
   - Navigation updates

4. **docs/archive/README.md** (~10 lines added)
   - QoL archive entry

### Moves

5. **docs/QoL-improvements/ → docs/archive/QoL-improvements/**
   - PLAN.md
   - 3 screenshot PNGs

---

## Success Criteria

After cleanup:

- ✅ ARCHITECTURE.md accurately describes current system (all 22 endpoints, profiles, chunking)
- ✅ DEPLOYMENT.md configuration is accurate for current features
- ✅ QoL planning materials archived (work is complete)
- ✅ docs/README.md navigation is current
- ✅ All changes committed with clear message
- ✅ No outdated information in active docs

---

## Notes

**What NOT to change**:

- SEARCH-MECHANISMS.md - Already current (updated Dec 31)
- DECISIONS.md - Already current (has DEC-085 for chunking)
- GLEANINGS.md - Already current (updated Dec 30)
- Chronicles files - Historical records, don't modify except to add new entries
- CONTEXT.md - Just updated in session wrap-up
- IMPLEMENTATION.md - Just updated in session wrap-up

**Philosophy**:

- Keep active docs accurate and current
- Archive completed planning materials
- Don't delete historical chronicles (they're the project memory)
- Link between docs rather than duplicating content

---

## Review Questions for User

1. **ARCHITECTURE.md scope**: Should this be comprehensive (all 22 endpoints) or high-level overview with links to API docs?

2. **QoL archive timing**: OK to archive now, or wait until Phase 3.5 is fully complete and merged to main?

3. **DEPLOYMENT.md**: How detailed should configuration examples be? Include all profile/chunking options?

4. **Priority**: Which docs are most important to update first? (Suggested: ARCHITECTURE.md → DEPLOYMENT.md → cleanup)

5. **Anything else**: Any other docs that feel outdated or need attention?
