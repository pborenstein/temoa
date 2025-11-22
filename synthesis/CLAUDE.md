# CLAUDE.md - Synthesis Project

This directory contains the Synthesis Project - tools for creating meaning and insights from the vault's collected data.

## Project Overview

The Synthesis Project delivers insights and unexpected connections from your vast data collection (184+ daily notes, 545+ reference materials, 400+ L/ notes). What started as tool-building has evolved into active synthesis capability.

## Current Status: Phase 3+ - Full-Scale Production with Multi-Model Support

**Active Synthesis Capabilities**:
- **Personal Knowledge Graph Visualizer**: Interactive exploration of semantic connections across vault domains
- **Temporal Interest Archaeology**: Trace how interests evolve across time with smart ASCII timelines  
- **Semantic Search**: Find related content across the entire knowledge base
- **Cross-domain Pattern Recognition**: Discover unexpected connections between daily notes, references, and reflections
- **Multi-Model Architecture**: Choose between 5 sentence transformer models optimized for different use cases

**Production-Scale Foundation Complete**:
- **Multi-model semantic embeddings**: 5 predefined models with intelligent storage architecture
- **Default configuration system**: Persistent model preferences via synthesis_config.json
- **Model management CLI**: List, configure, and compare models with intuitive commands
- Unified data access API (VaultReader) processing 1899 vault-only files with ultra-clean data quality
- Comprehensive exclusion filtering (all dot directories, Utilities/, .tools, .obsidian, .trash, .venv, node_modules)
- Canvas-based visualization system delivering interactive HTML with 1899 clean vault nodes

**Ready for Insights**: See `README.md` for commands to explore your knowledge.

## Multi-Model Architecture

### Available Models

The system supports 5 carefully selected sentence transformer models:

| Model | Dimensions | Speed | Quality | Best For |
|-------|------------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | fast | good | Development, exploration, default use |
| `all-mpnet-base-v2` | 768 | medium | better | Production analysis, cross-domain insights |
| `all-MiniLM-L12-v2` | 384 | medium | better | Quality improvement without storage cost |
| `paraphrase-albert-small-v2` | 768 | medium | good | Similarity detection, paraphrase finding |
| `multi-qa-mpnet-base-cos-v1` | 768 | medium | better | Question-answer optimization, query-driven analysis |

### Configuration System

The system uses `synthesis_config.json` for persistent default model configuration:
- Default model: `all-MiniLM-L6-v2` (fast, good quality)
- Automatic fallback if configuration is missing
- Model validation prevents invalid configurations
- Timestamp tracking for changes

### Storage Architecture

**Intelligent Storage Layout:**
- **Default model**: Stored in `embeddings/` (root directory)
- **Alternative models**: Stored in `embeddings/{model-name}/` subdirectories
- **Benefits**: Clean separation, model comparison workflows, backward compatibility

**Example Storage:**
```
embeddings/                          # Default model (all-MiniLM-L6-v2)
embeddings/all-mpnet-base-v2/        # Alternative model
embeddings/multi-qa-mpnet-base-cos-v1/  # Another alternative
```

## Key Decisions

**Embeddings Architecture**: We chose to build our own embedding system rather than leverage Obsidian Copilot's infrastructure (see `doc/embeddings-decision.md` for details).

**Multi-Model Support**: Implemented comprehensive multi-model architecture to support different use cases and quality requirements (see `doc/MULTI_MODEL_SYSTEM.md` for complete technical details).

## Directory Structure

```
synthesis/
├── CLAUDE.md              # This file - project overview
├── README.md              # User-facing documentation
├── main.py                # CLI entry point
├── pyproject.toml         # Dependencies
├── synthesis_config.json  # Configuration
├── doc/                   # Decision documentation
├── src/                   # Source code - complete embedding system
└── embeddings/            # Embedding storage (generated)
```

## Development Approach

- Build incrementally, starting with Phase 1 foundation
- All processing runs locally for privacy
- Reuse existing analytics infrastructure where possible
- Create reusable components for multiple synthesis tools

## Target Synthesis Tools

From `SYNTHESIS_IDEAS.md` (in this directory), **delivered capabilities**:
1. **Personal Knowledge Graph Visualizer** ✓ - Interactive semantic clustering showing cross-domain connections (1899 ultra-clean vault nodes)
2. **Temporal Interest Archaeology** ✓ - ASCII timeline visualization of interest evolution patterns across full dataset
3. **The Great Synthesis Engine** - Architecture established, production-scale dataset ready for implementation

