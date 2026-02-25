"""
Mindmap Database Layer - Generalized for Any Agent
Provides SQLite storage with semantic embeddings and graph relationships
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np

class MindMapDB:
    def __init__(self, db_path: str, embedding_model: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the mindmap database
        
        Args:
            db_path: Path to SQLite database file
            embedding_model: Sentence transformer model name for embeddings
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Load embedding model
        print(f"Loading embedding model: {embedding_model}...")
        self.model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Embedding dimension: {self.embedding_dim}")
        
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()
        
        # Nodes table with embeddings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                tags TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                embedding BLOB NOT NULL
            )
        """)
        
        # Edges table for relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship TEXT NOT NULL,
                created_at TEXT NOT NULL,
                semantic_strength REAL DEFAULT 0.0,
                FOREIGN KEY (source_id) REFERENCES nodes(id),
                FOREIGN KEY (target_id) REFERENCES nodes(id),
                UNIQUE(source_id, target_id, relationship)
            )
        """)
        
        # Access logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT NOT NULL,
                accessed_at TEXT NOT NULL,
                access_type TEXT NOT NULL,
                FOREIGN KEY (node_id) REFERENCES nodes(id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_tags ON nodes(tags)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_node ON access_logs(node_id)")
        
        self.conn.commit()
    
    def _serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """Convert numpy array to bytes for storage"""
        return embedding.tobytes()
    
    def _deserialize_embedding(self, blob: bytes) -> np.ndarray:
        """Convert bytes back to numpy array"""
        return np.frombuffer(blob, dtype=np.float32)
    
    def insert_node(self, node_id: str, content: str, tags: List[str], 
                   priority: str = "normal") -> Dict:
        """
        Insert a new node with semantic embedding
        
        Args:
            node_id: Unique identifier for the node
            content: Text content of the memory
            tags: List of semantic tags
            priority: Priority level (critical, high, normal, low)
            
        Returns:
            Dict with node_id and suggested connections
        """
        # Generate embedding
        embedding = self.model.encode(content, convert_to_numpy=True)
        embedding_blob = self._serialize_embedding(embedding)
        
        # Insert node
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO nodes (id, content, tags, priority, created_at, embedding)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            content,
            json.dumps(tags),
            priority,
            datetime.now().isoformat(),
            embedding_blob
        ))
        self.conn.commit()
        
        # Find similar nodes for auto-connection suggestions
        suggestions = self._find_similar_nodes(embedding, node_id, top_k=5, threshold=0.5)
        
        return {
            "node_id": node_id,
            "suggested_connections": suggestions
        }
    
    def _find_similar_nodes(self, query_embedding: np.ndarray, exclude_id: str, 
                           top_k: int = 5, threshold: float = 0.5) -> List[Dict]:
        """Find nodes semantically similar to query embedding"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, content, tags, embedding FROM nodes WHERE id != ?", (exclude_id,))
        
        similarities = []
        for row in cursor.fetchall():
            node_embedding = self._deserialize_embedding(row['embedding'])
            similarity = float(np.dot(query_embedding, node_embedding) / 
                             (np.linalg.norm(query_embedding) * np.linalg.norm(node_embedding)))
            
            if similarity >= threshold:
                similarities.append({
                    "node_id": row['id'],
                    "content": row['content'][:100] + "..." if len(row['content']) > 100 else row['content'],
                    "tags": json.loads(row['tags']),
                    "similarity": round(similarity, 3)
                })
        
        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def search_nodes(self, query: str, tags: Optional[List[str]] = None, 
                    top_k: int = 5) -> List[Dict]:
        """
        Search nodes by semantic similarity
        
        Args:
            query: Search query
            tags: Optional tag filter
            top_k: Number of results to return
            
        Returns:
            List of matching nodes with similarity scores
        """
        # Generate query embedding
        query_embedding = self.model.encode(query, convert_to_numpy=True)
        
        # Build SQL query with optional tag filter
        sql = "SELECT id, content, tags, priority, access_count, embedding FROM nodes"
        params = []
        
        if tags:
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
            sql += f" WHERE ({tag_conditions})"
            params = [f'%"{tag}"%' for tag in tags]
        
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        
        # Calculate similarities
        results = []
        for row in cursor.fetchall():
            node_embedding = self._deserialize_embedding(row['embedding'])
            similarity = float(np.dot(query_embedding, node_embedding) / 
                             (np.linalg.norm(query_embedding) * np.linalg.norm(node_embedding)))
            
            results.append({
                "node_id": row['id'],
                "content": row['content'],
                "tags": json.loads(row['tags']),
                "priority": row['priority'],
                "similarity": round(similarity, 3),
                "access_count": row['access_count']
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Log access for top results
        for result in results[:top_k]:
            self._log_access(result['node_id'], 'search')
        
        return results[:top_k]
    
    def connect_nodes(self, source_id: str, target_id: str, 
                     relationship: str) -> Dict:
        """
        Create a relationship between two nodes
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship: Type of relationship (builds_on, supports, etc.)
            
        Returns:
            Dict with connection details
        """
        # Calculate semantic strength
        cursor = self.conn.cursor()
        cursor.execute("SELECT embedding FROM nodes WHERE id IN (?, ?)", 
                      (source_id, target_id))
        rows = cursor.fetchall()
        
        if len(rows) != 2:
            raise ValueError("One or both nodes not found")
        
        emb1 = self._deserialize_embedding(rows[0]['embedding'])
        emb2 = self._deserialize_embedding(rows[1]['embedding'])
        semantic_strength = float(np.dot(emb1, emb2) / 
                                 (np.linalg.norm(emb1) * np.linalg.norm(emb2)))
        
        # Insert edge
        cursor.execute("""
            INSERT OR IGNORE INTO edges (source_id, target_id, relationship, created_at, semantic_strength)
            VALUES (?, ?, ?, ?, ?)
        """, (source_id, target_id, relationship, datetime.now().isoformat(), semantic_strength))
        self.conn.commit()
        
        return {
            "source_id": source_id,
            "target_id": target_id,
            "relationship": relationship,
            "semantic_strength": round(semantic_strength, 3)
        }
    
    def navigate_node(self, node_id: str) -> Dict:
        """
        Get a node and all its connections
        
        Args:
            node_id: Node to navigate to
            
        Returns:
            Dict with node content and all connected nodes
        """
        cursor = self.conn.cursor()
        
        # Get node
        cursor.execute("SELECT * FROM nodes WHERE id = ?", (node_id,))
        node_row = cursor.fetchone()
        
        if not node_row:
            raise ValueError(f"Node {node_id} not found")
        
        # Get outgoing connections
        cursor.execute("""
            SELECT e.target_id, e.relationship, e.semantic_strength, n.content, n.tags
            FROM edges e
            JOIN nodes n ON e.target_id = n.id
            WHERE e.source_id = ?
        """, (node_id,))
        outgoing = [dict(row) for row in cursor.fetchall()]
        
        # Get incoming connections
        cursor.execute("""
            SELECT e.source_id, e.relationship, e.semantic_strength, n.content, n.tags
            FROM edges e
            JOIN nodes n ON e.source_id = n.id
            WHERE e.target_id = ?
        """, (node_id,))
        incoming = [dict(row) for row in cursor.fetchall()]
        
        # Log access
        self._log_access(node_id, 'navigate')
        
        # Update access count
        cursor.execute("UPDATE nodes SET access_count = access_count + 1 WHERE id = ?", (node_id,))
        self.conn.commit()
        
        return {
            "node": {
                "id": node_row['id'],
                "content": node_row['content'],
                "tags": json.loads(node_row['tags']),
                "priority": node_row['priority'],
                "created_at": node_row['created_at'],
                "access_count": node_row['access_count'] + 1
            },
            "outgoing_connections": outgoing,
            "incoming_connections": incoming
        }
    
    def get_stats(self) -> Dict:
        """Get statistics about the mindmap"""
        cursor = self.conn.cursor()
        
        # Total counts
        cursor.execute("SELECT COUNT(*) as count FROM nodes")
        node_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM edges")
        edge_count = cursor.fetchone()['count']
        
        # Most connected node
        cursor.execute("""
            SELECT n.id, n.content, COUNT(e.id) as connection_count
            FROM nodes n
            LEFT JOIN edges e ON n.id = e.source_id OR n.id = e.target_id
            GROUP BY n.id
            ORDER BY connection_count DESC
            LIMIT 1
        """)
        most_connected = cursor.fetchone()
        
        # Most accessed node
        cursor.execute("""
            SELECT id, content, access_count
            FROM nodes
            ORDER BY access_count DESC
            LIMIT 1
        """)
        most_accessed = cursor.fetchone()
        
        return {
            "total_nodes": node_count,
            "total_edges": edge_count,
            "most_connected_node": dict(most_connected) if most_connected else None,
            "most_accessed_node": dict(most_accessed) if most_accessed else None
        }
    
    def _log_access(self, node_id: str, access_type: str):
        """Log node access"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO access_logs (node_id, accessed_at, access_type)
            VALUES (?, ?, ?)
        """, (node_id, datetime.now().isoformat(), access_type))
        self.conn.commit()
    
    def get_all_nodes(self) -> List[Dict]:
        """Get all nodes for visualization"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, content, tags, priority, access_count FROM nodes")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_edges(self) -> List[Dict]:
        """Get all edges for visualization"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT source_id, target_id, relationship, semantic_strength FROM edges")
        return [dict(row) for row in cursor.fetchall()]
