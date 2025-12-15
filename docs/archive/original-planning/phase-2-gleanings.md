# Phase 2: Gleanings Integration

**Goal**: Make gleanings searchable via semantic search

**Duration**: 3-4 days
**Status**: Not Started
**Dependencies**: Phase 1 complete

## Tasks

### 2.1: Gleanings Extraction Script

**Owner**: Developer
**Estimated Time**: 3 hours

**Actions**:
1. Create `scripts/extract_gleanings.py` (production version of Phase 0 prototype)
2. Add features:
   - Incremental extraction (track last run)
   - Tag inference from URL/title
   - Duplicate detection
   - Progress reporting

**Acceptance Criteria**:
- [ ] Extracts gleanings from daily notes
- [ ] Creates individual notes in `L/Gleanings/`
- [ ] Handles duplicates gracefully
- [ ] Tracks extraction state

---

### 2.2: Historical Gleanings Migration

**Owner**: Developer
**Estimated Time**: 2 hours

**Actions**:
1. Create `scripts/migrate_old_gleanings.py`
2. Read from `old-ideas/old-gleanings/gleanings_state.json`
3. Convert 505 historical gleanings to new format
4. Preserve metadata (dates, URLs, descriptions)

**Acceptance Criteria**:
- [ ] All 505 gleanings migrated
- [ ] Metadata preserved
- [ ] No duplicates created

---

### 2.3: Synthesis Re-indexing

**Owner**: Developer
**Estimated Time**: 1 hour

**Actions**:
1. Document re-indexing workflow in `docs/GLEANINGS.md`
2. Test Synthesis finds new gleanings
3. Verify search quality

**Acceptance Criteria**:
- [ ] Gleanings are indexed by Synthesis
- [ ] Search returns gleanings appropriately
- [ ] Performance is acceptable

---

### 2.4: Automated Extraction

**Owner**: Developer
**Estimated Time**: 2 hours

**Actions**:
1. Create systemd timer or cron job for regular extraction
2. Add `/reindex` endpoint to trigger Synthesis re-indexing
3. Document automation setup

**Acceptance Criteria**:
- [ ] Gleanings extracted automatically (daily)
- [ ] Can trigger re-indexing via API
- [ ] Errors are logged

---

## Phase 2 Deliverables

- [ ] `scripts/extract_gleanings.py` - Gleaning extraction
- [ ] `scripts/migrate_old_gleanings.py` - Historical migration
- [ ] `L/Gleanings/` - All gleanings as individual notes
- [ ] Automation setup (cron/systemd)
- [ ] Documentation in `docs/GLEANINGS.md`

## Phase 2 Success Criteria

- [ ] All 505+ gleanings are searchable
- [ ] New gleanings extracted regularly
- [ ] Search finds gleanings with good relevance
- [ ] Extraction is automated
