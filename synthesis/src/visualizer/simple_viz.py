"""
Simple static visualization for debugging.
"""
import json
from pathlib import Path
from .visualizer import PersonalKnowledgeGraphVisualizer


def create_simple_html(graph_data: dict, output_path: Path):
    """Create simple static HTML visualization for debugging."""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Debug Knowledge Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: white; }}
        #graph {{ width: 1200px; height: 800px; border: 1px solid #666; background: #000; }}
        .node {{ cursor: pointer; }}
        .node:hover {{ stroke-width: 3px; }}
        .link {{ stroke: #666; stroke-opacity: 0.3; }}
    </style>
</head>
<body>
    <h1>Debug Personal Knowledge Graph</h1>
    <p>Nodes: {len(graph_data['nodes'])}, Edges: {len(graph_data['edges'])}</p>
    
    <div id="graph"></div>
    
    <script>
        const data = {json.dumps(graph_data, indent=2)};
        console.log('Data loaded:', data.metadata);
        console.log('Sample node:', data.nodes[0]);
        console.log('Sample edge:', data.edges[0]);
        
        const width = 1200;
        const height = 800;
        
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        // First, just draw nodes as static circles
        console.log('Drawing nodes...');
        const nodes = svg.selectAll("circle")
            .data(data.nodes)
            .enter()
            .append("circle")
            .attr("cx", d => d.x)
            .attr("cy", d => d.y)
            .attr("r", 5)
            .attr("fill", d => d3.schemeCategory10[d.cluster])
            .attr("stroke", "white")
            .attr("stroke-width", 1);
        
        console.log('Nodes created:', nodes.size());
        
        // Add simple labels
        const labels = svg.selectAll("text")
            .data(data.nodes.slice(0, 20)) // Only first 20 labels
            .enter()
            .append("text")
            .attr("x", d => d.x + 8)
            .attr("y", d => d.y + 4)
            .text(d => d.title.substring(0, 15))
            .attr("font-size", "10px")
            .attr("fill", "white");
        
        console.log('Labels created:', labels.size());
        
        // Simple click handler
        nodes.on("click", function(event, d) {{
            console.log('Clicked node:', d);
            alert(`${{d.title}}\\nCluster: ${{d.cluster}}\\nDomain: ${{d.domain}}`);
        }});
        
        console.log('Visualization complete');
    </script>
</body>
</html>"""
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"Debug visualization created: {output_path}")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import ConfigManager

    config = ConfigManager()
    vault_root = config.get_vault_path()

    if vault_root is None:
        print("Error: No vault path configured.")
        print("Please set the vault path first:")
        print("  uv run main.py set-vault ~/Obsidian/amoxtli")
        sys.exit(1)

    visualizer = PersonalKnowledgeGraphVisualizer(
        vault_root=vault_root,
        embeddings_dir=Path("embeddings/")
    )

    graph_data = visualizer.generate_graph_data(similarity_threshold=0.5, num_clusters=5)
    create_simple_html(graph_data, Path("visualizations/debug_graph.html"))