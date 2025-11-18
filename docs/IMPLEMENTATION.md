# IMPLEMENTATION.md - Ixpantilia Development Plan

> **Approach**: Plan like waterfall, implement in agile
>
> This document provides a detailed implementation roadmap for Ixpantilia, broken into discrete phases with clear deliverables, acceptance criteria, and dependencies.

**Project**: Ixpantilia - Local Semantic Search Server for Obsidian Vault
**Created**: 2025-11-18
**Status**: Phase 0 (Discovery) - Not Started
**Estimated Timeline**: 4-6 weeks for Phases 0-2, ongoing for Phases 3-4

---

## Table of Contents

1. [Phase 0: Discovery & Validation](#phase-0-discovery--validation)
2. [Phase 1: Minimal Viable Search](#phase-1-minimal-viable-search)
3. [Phase 2: Gleanings Integration](#phase-2-gleanings-integration)
4. [Phase 3: Enhanced Features](#phase-3-enhanced-features)
5. [Phase 4: Vault-First LLM](#phase-4-vault-first-llm)
6. [Dependencies & Prerequisites](#dependencies--prerequisites)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Strategy](#deployment-strategy)

---

## Phase 0: Discovery & Validation

**Goal**: Answer all open questions and validate architectural assumptions before writing code

**Duration**: 1-2 days
**Status**: Not Started
**Priority**: CRITICAL - Blocks all other phases

### Tasks

#### 0.1: Test Synthesis Performance

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
- [ ] Search latency < 1 second for typical queries
- [ ] Know exact file count indexed
- [ ] Confirmed whether daily notes are indexed
- [ ] Performance baseline established

**Questions to Answer**:
- Is search fast enough for mobile use? (target: < 500ms)
- Are daily notes currently indexed by Synthesis?
- What's the memory footprint of Synthesis?

---

#### 0.2: Prototype Subprocess Integration

**Owner**: Developer
**Estimated Time**: 1 hour

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

#### 0.3: Design Mobile UX Mockup

**Owner**: Developer
**Estimated Time**: 2 hours

**Actions**:
1. Create `prototypes/search_ui.html` with minimal mobile interface:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
     <meta name="viewport" content="width=device-width, initial-scale=1">
     <title>Ixpantilia Mockup</title>
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
     <h1 style="margin-bottom: 20px;">🔍 Ixpantilia</h1>
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

#### 0.4: Extract Sample Gleanings

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

#### 0.5: Architecture Decision

**Owner**: Developer + Product Owner
**Estimated Time**: 1 hour (discussion)

**Actions**:
1. Review Phase 0 findings
2. Make key decisions:
   - **Deployment**: Standalone service or integrate into Apantli?
   - **Location**: Where should Ixpantilia code live?
   - **Caching**: Do we need caching initially?
   - **Gleanings**: Extract from daily notes or create directly?
   - **UI**: Web UI first or Obsidian plugin?

3. Document decisions in `docs/ARCHITECTURE_DECISIONS.md`:
   ```markdown
   # Architecture Decision Record

   ## ADR-001: Deployment Model
   **Decision**: [Standalone / Integrated with Apantli]
   **Rationale**: ...
   **Consequences**: ...

   ## ADR-002: Caching Strategy
   **Decision**: [No caching initially / Redis cache / In-memory LRU]
   **Rationale**: ...
   **Consequences**: ...
   ```

**Acceptance Criteria**:
- [ ] All major architectural questions answered
- [ ] Decisions documented with rationale
- [ ] Team aligned on approach
- [ ] Ready to proceed to Phase 1

---

### Phase 0 Deliverables

- [ ] `docs/phase0-results.md` - Performance measurements and findings
- [ ] `docs/ARCHITECTURE_DECISIONS.md` - Key technical decisions
- [ ] `prototypes/test_synthesis.py` - Subprocess integration proof of concept
- [ ] `prototypes/search_ui.html` - Mobile UI mockup
- [ ] `prototypes/extract_gleanings.py` - Gleaning extraction script
- [ ] `prototypes/sample_gleanings/` - 10 extracted sample gleanings

### Phase 0 Success Criteria

- [ ] Synthesis performance validated (< 1s search)
- [ ] Subprocess integration proven feasible
- [ ] Mobile UX validated (obsidian:// URIs work)
- [ ] Gleaning extraction validated (end-to-end flow works)
- [ ] All architectural decisions made and documented
- [ ] Team confident to proceed to implementation

---

## Phase 1: Minimal Viable Search

**Goal**: Build the simplest possible working search server

**Duration**: 3-5 days
**Status**: Not Started
**Dependencies**: Phase 0 complete

### Tasks

#### 1.1: Project Setup

**Owner**: Developer
**Estimated Time**: 1 hour

**Actions**:
1. Initialize Python project with uv:
   ```bash
   # Create project structure
   mkdir -p src/ixpantilia/ui tests
   touch src/ixpantilia/__init__.py

   # Initialize uv project
   uv init
   ```

2. Create `pyproject.toml`:
   ```toml
   [project]
   name = "ixpantilia"
   version = "0.1.0"
   description = "Local semantic search server for Obsidian vault"
   requires-python = ">=3.11"
   dependencies = [
       "fastapi>=0.104.0",
       "uvicorn[standard]>=0.24.0",
   ]

   [project.optional-dependencies]
   dev = [
       "pytest>=7.4.0",
       "pytest-asyncio>=0.21.0",
       "httpx>=0.25.0",  # For testing FastAPI
       "black>=23.0.0",
       "mypy>=1.6.0",
   ]

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```

3. Install dependencies:
   ```bash
   uv sync
   uv sync --extra dev
   ```

4. Create `config.example.json`:
   ```json
   {
     "vault_path": "~/Obsidian/amoxtli",
     "synthesis_path": "~/.obsidian/vaults/main/.tools/synthesis",
     "default_model": "all-MiniLM-L6-v2",
     "server": {
       "host": "0.0.0.0",
       "port": 8080
     },
     "search": {
       "default_limit": 10,
       "max_limit": 50,
       "timeout": 10
     }
   }
   ```

5. Create `.gitignore`:
   ```
   __pycache__/
   *.py[cod]
   .venv/
   .uv/
   config.json
   *.log
   .mypy_cache/
   .pytest_cache/
   ```

**Acceptance Criteria**:
- [ ] Python project structure created
- [ ] Dependencies managed with uv
- [ ] Configuration template exists
- [ ] Git repository properly configured

---

#### 1.2: Configuration Management

**Owner**: Developer
**Estimated Time**: 1 hour

**Actions**:
1. Create `src/ixpantilia/config.py`:
   ```python
   """Configuration management for Ixpantilia"""
   import json
   from pathlib import Path
   from typing import Dict, Any

   class Config:
       """Application configuration"""

       def __init__(self, config_path: Path = Path("config.json")):
           self.config_path = config_path
           self._config = self._load_config()

       def _load_config(self) -> Dict[str, Any]:
           """Load configuration from JSON file"""
           if not self.config_path.exists():
               raise FileNotFoundError(
                   f"Config file not found: {self.config_path}\n"
                   f"Copy config.example.json to config.json and update paths"
               )

           with open(self.config_path) as f:
               config = json.load(f)

           # Expand paths
           config["vault_path"] = Path(config["vault_path"]).expanduser()
           config["synthesis_path"] = Path(config["synthesis_path"]).expanduser()

           return config

       @property
       def vault_path(self) -> Path:
           return self._config["vault_path"]

       @property
       def synthesis_path(self) -> Path:
           return self._config["synthesis_path"]

       @property
       def default_model(self) -> str:
           return self._config["default_model"]

       @property
       def server_host(self) -> str:
           return self._config["server"]["host"]

       @property
       def server_port(self) -> int:
           return self._config["server"]["port"]

       @property
       def search_default_limit(self) -> int:
           return self._config["search"]["default_limit"]

       @property
       def search_max_limit(self) -> int:
           return self._config["search"]["max_limit"]

       @property
       def search_timeout(self) -> int:
           return self._config["search"]["timeout"]
   ```

2. Create tests: `tests/test_config.py`

**Acceptance Criteria**:
- [ ] Config loads from JSON file
- [ ] Paths are expanded properly
- [ ] Missing config raises helpful error
- [ ] All config values accessible via properties

---

#### 1.3: Synthesis Wrapper

**Owner**: Developer
**Estimated Time**: 2 hours

**Actions**:
1. Create `src/ixpantilia/synthesis.py`:
   ```python
   """Synthesis subprocess wrapper"""
   import subprocess
   import json
   from pathlib import Path
   from typing import Dict, Any, List, Optional

   class SynthesisError(Exception):
       """Synthesis operation failed"""
       pass

   class SynthesisClient:
       """Client for calling Synthesis via subprocess"""

       def __init__(self, synthesis_path: Path, timeout: int = 10):
           self.synthesis_path = synthesis_path
           self.timeout = timeout

           if not (synthesis_path / "main.py").exists():
               raise FileNotFoundError(
                   f"Synthesis not found at {synthesis_path}"
               )

       def search(
           self,
           query: str,
           model: Optional[str] = None,
           limit: Optional[int] = None
       ) -> Dict[str, Any]:
           """
           Perform semantic search via Synthesis

           Args:
               query: Search query string
               model: Optional model name (uses Synthesis default if not specified)
               limit: Optional result limit (applied client-side)

           Returns:
               Synthesis JSON response with results

           Raises:
               SynthesisError: If search fails
           """
           cmd = ["uv", "run", "main.py", "search", query, "--json"]

           if model:
               cmd.extend(["--model", model])

           try:
               result = subprocess.run(
                   cmd,
                   cwd=self.synthesis_path,
                   capture_output=True,
                   text=True,
                   timeout=self.timeout
               )
           except subprocess.TimeoutExpired:
               raise SynthesisError(f"Search timed out after {self.timeout}s")

           if result.returncode != 0:
               raise SynthesisError(
                   f"Synthesis search failed: {result.stderr}"
               )

           try:
               data = json.loads(result.stdout)
           except json.JSONDecodeError as e:
               raise SynthesisError(f"Invalid JSON from Synthesis: {e}")

           # Apply client-side limit if specified
           if limit and "results" in data:
               data["results"] = data["results"][:limit]

           return data

       def archaeology(
           self,
           query: str,
           threshold: float = 0.2,
           exclude_daily: bool = False
       ) -> Dict[str, Any]:
           """
           Perform temporal archaeology via Synthesis

           Args:
               query: Topic to analyze
               threshold: Similarity threshold (0.0-1.0)
               exclude_daily: Filter out daily notes

           Returns:
               Synthesis JSON response with timeline
           """
           cmd = [
               "uv", "run", "main.py", "archaeology", query,
               "--json", "--threshold", str(threshold)
           ]

           if exclude_daily:
               cmd.append("--exclude-daily")

           try:
               result = subprocess.run(
                   cmd,
                   cwd=self.synthesis_path,
                   capture_output=True,
                   text=True,
                   timeout=self.timeout
               )
           except subprocess.TimeoutExpired:
               raise SynthesisError(f"Archaeology timed out after {self.timeout}s")

           if result.returncode != 0:
               raise SynthesisError(
                   f"Synthesis archaeology failed: {result.stderr}"
               )

           try:
               return json.loads(result.stdout)
           except json.JSONDecodeError as e:
               raise SynthesisError(f"Invalid JSON from Synthesis: {e}")

       def stats(self) -> Dict[str, Any]:
           """Get vault statistics from Synthesis"""
           cmd = ["uv", "run", "main.py", "stats", "--json"]

           try:
               result = subprocess.run(
                   cmd,
                   cwd=self.synthesis_path,
                   capture_output=True,
                   text=True,
                   timeout=self.timeout
               )
           except subprocess.TimeoutExpired:
               raise SynthesisError(f"Stats timed out after {self.timeout}s")

           if result.returncode != 0:
               raise SynthesisError(f"Synthesis stats failed: {result.stderr}")

           try:
               return json.loads(result.stdout)
           except json.JSONDecodeError as e:
               raise SynthesisError(f"Invalid JSON from Synthesis: {e}")
   ```

2. Create tests: `tests/test_synthesis.py` (integration tests)

**Acceptance Criteria**:
- [ ] Can call Synthesis search via subprocess
- [ ] Can call Synthesis archaeology
- [ ] Can get stats
- [ ] Errors are handled gracefully
- [ ] Timeouts work correctly
- [ ] JSON parsing is robust

---

#### 1.4: FastAPI Server

**Owner**: Developer
**Estimated Time**: 3 hours

**Actions**:
1. Create `src/ixpantilia/server.py`:
   ```python
   """FastAPI server for Ixpantilia"""
   from fastapi import FastAPI, HTTPException, Query
   from fastapi.responses import HTMLResponse
   from fastapi.middleware.cors import CORSMiddleware
   from pathlib import Path
   from typing import Optional
   import logging

   from .config import Config
   from .synthesis import SynthesisClient, SynthesisError

   # Configure logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)

   # Load configuration
   config = Config()

   # Initialize Synthesis client
   synthesis = SynthesisClient(
       synthesis_path=config.synthesis_path,
       timeout=config.search_timeout
   )

   # Create FastAPI app
   app = FastAPI(
       title="Ixpantilia",
       description="Local semantic search server for Obsidian vault",
       version="0.1.0"
   )

   # Add CORS middleware for development
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )

   @app.get("/")
   async def root():
       """Serve search UI"""
       ui_path = Path(__file__).parent / "ui" / "search.html"

       if not ui_path.exists():
           raise HTTPException(status_code=500, detail="UI not found")

       html_content = ui_path.read_text()
       return HTMLResponse(content=html_content)

   @app.get("/search")
   async def search(
       q: str = Query(..., description="Search query"),
       limit: int = Query(
           default=None,
           description="Maximum number of results",
           ge=1,
           le=None  # Will be validated below
       ),
       model: Optional[str] = Query(
           default=None,
           description="Embedding model to use"
       )
   ):
       """
       Semantic search across vault using Synthesis

       Returns JSON with search results including obsidian:// URIs
       """
       # Apply limits
       if limit is None:
           limit = config.search_default_limit
       if limit > config.search_max_limit:
           limit = config.search_max_limit

       try:
           logger.info(f"Search: query='{q}', limit={limit}, model={model}")
           data = synthesis.search(query=q, model=model, limit=limit)

           return {
               "query": q,
               "results": data.get("results", []),
               "total": len(data.get("results", [])),
               "model": model or config.default_model
           }

       except SynthesisError as e:
           logger.error(f"Synthesis error: {e}")
           raise HTTPException(status_code=500, detail=str(e))

   @app.get("/health")
   async def health():
       """Health check endpoint"""
       try:
           # Quick test that Synthesis is accessible
           stats = synthesis.stats()
           return {
               "status": "healthy",
               "synthesis": "connected",
               "files_indexed": stats.get("file_count", 0)
           }
       except SynthesisError as e:
           return {
               "status": "unhealthy",
               "synthesis": "error",
               "error": str(e)
           }
   ```

2. Create minimal UI: `src/ixpantilia/ui/search.html` (adapt from Phase 0 mockup)

3. Create `src/ixpantilia/__main__.py` for running server:
   ```python
   """Main entry point for running Ixpantilia server"""
   import uvicorn
   from .config import Config

   if __name__ == "__main__":
       config = Config()
       uvicorn.run(
           "ixpantilia.server:app",
           host=config.server_host,
           port=config.server_port,
           reload=True  # Development mode
       )
   ```

**Acceptance Criteria**:
- [ ] Server starts successfully
- [ ] `/search` endpoint works
- [ ] `/health` endpoint works
- [ ] UI is served at `/`
- [ ] CORS configured for development
- [ ] Logging configured

---

#### 1.5: Mobile Web UI

**Owner**: Developer
**Estimated Time**: 2 hours

**Actions**:
1. Create `src/ixpantilia/ui/search.html` (enhanced from Phase 0 mockup):
   - Clean, mobile-optimized layout
   - Search input with Enter key support
   - Results display with obsidian:// links
   - Loading states
   - Error handling

2. Test UI on mobile device:
   - Start server
   - Access from mobile browser via Tailscale
   - Test search functionality
   - Verify obsidian:// links work

**Acceptance Criteria**:
- [ ] UI renders correctly on mobile (iPhone, Android)
- [ ] Search is functional
- [ ] Results display correctly
- [ ] Links open in Obsidian app
- [ ] No zoom on input focus (viewport configured)
- [ ] Loading/error states work

---

#### 1.6: Basic Testing

**Owner**: Developer
**Estimated Time**: 2 hours

**Actions**:
1. Create `tests/test_server.py`:
   ```python
   """Tests for FastAPI server"""
   import pytest
   from fastapi.testclient import TestClient
   from ixpantilia.server import app

   client = TestClient(app)

   def test_root():
       """Test root endpoint serves UI"""
       response = client.get("/")
       assert response.status_code == 200
       assert "text/html" in response.headers["content-type"]

   def test_search_endpoint():
       """Test search endpoint"""
       response = client.get("/search?q=semantic+search")
       assert response.status_code == 200
       data = response.json()
       assert "results" in data
       assert "query" in data
       assert data["query"] == "semantic search"

   def test_search_with_limit():
       """Test search with limit parameter"""
       response = client.get("/search?q=AI&limit=5")
       assert response.status_code == 200
       data = response.json()
       assert len(data["results"]) <= 5

   def test_health_endpoint():
       """Test health check"""
       response = client.get("/health")
       assert response.status_code == 200
       data = response.json()
       assert "status" in data
   ```

2. Run tests: `uv run pytest`

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Test coverage > 70%
- [ ] Integration tests work with real Synthesis

---

#### 1.7: Documentation

**Owner**: Developer
**Estimated Time**: 1 hour

**Actions**:
1. Update README.md with actual installation instructions
2. Create `docs/API.md` with endpoint documentation
3. Create `docs/DEPLOYMENT.md` with deployment instructions

**Acceptance Criteria**:
- [ ] README has clear quick start guide
- [ ] API endpoints documented
- [ ] Deployment process documented

---

### Phase 1 Deliverables

- [ ] Working FastAPI server (`src/ixpantilia/server.py`)
- [ ] Configuration system (`src/ixpantilia/config.py`)
- [ ] Synthesis wrapper (`src/ixpantilia/synthesis.py`)
- [ ] Mobile web UI (`src/ixpantilia/ui/search.html`)
- [ ] Basic test suite (`tests/`)
- [ ] Project documentation (README, API docs)
- [ ] `pyproject.toml` with dependencies

### Phase 1 Success Criteria

- [ ] Server runs and is accessible from mobile
- [ ] Search works end-to-end (query → Synthesis → results)
- [ ] Results open in Obsidian mobile app
- [ ] Response time < 2 seconds from mobile
- [ ] Basic tests pass
- [ ] Code is clean and documented

---

## Phase 2: Gleanings Integration

**Goal**: Make gleanings searchable via semantic search

**Duration**: 3-4 days
**Status**: Not Started
**Dependencies**: Phase 1 complete

### Tasks

#### 2.1: Gleanings Extraction Script

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

#### 2.2: Historical Gleanings Migration

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

#### 2.3: Synthesis Re-indexing

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

#### 2.4: Automated Extraction

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

### Phase 2 Deliverables

- [ ] `scripts/extract_gleanings.py` - Gleaning extraction
- [ ] `scripts/migrate_old_gleanings.py` - Historical migration
- [ ] `L/Gleanings/` - All gleanings as individual notes
- [ ] Automation setup (cron/systemd)
- [ ] Documentation in `docs/GLEANINGS.md`

### Phase 2 Success Criteria

- [ ] All 505+ gleanings are searchable
- [ ] New gleanings extracted regularly
- [ ] Search finds gleanings with good relevance
- [ ] Extraction is automated

---

## Phase 3: Enhanced Features

**Goal**: Make Ixpantilia indispensable for daily use

**Duration**: 5-7 days
**Status**: Not Started
**Dependencies**: Phase 2 complete

### Tasks

#### 3.1: Archaeology Endpoint

**Actions**:
1. Add `GET /archaeology` endpoint to server
2. Expose Synthesis temporal analysis via API
3. Update UI with archaeology view

**Acceptance Criteria**:
- [ ] Archaeology endpoint works
- [ ] Can query interest timeline
- [ ] Results show temporal patterns

---

#### 3.2: Enhanced UI

**Actions**:
1. Add filters (date range, file type, tags)
2. Show content previews in results
3. Add model selection dropdown
4. Improve mobile responsiveness

**Acceptance Criteria**:
- [ ] Filters work correctly
- [ ] Preview snippets are helpful
- [ ] Can switch models
- [ ] UI feels polished

---

#### 3.3: PWA Support

**Actions**:
1. Add service worker for offline capability
2. Create manifest.json for installation
3. Test PWA on iOS and Android

**Acceptance Criteria**:
- [ ] Can install as PWA
- [ ] Works offline (cached UI)
- [ ] App icon shows correctly

---

### Phase 3 Deliverables

- [ ] `/archaeology` endpoint
- [ ] `/stats` endpoint
- [ ] Enhanced UI with filters
- [ ] PWA support (manifest + service worker)
- [ ] Performance optimizations

### Phase 3 Success Criteria

- [ ] Daily usage > 5 searches/day
- [ ] Archaeology provides useful insights
- [ ] UI is preferred over Obsidian search
- [ ] PWA installed on mobile device

---

## Phase 4: Vault-First LLM

**Goal**: LLMs check vault before internet

**Duration**: 7-10 days
**Status**: Future
**Dependencies**: Phase 3 complete, Apantli integration

### Tasks

#### 4.1: Chat Endpoint with Context

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

#### 4.2: Citation System

**Actions**:
1. Implement citation extraction
2. Add source attribution to responses
3. Link citations back to vault notes

**Acceptance Criteria**:
- [ ] LLM cites vault sources
- [ ] Citations are clickable
- [ ] Attribution is accurate

---

### Phase 4 Deliverables

- [ ] `/chat` endpoint
- [ ] Apantli integration
- [ ] Citation system
- [ ] Vault-first chat UI

### Phase 4 Success Criteria

- [ ] Vault-first becomes default research mode
- [ ] LLM responses build on existing knowledge
- [ ] Citations work reliably

---

## Dependencies & Prerequisites

### System Requirements

- Python 3.11+
- uv package manager
- Synthesis installed and working
- Obsidian vault accessible
- Tailscale network (for mobile access)

### External Dependencies

- **Synthesis**: Must be installed and operational
- **Obsidian Mobile**: For testing obsidian:// URIs
- **Apantli** (Phase 4): LLM proxy for vault-first chat

---

## Testing Strategy

### Unit Tests
- Configuration loading
- Synthesis wrapper methods
- API endpoint logic

### Integration Tests
- Synthesis subprocess calls
- End-to-end search flow
- Mobile UI functionality

### Performance Tests
- Search response times
- Concurrent request handling
- Mobile network conditions

### Manual Tests
- Mobile browser compatibility
- obsidian:// URI behavior
- PWA installation

---

## Deployment Strategy

### Development
```bash
uv run python -m ixpantilia
```

### Production (Systemd)
```ini
[Unit]
Description=Ixpantilia Semantic Search Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/ixpantilia
ExecStart=/path/to/ixpantilia/.venv/bin/uvicorn ixpantilia.server:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

### Production (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uvicorn", "ixpantilia.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## Risk Management

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Synthesis performance inadequate | High | Phase 0 validates performance first |
| obsidian:// URIs don't work on mobile | High | Phase 0 tests on actual devices |
| Subprocess overhead too high | Medium | Measure in Phase 0, consider alternative integration |
| Gleanings extraction breaks on edge cases | Medium | Extensive testing with real data |

### Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Phase 0 reveals architectural issues | High | Plan for 2-week buffer before Phase 1 |
| Synthesis changes break integration | Medium | Version pin Synthesis, test regularly |
| Mobile testing requires physical devices | Low | Use Tailscale for remote testing |

---

## Success Metrics (Revisited)

### Phase 1 Metrics
- Search response time < 2s from mobile
- Can perform 10 consecutive searches without errors
- obsidian:// links work 100% of time

### Phase 2 Metrics
- All 505+ gleanings searchable
- Gleaning extraction runs daily without failures
- Search finds relevant gleanings in top 5 results

### Phase 3 Metrics
- Daily usage > 5 searches
- Archaeology used > 1x per week
- PWA installed and used regularly

### Phase 4 Metrics
- Vault-first chat used > 3x per week
- LLM responses cite vault sources > 50% of time
- User reports building on existing knowledge

---

## Appendix: Timeline

```
Week 1: Phase 0 (Discovery)
  Days 1-2: Performance testing, prototyping, architecture decisions

Week 2-3: Phase 1 (MVP)
  Days 3-5: Project setup, configuration, Synthesis wrapper
  Days 6-7: FastAPI server, basic UI
  Days 8-9: Testing, documentation, mobile validation

Week 4: Phase 2 (Gleanings)
  Days 10-11: Extraction scripts, migration
  Days 12-13: Automation, testing, refinement

Week 5-6: Phase 3 (Enhanced Features)
  Days 14-16: Archaeology endpoint, enhanced UI
  Days 17-19: PWA support, performance optimization
  Day 20: Testing, polish

Week 7+: Phase 4 (Vault-First LLM)
  Future development based on Phase 1-3 learnings
```

---

**Plan Created**: 2025-11-18
**Plan Status**: DRAFT - Pending Phase 0 validation
**Next Review**: After Phase 0 completion
