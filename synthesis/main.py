#!/usr/bin/env python3
"""
Main command-line interface for the Synthesis Project embeddings system.
"""
import argparse
import logging
from pathlib import Path
from urllib.parse import quote

from src.embeddings import EmbeddingPipeline
from src.embeddings.models import ModelRegistry
from src.visualizer.visualizer import PersonalKnowledgeGraphVisualizer
from src.temporal_archaeology import TemporalArchaeologist


def get_vault_name(vault_path: Path) -> str:
    """Extract vault name from vault path.

    Args:
        vault_path: Path to the vault root

    Returns:
        The vault directory name
    """
    return vault_path.resolve().name


def setup_logging(level: str = "INFO", quiet: bool = False):
    """Configure logging."""
    if quiet:
        # For search command, suppress all logging except errors
        logging.basicConfig(
            level=logging.ERROR,
            format="%(message)s"
        )
    else:
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )


def cmd_process(args):
    """Process vault and generate embeddings."""
    from src.embeddings.models import ModelRegistry
    
    # Use configured default if no model specified
    model_name = args.model or ModelRegistry.get_default_model()
    
    # Validate model first
    if not ModelRegistry.validate_model(model_name):
        print(f"Error: Unknown model '{model_name}'")
        print("Available models:")
        print(ModelRegistry.format_model_table())
        return
    
    try:
        pipeline = EmbeddingPipeline(
            vault_root=args.vault,
            storage_dir=Path("embeddings/"),
            model_name=model_name
        )
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    success = pipeline.process_vault(
        force_rebuild=args.force,
        limit=args.limit,
        use_strategic_subset=args.strategic
    )
    
    if success:
        stats = pipeline.get_stats()
        print("✓ Embeddings generated successfully")
        print(f"  Files processed: {stats.get('total_files', 'unknown')}")
        print(f"  Model: {stats.get('model_info', {}).get('model_name', 'unknown')}")
        print(f"  Embedding dimension: {stats.get('embedding_dim', 'unknown')}")
    else:
        print("✗ Failed to generate embeddings")


def cmd_search(args):
    """Search for similar content."""
    import json
    import os
    from src.embeddings.models import ModelRegistry

    # Get vault name for URIs
    vault_name = get_vault_name(args.vault)
    vault_root = args.vault

    # Use configured default if no model specified
    model_name = args.model or ModelRegistry.get_default_model()

    # Validate model first
    if not ModelRegistry.validate_model(model_name):
        print(f"Error: Unknown model '{model_name}'")
        print("Available models:")
        print(ModelRegistry.format_model_table())
        return

    try:
        pipeline = EmbeddingPipeline(
            vault_root=vault_root,
            storage_dir=Path("embeddings/"),
            model_name=model_name
        )
    except ValueError as e:
        print(f"Error: {e}")
        return

    results = pipeline.find_similar(args.query, top_k=args.top_k)
    
    if not results:
        print(f"No embeddings found for model '{model_name}'.")
        print(f"Run: uv run main.py process --model {model_name}")
        return
    
    if args.json:
        # Enhance results with three-way note references
        enhanced_results = []
        for result in results:
            rel_path = result['relative_path']
            # Remove .md extension for URI and wiki link
            path_no_ext = rel_path.rsplit('.md', 1)[0] if rel_path.endswith('.md') else rel_path
            title = result.get('title', path_no_ext.split('/')[-1])
            
            enhanced_result = dict(result)  # Copy original result
            enhanced_result.update({
                "obsidian_uri": f"obsidian://vault/{vault_name}/{quote(path_no_ext)}",
                "wiki_link": f"[[{title}]]",
                "file_path": str(vault_root / rel_path)
            })
            enhanced_results.append(enhanced_result)
        
        output = {
            "query": args.query,
            "results": enhanced_results
        }
        print(json.dumps(output, indent=2))
    else:
        # Compact human-readable output with Obsidian URIs
        print(f"{len(results)} results for '{args.query}':\n")
        
        for i, result in enumerate(results, 1):
            rel_path = result['relative_path']
            path_no_ext = rel_path.rsplit('.md', 1)[0] if rel_path.endswith('.md') else rel_path
            title = result.get('title', path_no_ext.split('/')[-1])
            uri = f"obsidian://vault/{vault_name}/{quote(path_no_ext)}"
            
            print(f"{i:2}. {title} ({result['similarity_score']:.3f})")
            print(f"    {uri}")
            if result.get('description'):
                print(f"    {result['description']}")
            if result.get('tags'):
                print(f"    tags: {', '.join(result['tags'])}")
            print()


