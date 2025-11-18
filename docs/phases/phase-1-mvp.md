# Phase 1: Minimal Viable Search

**Goal**: Build FastAPI server that wraps Synthesis with direct imports for fast search

**Duration**: 2-3 days
**Status**: READY TO START
**Dependencies**: Phase 0 complete ✅

**Architecture** (based on Phase 0 findings):
- FastAPI server imports Synthesis code directly (NOT subprocess)
- Model loaded ONCE at startup (~10-15s)
- Each search: direct function call (~400ms)
- Simple HTML UI for mobile testing
- Target: < 500ms response time

## Tasks

**IMPORTANT CHANGE from original plan**:
- ~~Task 1.3 was "Synthesis subprocess wrapper"~~
- **NOW**: Task 1.3 is "Synthesis direct import wrapper" (see DEC-009)
- Import Synthesis code directly, NOT via subprocess
- Load model once at startup, keep in memory
- This is the key to achieving ~400ms search time

---

### 1.1: Project Setup

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

### 1.2: Configuration Management

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

### 1.3: Synthesis Direct Import Wrapper

**UPDATED** (was subprocess, now direct import - see DEC-009)

**Owner**: Developer
**Estimated Time**: 2-3 hours

**Key Change**: Import Synthesis code directly instead of subprocess calls.
This keeps the model loaded in memory (~400ms vs ~3s per search).

**Actions**:
1. Add Synthesis to Python path in `src/ixpantilia/synthesis.py`:
   ```python
   """Synthesis direct import wrapper - loads model once, keeps in memory"""
   import sys
   from pathlib import Path
   from typing import Dict, Any, List, Optional

   class SynthesisError(Exception):
       """Synthesis operation failed"""
       pass

   class SynthesisClient:
       """Client for calling Synthesis via direct imports (NOT subprocess)"""

       def __init__(self, synthesis_path: Path, vault_path: Path, model: str = "all-MiniLM-L6-v2"):
           """
           Initialize Synthesis client with direct imports.

           This loads the sentence-transformer model into memory ONCE at startup.
           Subsequent searches reuse the loaded model (~400ms vs ~3s).

           Args:
               synthesis_path: Path to Synthesis directory (old-ideas/synthesis)
               vault_path: Path to Obsidian vault
               model: Model name to load (default: all-MiniLM-L6-v2)
           """
           self.synthesis_path = synthesis_path
           self.vault_path = vault_path
           self.model_name = model

           # Add Synthesis to Python path
           if str(synthesis_path) not in sys.path:
               sys.path.insert(0, str(synthesis_path))

           # Import Synthesis modules (after adding to path)
           try:
               from search_engine import SearchEngine
               from config import Config as SynthesisConfig
           except ImportError as e:
               raise SynthesisError(
                   f"Could not import Synthesis from {synthesis_path}: {e}"
               )

           # Initialize Synthesis search engine
           # This loads the model into memory (takes ~10-15s, but only once!)
           try:
               self.config = SynthesisConfig(vault_path=vault_path)
               self.engine = SearchEngine(config=self.config, model=model)
               print(f"✓ Loaded Synthesis model '{model}' into memory")
           except Exception as e:
               raise SynthesisError(f"Failed to initialize Synthesis: {e}")

       def search(
           self,
           query: str,
           limit: Optional[int] = None
       ) -> Dict[str, Any]:
           """
           Perform semantic search using loaded model.

           This is FAST (~400ms) because model is already in memory.

           Args:
               query: Search query string
               limit: Optional result limit (applied after search)

           Returns:
               Dict with 'results' key containing search matches

           Raises:
               SynthesisError: If search fails
           """
           try:
               results = self.engine.search(query)

               # Apply limit if specified
               if limit:
                   results = results[:limit]

               return {
                   "query": query,
                   "results": results,
                   "total": len(results),
                   "model": self.model_name
               }
           except Exception as e:
               raise SynthesisError(f"Search failed: {e}")

       def archaeology(
           self,
           query: str,
           threshold: float = 0.2
       ) -> Dict[str, Any]:
           """
           Perform temporal archaeology analysis.

           Args:
               query: Topic to analyze
               threshold: Similarity threshold (0.0-1.0)

           Returns:
               Dict with timeline and intensity data
           """
           try:
               timeline = self.engine.archaeology(query, threshold=threshold)
               return {
                   "query": query,
                   "threshold": threshold,
                   "timeline": timeline
               }
           except Exception as e:
               raise SynthesisError(f"Archaeology failed: {e}")
   ```

2. Note: The actual Synthesis API may differ - adjust imports/calls based on Synthesis codebase
3. Test model loads correctly at startup (should take ~10-15s)
4. Verify search is fast after startup (~400ms)

**Acceptance Criteria**:
- [ ] Can import Synthesis modules from old-ideas/synthesis/
- [ ] Model loads once at initialization (~10-15s)
- [ ] Search calls are fast (~400ms) after model loaded
- [ ] Can call search() and archaeology() methods
- [ ] Errors are handled gracefully
- [ ] Model stays in memory between searches

---

### 1.4: FastAPI Server

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

### 1.5: Mobile Web UI

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

### 1.6: Basic Testing

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

### 1.7: Documentation

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

## Phase 1 Deliverables

- [ ] Working FastAPI server (`src/ixpantilia/server.py`)
- [ ] Configuration system (`src/ixpantilia/config.py`)
- [ ] Synthesis wrapper (`src/ixpantilia/synthesis.py`)
- [ ] Mobile web UI (`src/ixpantilia/ui/search.html`)
- [ ] Basic test suite (`tests/`)
- [ ] Project documentation (README, API docs)
- [ ] `pyproject.toml` with dependencies

## Phase 1 Success Criteria

- [ ] Server runs and is accessible from mobile
- [ ] Search works end-to-end (query → Synthesis → results)
- [ ] Results open in Obsidian mobile app
- [ ] Response time < 2 seconds from mobile
- [ ] Basic tests pass
- [ ] Code is clean and documented