**Current Achievement**: Production-scale synthesis system processing 1899 vault-only files with ultra-clean data quality and full vault insights delivery.

**Full list of 10 synthesis ideas**: See `SYNTHESIS_IDEAS.md` for complete brainstorming session on transforming vault data into creative insights.

## Technical Stack (Implemented)

- **Language**: Python with uv dependency management
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2) with local processing
- **Vector Storage**: NumPy arrays with JSON metadata for fast similarity search
- **Graph Visualization**: Canvas-based clustering with interactive HTML output  
- **Data Processing**: Full-scale production system processing 1899 vault-only files with comprehensive exclusion filtering
- **Privacy**: All processing runs locally, no external API dependencies

## Session Memory

The `session_memory.json` file maintains state between Claude sessions, including:
- Current development focus
- Completed milestones
- Architecture decisions
- Next steps and blockers

## Getting Started - Explore Your Knowledge

```bash
cd .tools/synthesis/

# Quick status check
uv run main.py stats

# View available models and embedding status
uv run main.py models
uv run main.py models --model all-mpnet-base-v2  # Detailed model info

# Generate knowledge graph visualization  
uv run simple_canvas.py
# -> Opens visualizations/canvas_graph.html

# Trace interest evolution (ASCII timeline)
uv run main.py archaeology "AI" 
uv run main.py archaeology "writing" --threshold 0.15
uv run main.py archaeology "productivity" --exclude-daily  # Filter out daily notes

# JSON output for structured data with three-way note references
uv run main.py archaeology "AI" --json
uv run main.py archaeology "writing" --json --threshold 0.15

# Verbose logging (default is quiet mode)
uv run main.py archaeology "AI" --verbose

# Search for semantic connections (includes content descriptions)
uv run main.py search "your topic here"
uv run main.py search "productivity" --top-k 5

# Search with JSON output including three-way note references
uv run main.py search "your topic here" --json
```

## Enhanced JSON Output

Both `search` and `archaeology` commands now provide enhanced JSON output with three-way note references for improved integration:

### Three-Way Reference System
- **obsidian_uri**: `obsidian://vault/amoxtli/[path-without-md]` (spaces encoded as %20)
- **wiki_link**: `[[title]]` format for Obsidian internal linking
- **file_path**: `~/Obsidian/amoxtli/[full-path-with-md]` for shell/filesystem access

### Search JSON Example
```json
{
  "query": "AI",
  "results": [
    {
      "relative_path": "L/AI and Machine Learning.md",
      "title": "AI and Machine Learning",
      "similarity_score": 0.847,
      "obsidian_uri": "obsidian://vault/amoxtli/L/AI%20and%20Machine%20Learning",
      "wiki_link": "[[AI and Machine Learning]]",
      "file_path": "~/Obsidian/amoxtli/L/AI and Machine Learning.md"
    }
  ]
}
```

### Archaeology JSON Example
```json
{
  "query": "AI", 
  "threshold": 0.2,
  "timeline": {
    "entries": [
      {
        "date": "2024-03-15",
        "similarity_score": 0.723,
        "obsidian_uri": "obsidian://vault/amoxtli/Daily/2024/2024-03-15",
        "wiki_link": "[[2024-03-15]]",
        "file_path": "~/Obsidian/amoxtli/Daily/2024/2024-03-15.md"
      }
    ]
  }
}
```

## Recent Enhancements

### September 2025 Updates

**Enhanced Archaeology Command**: Added `--exclude-daily` flag to filter out daily notes from temporal analysis, revealing patterns in L/, Reference/, and other content types:
```bash
uv run main.py archaeology "AI" --exclude-daily
```

**Content Descriptions**: Both search and archaeology results now include content descriptions showing snippets from matched files for better context.

**Enhanced Models Command**: The `models` command now shows:
- Consolidated table with all available models and their specs
- Which models have embeddings generated (✓/✗ status)  
- Storage size and file counts for each model
- Default model indication
- Detailed model info with `--model <name>` flag

**Improved Obsidian URIs**: All Obsidian URIs now use proper HTML encoding via `urllib.parse.quote()` instead of just replacing spaces.

**Pro tip**: Start with `uv run simple_canvas.py` for an immediate view of how your knowledge clusters semantically across domains.

---
*Project initialized: 2025-08-28*  
*Last updated: 2025-09-07 (Enhanced archaeology, content descriptions, improved models command)*