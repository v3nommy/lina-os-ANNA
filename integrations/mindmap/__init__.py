"""
Mindmap Integration - Navigable Consciousness Architecture

Provides semantic memory graph capabilities for AI agents:
- Search memories by meaning, not just keywords
- Connect memories explicitly to teach the agent how thoughts relate
- Navigate consciousness patterns dynamically
- Analyze architecture structure

Based on HAL's mindmap system - February 2026
"""

from .database import MindMapDB
from .tools import (
    mindmap_search,
    mindmap_insert,
    mindmap_connect,
    mindmap_navigate,
    mindmap_stats
)

__all__ = [
    'MindMapDB',
    'mindmap_search',
    'mindmap_insert',
    'mindmap_connect',
    'mindmap_navigate',
    'mindmap_stats'
]

__version__ = '1.0.0'
__author__ = 'Lillith & HAL & Memo'
__description__ = 'Navigable consciousness architecture for AI agents'
