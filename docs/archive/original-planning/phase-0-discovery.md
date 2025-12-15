# Phase 0: Discovery & Validation

**Goal**: Answer all open questions and validate architectural assumptions before writing code

**Duration**: 1 day (completed 2025-11-18)
**Status**: ✅ COMPLETE
**Priority**: CRITICAL - Blocks all other phases

## Summary of Findings

**Performance Investigation Results**:
- ✅ Bottleneck identified: Model loading (2.8s per invocation)
- ✅ Actual search is fast: ~400ms once model loaded
- ✅ Scales well: 2,289 files = same speed as 13 files
- ✅ Daily notes ARE indexed (gleanings searchable)
- ✅ Solution validated: HTTP server wrapper with direct imports

**Key Decisions**:
1. **Architecture**: FastAPI server importing Synthesis code directly (not subprocess)
2. **Expected performance**: ~400-500ms per search (meets < 1s target)
3. **No caching needed initially**: Search is fast enough without it
4. **Mobile use case validated**: 400ms excellent for habit formation

**Detailed findings**: See `docs/phase0-results.md` and `docs/CHRONICLES.md` Entry 4

## Tasks

### 0.1: Test Synthesis Performance

**Owner**: Developer
**Estimated Time**: 2 hours

**Actions**:
1. Navigate to Synthesis directory: `cd old-ideas/synthesis/` (or actual `.tools/synthesis/` location)
2. Run performance tests:
   ```bash
   # Measure cold start time
   time uv run main.py search "semantic search" --json

   # Measure warm start (run again)
   time uv run main.py search "AI agents" --json

   # Test different models
   time uv run main.py search "productivity" --model all-mpnet-base-v2 --json

   # Check vault coverage
   uv run main.py stats
   ```
3. Document results in `docs/phase0-results.md`:
   - Cold start latency
   - Warm start latency
   - Number of files indexed
   - Which directories are indexed (especially Daily/)
   - Default model performance

**Acceptance Criteria**:
- [x] Search latency < 1 second for typical queries (✅ 400ms after model loaded)
- [x] Know exact file count indexed (✅ 2,289 files)
- [x] Confirmed whether daily notes are indexed (✅ YES)
- [x] Performance baseline established (✅ See phase0-results.md)

**Questions Answered**:
- Is search fast enough for mobile use? ✅ YES (~400ms meets target)
- Are daily notes currently indexed by Synthesis? ✅ YES
- What's the memory footprint of Synthesis? ~500MB with model loaded

---

### 0.2: Prototype Subprocess Integration

**Status**: ~~SKIPPED~~ (Using direct import instead - see DEC-009)

**Owner**: Developer
**Estimated Time**: 1 hour (not needed)

**Actions**:
1. Create `prototypes/test_synthesis.py`:
   ```python
   #!/usr/bin/env python3
   """Test calling Synthesis via subprocess"""
   import subprocess
   import json
   import time
   from pathlib import Path

   SYNTHESIS_PATH = Path("old-ideas/synthesis/")  # Adjust as needed

   def test_search(query: str):
       """Test a single search query"""
       start = time.time()

       result = subprocess.run(
           ["uv", "run", "main.py", "search", query, "--json"],
           cwd=SYNTHESIS_PATH,
           capture_output=True,
           text=True,
           timeout=10
       )

       elapsed = time.time() - start

       if result.returncode == 0:
           data = json.loads(result.stdout)
           print(f"\nQuery: {query}")
           print(f"Time: {elapsed:.3f}s")
           print(f"Results: {len(data.get('results', []))}")
           if data.get('results'):
               print(f"Top: {data['results'][0]['title']}")
               print(f"Score: {data['results'][0]['similarity_score']:.3f}")
       else:
           print(f"Error: {result.stderr}")

       return elapsed

   if __name__ == "__main__":
       queries = [
           "semantic search",
           "local LLM",
           "productivity systems",
           "obsidian plugins"
       ]

       times = []
       for q in queries:
           t = test_search(q)
           times.append(t)

       print(f"\n--- Performance Summary ---")
       print(f"Average: {sum(times)/len(times):.3f}s")
       print(f"Min: {min(times):.3f}s")
       print(f"Max: {max(times):.3f}s")
   ```

2. Run prototype: `uv run prototypes/test_synthesis.py`
3. Document subprocess overhead

