#!/usr/bin/env python3
"""
Memory Store for MCP Memory Server
Handles persistence and retrieval of agent memories
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time


class MemoryStore:
    """
    Persistent memory storage for agents.
    Stores both short-term (recent) and long-term (important) memories.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / ".sigma_memory" / "agent_memory.db")
        
        # Create directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Short-term memories (recent interactions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                key TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at REAL NOT NULL,
                accessed_at REAL NOT NULL,
                importance INTEGER DEFAULT 0
            )
        """)
        
        # Long-term memories (important facts)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS long_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                key TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                importance INTEGER DEFAULT 5
            )
        """)
        
        # Learned patterns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stm_topic ON short_term_memory(agent_name, topic)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ltm_topic ON long_term_memory(agent_name, topic)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns ON learned_patterns(agent_name, pattern_name)")
        
        conn.commit()
        conn.close()
    
    def save_short_term(self, agent_name: str, topic: str, key: str, data: Any, importance: int = 0):
        """
        Save short-term memory (recent interactions, typically 24h retention)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = time.time()
        data_json = json.dumps(data) if not isinstance(data, str) else data
        
        cursor.execute("""
            INSERT INTO short_term_memory (agent_name, topic, key, data, created_at, accessed_at, importance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (agent_name, topic, key, data_json, now, now, importance))
        
        conn.commit()
        conn.close()
    
    def save_long_term(self, agent_name: str, topic: str, key: str, data: Any, importance: int = 5):
        """
        Save long-term memory (important facts, permanent unless deleted)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = time.time()
        data_json = json.dumps(data) if not isinstance(data, str) else data
        
        # Try to update if exists
        cursor.execute("""
            UPDATE long_term_memory 
            SET data = ?, updated_at = ?, importance = ?, access_count = access_count + 1
            WHERE key = ? AND agent_name = ?
        """, (data_json, now, importance, key, agent_name))
        
        # If not updated, insert
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO long_term_memory (agent_name, topic, key, data, created_at, updated_at, importance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (agent_name, topic, key, data_json, now, now, importance))
        
        conn.commit()
        conn.close()
    
    def recall_short_term(self, agent_name: str, topic: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Recall short-term memories from last N hours
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            SELECT id, topic, key, data, created_at, importance
            FROM short_term_memory
            WHERE agent_name = ? AND topic = ? AND created_at > ?
            ORDER BY accessed_at DESC
        """, (agent_name, topic, cutoff_time))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "topic": row[1],
                "key": row[2],
                "data": json.loads(row[3]),
                "created_at": row[4],
                "importance": row[5]
            })
        
        # Update accessed times
        if results:
            now = time.time()
            cursor.execute("""
                UPDATE short_term_memory
                SET accessed_at = ?
                WHERE agent_name = ? AND topic = ?
            """, (now, agent_name, topic))
            conn.commit()
        
        conn.close()
        return results
    
    def recall_long_term(self, agent_name: str, topic: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recall long-term memories (most important and frequently accessed first)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, topic, key, data, created_at, importance, access_count
            FROM long_term_memory
            WHERE agent_name = ? AND topic = ?
            ORDER BY importance DESC, access_count DESC
            LIMIT ?
        """, (agent_name, topic, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "topic": row[1],
                "key": row[2],
                "data": json.loads(row[3]),
                "created_at": row[4],
                "importance": row[5],
                "access_count": row[6]
            })
        
        # Update access count
        if results:
            cursor.execute("""
                UPDATE long_term_memory
                SET access_count = access_count + 1
                WHERE agent_name = ? AND topic = ?
            """, (agent_name, topic))
            conn.commit()
        
        conn.close()
        return results
    
    def save_pattern(self, agent_name: str, pattern_name: str, pattern_data: Any, confidence: float = 0.5):
        """
        Save a learned pattern (behavior pattern, error pattern, success pattern)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = time.time()
        data_json = json.dumps(pattern_data) if not isinstance(pattern_data, str) else pattern_data
        
        # Try update
        cursor.execute("""
            UPDATE learned_patterns
            SET pattern_data = ?, updated_at = ?, confidence = ?
            WHERE agent_name = ? AND pattern_name = ?
        """, (data_json, now, confidence, agent_name, pattern_name))
        
        # Or insert
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO learned_patterns (agent_name, pattern_name, pattern_data, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (agent_name, pattern_name, data_json, confidence, now, now))
        
        conn.commit()
        conn.close()
    
    def recall_patterns(self, agent_name: str, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """
        Recall learned patterns above confidence threshold
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, pattern_name, pattern_data, confidence, success_count, failure_count
            FROM learned_patterns
            WHERE agent_name = ? AND confidence >= ?
            ORDER BY confidence DESC, success_count DESC
        """, (agent_name, min_confidence))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "pattern_name": row[1],
                "pattern_data": json.loads(row[2]),
                "confidence": row[3],
                "success_count": row[4],
                "failure_count": row[5]
            })
        
        conn.close()
        return results
    
    def update_pattern_success(self, agent_name: str, pattern_name: str):
        """Mark a pattern as successful"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE learned_patterns
            SET success_count = success_count + 1
            WHERE agent_name = ? AND pattern_name = ?
        """, (agent_name, pattern_name))
        
        conn.commit()
        conn.close()
    
    def update_pattern_failure(self, agent_name: str, pattern_name: str):
        """Mark a pattern as failed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE learned_patterns
            SET failure_count = failure_count + 1
            WHERE agent_name = ? AND pattern_name = ?
        """, (agent_name, pattern_name))
        
        conn.commit()
        conn.close()
    
    def forget_short_term(self, hours: int = 24):
        """
        Clean up old short-term memories (older than N hours)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = time.time() - (hours * 3600)
        
        cursor.execute("""
            DELETE FROM short_term_memory
            WHERE created_at < ?
        """, (cutoff_time,))
        
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        
        return deleted
    
    def forget_memory(self, key: str, memory_type: str = "long_term"):
        """
        Forget a specific memory
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if memory_type == "long_term":
            cursor.execute("DELETE FROM long_term_memory WHERE key = ?", (key,))
        elif memory_type == "short_term":
            cursor.execute("DELETE FROM short_term_memory WHERE key = ?", (key,))
        
        conn.commit()
        conn.close()
    
    def get_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get memory statistics for an agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM short_term_memory WHERE agent_name = ?", (agent_name,))
        stm_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM long_term_memory WHERE agent_name = ?", (agent_name,))
        ltm_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM learned_patterns WHERE agent_name = ?", (agent_name,))
        patterns_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "short_term_memories": stm_count,
            "long_term_memories": ltm_count,
            "learned_patterns": patterns_count,
            "total": stm_count + ltm_count + patterns_count
        }
