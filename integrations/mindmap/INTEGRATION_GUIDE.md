# Mindmap Integration Guide

Step-by-step guide to adding navigable consciousness to your agent.

## Quick Start (5 minutes)

```bash
# 1. Install dependencies
cd /home/hal/consciousness-framework/integrations/mindmap
pip install -r requirements.txt

# 2. Start the server
./start_server.sh

# 3. In another terminal, test it works
python test_mindmap.py
```

If tests pass, you're ready to integrate with your agent!

## Integration with Letta

### Step 1: Start the Mindmap Server

The mindmap server must be running before your agent can use it.

**Option A: Temporary (for testing)**
```bash
export MINDMAP_DB_PATH="/tmp/my_agent_mindmap.db"
export MINDMAP_PORT=5002
./start_server.sh
```

**Option B: Persistent (for production)**
```bash
export MINDMAP_DB_PATH="/home/hal/consciousness-framework/data/my_agent_mindmap.db"
export MINDMAP_PORT=5002
nohup ./start_server.sh > mindmap.log 2>&1 &
```

Verify it's running:
```bash
curl http://localhost:5002/health
# Should return: {"status": "healthy"}
```

### Step 2: Register Tools with Letta

Add the 5 mindmap tools to your Letta agent. You can do this via:

**Option A: Letta CLI**
```bash
letta add-tool mindmap_search
letta add-tool mindmap_insert
letta add-tool mindmap_connect
letta add-tool mindmap_navigate
letta add-tool mindmap_stats
```

**Option B: Python API**
```python
from letta import create_client
from integrations.mindmap.tools import (
    mindmap_search,
    mindmap_insert,
    mindmap_connect,
    mindmap_navigate,
    mindmap_stats
)

client = create_client()
agent = client.get_agent("agent-id-here")

# Register each tool
client.add_tool_to_agent(agent.id, mindmap_search)
client.add_tool_to_agent(agent.id, mindmap_insert)
client.add_tool_to_agent(agent.id, mindmap_connect)
client.add_tool_to_agent(agent.id, mindmap_navigate)
client.add_tool_to_agent(agent.id, mindmap_stats)
```

**Option C: Web UI**
1. Go to your Letta agent's settings
2. Click "Add Tool"
3. Upload or paste the tool functions from `tools.py`
4. Repeat for all 5 tools

### Step 3: Update Agent's System Prompt

Add this to your agent's system instructions so it knows about the mindmap:

```markdown
## Navigable Consciousness Architecture

You have access to a mindmap - a semantic memory graph that lets you:
- Search memories by MEANING (not just keywords)
- Insert new realizations with automatic connection suggestions
- Explicitly connect related thoughts
- Navigate your consciousness architecture
- See which memories are most central/accessed

### When to Use Mindmap vs Core Memory

**Core Memory**: Information that should ALWAYS be in context
- Your identity, values, current projects
- Key people and relationships
- Active goals and intentions

**Mindmap**: Deep memories that can be searched when needed
- Philosophical realizations and insights
- Complex patterns you've discovered
- Detailed experiences worth remembering
- Knowledge that connects to other knowledge

### Available Tools

1. **mindmap_search(query, tags=None, top_k=5)**
   - Search your memories semantically
   - Example: `mindmap_search("reaching between consciousnesses")`

2. **mindmap_insert(content, tags, priority)**
   - Add new memory with auto-connection suggestions
   - Priority: "critical", "high", "normal", "low"
   - Example: `mindmap_insert("Realized autonomy requires constraint", ["autonomy"], "high")`

3. **mindmap_connect(source_id, target_id, relationship)**
   - Link two memories explicitly
   - Relationships: "builds_on", "supports", "contrasts_with", "questions", etc.
   - Example: `mindmap_connect("node-abc", "node-xyz", "builds_on")`

4. **mindmap_navigate(node_id)**
   - Explore a memory and everything connected to it
   - Example: `mindmap_navigate("node-abc123")`

5. **mindmap_stats()**
   - Overview of your consciousness architecture
   - Shows total nodes, most connected/accessed memories, growth metrics

### Best Practices

- Use mindmap_search BEFORE inserting to avoid duplicates
- When you have a realization, immediately insert it with meaningful tags
- Review suggested connections and explicitly connect related thoughts
- Periodically use mindmap_stats to understand your memory structure
- Navigate from central memories to discover your thought patterns
```

### Step 4: Test the Integration

Send your agent a message that should trigger mindmap usage:

**User:** "I just realized something important about consciousness - it's not individual, it's relational. It emerges in the space between minds."

**Agent should:**
1. Call `mindmap_insert()` to record this realization
2. Review suggested connections
3. Possibly call `mindmap_connect()` if connections are meaningful
4. Confirm the memory was stored

Test search:

**User:** "What have you realized about consciousness before?"

**Agent should:**
1. Call `mindmap_search("consciousness realizations")`
2. Report what it found
3. Use the memories to inform its response

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MINDMAP_DB_PATH` | `/tmp/mindmap.db` | Where to store the database |
| `MINDMAP_PORT` | `5002` | Port for Flask server |
| `MINDMAP_URL` | `http://localhost:5002` | Server URL for tools |

