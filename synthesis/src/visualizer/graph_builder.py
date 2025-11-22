"""
Knowledge graph builder for the Personal Knowledge Graph Visualizer.
"""
import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from pathlib import Path

logger = logging.getLogger(__name__)


class GraphNode:
    """Represents a node in the knowledge graph."""
    
    def __init__(
        self, 
        node_id: str,
        title: str,
        relative_path: str,
        cluster: int,
        x: float, 
        y: float,
        tags: List[str] = None,
        content_length: int = 0,
        created_date: str = None
    ):
        self.id = node_id
        self.title = title
        self.relative_path = relative_path
        self.cluster = cluster
        self.x = x
        self.y = y
        self.tags = tags or []
        self.content_length = content_length
        self.created_date = created_date
        self.domain = self._extract_domain()
    
    def _extract_domain(self) -> str:
        """Extract domain category from file path."""
        path = self.relative_path.lower()
        if "/daily/" in path:
            return "daily"
        elif "/reference/tech/" in path:
            return "tech"
        elif "/reference/culture/" in path:
            return "culture"
        elif "/l/" in path:
            return "personal"
        elif "/reference/" in path:
            return "reference"
        else:
            return "other"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "relative_path": self.relative_path,
            "cluster": int(self.cluster),
            "x": float(self.x),
            "y": float(self.y),
            "tags": self.tags,
            "content_length": self.content_length,
            "created_date": self.created_date,
            "domain": self.domain
        }


class GraphEdge:
    """Represents an edge (connection) in the knowledge graph."""
    
    def __init__(self, source: str, target: str, similarity: float):
        self.source = source
        self.target = target
        self.similarity = similarity
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": self.source,
            "target": self.target,
            "similarity": float(self.similarity)
        }


class KnowledgeGraphBuilder:
    """Builds knowledge graphs from embedding data."""
    
    def __init__(self):
        """Initialize the graph builder."""
        self.nodes = []
        self.edges = []
        logger.info("KnowledgeGraphBuilder initialized")
    
    def create_graph(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict],
        similarity_threshold: float = 0.3,
        max_connections_per_node: int = 5,
        num_clusters: int = 8
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Create knowledge graph from embeddings and metadata.
        
        Args:
            embeddings: Array of embedding vectors
            metadata: List of metadata dicts for each embedding
            similarity_threshold: Minimum similarity for creating edges
            max_connections_per_node: Maximum edges per node
            num_clusters: Number of clusters for grouping
            
        Returns:
            Tuple of (nodes, edges)
        """
        logger.info(f"Creating knowledge graph from {len(embeddings)} embeddings")
        
        # Create 2D coordinates using PCA
        coordinates = self._create_2d_layout(embeddings)
        
        # Cluster embeddings
        clusters = self._cluster_embeddings(embeddings, num_clusters)
        
        # Create nodes
        nodes = self._create_nodes(metadata, coordinates, clusters)
        
        # Create edges based on similarity
        edges = self._create_edges(
            embeddings, 
            nodes, 
            similarity_threshold, 
            max_connections_per_node
        )
        
        logger.info(f"Created graph with {len(nodes)} nodes and {len(edges)} edges")
        return nodes, edges
    
    def _create_2d_layout(self, embeddings: np.ndarray) -> np.ndarray:
        """Create 2D coordinates from high-dimensional embeddings using PCA."""
        logger.info("Creating 2D layout with PCA")
        pca = PCA(n_components=2, random_state=42)
        coordinates_2d = pca.fit_transform(embeddings)
        
        # Normalize to reasonable coordinate range
        coordinates_2d = (coordinates_2d - coordinates_2d.min()) / (coordinates_2d.max() - coordinates_2d.min())
        coordinates_2d = coordinates_2d * 800 + 100  # Scale to 100-900 range
        
        return coordinates_2d
    
    def _cluster_embeddings(self, embeddings: np.ndarray, num_clusters: int) -> np.ndarray:
        """Cluster embeddings to identify topic groups."""
        logger.info(f"Clustering embeddings into {num_clusters} clusters")
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(embeddings)
        return clusters
    
    def _create_nodes(
        self, 
        metadata: List[Dict], 
        coordinates: np.ndarray, 
        clusters: np.ndarray
    ) -> List[GraphNode]:
        """Create graph nodes from metadata and layout information."""
        nodes = []
        
        for i, meta in enumerate(metadata):
            node_id = f"node_{i}"
            title = meta.get("title", Path(meta["relative_path"]).stem)
            
            node = GraphNode(
                node_id=node_id,
                title=title,
                relative_path=meta["relative_path"],
                cluster=int(clusters[i]),
                x=float(coordinates[i][0]),
                y=float(coordinates[i][1]),
                tags=meta.get("tags", []),
                content_length=meta.get("content_length", 0),
                created_date=meta.get("created_date")
            )
            nodes.append(node)
        
        return nodes
    
    def _create_edges(
        self,
        embeddings: np.ndarray,
        nodes: List[GraphNode], 
        similarity_threshold: float,
        max_connections_per_node: int
    ) -> List[GraphEdge]:
        """Create edges between similar nodes."""
        edges = []
        
        for i, node_a in enumerate(nodes):
            similarities = []
            
            # Calculate similarity to all other nodes
            for j, node_b in enumerate(nodes):
                if i != j:
                    similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                    similarities.append((j, similarity))
            
            # Sort by similarity and take top connections
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_connections = similarities[:max_connections_per_node]
            
            # Create edges above threshold
            for j, similarity in top_connections:
                if similarity >= similarity_threshold:
                    edge = GraphEdge(
                        source=node_a.id,
                        target=nodes[j].id,
                        similarity=similarity
                    )
                    edges.append(edge)
        
        return edges
    
    def _cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    
    def get_cluster_info(self, nodes: List[GraphNode]) -> Dict[int, Dict]:
        """Get information about each cluster."""
        cluster_info = {}
        
        for node in nodes:
            cluster_id = node.cluster
            if cluster_id not in cluster_info:
                cluster_info[cluster_id] = {
                    "nodes": [],
                    "domains": set(),
                    "tags": set(),
                    "size": 0
                }
            
            cluster_info[cluster_id]["nodes"].append(node.title)
            cluster_info[cluster_id]["domains"].add(node.domain)
            cluster_info[cluster_id]["tags"].update(node.tags)
            cluster_info[cluster_id]["size"] += 1
        
        # Convert sets to lists for JSON serialization
        for cluster_id in cluster_info:
            cluster_info[cluster_id]["domains"] = list(cluster_info[cluster_id]["domains"])
            cluster_info[cluster_id]["tags"] = list(cluster_info[cluster_id]["tags"])
        
        return cluster_info