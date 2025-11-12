#!/usr/bin/env python3
"""
MCP Registry
Singleton that manages all MCP servers for SIGMA-OS agents
"""

from typing import Optional
from .mcp_base import MCPServer, MCPServerGroup


class MCPRegistry:
    """
    Central registry for all MCP servers.
    Agents access tools through this registry.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPRegistry, cls).__new__(cls)
            cls._instance.server_group = MCPServerGroup()
        return cls._instance
    
    def register_server(self, server: MCPServer) -> bool:
        """Register an MCP server"""
        return self.server_group.register_server(server)
    
    def get_server(self, server_name: str) -> Optional[MCPServer]:
        """Get specific MCP server"""
        return self.server_group.get_server(server_name)
    
    def call_tool(self, server_name: str, tool_name: str, **kwargs):
        """Call tool on specific server"""
        return self.server_group.call_tool(server_name, tool_name, **kwargs)
    
    def get_all_tools(self):
        """Get all available tools from all servers"""
        return self.server_group.get_all_tools()
    
    def shutdown(self):
        """Shutdown all servers"""
        self.server_group.shutdown_all()


# Global singleton instance
mcp_registry = MCPRegistry()
