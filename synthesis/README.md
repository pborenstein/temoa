# Synthesis Project

## Quick Start

```bash
cd synthesis/
```

## Commands

### Model Management

```bash
# List all available models with specifications
uv run main.py models

# Detailed information about specific model
uv run main.py models --model all-mpnet-base-v2

# Show compatible models (same dimensions)
uv run main.py models --compatible all-MiniLM-L6-v2

# Set default model system-wide
uv run main.py set-default-model all-mpnet-base-v2
```

### Generate Embeddings

```bash
# Generate embeddings with default model
uv run main.py process

# Generate embeddings with specific model
uv run main.py process --model all-mpnet-base-v2

# Force rebuild with different model
uv run main.py process --model multi-qa-mpnet-base-cos-v1 --force
```

### Search Content

```bash
# Search with default model (human-readable output)
uv run main.py search "your query here"

# Search with specific model
uv run main.py search "your query here" --model all-mpnet-base-v2

# JSON output with three-way note references
uv run main.py search "your query here" --json

# JSON output with specific model
uv run main.py search "your query here" --model multi-qa-mpnet-base-cos-v1 --json
```

### View Statistics
```bash
uv run main.py stats
```

### Generate Knowledge Graph
```bash
uv run main.py visualize
```

### Trace Interest Evolution

```bash
# ASCII timeline output with default model (quiet mode)
uv run main.py archaeology "AI"
uv run main.py archaeology "writing" --threshold 0.15

# ASCII timeline with specific model
uv run main.py archaeology "AI" --model all-mpnet-base-v2
uv run main.py archaeology "writing" --model multi-qa-mpnet-base-cos-v1 --threshold 0.15

# JSON output for structured data with three-way note references
uv run main.py archaeology "AI" --json
uv run main.py archaeology "writing" --json --threshold 0.15

# JSON output with specific model
uv run main.py archaeology "AI" --model all-mpnet-base-v2 --json

# Verbose logging output
uv run main.py archaeology "AI" --verbose
```

#### JSON Output Format

Both `search` and `archaeology` commands now provide enhanced JSON output with three-way note references:

```json
{
  "query": "AI",
  "results": [
    {
      "relative_path": "Daily/2024/2024-03-15.md",
      "title": "Daily Note - March 15",
      "similarity_score": 0.847,
      "obsidian_uri": "obsidian://vault/your-vault/Daily/2024/2024-03-15",
      "wiki_link": "[[Daily Note - March 15]]",
      "file_path": "~/Obsidian/your-vault/Daily/2024/2024-03-15.md"
    }
  ]
}
```

#### Archaeology JSON Format

The archaeology command returns timeline entries with enhanced references:

```json
{
  "query": "AI",
  "threshold": 0.2,
  "timeline": {
    "entries": [
      {
        "date": "2024-03-15",
        "similarity_score": 0.723,
        "obsidian_uri": "obsidian://vault/your-vault/Daily/2024/2024-03-15",
        "wiki_link": "[[2024-03-15]]",
        "file_path": "~/Obsidian/your-vault/Daily/2024/2024-03-15.md"
      }
    ]
  }
}
```

#### Three-Way Reference System

- **obsidian_uri**: Direct Obsidian protocol link (spaces encoded as %20)
- **wiki_link**: Obsidian internal link format for copying into notes
- **file_path**: File system path with tilde (~) expansion for shell access

### Simple Canvas Visualization

```bash
uv run simple_canvas.py
```

### Model Comparison Workflows

```bash
# Generate embeddings for multiple models
uv run main.py process --model all-MiniLM-L6-v2
uv run main.py process --model all-mpnet-base-v2

# Compare search results across models
uv run main.py search "complex topic" --model all-MiniLM-L6-v2
uv run main.py search "complex topic" --model all-mpnet-base-v2

# Compare temporal archaeology across models
uv run main.py archaeology "interests" --model all-MiniLM-L6-v2 --json
uv run main.py archaeology "interests" --model all-mpnet-base-v2 --json
```

## Model Selection Guide

### Available Models

| Model | Dimensions | Speed | Quality | Best For |
|-------|------------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | fast | good | Development, exploration (default) |
| `all-mpnet-base-v2` | 768 | medium | better | Production analysis, cross-domain insights |
| `all-MiniLM-L12-v2` | 384 | medium | better | Quality improvement without storage cost |
| `paraphrase-albert-small-v2` | 768 | medium | good | Similarity detection, paraphrase finding |
| `multi-qa-mpnet-base-cos-v1` | 768 | medium | better | Question-answer optimization |

### Recommendations

**For Development & Exploration:**
- Use `all-MiniLM-L6-v2` (default) - fast processing, good quality

**For Production & Final Analysis:**
- Use `all-mpnet-base-v2` - superior semantic understanding, better insights

**For Specialized Use Cases:**
- Use `paraphrase-albert-small-v2` for finding similar content and alternative expressions
- Use `multi-qa-mpnet-base-cos-v1` for query-driven exploration and Q&A analysis
- Use `all-MiniLM-L12-v2` for better quality than L6 with same storage requirements

## Output

- Embeddings stored in `embeddings/`
- Visualizations saved to `visualizations/`
- Canvas graph: `visualizations/canvas_graph.html`
- Knowledge graph: `visualizations/knowledge_graph.html`

## Status

**Phase 3+ Complete - Multi-Model Production System**

1899 vault-only files processed with multi-model support:

**Multi-Model Architecture:**
- 5 predefined sentence transformer models with optimized storage
- Default model configuration via `synthesis_config.json`
- Model management CLI with validation and comparison tools
- Intelligent storage: default model in root, alternatives in subdirectories
- Backward compatibility maintained for existing installations

**Core Capabilities:**
- Ultra-clean data quality: excludes ALL dot directories and utility files
- Comprehensive exclusion filtering for maximum accuracy
- Semantic search with model selection across pure vault content
- Knowledge graph visualization with 1899 ultra-clean vault nodes
- Temporal Interest Archaeology with model-specific timeline analysis
- Cross-domain pattern recognition at production scale
- Robust error handling and graceful model fallback

**Technical Foundation:**
- Model registry with specifications and compatibility checking
- Dynamic storage path resolution for multi-model workflows
- Enhanced JSON output with three-way note references
- Configuration persistence and validation system