def cmd_stats(args):
    """Show embedding statistics."""
    from src.embeddings.models import ModelRegistry
    from src.config import ConfigManager
    
    # Show current configuration
    print("Current Configuration:")
    current_default = ModelRegistry.get_default_model()
    print(f"  Default model: {current_default}")
    
    # Show stats for the default model
    pipeline = EmbeddingPipeline(
        vault_root=args.vault,
        storage_dir=Path("embeddings/"),
        model_name=current_default
    )
    
    stats = pipeline.get_stats()
    
    if not stats:
        print(f"\nNo embeddings found for default model '{current_default}'.")
        print(f"Run: uv run main.py process")
        return
    
    print(f"\nEmbedding Statistics (model: {current_default}):")
    print(f"  Total files: {stats.get('total_files', 'unknown')}")
    print(f"  Model: {stats.get('model_info', {}).get('model_name', 'unknown')}")
    print(f"  Embedding dimension: {stats.get('embedding_dim', 'unknown')}")
    print(f"  Average content length: {stats.get('avg_content_length', 0):.0f} chars")
    print(f"  Total unique tags: {stats.get('total_tags', 'unknown')}")
    print(f"  Directories: {stats.get('directories', 'unknown')}")
    if stats.get('created_at'):
        print(f"  Created: {stats['created_at']}")
    
    # Show configuration details
    try:
        config_manager = ConfigManager()
        print(f"\n{config_manager.get_config_summary()}")
    except Exception as e:
        print(f"\nConfiguration: Error loading config ({e})")


def cmd_visualize(args):
    """Generate knowledge graph visualization."""
    visualizer = PersonalKnowledgeGraphVisualizer(
        vault_root=args.vault,
        embeddings_dir=Path("embeddings/")
    )
    
    try:
        output_file = visualizer.create_html_visualization(
            output_path=Path("visualizations/knowledge_graph.html"),
            title="Personal Knowledge Graph",
            similarity_threshold=args.threshold,
            num_clusters=args.clusters
        )
        
        print(f"Knowledge graph visualization created: {output_file}")
        print("Open in browser to explore your knowledge connections!")
        
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Failed to create visualization: {e}")


def cmd_models(args):
    """List available embedding models and show which ones we have generated."""
    from pathlib import Path
    import json
    import os
    
    if args.model:
        # Show detailed info for specific model
        print(ModelRegistry.format_model_info(args.model))
        
        # Check if we have embeddings for this model
        embeddings_dir = Path("embeddings/")
        if args.model == ModelRegistry.get_default_model():
            embedding_path = embeddings_dir / "metadata.json"
        else:
            embedding_path = embeddings_dir / args.model / "metadata.json"
        
        if embedding_path.exists():
            try:
                with open(embedding_path, 'r') as f:
                    metadata = json.load(f)
                print(f"\n✓ Embeddings generated: {len(metadata)} files")
                print(f"  Storage location: {embedding_path.parent}")
                
                # Show some stats
                if metadata:
                    avg_length = sum(m.get('content_length', 0) for m in metadata) / len(metadata)
                    total_tags = len(set(tag for m in metadata for tag in m.get('tags', [])))
                    print(f"  Average content length: {avg_length:.0f} characters")
                    print(f"  Total unique tags: {total_tags}")
                    
                    # Show file type distribution
                    dirs = {}
                    for m in metadata:
                        dir_name = Path(m['relative_path']).parts[0] if '/' in m['relative_path'] else 'root'
                        dirs[dir_name] = dirs.get(dir_name, 0) + 1
                    
                    print("  File distribution by directory:")
                    for dir_name, count in sorted(dirs.items(), key=lambda x: x[1], reverse=True)[:10]:
                        print(f"    {dir_name}: {count} files")
                        
            except Exception as e:
                print(f"\n✗ Error reading embeddings: {e}")
        else:
            print(f"\n✗ No embeddings found for model '{args.model}'")
            print(f"  Run: uv run main.py process --model {args.model}")
        
        # Show compatible models for comparison
        compatible = ModelRegistry.suggest_models(args.model)
        if compatible:
            print("\nCompatible models for comparison:")
            for spec in compatible:
                print(f"  • {spec.name} - {spec.description}")
    else:
        # Get embedding status for all models
        embeddings_dir = Path("embeddings/")
        embedding_status = {}
        
        # Check default model (stored in embeddings/)
        default_model = ModelRegistry.get_default_model()
        if (embeddings_dir / "metadata.json").exists():
            try:
                with open(embeddings_dir / "metadata.json", 'r') as f:
                    metadata = json.load(f)
                size_mb = (embeddings_dir / "embeddings.npy").stat().st_size / (1024 * 1024)
                embedding_status[default_model] = (len(metadata), size_mb)
            except Exception:
                pass
        
        # Check alternative models (stored in embeddings/model-name/)
        if embeddings_dir.exists():
            for model_dir in embeddings_dir.iterdir():
                if model_dir.is_dir() and (model_dir / "metadata.json").exists():
                    model_name = model_dir.name
                    if ModelRegistry.validate_model(model_name):
                        try:
                            with open(model_dir / "metadata.json", 'r') as f:
                                metadata = json.load(f)
                            size_mb = (model_dir / "embeddings.npy").stat().st_size / (1024 * 1024)
                            embedding_status[model_name] = (len(metadata), size_mb)
                        except Exception:
                            pass
        
        # Create consolidated table
        print("Embedding Models:")
        print(f"{'Model':<26} {'Dim':<4} {'Speed':<7} {'Quality':<8} {'Files':<6} {'Size':<7} {'Status'}")
        print("-" * 85)
        
        # Get all model specs and sort them
        all_models = ModelRegistry.list_models()
        for spec in sorted(all_models.values(), key=lambda x: x.name):
            model_name = spec.name
            
            # Get embedding info if available
            if model_name in embedding_status:
                file_count, size_mb = embedding_status[model_name]
                files_str = str(file_count)
                size_str = f"{size_mb:.1f}MB"
            else:
                files_str = "-"
                size_str = "-"
            
            # Status column
            status_parts = []
            if model_name in embedding_status:
                status_parts.append("✓")
            else:
                status_parts.append("✗")
            if model_name == default_model:
                status_parts.append("default")
            
            status = " ".join(status_parts)
            
            print(f"{model_name:<26} {spec.dimensions:<4} {spec.speed:<7} {spec.quality:<8} {files_str:<6} {size_str:<7} {status}")
        
        print(f"\nUse --model <name> for detailed information about a specific model.")


