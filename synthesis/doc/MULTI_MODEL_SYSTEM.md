# Multi-Model System Architecture

## Overview

The Synthesis Project features a comprehensive multi-model system that allows users to work with different sentence transformer models for varied use cases and quality requirements. The system provides model management, default configuration, and intelligent storage architecture.

## Architecture

### Model Registry

The system maintains a registry of 5 predefined sentence transformer models, each optimized for different scenarios:

| Model | Dimensions | Speed | Quality | Use Case |
|-------|------------|--------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | fast | good | General purpose, development, fast iteration |
| `all-mpnet-base-v2` | 768 | medium | better | Production use, better accuracy, cross-domain connections |
| `all-MiniLM-L12-v2` | 384 | medium | better | Improved quality without storage increase |
| `paraphrase-albert-small-v2` | 768 | medium | good | Finding similar content, paraphrase detection |
| `multi-qa-mpnet-base-cos-v1` | 768 | medium | better | Question-answer matching, query optimization |

### Configuration System

The system uses `synthesis_config.json` to manage default model configuration:

```json
{
  "default_model": "all-MiniLM-L6-v2",
  "created_at": "2025-09-06T22:44:32.729217",
  "last_updated": "2025-09-06T22:45:37.091566"
}
```

**Key Features:**
- Persistent default model configuration across sessions
- Automatic timestamp tracking for configuration changes
- Fallback to `all-MiniLM-L6-v2` if configuration is unavailable
- Validation of model names before setting defaults

### Storage Architecture

The system implements intelligent storage management to support multiple models efficiently:

**Default Model Storage:**
- Default model embeddings stored in `embeddings/` (root level)
- Maintains backward compatibility with existing installations
- Reduces path complexity for the most commonly used model

**Alternative Model Storage:**
- Non-default models stored in `embeddings/{model-name}/`
- Example: `embeddings/all-mpnet-base-v2/`, `embeddings/multi-qa-mpnet-base-cos-v1/`
- Isolated storage prevents conflicts between model embeddings
- Clean organization for comparing multiple model outputs

**Storage Examples:**
```
embeddings/                           # Default model (all-MiniLM-L6-v2)
├── embeddings.npy
├── file_paths.json
├── stats.json
└── embeddings_metadata.json

embeddings/all-mpnet-base-v2/        # Alternative model
├── embeddings.npy
├── file_paths.json
├── stats.json
└── embeddings_metadata.json
```

## CLI Commands

### Model Management

#### List Available Models
```bash
# Show all available models with specifications
uv run main.py models

# Show detailed information about a specific model
uv run main.py models --model all-mpnet-base-v2

# Show models compatible with current model (same dimensions)
uv run main.py models --compatible all-MiniLM-L6-v2
```

#### Configure Default Model
```bash
# Set default model for all operations
uv run main.py set-default-model all-mpnet-base-v2

# View current default model
uv run main.py models  # Shows default at bottom
```

### Model-Specific Operations

#### Generate Embeddings for Specific Model
```bash
# Process with default model
uv run main.py process

# Process with specific model
uv run main.py process --model all-mpnet-base-v2

# Force rebuild with different model
uv run main.py process --model multi-qa-mpnet-base-cos-v1 --force
```

#### Search with Specific Models
```bash
# Search using default model
uv run main.py search "artificial intelligence"

# Search using specific model
uv run main.py search "artificial intelligence" --model all-mpnet-base-v2

# Compare results across models
uv run main.py search "AI" --model all-MiniLM-L6-v2
uv run main.py search "AI" --model all-mpnet-base-v2
```

#### Temporal Archaeology with Models
```bash
# Default model archaeology
uv run main.py archaeology "writing"

# Specific model archaeology
uv run main.py archaeology "writing" --model multi-qa-mpnet-base-cos-v1

# JSON output with model specification
uv run main.py archaeology "writing" --model all-mpnet-base-v2 --json
```

## Model Selection Guidelines

### For Development and Iteration
- **Recommended:** `all-MiniLM-L6-v2`
- **Why:** Fast processing, good quality, efficient storage (384 dimensions)
- **Best for:** Initial exploration, testing queries, rapid development cycles

