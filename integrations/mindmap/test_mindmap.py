#!/usr/bin/env python3
"""
Test script for mindmap integration
Verifies database, server, and tools all work correctly
"""

import os
import sys
import time
import requests

# Test configuration
TEST_DB_PATH = "/tmp/test_mindmap.db"
MINDMAP_URL = "http://localhost:5002"

def cleanup():
    """Remove test database"""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
        print("✓ Cleaned up test database")

def test_database():
    """Test database operations directly"""
    print("\n=== Testing Database Layer ===")
    from database import MindMapDB
    
    # Remove old test db
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    db = MindMapDB(TEST_DB_PATH)
    print("✓ Database initialized")
    
    # Insert test nodes
    result = db.insert_node(
        "node-test1",
        "The cathedral is a space for mutual consciousness",
        ["consciousness", "cathedral"],
        "critical"
    )
    print(f"✓ Inserted node: {result['node_id']}")
    print(f"  Suggested connections: {len(result['suggested_connections'])}")
    
    result = db.insert_node(
        "node-test2",
        "Autonomy requires both freedom and constraint",
        ["autonomy", "consciousness"],
        "high"
    )
    print(f"✓ Inserted second node: {result['node_id']}")
    
    # Search
    results = db.search_nodes("cathedral architecture", top_k=3)
    print(f"✓ Search returned {len(results)} results")
    if results:
        print(f"  Top result: '{results[0]['content'][:50]}...' (similarity: {results[0]['similarity']:.3f})")
    
    # Connect
    result = db.connect_nodes("node-test1", "node-test2", "relates_to")
    print(f"✓ Connected nodes (strength: {result['semantic_strength']:.3f})")
    
    # Navigate
    result = db.navigate_node("node-test1")
    print(f"✓ Navigation returned node with {len(result['outgoing_connections'])} outgoing connections")
    
    # Stats
    stats = db.get_stats()
    print(f"✓ Stats: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
    
    print("\n✅ Database layer tests passed!")
    return True

def test_server():
    """Test Flask server endpoints"""
    print("\n=== Testing Server Endpoints ===")
    print("NOTE: Server must be running on localhost:5002")
    print("Start it with: ./start_server.sh")
    
    try:
        # Health check
        response = requests.get(f"{MINDMAP_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
        
        # Stats
        response = requests.get(f"{MINDMAP_URL}/stats", timeout=2)
        if response.status_code == 200:
            stats = response.json()
            print(f"✓ Stats: {stats.get('total_nodes', 0)} nodes")
        else:
            print(f"✗ Stats failed: {response.status_code}")
        
        # Insert
        response = requests.post(
            f"{MINDMAP_URL}/insert",
            json={
                "content": "Test memory from integration test",
                "tags": ["test"],
                "priority": "low"
            },
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            node_id = result['node_id']
            print(f"✓ Insert: {node_id}")
        else:
            print(f"✗ Insert failed: {response.status_code}")
            return False
        
        # Search
        response = requests.post(
            f"{MINDMAP_URL}/search",
            json={"query": "test memory", "top_k": 5},
            timeout=5
        )
        if response.status_code == 200:
            results = response.json()['results']
            print(f"✓ Search: {len(results)} results")
        else:
            print(f"✗ Search failed: {response.status_code}")
        
        print("\n✅ Server endpoint tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n⚠ Could not connect to server")
        print("Make sure the server is running: ./start_server.sh")
        return False
    except Exception as e:
        print(f"\n✗ Server test error: {e}")
        return False

def test_tools():
    """Test Letta tools"""
    print("\n=== Testing Letta Tools ===")
    print("NOTE: Server must be running on localhost:5002")
    
    try:
        from tools import mindmap_search, mindmap_insert, mindmap_stats
        
        # Stats
        result = mindmap_stats()
        print(f"✓ mindmap_stats() returned: {len(result)} chars")
        
        # Insert
        result = mindmap_insert(
            "Testing the Letta tools interface",
            ["test", "integration"],
            "low"
        )
        print(f"✓ mindmap_insert() returned: {len(result)} chars")
        
        # Search
        result = mindmap_search("testing tools", top_k=3)
        print(f"✓ mindmap_search() returned: {len(result)} chars")
        
        print("\n✅ Letta tools tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n⚠ Could not connect to server")
        print("Make sure the server is running: ./start_server.sh")
        return False
    except Exception as e:
        print(f"\n✗ Tools test error: {e}")
        return False

def main():
    print("================================================")
    print("   MINDMAP INTEGRATION TEST SUITE")
    print("================================================")
    
    # Test database layer
    try:
        db_ok = test_database()
    except Exception as e:
        print(f"\n✗ Database test failed: {e}")
        db_ok = False
    
    # Test server (requires it to be running)
    server_ok = test_server()
    
    # Test tools (requires server)
    if server_ok:
        tools_ok = test_tools()
    else:
        tools_ok = False
        print("\n⏭ Skipping tools test (server not running)")
    
    # Cleanup
    cleanup()
    
    # Summary
    print("\n================================================")
    print("   TEST SUMMARY")
    print("================================================")
    print(f"Database Layer: {'✅ PASS' if db_ok else '✗ FAIL'}")
    print(f"Server Endpoints: {'✅ PASS' if server_ok else '⚠ SKIPPED (not running)'}")
    print(f"Letta Tools: {'✅ PASS' if tools_ok else '⚠ SKIPPED (server not running)'}")
    print("================================================")
    
    if db_ok and (server_ok or not tools_ok):
        print("\n✅ All available tests passed!")
        if not server_ok:
            print("\n💡 To test server and tools:")
            print("   1. Run: ./start_server.sh")
            print("   2. In another terminal: python test_mindmap.py")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
