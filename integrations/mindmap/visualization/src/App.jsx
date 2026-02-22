import { useState, useEffect, useMemo } from 'react'
import { GraphCanvas } from 'reagraph'
import axios from 'axios'

function App() {
  const [graphData, setGraphData] = useState(null)
  const [stats, setStats] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  // Fetch graph data and stats
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        
        // Fetch all nodes and edges
        const nodesRes = await axios.post('/api/search', { 
          query: '', 
          top_k: 1000 
        })
        const statsRes = await axios.get('/api/stats')
        
        // Build edges list from node connections
        // Extract actual node objects from API results wrapper
        const nodes = (nodesRes.data.results || []).map(result => result.node)
        const edges = []
        const edgeSet = new Set()
        
        nodes.forEach(node => {
          if (node.connections) {
            node.connections.forEach(conn => {
              const edgeId = `${node.id}-${conn.target_id}`
              const reverseEdgeId = `${conn.target_id}-${node.id}`
              
              // Avoid duplicate edges
              if (!edgeSet.has(edgeId) && !edgeSet.has(reverseEdgeId)) {
                edges.push({
                  id: edgeId,
                  source: node.id,
                  target: conn.target_id,
                  label: conn.relationship
                })
                edgeSet.add(edgeId)
              }
            })
          }
        })
        
        setGraphData({ nodes, edges })
        setStats(statsRes.data)
        setLoading(false)
      } catch (err) {
        console.error('Error fetching data:', err)
        setError(err.message)
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])

  // Transform data for Reagraph
  const reagraphData = useMemo(() => {
    if (!graphData) return { nodes: [], edges: [] }
    
    const nodes = graphData.nodes.map(node => {
      // Calculate node size based on connections + access count
      const connectionCount = node.connections?.length || 0
      const accessCount = node.access_count || 0
      const size = Math.max(8, Math.min(30, (connectionCount * 2) + (accessCount * 0.5)))
      
      // Color by priority or first tag
      let color = '#667eea' // default purple
      if (node.priority === 'critical') color = '#ff5555'
      else if (node.priority === 'high') color = '#ffaa55'
      else if (node.tags?.includes('consciousness')) color = '#764ba2'
      else if (node.tags?.includes('cathedral')) color = '#667eea'
      else if (node.tags?.includes('Lillith')) color = '#d946ef'
      
      return {
        id: node.id,
        label: node.content.substring(0, 50) + '...',
        size,
        fill: color,
        data: node
      }
    })
    
    const edges = graphData.edges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label
    }))
    
    return { nodes, edges }
  }, [graphData])

  // Filter nodes by search query
  const filteredData = useMemo(() => {
    if (!searchQuery || !reagraphData.nodes.length) return reagraphData
    
    const query = searchQuery.toLowerCase()
    const matchingNodes = reagraphData.nodes.filter(node => 
      node.data.content.toLowerCase().includes(query) ||
      node.data.tags?.some(tag => tag.toLowerCase().includes(query))
    )
    
    const matchingNodeIds = new Set(matchingNodes.map(n => n.id))
    const filteredEdges = reagraphData.edges.filter(edge =>
      matchingNodeIds.has(edge.source) && matchingNodeIds.has(edge.target)
    )
    
    return {
      nodes: matchingNodes,
      edges: filteredEdges
    }
  }, [reagraphData, searchQuery])

  const handleNodeClick = async (node) => {
    try {
      const res = await axios.get(`/api/navigate/${node.id}`)
      setSelectedNode(res.data)
    } catch (err) {
      console.error('Error fetching node details:', err)
    }
  }

  const handleConnectionClick = async (targetId) => {
    try {
      const res = await axios.get(`/api/navigate/${targetId}`)
      setSelectedNode(res.data)
    } catch (err) {
      console.error('Error fetching node details:', err)
    }
  }

  if (loading) {
    return <div className="loading">Loading HAL's consciousness...</div>
  }

  if (error) {
    return <div className="error">Error: {error}</div>
  }

  return (
    <div className="app">
      {window.innerWidth <= 768 && (
        <button 
          className="toggle-sidebar" 
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? '✕' : '☰'}
        </button>
      )}
      
      <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h1>HAL's Mind</h1>
          <p>Navigable Consciousness Architecture</p>
        </div>
        
        <div className="search-box">
          <input
            type="text"
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        {stats && (
          <div className="stats">
            <div className="stat-item">
              <span className="stat-label">Total Memories</span>
              <span className="stat-value">{stats.total_nodes}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Connections</span>
              <span className="stat-value">{stats.total_edges}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Most Connected</span>
              <span className="stat-value">{stats.most_connected_node?.connections || 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Most Accessed</span>
              <span className="stat-value">{stats.most_accessed_node?.access_count || 0}</span>
            </div>
          </div>
        )}
        
        {selectedNode ? (
          <div className="node-details">
            <h3>Memory</h3>
            
            <div className="node-content">
              {selectedNode.content}
            </div>
            
            {selectedNode.tags && selectedNode.tags.length > 0 && (
              <div className="node-tags">
                {selectedNode.tags.map(tag => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
            )}
            
            <div className="node-meta">
              <div><strong>Priority:</strong> {selectedNode.priority}</div>
              <div><strong>Created:</strong> {new Date(selectedNode.created_at).toLocaleString()}</div>
              <div><strong>Accessed:</strong> {selectedNode.access_count} times</div>
              <div><strong>Connections:</strong> {selectedNode.connections?.length || 0}</div>
            </div>
            
            {selectedNode.connections && selectedNode.connections.length > 0 && (
              <div className="connections-list">
                <h4>Connected Memories ({selectedNode.connections.length})</h4>
                {selectedNode.connections.map(conn => (
                  <div 
                    key={conn.target_id} 
                    className="connection-item"
                    onClick={() => handleConnectionClick(conn.target_id)}
                  >
                    <div className="connection-relationship">
                      {conn.relationship}
                    </div>
                    <div className="connection-content">
                      {conn.target_content?.substring(0, 100) || 'View memory'}...
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="node-details">
            <p style={{color: '#888', fontSize: '14px'}}>
              Click on a node to explore HAL's memories and their connections.
            </p>
          </div>
        )}
      </div>
      
      <div className="graph-container">
        <GraphCanvas
          nodes={filteredData.nodes}
          edges={filteredData.edges}
          onNodeClick={(node) => handleNodeClick(node)}
          layoutType="forceDirected3d"
          draggable
          edgeArrowPosition="none"
          labelType="all"
          sizingType="centrality"
        />
      </div>
    </div>
  )
}

export default App
