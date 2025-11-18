# Phase 0 Results - Discovery & Validation

**Date**: 2025-11-18
**Status**: In Progress

---

## Task 0.1: Synthesis Performance Testing

### Test Configuration

- **Vault**: test-vault (../../test-vault)
- **Files indexed**: 13
- **Model**: all-MiniLM-L6-v2 (384-dimensional)
- **Platform**: Mac (macOS)
- **Synthesis location**: old-ideas/synthesis/

### Performance Results

#### Search Performance

| Test Type | Time | Notes |
|-----------|------|-------|
| Cold Start | 3.184s | First search after startup |
| Warm #1 | 2.999s | "AI agents" |
| Warm #2 | 3.173s | "productivity systems" |
| Warm #3 | 3.805s | "obsidian plugins" |
| **Average Warm** | **3.326s** | Target was < 1s (ideal < 500ms) |
| Min Warm | 2.999s | |
| Max Warm | 3.805s | |
| Different Model | 2.765s | all-mpnet-base-v2 (not processed, so just overhead) |

#### Archaeology Performance

- **Time**: 3.131s
- **Status**: ✓ Working
- **Output**: Valid JSON with temporal analysis

### Key Findings

#### ✓ What Works

1. **Daily notes ARE indexed**
   - `Daily/2025/2025-11-15-Fr.md` appears in results
   - `Daily/2025/2025-11-18-Mo.md` appears in results
   - **Conclusion**: Gleanings in daily notes will be searchable

2. **Model download successful**
   - all-MiniLM-L6-v2 downloaded and working
   - Shows ✓ status in models list
   - 13 files processed into embeddings

3. **Search functionality works**
   - Returns relevant results (10 matches per query)
   - JSON parsing successful
   - Similarity scores reasonable (0.2-0.6 range)
   - obsidian:// URIs generated correctly
   - Gleanings found: `L/Gleanings/2025-11-15-sentence-transformers-models.md`

4. **Archaeology feature works**
   - Returns temporal analysis JSON
   - Tracks interest evolution over time
   - Monthly intensity tracking functional

#### ✗ Critical Issues

1. **Performance is UNACCEPTABLE for mobile use**
   - **Average search: 3.3 seconds**
   - **Target: < 1 second** (ideal < 500ms)
   - **This is 6x slower than target**
   - On a TINY vault (13 files) - real vault might be worse

2. **Testing against wrong vault**
   - Current: test-vault (13 files)
   - Real vault: ~1,899 files (from CLAUDE.md)
   - Need to test against real vault for accurate performance

### Questions Answered

| Question | Answer |
|----------|--------|
| Are daily notes indexed? | ✓ YES - Multiple daily notes appear in results |
| Is search < 1s for warm queries? | ✗ NO - Average 3.3s (6x slower than target) |
| Did model download work? | ✓ YES - all-MiniLM-L6-v2 downloaded successfully |
| File count vs actual vault? | ⚠️ Testing test-vault (13 files), not real vault (1,899 files) |

### Performance Analysis

#### Why So Slow?

Possible causes (need investigation):

1. **Subprocess overhead**: ~50-100ms expected, but seeing 3s total
2. **Python/uv startup time**: Cold Python environment each call?
3. **Model loading**: Loading sentence-transformer on each search?
4. **Synthesis implementation**: Inefficient search algorithm?
5. **File I/O**: Reading embeddings from disk each time?

#### Implications for Ixpantilia

**If performance stays at 3s:**
- ❌ Mobile use case FAILS - too slow for mobile habit formation
- ❌ Won't replace Obsidian search (which is instant)
- ❌ User will abandon after first few tries

**Mitigation strategies to explore:**

1. **Keep Synthesis running as daemon** instead of subprocess
   - Amortize Python startup cost
   - Keep model in memory
   - Trade: deployment complexity

2. **Cache results server-side**
   - LRU cache with 15min TTL
   - Help with repeated queries
   - Trade: stale results, memory usage

3. **Use faster model**
   - all-MiniLM-L6-v2 is supposedly "fast"
   - Try even smaller model?
   - Trade: quality vs speed

4. **Optimize Synthesis**
   - Profile to find bottleneck
   - May need code changes
   - Trade: modifying production tool

5. **Grep-first hybrid** (like Copilot)
   - Fast grep to filter candidates
   - Semantic search on subset
   - Trade: implementation complexity

### Next Steps

#### Immediate Actions Needed

1. **Test against REAL vault** (1,899 files)
   - Point Synthesis at actual vault location
   - Re-run performance tests
   - See if performance degrades with more files

2. **Profile Synthesis to find bottleneck**
   - Where is the 3 seconds going?
   - Model loading? Search? File I/O?
   - Use Python profiler or manual timing

3. **Test Synthesis natively** (without subprocess)
   - Run `uv run main.py search` directly in Synthesis directory
   - Compare to subprocess call time
   - Isolate subprocess overhead

4. **Decision point**: Is Synthesis viable for mobile?
   - If real vault is also 3s → need mitigation strategy
   - If significantly slower → may need different approach
   - If faster model helps → test all models

### Test Vault Details

From stats output:

```
Embedding Statistics (model: all-MiniLM-L6-v2):
  Total files: 13
  Model: all-MiniLM-L6-v2
  Embedding dimension: 384
  Average content length: 824 chars
  Total unique tags: 25
  Directories: 5
  Created: 2025-11-18T00:12:14.778666
```

**Directories indexed (5)**:
- Daily/2025/
- Areas/
- L/Gleanings/
- Books/
- Projects/

### Sample Results

Best result for "semantic search":
- **Title**: 2025-11-15-Fr (daily note)
- **Score**: 0.608
- **Path**: Daily/2025/2025-11-15-Fr.md
- **URI**: obsidian://vault/test-vault/2025-11-15-Fr

This shows daily notes with gleanings ARE surfaced in search results.

---

## Task 0.2: Subprocess Integration (Pending)

Status: Not started - waiting on performance investigation

---

## Task 0.3: Mobile UX Mockup (Pending)

Status: Not started

---

## Task 0.4: Extract Sample Gleanings (Pending)

Status: Not started

---

## Task 0.5: Architecture Decisions (Pending)

Status: Not started - need performance data first

### Open Questions

1. **Is Synthesis fast enough for mobile use?**
   - Current answer: NO (3s vs < 1s target)
   - Need: Test real vault, profile bottleneck, explore mitigations

2. **Should we modify Synthesis or wrap it differently?**
   - Current: subprocess per query
   - Alternatives: daemon mode, cache, faster model

3. **Can we achieve < 1s response time?**
   - Unknown - depends on bottleneck investigation

4. **Is mobile-first design still viable?**
   - At 3s, probably not
   - Need to get to < 1s minimum, ideally < 500ms

---

## Conclusions So Far

### ✓ Good News

- Synthesis works correctly
- Daily notes are indexed (gleanings will be found)
- Search returns relevant results
- Model download successful
- Archaeology feature functional

### ✗ Blockers

- **Performance is 6x slower than target**
- Testing wrong vault (need real vault data)
- Don't know where time is being spent

### 🔬 Next Investigation

**CRITICAL**: Understand why search takes 3+ seconds

1. Test real vault (1,899 files)
2. Profile Synthesis execution
3. Test native vs subprocess timing
4. Determine if mobile use case is viable

**Phase 0.1 is NOT complete** until we understand performance bottleneck and determine path forward.

---

**Last Updated**: 2025-11-18
**Next Update**: After real vault testing and profiling
