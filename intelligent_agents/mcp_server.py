#!/usr/bin/env python3
"""
SIGMA-OS MCP (Model Context Protocol) Server
Exposes all agent capabilities as MCP tools for seamless integration with Claude and other LLMs
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import agents
from intelligent_agents import (
    SystemAgent,
    EmailAgent,
    WebAgent,
    AgentStatus,
    AgentUpdate
)
from intelligent_agents.model_manager import model_manager
from intelligent_agents.output_formatter import output_formatter


@dataclass
class MCPToolResult:
    """Standardized result from MCP tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self):
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata or {}
        }


class SIGMAMCPServer:
    """
    MCP Server for SIGMA-OS
    Exposes agent capabilities as standardized tools for Claude and other LLMs
    """
    
    def __init__(self):
        """Initialize MCP server with all agents"""
        self.agents = {
            'system': SystemAgent(),
            'email': EmailAgent(),
            'web': WebAgent()
        }
        
        self.tools = self._register_tools()
        logger.info("✅ SIGMA MCP Server initialized with 3 agents and 15+ tools")
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available MCP tools"""
        return {
            # System Agent Tools
            'execute_command': {
                'agent': 'system',
                'description': 'Execute shell commands with intelligent output formatting',
                'parameters': {
                    'command': 'str - The command to execute',
                    'timeout': 'int - Optional timeout in seconds (default: 30)'
                }
            },
            'read_file': {
                'agent': 'system',
                'description': 'Read file contents intelligently',
                'parameters': {
                    'path': 'str - File path to read',
                    'lines': 'str - Optional line range (e.g., "1-50")'
                }
            },
            'write_file': {
                'agent': 'system',
                'description': 'Write content to a file',
                'parameters': {
                    'path': 'str - File path',
                    'content': 'str - Content to write',
                    'mode': 'str - Write mode (w=overwrite, a=append)'
                }
            },
            'list_files': {
                'agent': 'system',
                'description': 'List directory contents with metadata',
                'parameters': {
                    'path': 'str - Directory path',
                    'pattern': 'str - Optional glob pattern (e.g., "*.py")',
                    'recursive': 'bool - Recursively list subdirectories'
                }
            },
            'get_system_info': {
                'agent': 'system',
                'description': 'Get detailed system information (OS, CPU, Memory, Disk)',
                'parameters': {}
            },
            'take_screenshot': {
                'agent': 'system',
                'description': 'Capture screenshot of the entire screen or specific region',
                'parameters': {
                    'region': 'str - Optional region (x,y,width,height) or "full"'
                }
            },
            'list_processes': {
                'agent': 'system',
                'description': 'List running processes with resource usage',
                'parameters': {
                    'filter': 'str - Optional process name filter',
                    'limit': 'int - Max results to return'
                }
            },
            'get_disk_usage': {
                'agent': 'system',
                'description': 'Get disk usage information',
                'parameters': {
                    'path': 'str - Optional path to check (default: root)'
                }
            },
            
            # Email Agent Tools
            'send_email': {
                'agent': 'email',
                'description': 'Send email via Gmail',
                'parameters': {
                    'to': 'str - Recipient email address',
                    'subject': 'str - Email subject',
                    'body': 'str - Email body',
                    'cc': 'str - Optional CC addresses (comma-separated)',
                    'attachments': 'list - Optional file paths to attach'
                }
            },
            'read_emails': {
                'agent': 'email',
                'description': 'Read recent emails from Gmail',
                'parameters': {
                    'query': 'str - Gmail search query (default: "is:unread")',
                    'limit': 'int - Number of emails to fetch (default: 10)',
                    'labels': 'str - Optional Gmail label filter'
                }
            },
            'search_emails': {
                'agent': 'email',
                'description': 'Search emails using Gmail search syntax',
                'parameters': {
                    'query': 'str - Gmail search query',
                    'limit': 'int - Max results (default: 20)'
                }
            },
            
            # Web Agent Tools
            'browse_web': {
                'agent': 'web',
                'description': 'Browse website and extract information',
                'parameters': {
                    'url': 'str - Website URL to browse',
                    'action': 'str - Action to perform (view, extract, search)',
                    'selector': 'str - Optional CSS selector for extraction'
                }
            },
            'fill_form': {
                'agent': 'web',
                'description': 'Fill and submit web forms',
                'parameters': {
                    'url': 'str - Website URL with form',
                    'fields': 'dict - Form field values {selector: value}',
                    'submit': 'bool - Whether to submit form'
                }
            },
            'scrape_data': {
                'agent': 'web',
                'description': 'Scrape structured data from web pages',
                'parameters': {
                    'url': 'str - Website URL',
                    'selectors': 'dict - CSS selectors {name: selector}',
                    'format': 'str - Output format (json, csv, table)'
                }
            },
            
            # System Analysis Tools
            'analyze_output': {
                'agent': 'system',
                'description': 'Format and analyze command output intelligently',
                'parameters': {
                    'output': 'str - Raw output to analyze',
                    'command': 'str - Command that produced output',
                    'add_insights': 'bool - Add AI-powered insights'
                }
            },
            'get_models': {
                'agent': 'system',
                'description': 'Get list of available AI models',
                'parameters': {}
            }
        }
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> MCPToolResult:
        """
        Call an MCP tool and return standardized result
        """
        try:
            if tool_name not in self.tools:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown tool: {tool_name}"
                )
            
            tool_config = self.tools[tool_name]
            agent_name = tool_config['agent']
            agent = self.agents.get(agent_name)
            
            if not agent:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"Agent not found: {agent_name}"
                )
            
            logger.info(f"📋 Calling tool: {tool_name}")
            
            # Route to appropriate handler
            if tool_name == 'execute_command':
                return await self._execute_command(params)
            elif tool_name == 'read_file':
                return await self._read_file(params)
            elif tool_name == 'write_file':
                return await self._write_file(params)
            elif tool_name == 'list_files':
                return await self._list_files(params)
            elif tool_name == 'get_system_info':
                return await self._get_system_info(params)
            elif tool_name == 'take_screenshot':
                return await self._take_screenshot(params)
            elif tool_name == 'list_processes':
                return await self._list_processes(params)
            elif tool_name == 'get_disk_usage':
                return await self._get_disk_usage(params)
            elif tool_name == 'send_email':
                return await self._send_email(params)
            elif tool_name == 'read_emails':
                return await self._read_emails(params)
            elif tool_name == 'search_emails':
                return await self._search_emails(params)
            elif tool_name == 'browse_web':
                return await self._browse_web(params)
            elif tool_name == 'fill_form':
                return await self._fill_form(params)
            elif tool_name == 'scrape_data':
                return await self._scrape_data(params)
            elif tool_name == 'analyze_output':
                return await self._analyze_output(params)
            elif tool_name == 'get_models':
                return await self._get_models(params)
            else:
                return MCPToolResult(
                    success=False,
                    data=None,
                    error=f"Tool handler not implemented: {tool_name}"
                )
        
        except Exception as e:
            logger.error(f"❌ Tool execution error: {str(e)}")
            return MCPToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    # ==================== SYSTEM AGENT TOOLS ====================
    
    async def _execute_command(self, params: Dict[str, Any]) -> MCPToolResult:
        """Execute shell command"""
        try:
            command = params.get('command', '')
            timeout = params.get('timeout', 30)
            
            if not command:
                return MCPToolResult(success=False, data=None, error="command parameter required")
            
            result = self.agents['system'].run(
                task=f"Execute: {command}",
                context={'command': command, 'timeout': timeout}
            )
            
            return MCPToolResult(
                success=result.get('success', False),
                data=result,
                metadata={'command': command}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _read_file(self, params: Dict[str, Any]) -> MCPToolResult:
        """Read file contents"""
        try:
            path = params.get('path', '')
            lines = params.get('lines', '')
            
            if not path:
                return MCPToolResult(success=False, data=None, error="path parameter required")
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return MCPToolResult(
                success=True,
                data={'content': content, 'path': path, 'size': len(content)},
                metadata={'path': path, 'lines': lines}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _write_file(self, params: Dict[str, Any]) -> MCPToolResult:
        """Write to file"""
        try:
            path = params.get('path', '')
            content = params.get('content', '')
            mode = params.get('mode', 'w')
            
            if not path:
                return MCPToolResult(success=False, data=None, error="path parameter required")
            
            # Create directories if needed
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
            
            return MCPToolResult(
                success=True,
                data={'path': path, 'size': len(content), 'mode': mode},
                metadata={'path': path}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _list_files(self, params: Dict[str, Any]) -> MCPToolResult:
        """List directory contents"""
        try:
            path = params.get('path', '.')
            pattern = params.get('pattern', '*')
            recursive = params.get('recursive', False)
            
            from pathlib import Path
            p = Path(path)
            
            if recursive:
                files = list(p.glob(f'**/{pattern}'))
            else:
                files = list(p.glob(pattern))
            
            file_list = [
                {
                    'name': str(f.name),
                    'type': 'dir' if f.is_dir() else 'file',
                    'size': f.stat().st_size if f.is_file() else 0
                }
                for f in files
            ]
            
            return MCPToolResult(
                success=True,
                data={'files': file_list, 'count': len(file_list)},
                metadata={'path': path, 'pattern': pattern}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _get_system_info(self, params: Dict[str, Any]) -> MCPToolResult:
        """Get system information"""
        try:
            import psutil
            import platform
            
            info = {
                'platform': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory': {
                    'total': psutil.virtual_memory().total,
                    'used': psutil.virtual_memory().used,
                    'percent': psutil.virtual_memory().percent
                },
                'disk': {
                    'total': psutil.disk_usage('/').total,
                    'used': psutil.disk_usage('/').used,
                    'percent': psutil.disk_usage('/').percent
                }
            }
            
            return MCPToolResult(success=True, data=info)
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _take_screenshot(self, params: Dict[str, Any]) -> MCPToolResult:
        """Take screenshot"""
        try:
            region = params.get('region', 'full')
            
            result = self.agents['system'].run(
                task="Take screenshot of entire screen",
                context={'action': 'screenshot', 'region': region}
            )
            
            return MCPToolResult(
                success=result.get('success', False),
                data=result,
                metadata={'region': region}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _list_processes(self, params: Dict[str, Any]) -> MCPToolResult:
        """List running processes"""
        try:
            import psutil
            
            filter_name = params.get('filter', '')
            limit = params.get('limit', 50)
            
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if filter_name and filter_name.lower() not in proc.info['name'].lower():
                        continue
                    
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'],
                        'memory': proc.info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes = sorted(processes, key=lambda x: x['cpu'] + x['memory'], reverse=True)[:limit]
            
            return MCPToolResult(
                success=True,
                data={'processes': processes, 'count': len(processes)},
                metadata={'filter': filter_name, 'limit': limit}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _get_disk_usage(self, params: Dict[str, Any]) -> MCPToolResult:
        """Get disk usage"""
        try:
            import psutil
            
            path = params.get('path', '/')
            usage = psutil.disk_usage(path)
            
            return MCPToolResult(
                success=True,
                data={
                    'path': path,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                }
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    # ==================== EMAIL AGENT TOOLS ====================
    
    async def _send_email(self, params: Dict[str, Any]) -> MCPToolResult:
        """Send email"""
        try:
            to = params.get('to', '')
            subject = params.get('subject', '')
            body = params.get('body', '')
            
            if not (to and subject and body):
                return MCPToolResult(success=False, data=None, error="to, subject, body parameters required")
            
            result = self.agents['email'].run(
                task=f"Send email to {to} with subject '{subject}'",
                context={'to': to, 'subject': subject, 'body': body}
            )
            
            return MCPToolResult(
                success=result.get('success', False),
                data=result,
                metadata={'recipient': to}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _read_emails(self, params: Dict[str, Any]) -> MCPToolResult:
        """Read emails"""
        try:
            query = params.get('query', 'is:unread')
            limit = params.get('limit', 10)
            
            result = self.agents['email'].run(
                task=f"Read {limit} emails with query: {query}",
                context={'query': query, 'limit': limit, 'action': 'read'}
            )
            
            return MCPToolResult(
                success=result.get('success', False),
                data=result,
                metadata={'query': query, 'limit': limit}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _search_emails(self, params: Dict[str, Any]) -> MCPToolResult:
        """Search emails"""
        try:
            query = params.get('query', '')
            limit = params.get('limit', 20)
            
            if not query:
                return MCPToolResult(success=False, data=None, error="query parameter required")
            
            result = self.agents['email'].run(
                task=f"Search emails with query: {query}",
                context={'query': query, 'limit': limit, 'action': 'search'}
            )
            
            return MCPToolResult(
                success=result.get('success', False),
                data=result,
                metadata={'query': query}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    # ==================== WEB AGENT TOOLS ====================
    
    async def _browse_web(self, params: Dict[str, Any]) -> MCPToolResult:
        """Browse web"""
        try:
            url = params.get('url', '')
            action = params.get('action', 'view')
            
            if not url:
                return MCPToolResult(success=False, data=None, error="url parameter required")
            
            result = self.agents['web'].run(
                task=f"Browse {url} and {action}",
                context={'url': url, 'action': action}
            )
            
            return MCPToolResult(
                success=result.get('success', False),
                data=result,
                metadata={'url': url, 'action': action}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _fill_form(self, params: Dict[str, Any]) -> MCPToolResult:
        """Fill web form"""
        try:
            url = params.get('url', '')
            fields = params.get('fields', {})
            submit = params.get('submit', True)
            
            if not url:
                return MCPToolResult(success=False, data=None, error="url parameter required")
            
            result = self.agents['web'].run(
                task=f"Fill form on {url} and submit={submit}",
                context={'url': url, 'fields': fields, 'submit': submit, 'action': 'fill_form'}
            )
            
            return MCPToolResult(
                success=result.get('success', False),
                data=result,
                metadata={'url': url, 'submit': submit}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _scrape_data(self, params: Dict[str, Any]) -> MCPToolResult:
        """Scrape web data"""
        try:
            url = params.get('url', '')
            selectors = params.get('selectors', {})
            
            if not url:
                return MCPToolResult(success=False, data=None, error="url parameter required")
            
            result = self.agents['web'].run(
                task=f"Scrape data from {url}",
                context={'url': url, 'selectors': selectors, 'action': 'scrape'}
            )
            
            return MCPToolResult(
                success=result.get('success', False),
                data=result,
                metadata={'url': url}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    # ==================== ANALYSIS TOOLS ====================
    
    async def _analyze_output(self, params: Dict[str, Any]) -> MCPToolResult:
        """Analyze and format output"""
        try:
            output = params.get('output', '')
            command = params.get('command', '')
            add_insights = params.get('add_insights', False)
            
            if not output:
                return MCPToolResult(success=False, data=None, error="output parameter required")
            
            formatted = output_formatter.format(output, command)
            
            if add_insights:
                formatted = output_formatter.add_ai_insights(formatted)
            
            return MCPToolResult(
                success=True,
                data=formatted,
                metadata={'command': command}
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))
    
    async def _get_models(self, params: Dict[str, Any]) -> MCPToolResult:
        """Get available AI models"""
        try:
            models = model_manager.get_available_models()
            
            return MCPToolResult(
                success=True,
                data={
                    'models': models,
                    'current_thinking': model_manager.current_thinking_model,
                    'current_execution': model_manager.current_execution_model
                }
            )
        except Exception as e:
            return MCPToolResult(success=False, data=None, error=str(e))


# Global MCP server instance
mcp_server = SIGMAMCPServer()


async def main():
    """Test MCP server"""
    print("\n🚀 SIGMA-OS MCP Server Started\n")
    
    # List available tools
    print("📋 Available Tools:")
    for tool_name, config in mcp_server.tools.items():
        print(f"  • {tool_name}: {config['description']}")
    
    print("\n✅ MCP Server ready for integration with Claude and other LLMs")


if __name__ == "__main__":
    asyncio.run(main())
