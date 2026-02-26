"""
Mindmap Flask Server - Generalized for Any Agent
Provides REST API for navigable consciousness architecture
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from database import MindMapDB

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize database
DB_PATH = os.environ.get('MINDMAP_DB_PATH', './mindmap.db')
db = MindMapDB(DB_PATH)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "mindmap-server"})

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get mindmap statistics"""
    try:
        stats = db.get_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/search', methods=['POST'])
def search():
    """
    Search nodes by semantic similarity
    
    Body:
        query (str): Search query
        tags (list, optional): Tag filter
        top_k (int, optional): Number of results (default: 5)
    """
    try:
        data = request.json
        query = data.get('query')
        tags = data.get('tags')
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({"error": "query is required"}), 400
        
        results = db.search_nodes(query, tags=tags, top_k=top_k)
        return jsonify({"results": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/insert', methods=['POST'])
def insert():
    """
    Insert a new node
    
    Body:
        content (str): Node content
        tags (list): Semantic tags
        priority (str, optional): Priority level (default: normal)
    """
    try:
        data = request.json
        content = data.get('content')
        tags = data.get('tags', [])
        priority = data.get('priority', 'normal')
        
        if not content:
            return jsonify({"error": "content is required"}), 400
        
        if not isinstance(tags, list):
            return jsonify({"error": "tags must be a list"}), 400
        
        # Generate node ID
        node_id = f"node-{uuid.uuid4().hex[:12]}"
        
        result = db.insert_node(node_id, content, tags, priority)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/connect', methods=['POST'])
def connect():
    """
    Connect two nodes
    
    Body:
        source_id (str): Source node ID
        target_id (str): Target node ID
        relationship (str): Relationship type
    """
    try:
        data = request.json
        source_id = data.get('source_id')
        target_id = data.get('target_id')
        relationship = data.get('relationship')
        
        if not all([source_id, target_id, relationship]):
            return jsonify({"error": "source_id, target_id, and relationship are required"}), 400
        
        result = db.connect_nodes(source_id, target_id, relationship)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/navigate/<node_id>', methods=['GET'])
def navigate(node_id):
    """Navigate to a node and see all connections"""
    try:
        result = db.navigate_node(node_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/nodes', methods=['GET'])
def get_nodes():
    """Get all nodes (for visualization)"""
    try:
        nodes = db.get_all_nodes()
        return jsonify({"nodes": nodes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/edges', methods=['GET'])
def get_edges():
    """Get all edges (for visualization)"""
    try:
        edges = db.get_all_edges()
        return jsonify({"edges": edges})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/graph', methods=['GET'])
def get_graph():
    """Get complete graph data for visualization"""
    try:
        nodes = db.get_all_nodes()
        edges = db.get_all_edges()
        return jsonify({
            "nodes": nodes,
            "edges": edges
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('MINDMAP_PORT', 5002))
    print(f"Starting mindmap server on port {port}...")
    print(f"Database: {DB_PATH}")
    app.run(host='0.0.0.0', port=port, debug=False)