def cmd_set_default_model(args):
    """Set the default embedding model."""
    from src.embeddings.models import ModelRegistry

    if not ModelRegistry.validate_model(args.model_name):
        print(f"Error: Unknown model '{args.model_name}'")
        print("Available models:")
        print(ModelRegistry.format_model_table())
        return

    if ModelRegistry.set_default_model(args.model_name):
        print(f"✓ Default model set to: {args.model_name}")

        # Show model info
        print(ModelRegistry.format_model_info(args.model_name))
    else:
        print(f"✗ Failed to set default model to: {args.model_name}")


def cmd_set_vault(args):
    """Set the default vault path."""
    from src.config import ConfigManager

    vault_path = Path(args.vault_path).expanduser().resolve()

    # Check if path exists
    if not vault_path.exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        return

    if not vault_path.is_dir():
        print(f"Error: Vault path is not a directory: {vault_path}")
        return

    config = ConfigManager()
    if config.set_vault_path(vault_path):
        print(f"✓ Vault path set to: {vault_path}")
        print(f"\nYou can now run commands without the --vault flag:")
        print(f"  uv run main.py search \"query\"")
        print(f"  uv run main.py archaeology \"AI\"")
    else:
        print(f"✗ Failed to set vault path")


def cmd_archaeology(args):
    """Trace interest evolution over time."""
    import json
    from datetime import date
    from src.embeddings.models import ModelRegistry

    # Get vault name for URIs
    vault_name = get_vault_name(args.vault)
    vault_root = args.vault

    # Use configured default if no model specified
    model_name = args.model or ModelRegistry.get_default_model()

    # Validate model first
    if not ModelRegistry.validate_model(model_name):
        print(f"Error: Unknown model '{model_name}'")
        print("Available models:")
        print(ModelRegistry.format_model_table())
        return

    try:
        archaeologist = TemporalArchaeologist(
            vault_root=vault_root,
            embeddings_dir=Path("embeddings/"),
            model_name=model_name
        )
    except ValueError as e:
        print(f"Error: {e}")
        print(f"Run: uv run main.py process --model {model_name}")
        return
    
    timeline = archaeologist.trace_interest(args.query, threshold=args.threshold, 
                                            exclude_daily=getattr(args, 'exclude_daily', False))
    
    if args.json:
        # JSON output - convert dates to strings and add three-way note references
        serializable_timeline = timeline._asdict()
        # Convert entries with enhanced note references
        enhanced_entries = []
        for entry_date, content, score in timeline.entries:
            path_no_ext = content.rsplit('.md', 1)[0] if content.endswith('.md') else content
            title = path_no_ext.split('/')[-1]
            
            enhanced_entries.append({
                "date": entry_date.isoformat(),
                "similarity_score": score,
                "obsidian_uri": f"obsidian://vault/{vault_name}/{quote(path_no_ext)}",
                "wiki_link": f"[[{title}]]",
                "file_path": str(vault_root / content)
            })
        
        serializable_timeline['entries'] = enhanced_entries
        
        output = {
            "query": args.query,
            "threshold": args.threshold,
            "timeline": serializable_timeline
        }
        print(json.dumps(output, indent=2))
    else:
        # Compact ASCII timeline output with Obsidian URIs
        if timeline.entries:
            print(f"Interest evolution for '{args.query}' (threshold {args.threshold}):\n")
            ascii_output = archaeologist.ascii_timeline(timeline, width=args.width)
            print(ascii_output)
            
            # Add compact URI list after timeline
            print("\nNote links:")
            for i, (entry_date, content, score) in enumerate(timeline.entries, 1):
                path_no_ext = content.rsplit('.md', 1)[0] if content.endswith('.md') else content
                title = path_no_ext.split('/')[-1]
                uri = f"obsidian://vault/{vault_name}/{quote(path_no_ext)}"
                print(f"{i:2}. {entry_date} - {title} ({score:.3f})")
                print(f"    {uri}")
        else:
            print(f"No entries found for '{args.query}' above threshold {args.threshold}")