### For Production and Best Quality
- **Recommended:** `all-mpnet-base-v2`
- **Why:** Superior semantic understanding, better cross-domain connections
- **Best for:** Final synthesis outputs, detailed analysis, publication-ready insights

### For Specific Use Cases

**Paraphrase and Similarity Detection:**
- **Model:** `paraphrase-albert-small-v2`
- **Use for:** Finding alternative expressions, detecting similar concepts across different wording

**Question-Answer Optimization:**
- **Model:** `multi-qa-mpnet-base-cos-v1`
- **Use for:** Query optimization, question-based exploration, FAQ-style analysis

**Balanced Quality without Storage Increase:**
- **Model:** `all-MiniLM-L12-v2`
- **Use for:** Better quality than L6 while maintaining 384 dimensions and existing storage

## Performance Characteristics

### Processing Speed (Relative)
1. `all-MiniLM-L6-v2` - Fastest (384 dim)
2. `all-MiniLM-L12-v2` - Fast (384 dim, more layers)
3. `all-mpnet-base-v2` - Medium (768 dim)
4. `paraphrase-albert-small-v2` - Medium (768 dim)
5. `multi-qa-mpnet-base-cos-v1` - Medium (768 dim)

### Storage Requirements
- **384-dimension models:** ~50% storage of 768-dimension models
- **768-dimension models:** Higher storage but better semantic precision

### Quality Trade-offs
- **Fast models:** Good for exploration, may miss nuanced connections
- **Better models:** Superior accuracy, better cross-domain insights, worth the computational cost for final analysis

## Migration and Compatibility

### Upgrading Default Model
1. Process vault with new model: `uv run main.py process --model new-model-name`
2. Test search quality: `uv run main.py search "test query" --model new-model-name`
3. Set as default: `uv run main.py set-default-model new-model-name`

### Backward Compatibility
- Existing default model embeddings remain in `embeddings/`
- All existing commands work without modification
- Configuration system gracefully handles missing config files
- Model validation prevents invalid configurations

### Comparing Models
```bash
# Generate embeddings for comparison
uv run main.py process --model all-MiniLM-L6-v2
uv run main.py process --model all-mpnet-base-v2

# Compare search results
uv run main.py search "complex topic" --model all-MiniLM-L6-v2
uv run main.py search "complex topic" --model all-mpnet-base-v2

# Analyze different temporal patterns
uv run main.py archaeology "interests" --model all-MiniLM-L6-v2
uv run main.py archaeology "interests" --model all-mpnet-base-v2
```

## Technical Implementation

### Model Registry Class
The `ModelRegistry` class provides centralized model management:
- **Model Validation:** Ensures only supported models are used
- **Default Configuration:** Manages persistent default model settings
- **Model Information:** Provides detailed specifications for each model
- **Compatibility Analysis:** Suggests models for comparison based on dimensions

### Configuration Manager Integration
The system integrates with the existing `ConfigManager` for:
- Persistent storage of user preferences
- Automatic configuration file creation
- Error handling and fallback behavior
- Timestamp tracking for configuration changes

### Storage Path Resolution
Dynamic storage path resolution based on model selection:
```python
# Default model uses root embeddings directory
if model_name == default_model:
    storage_path = "embeddings/"
else:
    storage_path = f"embeddings/{model_name}/"
```

This architecture ensures clean separation between models while maintaining simplicity for the common case.

## Future Extensions

The multi-model architecture is designed for extensibility:

### Adding New Models
1. Add model specification to `ModelRegistry.MODELS`
2. Specify dimensions, speed, quality, and use case
3. Model automatically available in all CLI commands

### Custom Model Support
Future versions could support:
- User-defined model specifications
- Custom model loading from HuggingFace Hub
- Model fine-tuning for specific vault content

### Advanced Features
Potential enhancements:
- Ensemble voting across multiple models
- Model performance analytics and recommendations
- Automatic model selection based on query type
- Cross-model similarity analysis for validation

---
*Multi-model system implemented: 2025-09-06*
*Documentation created: 2025-09-07*