"""
Personal Knowledge Graph Visualizer for the Synthesis Project.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..embeddings import EmbeddingPipeline
from .graph_builder import KnowledgeGraphBuilder, GraphNode, GraphEdge

logger = logging.getLogger(__name__)


class PersonalKnowledgeGraphVisualizer:
    """Main visualizer for creating interactive knowledge graph visualizations."""
    
    def __init__(self, vault_root: Path, embeddings_dir: Path):
        """Initialize visualizer with vault and embeddings paths."""
        self.vault_root = Path(vault_root)
        self.embeddings_dir = Path(embeddings_dir)
        self.pipeline = EmbeddingPipeline(vault_root, embeddings_dir)
        self.graph_builder = KnowledgeGraphBuilder()
        
        logger.info(f"Visualizer initialized for {vault_root}")
    
    def generate_graph_data(
        self,
        similarity_threshold: float = 0.3,
        max_connections: int = 5,
        num_clusters: int = 8
    ) -> Dict:
        """Generate graph data for visualization.
        
        Args:
            similarity_threshold: Minimum similarity for creating edges
            max_connections: Maximum edges per node
            num_clusters: Number of clusters for grouping
            
        Returns:
            Dictionary with nodes, edges, and metadata for visualization
        """
        logger.info("Generating knowledge graph data")
        
        # Load embeddings
        embeddings, metadata, index_info = self.pipeline.store.load_embeddings()
        if embeddings is None:
            raise ValueError("No embeddings found. Run 'uv run main.py process --strategic' first.")
        
        # Create graph
        nodes, edges = self.graph_builder.create_graph(
            embeddings, 
            metadata,
            similarity_threshold=similarity_threshold,
            max_connections_per_node=max_connections,
            num_clusters=num_clusters
        )
        
        # Get cluster analysis
        cluster_info = self.graph_builder.get_cluster_info(nodes)
        
        # Prepare visualization data
        graph_data = {
            "nodes": [node.to_dict() for node in nodes],
            "edges": [edge.to_dict() for edge in edges],
            "clusters": cluster_info,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "similarity_threshold": similarity_threshold,
                "num_clusters": num_clusters,
                "embedding_model": index_info.get("model_info", {}).get("model_name") if index_info else "unknown"
            }
        }
        
        logger.info(f"Generated graph: {len(nodes)} nodes, {len(edges)} edges, {len(cluster_info)} clusters")
        return graph_data
    
    def save_graph_data(self, output_path: Path, **kwargs) -> Path:
        """Generate and save graph data to JSON file.
        
        Args:
            output_path: Path to save graph JSON
            **kwargs: Arguments passed to generate_graph_data()
            
        Returns:
            Path to saved file
        """
        graph_data = self.generate_graph_data(**kwargs)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2, default=str)
        
        logger.info(f"Saved graph data to: {output_path}")
        return output_path
    
    def create_html_visualization(
        self, 
        output_path: Path,
        title: str = "Personal Knowledge Graph",
        **kwargs
    ) -> Path:
        """Create complete HTML visualization with embedded data.
        
        Args:
            output_path: Path to save HTML file
            title: Title for the visualization
            **kwargs: Arguments passed to generate_graph_data()
            
        Returns:
            Path to saved HTML file
        """
        graph_data = self.generate_graph_data(**kwargs)
        
        html_content = self._generate_html_template(graph_data, title)
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Created HTML visualization: {output_path}")
        return output_path
    
    def _generate_html_template(self, graph_data: Dict, title: str) -> str:
        """Generate complete HTML with D3.js visualization."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
        }}
        
        #graph {{
            width: 100%;
            height: 80vh;
            border: 1px solid #333;
            background: #111;
        }}
        
        .node {{
            stroke: #fff;
            stroke-width: 1.5px;
            cursor: pointer;
        }}
        
        .node:hover {{
            stroke-width: 3px;
        }}
        
        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
        }}
        
        .info-panel {{
            position: fixed;
            top: 20px;
            right: 20px;
            width: 300px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 15px;
            font-size: 12px;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .cluster-legend {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 15px;
            font-size: 11px;
        }}
        
        .cluster-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        
        .cluster-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div id="graph"></div>
    
    <div class="info-panel">
        <h3>Node Information</h3>
        <div id="node-info">Click a node to see details</div>
    </div>
    
    <div class="cluster-legend">
        <h3>Clusters</h3>
        <div id="cluster-legend"></div>
    </div>

    <script>
        const graphData = {json.dumps(graph_data, indent=2)};
        
        // Color scheme for clusters
        const clusterColors = d3.schemeCategory10;
        
        // Set up SVG
        const width = document.getElementById('graph').clientWidth;
        const height = document.getElementById('graph').clientHeight;
        
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        // Create force simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2));
        
        // Create links
        const links = svg.append("g")
            .selectAll("line")
            .data(graphData.edges)
            .enter()
            .append("line")
            .attr("class", "link")
            .style("stroke-width", d => Math.sqrt(d.similarity) * 2);
        
        // Create nodes
        const nodes = svg.append("g")
            .selectAll("circle")
            .data(graphData.nodes)
            .enter()
            .append("circle")
            .attr("class", "node")
            .attr("r", d => Math.sqrt(d.content_length / 100) + 3)
            .style("fill", d => clusterColors[d.cluster % 10])
            .on("click", function(event, d) {{
                showNodeInfo(d);
            }})
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Add labels
        const labels = svg.append("g")
            .selectAll("text")
            .data(graphData.nodes)
            .enter()
            .append("text")
            .text(d => d.title.length > 20 ? d.title.substring(0, 20) + "..." : d.title)
            .style("font-size", "10px")
            .style("fill", "#ccc")
            .style("text-anchor", "middle");
        
        // Update positions on simulation tick
        simulation.on("tick", () => {{
            links
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            nodes
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            labels
                .attr("x", d => d.x)
                .attr("y", d => d.y - 15);
        }});
        
        // Drag functions
        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}
        
        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}
        
        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
        
        // Show node information
        function showNodeInfo(node) {{
            const infoDiv = document.getElementById('node-info');
            infoDiv.innerHTML = `
                <h4>${{node.title}}</h4>
                <p><strong>Path:</strong> ${{node.relative_path}}</p>
                <p><strong>Domain:</strong> ${{node.domain}}</p>
                <p><strong>Cluster:</strong> ${{node.cluster}}</p>
                <p><strong>Content Length:</strong> ${{node.content_length}} chars</p>
                ${{node.tags.length > 0 ? `<p><strong>Tags:</strong> ${{node.tags.join(', ')}}</p>` : ''}}
                ${{node.created_date ? `<p><strong>Created:</strong> ${{node.created_date}}</p>` : ''}}
            `;
        }}
        
        // Create cluster legend
        function createClusterLegend() {{
            const legendDiv = d3.select('#cluster-legend');
            
            Object.entries(graphData.clusters).forEach(([clusterId, info]) => {{
                const item = legendDiv.append('div').attr('class', 'cluster-item');
                
                item.append('div')
                    .attr('class', 'cluster-color')
                    .style('background-color', clusterColors[clusterId % 10]);
                
                item.append('span')
                    .text(`Cluster ${{clusterId}} (${{info.size}} files): ${{info.domains.join(', ')}}`);
            }});
        }}
        
        createClusterLegend();
        
        console.log('Knowledge graph loaded:', graphData.metadata);
    </script>
</body>
</html>"""
    
    def analyze_clusters(self, nodes: List[GraphNode]) -> Dict:
        """Analyze cluster characteristics for insights."""
        cluster_info = self.get_cluster_info(nodes)
        
        analysis = {
            "cluster_count": len(cluster_info),
            "largest_cluster": max(cluster_info.values(), key=lambda x: x["size"]),
            "domain_distribution": {},
            "cross_domain_clusters": []
        }
        
        # Analyze domain distribution
        for cluster_id, info in cluster_info.items():
            if len(info["domains"]) > 1:
                analysis["cross_domain_clusters"].append({
                    "cluster": cluster_id,
                    "domains": info["domains"],
                    "size": info["size"],
                    "sample_nodes": info["nodes"][:3]
                })
        
        return analysis