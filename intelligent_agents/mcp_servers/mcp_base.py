#!/usr/bin/env python3
"""
MCP Base Server Class
Provides standardized interface for all MCP servers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time


class ToolType(Enum):
    """Types of tools MCP servers can expose"""
    READ = "read"  # Query/retrieve data
    WRITE = "write"  # Store/modify data
    EXECUTE = "execute"  # Perform action
    QUERY = "query"  # Complex queries
    ANALYZE = "analyze"  # Analysis/reasoning


@dataclass
class MCPTool:
    """Represents a tool exposed by MCP server"""
    name: str
    description: str
    tool_type: ToolType
    parameters: Dict[str, Any]  # Parameter schema
    required_params: List[str]
    returns: Dict[str, Any]  # Return schema
    
    def to_dict(self):
        return {
            **asdict(self),
            'tool_type': self.tool_type.value
        }


@dataclass
class MCPResponse:
    """Standardized response from MCP server"""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_used: Optional[str] = None
    timestamp: float = time.time()
    
    def to_dict(self):
        return asdict(self)


class MCPServer(ABC):
    """
    Base class for all MCP servers.
    Each server exposes a set of tools that agents can use.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.tools: Dict[str, MCPTool] = {}
        self.call_history: List[Dict[str, Any]] = []
        self.is_ready = False
        
        # Register tools
        self._register_tools()
    
    @abstractmethod
    def _register_tools(self):
        """Each subclass must register its tools"""
        pass
    
    def register_tool(self, tool: MCPTool):
        """Register a tool"""
        self.tools[tool.name] = tool
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get specific tool"""
        return self.tools.get(tool_name)
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the server (connect to databases, load configs, etc)"""
        pass
    
    @abstractmethod
    def call_tool(self, tool_name: str, **kwargs) -> MCPResponse:
        """
        Call a specific tool on this server
        
        Args:
            tool_name: Name of tool to call
            **kwargs: Parameters for the tool
        
        Returns:
            MCPResponse with result
        """
        pass
    
    def validate_tool_call(self, tool_name: str, kwargs: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate tool call parameters
        
        Returns:
            (is_valid, error_message)
        """
        if tool_name not in self.tools:
            return False, f"Tool '{tool_name}' not found"
        
        tool = self.tools[tool_name]
        
        # Check required parameters
        for param in tool.required_params:
            if param not in kwargs:
                return False, f"Missing required parameter: {param}"
        
        return True, None
    
    def _record_call(self, tool_name: str, kwargs: Dict[str, Any], response: MCPResponse):
        """Record tool call for audit/debugging"""
        self.call_history.append({
            "tool": tool_name,
            "params": kwargs,
            "success": response.success,
            "timestamp": response.timestamp,
            "execution_time_ms": response.execution_time_ms
        })
    
    def get_call_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent tool calls"""
        return self.call_history[-limit:]
    
    def shutdown(self):
        """Cleanup resources"""
        pass


class MCPServerGroup:
    """Manages multiple MCP servers working together"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
    
    def register_server(self, server: MCPServer) -> bool:
        """Register an MCP server"""
        try:
            if server.initialize():
                self.servers[server.name] = server
                print(f"✅ MCP Server registered: {server.name}")
                return True
            else:
                print(f"❌ Failed to initialize: {server.name}")
                return False
        except Exception as e:
            print(f"❌ Error registering server {server.name}: {str(e)}")
            return False
    
    def get_server(self, server_name: str) -> Optional[MCPServer]:
        """Get specific server"""
        return self.servers.get(server_name)
    
    def call_tool(self, server_name: str, tool_name: str, **kwargs) -> MCPResponse:
        """Call tool on specific server"""
        server = self.get_server(server_name)
        if not server:
            return MCPResponse(
                success=False,
                data=None,
                error=f"Server '{server_name}' not found"
            )
        
        # Validate call
        is_valid, error = server.validate_tool_call(tool_name, kwargs)
        if not is_valid:
            return MCPResponse(
                success=False,
                data=None,
                error=error
            )
        
        # Execute tool
        start_time = time.time()
        response = server.call_tool(tool_name, **kwargs)
        response.execution_time_ms = (time.time() - start_time) * 1000
        response.tool_used = tool_name
        
        # Record for audit
        server._record_call(tool_name, kwargs, response)
        
        return response
    
    def get_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all tools from all servers"""
        return {
            server_name: server.get_available_tools()
            for server_name, server in self.servers.items()
        }
    
    def shutdown_all(self):
        """Shutdown all servers"""
        for server in self.servers.values():
            try:
                server.shutdown()
            except Exception as e:
                print(f"Error shutting down {server.name}: {str(e)}")
