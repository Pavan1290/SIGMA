#!/usr/bin/env python3
"""
Database MCP Server
Provides agents with structured data access, caching, and persistence
Agents can store and retrieve structured data, user preferences, and analytics
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from ..mcp_base import MCPServer, MCPTool, MCPResponse, ToolType


class DatabaseMCPServer(MCPServer):
    """
    MCP Server for database operations.
    Provides agents with persistent data storage and querying.
    """
    
    def __init__(self, db_path: str = None):
        super().__init__(
            name="database",
            description="Database server - persistent storage for agents"
        )
        
        if db_path is None:
            db_path = str(Path.home() / ".sigma_memory" / "agent_data.db")
        
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _register_tools(self):
        """Register database tools"""
        
        self.register_tool(MCPTool(
            name="create_table",
            description="Create a new table in the database",
            tool_type=ToolType.WRITE,
            parameters={
                "table_name": "str - Name of the table",
                "columns": "dict - Column definitions {name: type}"
            },
            required_params=["table_name", "columns"],
            returns={
                "success": "bool",
                "table_name": "str"
            }
        ))
        
        self.register_tool(MCPTool(
            name="insert_data",
            description="Insert data into a table",
            tool_type=ToolType.WRITE,
            parameters={
                "table_name": "str - Table name",
                "data": "dict or list of dicts - Data to insert"
            },
            required_params=["table_name", "data"],
            returns={
                "success": "bool",
                "rows_inserted": "int"
            }
        ))
        
        self.register_tool(MCPTool(
            name="query_data",
            description="Query data from the database",
            tool_type=ToolType.READ,
            parameters={
                "table_name": "str - Table to query",
                "where": "str - WHERE clause (optional)",
                "limit": "int - Max rows (default 100)"
            },
            required_params=["table_name"],
            returns={
                "data": "list of dicts",
                "count": "int"
            }
        ))
        
        self.register_tool(MCPTool(
            name="update_data",
            description="Update data in the database",
            tool_type=ToolType.WRITE,
            parameters={
                "table_name": "str - Table name",
                "data": "dict - Updated values",
                "where": "str - WHERE clause"
            },
            required_params=["table_name", "data", "where"],
            returns={
                "success": "bool",
                "rows_updated": "int"
            }
        ))
        
        self.register_tool(MCPTool(
            name="delete_data",
            description="Delete data from the database",
            tool_type=ToolType.WRITE,
            parameters={
                "table_name": "str - Table name",
                "where": "str - WHERE clause"
            },
            required_params=["table_name", "where"],
            returns={
                "success": "bool",
                "rows_deleted": "int"
            }
        ))
        
        self.register_tool(MCPTool(
            name="store_user_preference",
            description="Store a user preference",
            tool_type=ToolType.WRITE,
            parameters={
                "user_id": "str - User identifier",
                "key": "str - Preference key",
                "value": "any - Preference value"
            },
            required_params=["user_id", "key", "value"],
            returns={
                "success": "bool"
            }
        ))
        
        self.register_tool(MCPTool(
            name="get_user_preference",
            description="Retrieve a user preference",
            tool_type=ToolType.READ,
            parameters={
                "user_id": "str - User identifier",
                "key": "str - Preference key"
            },
            required_params=["user_id", "key"],
            returns={
                "value": "any",
                "found": "bool"
            }
        ))
        
        self.register_tool(MCPTool(
            name="store_task_history",
            description="Store a task execution in history",
            tool_type=ToolType.WRITE,
            parameters={
                "agent_name": "str - Agent name",
                "task": "str - Task description",
                "result": "dict - Task result",
                "duration_ms": "float - Execution time"
            },
            required_params=["agent_name", "task", "result"],
            returns={
                "success": "bool",
                "task_id": "int"
            }
        ))
        
        self.register_tool(MCPTool(
            name="get_task_history",
            description="Get agent task history",
            tool_type=ToolType.READ,
            parameters={
                "agent_name": "str - Agent name",
                "limit": "int - Max records (default 50)"
            },
            required_params=["agent_name"],
            returns={
                "tasks": "list of dicts",
                "count": "int"
            }
        ))
    
    def initialize(self) -> bool:
        """Initialize database server"""
        try:
            self._init_db()
            self.is_ready = True
            print(f"✅ Database MCP Server initialized at {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Database MCP Server: {str(e)}")
            return False
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                UNIQUE(user_id, key)
            )
        """)
        
        # Task history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                task TEXT NOT NULL,
                result TEXT NOT NULL,
                success BOOLEAN DEFAULT 1,
                duration_ms REAL DEFAULT 0,
                created_at REAL NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_prefs ON user_preferences(user_id, key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_history ON task_history(agent_name, created_at)")
        
        conn.commit()
        conn.close()
    
    def call_tool(self, tool_name: str, **kwargs) -> MCPResponse:
        """Execute database tool"""
        try:
            if tool_name == "create_table":
                return self._create_table(**kwargs)
            elif tool_name == "insert_data":
                return self._insert_data(**kwargs)
            elif tool_name == "query_data":
                return self._query_data(**kwargs)
            elif tool_name == "update_data":
                return self._update_data(**kwargs)
            elif tool_name == "delete_data":
                return self._delete_data(**kwargs)
            elif tool_name == "store_user_preference":
                return self._store_user_preference(**kwargs)
            elif tool_name == "get_user_preference":
                return self._get_user_preference(**kwargs)
            elif tool_name == "store_task_history":
                return self._store_task_history(**kwargs)
            elif tool_name == "get_task_history":
                return self._get_task_history(**kwargs)
            else:
                return MCPResponse(
                    success=False,
                    data=None,
                    error=f"Unknown tool: {tool_name}"
                )
        except Exception as e:
            return MCPResponse(
                success=False,
                data=None,
                error=f"Tool execution failed: {str(e)}"
            )
    
    def _create_table(self, **kwargs) -> MCPResponse:
        """Create a new table"""
        table_name = kwargs.get("table_name")
        columns = kwargs.get("columns", {})
        
        # Build CREATE TABLE statement
        col_defs = []
        for col_name, col_type in columns.items():
            col_defs.append(f"{col_name} {col_type}")
        
        create_stmt = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(create_stmt)
        conn.commit()
        conn.close()
        
        return MCPResponse(
            success=True,
            data={"table_name": table_name, "columns": len(columns)}
        )
    
    def _insert_data(self, **kwargs) -> MCPResponse:
        """Insert data into table"""
        table_name = kwargs.get("table_name")
        data = kwargs.get("data")
        
        if not isinstance(data, list):
            data = [data]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        rows_inserted = 0
        for record in data:
            cols = list(record.keys())
            vals = [record[col] for col in cols]
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            
            stmt = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
            cursor.execute(stmt, vals)
            rows_inserted += 1
        
        conn.commit()
        conn.close()
        
        return MCPResponse(
            success=True,
            data={"rows_inserted": rows_inserted, "table": table_name}
        )
    
    def _query_data(self, **kwargs) -> MCPResponse:
        """Query data from table"""
        table_name = kwargs.get("table_name")
        where_clause = kwargs.get("where", "")
        limit = kwargs.get("limit", 100)
        
        stmt = f"SELECT * FROM {table_name}"
        if where_clause:
            stmt += f" WHERE {where_clause}"
        stmt += f" LIMIT {limit}"
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return dict-like rows
        cursor = conn.cursor()
        cursor.execute(stmt)
        
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        
        conn.close()
        
        return MCPResponse(
            success=True,
            data={"data": data, "count": len(data), "limit": limit}
        )
    
    def _update_data(self, **kwargs) -> MCPResponse:
        """Update data in table"""
        table_name = kwargs.get("table_name")
        data = kwargs.get("data", {})
        where_clause = kwargs.get("where")
        
        if not where_clause:
            return MCPResponse(
                success=False,
                data=None,
                error="WHERE clause is required for updates"
            )
        
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        vals = list(data.values())
        vals.append(where_clause)  # Append where value
        
        stmt = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(stmt, vals[:-1] + [where_clause])  # Fix: don't append where_clause as value
        rows_updated = cursor.rowcount
        conn.commit()
        conn.close()
        
        return MCPResponse(
            success=True,
            data={"rows_updated": rows_updated, "table": table_name}
        )
    
    def _delete_data(self, **kwargs) -> MCPResponse:
        """Delete data from table"""
        table_name = kwargs.get("table_name")
        where_clause = kwargs.get("where")
        
        if not where_clause:
            return MCPResponse(
                success=False,
                data=None,
                error="WHERE clause is required for deletions"
            )
        
        stmt = f"DELETE FROM {table_name} WHERE {where_clause}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(stmt)
        rows_deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return MCPResponse(
            success=True,
            data={"rows_deleted": rows_deleted, "table": table_name}
        )
    
    def _store_user_preference(self, **kwargs) -> MCPResponse:
        """Store user preference"""
        user_id = kwargs.get("user_id")
        key = kwargs.get("key")
        value = kwargs.get("value")
        
        now = time.time()
        value_str = json.dumps(value) if not isinstance(value, str) else value
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_preferences (user_id, key, value, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, key, value_str, now, now))
        
        conn.commit()
        conn.close()
        
        return MCPResponse(
            success=True,
            data={"user_id": user_id, "key": key}
        )
    
    def _get_user_preference(self, **kwargs) -> MCPResponse:
        """Get user preference"""
        user_id = kwargs.get("user_id")
        key = kwargs.get("key")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value FROM user_preferences
            WHERE user_id = ? AND key = ?
        """, (user_id, key))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            value = result[0]
            try:
                value = json.loads(value)
            except:
                pass
            return MCPResponse(
                success=True,
                data={"value": value, "found": True}
            )
        else:
            return MCPResponse(
                success=True,
                data={"value": None, "found": False}
            )
    
    def _store_task_history(self, **kwargs) -> MCPResponse:
        """Store task history"""
        agent_name = kwargs.get("agent_name")
        task = kwargs.get("task")
        result = kwargs.get("result", {})
        duration_ms = kwargs.get("duration_ms", 0.0)
        
        success = result.get("success", True)
        result_str = json.dumps(result)
        now = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO task_history (agent_name, task, result, success, duration_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (agent_name, task, result_str, success, duration_ms, now))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return MCPResponse(
            success=True,
            data={"task_id": task_id, "agent": agent_name}
        )
    
    def _get_task_history(self, **kwargs) -> MCPResponse:
        """Get task history"""
        agent_name = kwargs.get("agent_name")
        limit = kwargs.get("limit", 50)
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, task, success, duration_ms, created_at FROM task_history
            WHERE agent_name = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (agent_name, limit))
        
        rows = cursor.fetchall()
        tasks = [dict(row) for row in rows]
        
        conn.close()
        
        return MCPResponse(
            success=True,
            data={"tasks": tasks, "count": len(tasks), "agent": agent_name}
        )