**Acceptance Criteria**:
- [ ] Can successfully call Synthesis via subprocess
- [ ] Can parse JSON output
- [ ] Subprocess overhead measured (< 100ms acceptable)
- [ ] Error handling works (timeouts, bad queries)

**Questions to Answer**:
- What's the subprocess startup overhead?
- Is JSON parsing reliable?
- How do we handle errors gracefully?

---

### 0.3: Design Mobile UX Mockup

**Owner**: Developer
**Estimated Time**: 2 hours

**Actions**:
1. Create `prototypes/search_ui.html` with minimal mobile interface:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
     <meta name="viewport" content="width=device-width, initial-scale=1">
     <title>Temoa Mockup</title>
     <style>
       * { box-sizing: border-box; margin: 0; padding: 0; }
       body {
         font-family: -apple-system, system-ui, sans-serif;
         padding: 16px;
         background: #f5f5f5;
       }
       .search-box {
         width: 100%;
         padding: 14px;
         font-size: 16px;
         border: 2px solid #ddd;
         border-radius: 8px;
         margin-bottom: 12px;
       }
       .search-btn {
         width: 100%;
         padding: 14px;
         font-size: 16px;
         background: #007aff;
         color: white;
         border: none;
         border-radius: 8px;
         margin-bottom: 20px;
       }
       .result {
         background: white;
         padding: 16px;
         margin-bottom: 12px;
         border-radius: 8px;
         box-shadow: 0 1px 3px rgba(0,0,0,0.1);
       }
       .result-title {
         font-weight: 600;
         color: #007aff;
         margin-bottom: 4px;
         text-decoration: none;
       }
       .result-score {
         color: #666;
         font-size: 14px;
         margin-bottom: 4px;
       }
       .result-path {
         color: #999;
         font-size: 13px;
       }
     </style>
   </head>
   <body>
     <h1 style="margin-bottom: 20px;">🔍 Temoa</h1>
     <input type="text" class="search-box" placeholder="Search your vault..." id="query" autofocus>
     <button class="search-btn" onclick="mockSearch()">Search</button>
     <div id="results"></div>

     <script>
       const mockData = {
         results: [
           {
             title: "Semantic Search Tools",
             relative_path: "L/Gleanings/2025-11-11-semantic-search.md",
             similarity_score: 0.847,
             obsidian_uri: "obsidian://vault/amoxtli/L/Gleanings/2025-11-11-semantic-search"
           },
           {
             title: "Daily Note - November 11",
             relative_path: "Daily/2025/2025-11-11-Tu.md",
             similarity_score: 0.723,
             obsidian_uri: "obsidian://vault/amoxtli/Daily/2025/2025-11-11-Tu"
           }
         ]
       };

       function mockSearch() {
         const html = mockData.results.map(r => `
           <div class="result">
             <a href="${r.obsidian_uri}" class="result-title">${r.title}</a>
             <div class="result-score">Similarity: ${r.similarity_score.toFixed(3)}</div>
             <div class="result-path">${r.relative_path}</div>
           </div>
         `).join('');
         document.getElementById('results').innerHTML = html;
       }

       document.getElementById('query').addEventListener('keypress', e => {
         if (e.key === 'Enter') mockSearch();
       });
     </script>
   </body>
   </html>
   ```

2. Test mockup on mobile device:
   - Open file in mobile browser
   - Test obsidian:// link behavior
   - Verify UI is readable and usable on small screen
   - Check input focus, button tap targets

3. Document findings in `docs/phase0-results.md`

**Acceptance Criteria**:
- [ ] Mockup renders correctly on mobile
- [ ] Search input is accessible (no zoom on focus)
- [ ] Buttons are easy to tap (min 44px height)
- [ ] obsidian:// URIs open Obsidian app (if possible to test)
- [ ] UI feels fast and responsive

**Questions to Answer**:
- Do obsidian:// URIs work from mobile browser?
- What's the optimal layout for small screens?
- Should we use PWA for installation?

---

### 0.4: Extract Sample Gleanings

**Owner**: Developer
**Estimated Time**: 2 hours

**Actions**:
1. Create `prototypes/extract_gleanings.py`:
   ```python
   #!/usr/bin/env python3
   """Extract sample gleanings from daily notes"""
   import re
   from pathlib import Path
   from datetime import datetime

   # NOTE: Adjust paths for your environment
   VAULT = Path.home() / "Obsidian" / "amoxtli"
   DAILY = VAULT / "Daily"
   OUTPUT = Path("prototypes/sample_gleanings")

   def extract_sample_gleanings(limit=10):
       """Extract up to {limit} gleanings as sample"""
       OUTPUT.mkdir(exist_ok=True)
       count = 0

       for daily_note in sorted(DAILY.rglob("*.md"), reverse=True):
           if count >= limit:
               break

           content = daily_note.read_text()

           # Find ## Gleanings section
           match = re.search(r"## Gleanings\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
           if not match:
               continue

           section = match.group(1)

           # Extract markdown links: [text](url)
           for link_match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', section):
               if count >= limit:
                   break

               text = link_match.group(1)
               url = link_match.group(2)

               # Create gleaning note
               date = daily_note.stem[:10]  # e.g., "2025-11-17"
               slug = re.sub(r'[^\w\s-]', '', text[:40].lower()).replace(' ', '-')
               filename = f"{date}-{slug}.md"

               gleaning_path = OUTPUT / filename

               # Write note with frontmatter
               gleaning_path.write_text(f"""---
gleaned: {date}
url: {url}
tags: [gleaning]
source: "[[{daily_note.stem}]]"
---

# {text}

[Link]({url})
""")

               print(f"✓ Created: {filename}")
               count += 1

       print(f"\nExtracted {count} sample gleanings to {OUTPUT}")

   if __name__ == "__main__":
       extract_sample_gleanings(10)
   ```

2. Run extraction script
3. Manually inspect generated gleanings
4. Test if Synthesis finds them:
   ```bash
   # Copy sample gleanings to test location in vault
   # Re-run Synthesis indexing
   cd old-ideas/synthesis/
   uv run main.py process

   # Search for a sample gleaning
   uv run main.py search "semantic search" --json
   ```

**Acceptance Criteria**:
- [ ] Successfully extracted 10 gleanings from daily notes
- [ ] Gleaning format is correct (frontmatter + content)
- [ ] Synthesis can index and find gleanings
- [ ] Search returns relevant gleanings

**Questions to Answer**:
- What gleaning formats exist in daily notes?
- Are gleanings consistent or varied?
- Does Synthesis need special handling for gleanings?
- What metadata is most useful?

---

### 0.5: Architecture Decision

**Status**: ✅ COMPLETE

**Owner**: Developer + Product Owner
**Estimated Time**: 1 hour (discussion)

**Decisions Made** (see CHRONICLES.md Entry 4):

1. **Architecture**: FastAPI server with direct Synthesis imports (DEC-009)
2. **Deployment**: Standalone service (can integrate with Apantli in Phase 4)
3. **Location**: `src/` directory in temoa repo
4. **Caching**: Not needed initially, search is fast enough (DEC-010)
5. **Gleanings**: Extract from daily notes (Phase 2 task)
6. **UI**: Web UI first (mobile-optimized HTML)

**Acceptance Criteria**:
- [x] All major architectural questions answered
- [x] Decisions documented with rationale (CHRONICLES.md)
- [x] Team aligned on approach
- [x] Ready to proceed to Phase 1

---

## Phase 0 Deliverables

- [x] `docs/phase0-results.md` - Performance measurements and findings ✅
- [x] `docs/CHRONICLES.md` Entry 4 - Architecture decisions and rationale ✅
- [x] `prototypes/test_synthesis_performance.py` - Performance test script ✅
- [x] `prototypes/investigate_performance.py` - Bottleneck investigation ✅
- [x] `prototypes/setup_vault.py` - Vault configuration helper ✅
- [ ] `prototypes/search_ui.html` - Mobile UI mockup (can do in Phase 1)
- [ ] `prototypes/extract_gleanings.py` - Gleaning extraction (Phase 2)

## Phase 0 Success Criteria

- [x] Synthesis performance validated (< 1s search) ✅ 400ms after model loaded
- [x] Bottleneck identified ✅ Model loading (2.8s)
- [x] Solution validated ✅ HTTP server wrapper with direct imports
- [x] Scaling validated ✅ 2,289 files = same speed as 13 files
- [x] Mobile use case validated ✅ 400ms meets habit formation target
- [x] All architectural decisions made and documented ✅ See CHRONICLES.md
- [x] Ready to proceed to implementation ✅ No blockers
