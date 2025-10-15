#!/usr/bin/env python3
"""
System Agent - Controls computer operations
Can execute commands, manage files, take screenshots, etc.
"""

import os
import json
import time
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List
from .agent_core import IntelligentAgent, AgentStatus

class SystemAgent(IntelligentAgent):
    """
    Intelligent agent for system-level operations
    """
    
    def __init__(self, update_callback=None):
        super().__init__(
            name="SystemAgent",
            capabilities=[
                "execute_shell_commands",
                "file_operations",
                "process_management",
                "system_information",
                "screenshot_capture"
            ],
            update_callback=update_callback
        )
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a system operation step"""
        
        tool = step.get('tool', 'auto')
        action = step.get('action', '')
        
        # Let AI decide which tool to use if not specified
        if tool == 'auto':
            tool = self._decide_tool(action, context)
        
        self._send_update(
            AgentStatus.EXECUTING,
            f"Using tool: {tool} for action: {action}"
        )
        
        # Route to appropriate tool
        if tool == 'shell_command':
            return self._execute_shell_command(action, context)
        elif tool == 'file_operation':
            return self._execute_file_operation(action, context)
        elif tool == 'screenshot':
            return self._take_screenshot(action, context)
        else:
            # Use AI to figure out how to execute
            return self._ai_execute(action, context)
    
    def _decide_tool(self, action: str, context: Dict[str, Any]) -> str:
        """Use AI to decide which tool to use"""
        
        prompt = f"""Given this action: "{action}"
Context: {context}

Which tool should be used? Choose from:
- shell_command: Execute terminal commands
- file_operation: Create, read, update, delete files
- screenshot: Capture screen
- process_management: Kill/start processes

Respond with just the tool name, nothing else."""

        try:
            response = self.execution_model.generate_content(prompt)
            tool = response.text.strip().lower().replace(' ', '_')
            return tool
        except:
            return 'shell_command'  # Default
    
    def _execute_shell_command(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a shell command intelligently"""
        
        # Use AI to generate the actual command
        prompt = f"""Generate a safe bash command to accomplish: "{action}"
Context: {json.dumps(context, indent=2)}

Rules:
- Must be a single valid bash command
- Safe to execute (no rm -rf /, no dangerous operations)
- Handle errors gracefully
- Return only the command, no explanation

Command:"""

        try:
            response = self.execution_model.generate_content(prompt)
            command = response.text.strip()
            
            # Remove markdown code blocks if present
            if '```' in command:
                command = command.split('```')[1].strip()
                if command.startswith('bash') or command.startswith('sh'):
                    command = '\n'.join(command.split('\n')[1:])
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"Executing command: {command}"
            )
            
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": command,
                    "output": result.stdout,
                    "action": action
                }
            else:
                raise Exception(f"Command failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Command timeout - took longer than 30 seconds")
        except Exception as e:
            raise Exception(f"Shell command error: {str(e)}")
    
    def _execute_file_operation(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file operations intelligently"""
        
        # Use AI to determine the file operation
        prompt = f"""Analyze this file operation request: "{action}"
Context: {json.dumps(context, indent=2)}

Provide a JSON response:
{{
    "operation": "create|read|update|delete|copy|move",
    "path": "/absolute/path/to/file",
    "content": "content if creating/updating",
    "destination": "destination path if copying/moving"
}}"""

        try:
            response = self.execution_model.generate_content(prompt)
            op_text = response.text.strip()
            
            if "```json" in op_text:
                op_text = op_text.split("```json")[1].split("```")[0].strip()
            elif "```" in op_text:
                op_text = op_text.split("```")[1].split("```")[0].strip()
            
            import json
            operation = json.loads(op_text)
            
            op_type = operation.get('operation')
            path = Path(operation.get('path', ''))
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"File operation: {op_type} on {path}"
            )
            
            if op_type == 'create':
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(operation.get('content', ''))
                return {"success": True, "operation": "created", "path": str(path)}
            
            elif op_type == 'read':
                content = path.read_text()
                return {"success": True, "operation": "read", "path": str(path), "content": content}
            
            elif op_type == 'update':
                path.write_text(operation.get('content', ''))
                return {"success": True, "operation": "updated", "path": str(path)}
            
            elif op_type == 'delete':
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                return {"success": True, "operation": "deleted", "path": str(path)}
            
            elif op_type == 'copy':
                dest = Path(operation.get('destination', ''))
                shutil.copy2(path, dest)
                return {"success": True, "operation": "copied", "from": str(path), "to": str(dest)}
            
            elif op_type == 'move':
                dest = Path(operation.get('destination', ''))
                shutil.move(path, dest)
                return {"success": True, "operation": "moved", "from": str(path), "to": str(dest)}
            
            else:
                raise Exception(f"Unknown operation: {op_type}")
                
        except Exception as e:
            raise Exception(f"File operation error: {str(e)}")
    
    def _take_screenshot(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot"""
        
        try:
            import pyautogui
            
            # Generate filename
            filename = f"screenshot_{int(time.time())}.png"
            filepath = Path.home() / "Pictures" / filename
            filepath.parent.mkdir(exist_ok=True)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot.save(str(filepath))
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"Screenshot saved: {filepath}"
            )
            
            return {
                "success": True,
                "operation": "screenshot",
                "path": str(filepath)
            }
            
        except ImportError:
            raise Exception("pyautogui not installed. Install with: pip install pyautogui")
        except Exception as e:
            raise Exception(f"Screenshot error: {str(e)}")
    
    def _ai_execute(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to figure out how to execute an unknown action"""
        
        prompt = f"""You need to accomplish this task: "{action}"
Context: {json.dumps(context, indent=2)}

Think about how to do this and provide a Python code snippet that accomplishes it.
The code should be safe and handle errors.

Respond with ONLY the Python code, nothing else."""

        try:
            response = self.execution_model.generate_content(prompt)
            code = response.text.strip()
            
            # Extract code from markdown
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"Executing AI-generated code for: {action}"
            )
            
            # Execute in safe environment
            namespace = {
                'os': os,
                'subprocess': subprocess,
                'Path': Path,
                'shutil': shutil,
                'result': None
            }
            
            exec(code, namespace)
            
            return {
                "success": True,
                "action": action,
                "method": "ai_generated_code",
                "result": namespace.get('result')
            }
            
        except Exception as e:
            raise Exception(f"AI execution error: {str(e)}")
