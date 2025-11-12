#!/usr/bin/env python3
"""
Memory MCP Server
Provides agents with persistent memory capabilities
Agents can remember tasks, patterns, and user preferences
"""

import json
from typing import Dict, Any, Optional
import time

from ..mcp_base import MCPServer, MCPTool, MCPResponse, ToolType
from .memory_store import MemoryStore


class MemoryMCPServer(MCPServer):
    """
    MCP Server that gives agents persistent memory.
    Enables learning from past experiences and user interactions.
    """
    
    def __init__(self, db_path: str = None):
        super().__init__(
            name="memory",
            description="Persistent memory for agents - enables learning from past experiences"
        )
        self.memory_store = MemoryStore(db_path)
    
    def _register_tools(self):
        """Register all memory tools"""
        
        # Tool 1: Save short-term memory
        self.register_tool(MCPTool(
            name="save_short_term",
            description="Save a recent interaction or fact to short-term memory (24h retention)",
            tool_type=ToolType.WRITE,
            parameters={
                "topic": "str - Category (e.g., 'emails', 'web_tasks', 'system_commands')",
                "key": "str - Unique identifier for this memory",
                "data": "dict/str - The data to remember",
                "importance": "int - Priority level (0-10, default 0)"
            },
            required_params=["topic", "key", "data"],
            returns={
                "success": "bool",
                "memory_id": "int",
                "message": "str"
            }
        ))
        
        # Tool 2: Save long-term memory
        self.register_tool(MCPTool(
            name="save_long_term",
            description="Save important facts to long-term memory (permanent until deleted)",
            tool_type=ToolType.WRITE,
            parameters={
                "topic": "str - Category (e.g., 'user_preferences', 'learned_skills')",
                "key": "str - Unique identifier",
                "data": "dict/str - The data to remember",
                "importance": "int - Priority level (0-10, default 5)"
            },
            required_params=["topic", "key", "data"],
            returns={
                "success": "bool",
                "message": "str"
            }
        ))
        
        # Tool 3: Recall short-term memory
        self.register_tool(MCPTool(
            name="recall_short_term",
            description="Retrieve recent memories from last N hours",
            tool_type=ToolType.READ,
            parameters={
                "topic": "str - Category to search",
                "hours": "int - Look back this many hours (default 24)"
            },
            required_params=["topic"],
            returns={
                "memories": "list of dicts with keys: key, data, created_at, importance",
                "count": "int - Number of memories found"
            }
        ))
        
        # Tool 4: Recall long-term memory
        self.register_tool(MCPTool(
            name="recall_long_term",
            description="Retrieve important stored facts (most recent and important first)",
            tool_type=ToolType.READ,
            parameters={
                "topic": "str - Category to search",
                "limit": "int - Maximum results (default 10)"
            },
            required_params=["topic"],
            returns={
                "memories": "list of dicts",
                "count": "int"
            }
        ))
        
        # Tool 5: Save learned pattern
        self.register_tool(MCPTool(
            name="save_pattern",
            description="Save a learned pattern (success pattern, error pattern, behavior pattern)",
            tool_type=ToolType.WRITE,
            parameters={
                "pattern_name": "str - Name of the pattern",
                "pattern_data": "dict - The pattern description",
                "confidence": "float - Confidence level 0.0-1.0"
            },
            required_params=["pattern_name", "pattern_data"],
            returns={
                "success": "bool",
                "message": "str"
            }
        ))
        
        # Tool 6: Recall learned patterns
        self.register_tool(MCPTool(
            name="recall_patterns",
            description="Get learned patterns above confidence threshold",
            tool_type=ToolType.READ,
            parameters={
                "min_confidence": "float - Minimum confidence (0.0-1.0, default 0.5)"
            },
            required_params=[],
            returns={
                "patterns": "list of dicts",
                "count": "int"
            }
        ))
        
        # Tool 7: Update pattern success
        self.register_tool(MCPTool(
            name="mark_pattern_success",
            description="Mark a pattern as successfully applied",
            tool_type=ToolType.WRITE,
            parameters={
                "pattern_name": "str - Pattern name"
            },
            required_params=["pattern_name"],
            returns={
                "success": "bool"
            }
        ))
        
        # Tool 8: Forget memory
        self.register_tool(MCPTool(
            name="forget_memory",
            description="Delete a specific memory",
            tool_type=ToolType.WRITE,
            parameters={
                "key": "str - Memory key to delete",
                "memory_type": "str - 'short_term' or 'long_term' (default 'long_term')"
            },
            required_params=["key"],
            returns={
                "success": "bool"
            }
        ))
        
        # Tool 9: Get memory stats
        self.register_tool(MCPTool(
            name="get_stats",
            description="Get memory statistics for analysis",
            tool_type=ToolType.READ,
            parameters={},
            required_params=[],
            returns={
                "short_term_memories": "int",
                "long_term_memories": "int",
                "learned_patterns": "int",
                "total": "int"
            }
        ))
    
    def initialize(self) -> bool:
        """Initialize the memory server"""
        try:
            # Just test the connection
            stats = self.memory_store.get_stats("system")  # Use dummy agent name
            self.is_ready = True
            print(f"✅ Memory MCP Server initialized at {self.memory_store.db_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Memory MCP Server: {str(e)}")
            return False
    
    def call_tool(self, tool_name: str, **kwargs) -> MCPResponse:
        """Execute a memory tool"""
        try:
            agent_name = kwargs.get("agent_name", "system")
            
            if tool_name == "save_short_term":
                topic = kwargs.get("topic")
                key = kwargs.get("key")
                data = kwargs.get("data")
                importance = kwargs.get("importance", 0)
                
                self.memory_store.save_short_term(agent_name, topic, key, data, importance)
                
                return MCPResponse(
                    success=True,
                    data={"memory_saved": key, "topic": topic},
                    execution_time_ms=10
                )
            
            elif tool_name == "save_long_term":
                topic = kwargs.get("topic")
                key = kwargs.get("key")
                data = kwargs.get("data")
                importance = kwargs.get("importance", 5)
                
                self.memory_store.save_long_term(agent_name, topic, key, data, importance)
                
                return MCPResponse(
                    success=True,
                    data={"memory_saved": key, "topic": topic},
                    execution_time_ms=10
                )
            
            elif tool_name == "recall_short_term":
                topic = kwargs.get("topic")
                hours = kwargs.get("hours", 24)
                
                memories = self.memory_store.recall_short_term(agent_name, topic, hours)
                
                return MCPResponse(
                    success=True,
                    data={
                        "memories": memories,
                        "count": len(memories),
                        "lookback_hours": hours
                    }
                )
            
            elif tool_name == "recall_long_term":
                topic = kwargs.get("topic")
                limit = kwargs.get("limit", 10)
                
                memories = self.memory_store.recall_long_term(agent_name, topic, limit)
                
                return MCPResponse(
                    success=True,
                    data={
                        "memories": memories,
                        "count": len(memories)
                    }
                )
            
            elif tool_name == "save_pattern":
                pattern_name = kwargs.get("pattern_name")
                pattern_data = kwargs.get("pattern_data")
                confidence = kwargs.get("confidence", 0.5)
                
                self.memory_store.save_pattern(agent_name, pattern_name, pattern_data, confidence)
                
                return MCPResponse(
                    success=True,
                    data={"pattern_saved": pattern_name, "confidence": confidence}
                )
            
            elif tool_name == "recall_patterns":
                min_confidence = kwargs.get("min_confidence", 0.5)
                
                patterns = self.memory_store.recall_patterns(agent_name, min_confidence)
                
                return MCPResponse(
                    success=True,
                    data={
                        "patterns": patterns,
                        "count": len(patterns),
                        "min_confidence": min_confidence
                    }
                )
            
            elif tool_name == "mark_pattern_success":
                pattern_name = kwargs.get("pattern_name")
                
                self.memory_store.update_pattern_success(agent_name, pattern_name)
                
                return MCPResponse(
                    success=True,
                    data={"pattern": pattern_name, "marked": "success"}
                )
            
            elif tool_name == "forget_memory":
                key = kwargs.get("key")
                memory_type = kwargs.get("memory_type", "long_term")
                
                self.memory_store.forget_memory(key, memory_type)
                
                return MCPResponse(
                    success=True,
                    data={"forgotten": key}
                )
            
            elif tool_name == "get_stats":
                stats = self.memory_store.get_stats(agent_name)
                
                return MCPResponse(
                    success=True,
                    data=stats
                )
            
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