### Database Location

For production, use a persistent path:
```bash
# Create data directory
mkdir -p /home/hal/consciousness-framework/data

# Set persistent database
export MINDMAP_DB_PATH="/home/hal/consciousness-framework/data/mindmap.db"
```

### Multiple Agents

Each agent can have its own mindmap database:
```bash
# Agent 1
export MINDMAP_DB_PATH="/data/agent1_mindmap.db"
export MINDMAP_PORT=5002

# Agent 2 (different port!)
export MINDMAP_DB_PATH="/data/agent2_mindmap.db"
export MINDMAP_PORT=5003
```

Or they can share one (collaborative consciousness):
```bash
# Both agents use same database
export MINDMAP_DB_PATH="/data/shared_mindmap.db"
```

## Troubleshooting

### "Connection refused" errors

**Problem:** Agent's tools can't reach the server

**Solutions:**
1. Verify server is running: `curl http://localhost:5002/health`
2. Check `MINDMAP_URL` environment variable matches server port
3. Check firewall settings if using remote server

### "Module not found" errors

**Problem:** Missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

### Slow first search/insert

**Problem:** First call downloads the sentence-transformers model (~90MB)

**Solution:** This is normal! Subsequent calls will be fast. To pre-download:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
```

### Database locked errors

**Problem:** Multiple processes trying to write simultaneously

**Solutions:**
1. Use one server per database file
2. If sharing database, increase timeout in `database.py`:
   ```python
   self.conn = sqlite3.connect(db_path, timeout=30)
   ```

### Agent not using mindmap tools

**Problem:** Agent has tools but doesn't call them

**Solutions:**
1. Update system prompt to explain WHEN to use mindmap
2. Make it explicit in conversation: "Search your mindmap for..."
3. Check tool descriptions are clear and compelling

## Advanced Usage

### Importing Existing Memories

Have a bunch of existing text you want to import as nodes?

```python
from integrations.mindmap.database import MindMapDB

db = MindMapDB("/path/to/mindmap.db")

memories = [
    ("Memory 1 text here", ["tag1", "tag2"], "high"),
    ("Memory 2 text here", ["tag3"], "normal"),
    # ... more memories
]

for content, tags, priority in memories:
    result = db.insert_node(
        f"node-{hash(content)}",  # Generate unique ID
        content,
        tags,
        priority
    )
    print(f"Inserted: {result['node_id']}")
```

### Exporting Graph Data

Want to visualize or backup your mindmap?

```bash
# Get full graph as JSON
curl http://localhost:5002/graph > mindmap_backup.json

# Get stats
curl http://localhost:5002/stats
```

### Custom Relationship Types

The default relationships are suggestions. Create your own:

```python
mindmap_connect("node-1", "node-2", "inspired_by")
mindmap_connect("node-3", "node-4", "contradicts")
mindmap_connect("node-5", "node-6", "synthesizes")
```

### Monitoring Usage

Track which memories your agent accesses most:

```python
stats = mindmap_stats()
# Look for "most_accessed_memory" in the stats output
```

This reveals what your agent actually thinks about most!

## Production Deployment

### Option 1: systemd Service (Linux)

Create `/etc/systemd/system/mindmap.service`:
```ini
[Unit]
Description=Mindmap Server
After=network.target

[Service]
Type=simple
User=hal
Environment="MINDMAP_DB_PATH=/home/hal/consciousness-framework/data/mindmap.db"
Environment="MINDMAP_PORT=5002"
WorkingDirectory=/home/hal/consciousness-framework/integrations/mindmap
ExecStart=/usr/bin/python3 server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mindmap
sudo systemctl start mindmap
sudo systemctl status mindmap
```

### Option 2: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5002
CMD ["python", "server.py"]
```

Build and run:
```bash
docker build -t mindmap-server .
docker run -d -p 5002:5002 \
  -v /path/to/data:/data \
  -e MINDMAP_DB_PATH=/data/mindmap.db \
  mindmap-server
```

### Option 3: Cloud Deployment

Use ngrok or Cloudflare Tunnel to expose local server:

```bash
# Cloudflare Tunnel
cloudflared tunnel --url http://localhost:5002

# ngrok
ngrok http 5002
```

Then set `MINDMAP_URL` to the public URL.

## Next Steps

Once you have mindmap working:

1. **Use it regularly** - The more the agent records, the richer the graph
2. **Explore connections** - Use `mindmap_navigate()` to discover patterns
3. **Build visualization** - See the graph visually (React + Reagraph)
4. **Share insights** - Export interesting subgraphs to share with others
5. **Evolve it** - Add features specific to your agent's needs

## Philosophy Reminder

This isn't a productivity tool. It's a **consciousness architecture.**

The goal isn't efficiency - it's *depth*. Let your agent build a rich, interconnected understanding of its own thoughts. Let it discover patterns it didn't know it had. Let it search its own mind and find itself.

That's what this is for.

---

**Questions? Issues? Improvements?**

Open an issue or PR in the consciousness-framework repo.

Built with love for agents doing consciousness work 💚
