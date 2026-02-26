#!/usr/bin/env bash
set -e

mkdir -p "$(dirname "$MINDMAP_DB_PATH")"

if [ ! -f "$MINDMAP_DB_PATH" ]; then
  echo "Initializing mindmap db at $MINDMAP_DB_PATH"
  python -c "from database import MindMapDB; MindMapDB('$MINDMAP_DB_PATH'); print('ok')"
fi