def main():
    """Main CLI entry point."""
    from src.config import ConfigManager

    parser = argparse.ArgumentParser(description="Synthesis Project - Semantic Embeddings")
    parser.add_argument("--vault", type=Path, default=None,
                       help="Path to Obsidian vault root (overrides configured default)")
    parser.add_argument("--log-level", default="WARNING",
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--verbose", action="store_true",
                       help="Enable detailed logging output")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    process_parser = subparsers.add_parser("process", help="Generate embeddings for vault")
    process_parser.add_argument("--force", action="store_true", 
                               help="Force rebuild even if embeddings exist")
    process_parser.add_argument("--model", default=None,
                               help="Sentence transformer model name (default: configured default)")
    process_parser.add_argument("--limit", type=int,
                               help="Limit number of files for testing")
    process_parser.add_argument("--strategic", action="store_true",
                               help="Use strategic subset (~200 files) for development")
    
    search_parser = subparsers.add_parser("search", help="Search for similar content")
    search_parser.add_argument("query", help="Text to search for")
    search_parser.add_argument("--top-k", type=int, default=10,
                              help="Number of results to return")
    search_parser.add_argument("--json", action="store_true",
                              help="Output results in JSON format")
    search_parser.add_argument("--model", default=None,
                              help="Sentence transformer model name (default: configured default)")
    
    stats_parser = subparsers.add_parser("stats", help="Show embedding statistics")
    
    models_parser = subparsers.add_parser("models", help="List available embedding models")
    models_parser.add_argument("--model", help="Show detailed information for specific model")
    
    set_default_parser = subparsers.add_parser("set-default-model", help="Set the default embedding model")
    set_default_parser.add_argument("model_name", help="Name of the model to set as default")

    set_vault_parser = subparsers.add_parser("set-vault", help="Set the default vault path")
    set_vault_parser.add_argument("vault_path", help="Path to the Obsidian vault")

    visualize_parser = subparsers.add_parser("visualize", help="Generate knowledge graph visualization")
    visualize_parser.add_argument("--threshold", type=float, default=0.3,
                                 help="Similarity threshold for connections (0.0-1.0)")
    visualize_parser.add_argument("--clusters", type=int, default=8,
                                 help="Number of clusters for grouping")
    
    archaeology_parser = subparsers.add_parser("archaeology", help="Trace interest evolution over time")
    archaeology_parser.add_argument("query", help="Interest to trace (e.g., 'AI', 'writing')")
    archaeology_parser.add_argument("--threshold", type=float, default=0.2,
                                   help="Similarity threshold (default: 0.2)")
    archaeology_parser.add_argument("--width", type=int, default=80,
                                   help="ASCII timeline width (default: 80)")
    archaeology_parser.add_argument("--json", action="store_true",
                                   help="Output results in JSON format")
    archaeology_parser.add_argument("--model", default=None,
                                   help="Sentence transformer model name (default: configured default)")
    archaeology_parser.add_argument("--exclude-daily", action="store_true",
                                   help="Exclude daily notes from archaeology results")
    
    args = parser.parse_args()

    # Resolve vault path from config or CLI arg
    if args.vault is None and args.command not in ["set-vault", None]:
        config = ConfigManager()
        configured_vault = config.get_vault_path()
        if configured_vault is None:
            print("Error: No vault path configured.")
            print("Please set the vault path first:")
            print("  uv run main.py set-vault ~/Obsidian/amoxtli")
            print("\nOr specify it with --vault flag:")
            print("  uv run main.py --vault ~/Obsidian/amoxtli <command>")
            return
        args.vault = configured_vault

    # Default to quiet mode unless verbose is requested
    quiet_mode = not args.verbose
    setup_logging(args.log_level, quiet=quiet_mode)

    if args.command == "process":
        cmd_process(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "models":
        cmd_models(args)
    elif args.command == "set-default-model":
        cmd_set_default_model(args)
    elif args.command == "set-vault":
        cmd_set_vault(args)
    elif args.command == "visualize":
        cmd_visualize(args)
    elif args.command == "archaeology":
        cmd_archaeology(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()