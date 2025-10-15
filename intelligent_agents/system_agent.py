#!/usr/bin/env python3
"""
System Agent - Controls computer operations
Can execute commands, manage files, take screenshots, etc.
ENHANCED with Context-Aware Execution Engine
"""

import os
import json
import time
import subprocess
import shutil
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional
from .agent_core import IntelligentAgent, AgentStatus

class ContextAwareEngine:
    """
    Context-Aware Engine that tracks environment, working directory,
    and provides intelligent path resolution
    """
    def __init__(self):
        self.cwd = os.getcwd()
        self.home = str(Path.home())
        self.desktop = os.path.join(self.home, "Desktop")
        self.documents = os.path.join(self.home, "Documents")
        self.downloads = os.path.join(self.home, "Downloads")
        self.os_type = platform.system()
        self.shell = os.environ.get('SHELL', '/bin/bash')
        self.env_vars = dict(os.environ)
        
    def resolve_path(self, path_hint: str) -> str:
        """Intelligently resolve a path from various hints"""
        path_hint = path_hint.strip()
        
        # Handle special keywords
        if path_hint.lower() in ['desktop', 'on desktop', 'to desktop']:
            return self.desktop
        elif path_hint.lower() in ['documents', 'docs']:
            return self.documents
        elif path_hint.lower() in ['downloads']:
            return self.downloads
        elif path_hint.lower() in ['home', '~']:
            return self.home
        
        # Expand ~ and environment variables
        expanded = os.path.expanduser(os.path.expandvars(path_hint))
        
        # If absolute path, use it
        if os.path.isabs(expanded):
            return expanded
        
        # If relative, join with cwd
        return os.path.join(self.cwd, expanded)
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context information"""
        return {
            "cwd": self.cwd,
            "home": self.home,
            "desktop": self.desktop,
            "documents": self.documents,
            "downloads": self.downloads,
            "os": self.os_type,
            "shell": self.shell
        }
    
    def set_cwd(self, new_cwd: str):
        """Update current working directory"""
        if os.path.isdir(new_cwd):
            self.cwd = new_cwd
            os.chdir(new_cwd)
            return True
        return False

class SystemAgent(IntelligentAgent):
    """
    Intelligent agent for system-level operations with context awareness
    """
    
    def __init__(self, update_callback=None):
        super().__init__(
            name="SystemAgent",
            capabilities=[
                "execute_shell_commands",
                "file_operations",
                "process_management",
                "system_information",
                "screenshot_capture",
                "context_aware_execution"
            ],
            update_callback=update_callback
        )
        
        # Initialize context-aware engine
        self.context_engine = ContextAwareEngine()
        
        # Execution log for debugging
        self.execution_log = []
    
    def _log_execution(self, action: str, details: Dict[str, Any]):
        """Log execution for debugging"""
        log_entry = {
            "timestamp": time.time(),
            "action": action,
            "details": details,
            "context": self.context_engine.get_context()
        }
        self.execution_log.append(log_entry)
        print(f"[SYSTEM AGENT] {action}: {json.dumps(details, indent=2)}")
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a system operation step with enhanced context awareness"""
        
        tool = step.get('tool', 'auto')
        action = step.get('action', '')
        
        # Merge context with engine context
        full_context = {**self.context_engine.get_context(), **(context or {})}
        
        # Let AI decide which tool to use if not specified
        if tool == 'auto':
            tool = self._decide_tool(action, full_context)

        # Normalize common synonyms from AI outputs
        tool_map = {
            'execute_shell_command': 'shell_command',
            'execute_shell_commands': 'shell_command',
            'shell': 'shell_command',
            'shell_commands': 'shell_command',
            'file_operations': 'file_operation',
            'file': 'file_operation',
            'files': 'file_operation',
            'screenshot_capture': 'screenshot',
            'capture_screenshot': 'screenshot',
        }
        tool = tool_map.get(str(tool).strip().lower(), tool)
        
        self._send_update(
            AgentStatus.EXECUTING,
            f"🔧 Tool: {tool} | Action: {action}"
        )
        
        self._log_execution("STEP_START", {
            "tool": tool,
            "action": action,
            "step": step
        })
        
        # Route to appropriate tool
        try:
            if tool == 'shell_command':
                result = self._execute_shell_command(action, full_context)
            elif tool == 'file_operation':
                result = self._execute_file_operation(action, full_context)
            elif tool == 'screenshot':
                result = self._take_screenshot(action, full_context)
            else:
                # Use AI to figure out how to execute
                result = self._ai_execute(action, full_context)
            
            self._log_execution("STEP_SUCCESS", {
                "tool": tool,
                "result": result
            })
            
            return result
            
        except Exception as e:
            self._log_execution("STEP_ERROR", {
                "tool": tool,
                "error": str(e)
            })
            raise
    
    def _decide_tool(self, action: str, context: Dict[str, Any]) -> str:
        """Use AI to decide which tool to use"""
        
        # Quick keyword matching for common cases
        action_lower = action.lower()
        
        # Screenshot keywords - HIGHEST PRIORITY
        if any(word in action_lower for word in ['screenshot', 'capture screen', 'screen grab', 'take picture of screen']):
            return 'screenshot'
        
        # File operation keywords
        if any(word in action_lower for word in ['create file', 'create folder', 'make directory', 'mkdir', 'touch']):
            return 'file_operation'
        
        # Shell command keywords
        if any(word in action_lower for word in ['list', 'ls', 'find', 'grep', 'check', 'show', 'ps', 'kill']):
            return 'shell_command'
        
        # If no clear match, ask AI
        prompt = f"""Given this action: "{action}"
Current Context:
- Working Directory: {context.get('cwd', 'unknown')}
- OS: {context.get('os', 'unknown')}
- Desktop: {context.get('desktop', 'unknown')}

Which tool should be used? Choose from:
- shell_command: Execute terminal/bash commands (ls, cd, grep, find, ps, etc.)
- file_operation: Create, read, update, delete files and directories (PREFERRED for file/folder creation)
- screenshot: Capture screen (for screenshot/screen capture tasks)
- process_management: Kill/start processes

CRITICAL RULES: 
- For ANY screenshot/screen capture → MUST use "screenshot"
- For "create file" or "create folder" → use file_operation
- For "list", "show", "check", "find" → use shell_command

Respond with just the tool name, nothing else."""

        try:
            response = self._get_execution_model().generate_content(prompt)
            tool = response.text.strip().lower().replace(' ', '_')
            self._log_execution("TOOL_DECISION", {"action": action, "tool": tool})
            return tool
        except Exception as e:
            self._log_execution("TOOL_DECISION_ERROR", {"error": str(e)})
            # Default to file_operation if action contains "create" or "file"
            if "create" in action.lower() and ("file" in action.lower() or "folder" in action.lower()):
                return 'file_operation'
            return 'shell_command'
    
    def _execute_shell_command(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a shell command intelligently with proper working directory"""
        
        # Use AI to generate the actual command with context awareness
        prompt = f"""Generate a safe bash command to accomplish: "{action}"

Current System Context:
- Working Directory: {context.get('cwd')}
- Home Directory: {context.get('home')}
- Desktop: {context.get('desktop')}
- OS: {context.get('os')}
- Shell: {context.get('shell')}

Important Rules:
1. Generate ONLY the command, no explanation
2. Use absolute paths when working with files
3. DO NOT add || true or || echo to commands - let failures fail naturally
4. For file creation, use touch or echo > file
5. For directory creation, use mkdir -p
6. Safe to execute (no rm -rf /, no dangerous operations)
7. If action mentions "desktop", use: {context.get('desktop')}
8. If action mentions "home", use: {context.get('home')}
9. Return CLEAN commands only - no error suppression

Examples:
- "create a file test.txt on desktop" → touch {context.get('desktop')}/test.txt
- "list files" → ls -la {context.get('cwd')}
- "check disk space" → df -h
- "show current directory" → pwd

Command:"""

        try:
            response = self._get_execution_model().generate_content(prompt)
            command = response.text.strip()
            
            # Remove markdown code blocks if present
            if '```' in command:
                lines = command.split('\n')
                command_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or not line.strip().startswith('```'):
                        command_lines.append(line)
                command = '\n'.join(command_lines).strip()
            
            # Remove any remaining bash/sh prefix
            if command.startswith('bash') or command.startswith('sh'):
                command = ' '.join(command.split()[1:])
            
            # CRITICAL: Remove error suppression that AI might add
            # Remove || true, || echo, etc.
            if '||' in command:
                # Only keep the part before ||
                command = command.split('||')[0].strip()
            
            # Remove trailing ; or && that might cause issues
            command = command.rstrip(';').strip()
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"💻 Executing: {command}"
            )
            
            self._log_execution("SHELL_COMMAND", {
                "command": command,
                "cwd": context.get('cwd')
            })
            
            # Execute the command with proper working directory
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=context.get('cwd'),
                env=self.context_engine.env_vars
            )
            
            output = result.stdout.strip()
            error = result.stderr.strip()
            
            # Check if it's a cd command - update context
            if command.strip().startswith('cd '):
                new_dir = command.strip()[3:].strip()
                new_dir = self.context_engine.resolve_path(new_dir)
                self.context_engine.set_cwd(new_dir)
            
            if result.returncode == 0:
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Command successful: {output[:100] if output else 'No output'}"
                )
                
                return {
                    "success": True,
                    "command": command,
                    "output": output,
                    "error": error if error else None,
                    "action": action,
                    "exit_code": 0
                }
            else:
                # Command failed but we have details
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"⚠️ Command returned non-zero: {error[:100]}"
                )
                
                raise Exception(f"Command failed (exit {result.returncode}): {error or 'Unknown error'}")
                
        except subprocess.TimeoutExpired:
            error_msg = "Command timeout - took longer than 60 seconds"
            self._log_execution("SHELL_TIMEOUT", {"command": command})
            raise Exception(error_msg)
        except Exception as e:
            self._log_execution("SHELL_ERROR", {"error": str(e)})
            raise Exception(f"Shell command error: {str(e)}")
    
    def _execute_file_operation(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file operations intelligently with context-aware path resolution"""
        
        # Use AI to determine the file operation with full context
        prompt = f"""Analyze this file operation request: "{action}"

Current System Context:
- Working Directory: {context.get('cwd')}
- Home Directory: {context.get('home')}
- Desktop: {context.get('desktop')}
- Documents: {context.get('documents')}
- Downloads: {context.get('downloads')}

Provide a JSON response for the file operation:
{{
    "operation": "create|read|update|delete|copy|move|mkdir",
    "path": "/absolute/path/to/file or directory",
    "content": "content if creating/updating file",
    "destination": "destination path if copying/moving"
}}

Path Resolution Rules:
- If action says "desktop" or "on desktop": use {context.get('desktop')}/filename
- If action says "documents": use {context.get('documents')}/filename  
- If action says "home": use {context.get('home')}/filename
- If relative path given: use {context.get('cwd')}/filename
- Always use absolute paths

Examples:
- "create a file test.txt on desktop" → {{"operation": "create", "path": "{context.get('desktop')}/test.txt", "content": ""}}
- "create folder MyFolder on desktop" → {{"operation": "mkdir", "path": "{context.get('desktop')}/MyFolder"}}
- "read file data.json" → {{"operation": "read", "path": "{context.get('cwd')}/data.json"}}

JSON Response:"""

        try:
            response = self._get_execution_model().generate_content(prompt)
            op_text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in op_text:
                op_text = op_text.split("```json")[1].split("```")[0].strip()
            elif "```" in op_text:
                op_text = op_text.split("```")[1].split("```")[0].strip()
            
            operation = json.loads(op_text)
            
            op_type = str(operation.get('operation', '')).strip().lower()
            raw_path = str(operation.get('path', '')).strip()
            
            if not raw_path:
                raise Exception("Missing 'path' for file operation")
            
            # Use context-aware path resolution
            path = Path(self.context_engine.resolve_path(raw_path))
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"📁 File Operation: {op_type} on {path}"
            )
            
            self._log_execution("FILE_OPERATION", {
                "operation": op_type,
                "path": str(path),
                "raw_path": raw_path
            })
            
            # Execute the file operation
            if op_type == 'create':
                # Create parent directories
                path.parent.mkdir(parents=True, exist_ok=True)
                content = operation.get('content', '')
                path.write_text(content)
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Created file: {path}"
                )
                
                return {
                    "success": True,
                    "operation": "created",
                    "path": str(path),
                    "size": len(content),
                    "exists": path.exists()
                }
            
            elif op_type == 'mkdir':
                # Create directory
                path.mkdir(parents=True, exist_ok=True)
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Created directory: {path}"
                )
                
                return {
                    "success": True,
                    "operation": "mkdir",
                    "path": str(path),
                    "exists": path.exists(),
                    "is_dir": path.is_dir()
                }
            
            elif op_type == 'read':
                if not path.exists():
                    raise Exception(f"File not found: {path}")
                
                content = path.read_text()
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Read file: {path} ({len(content)} bytes)"
                )
                
                return {
                    "success": True,
                    "operation": "read",
                    "path": str(path),
                    "content": content,
                    "size": len(content)
                }
            
            elif op_type == 'update':
                if not path.exists():
                    raise Exception(f"File not found: {path}")
                
                content = operation.get('content', '')
                path.write_text(content)
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Updated file: {path}"
                )
                
                return {
                    "success": True,
                    "operation": "updated",
                    "path": str(path),
                    "size": len(content)
                }
            
            elif op_type == 'delete':
                if not path.exists():
                    raise Exception(f"Path not found: {path}")
                
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Deleted: {path}"
                )
                
                return {
                    "success": True,
                    "operation": "deleted",
                    "path": str(path),
                    "exists": path.exists()
                }
            
            elif op_type == 'copy':
                dest_path = operation.get('destination', '')
                if not dest_path:
                    raise Exception("Missing destination for copy operation")
                
                dest = Path(self.context_engine.resolve_path(dest_path))
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                if path.is_file():
                    shutil.copy2(path, dest)
                elif path.is_dir():
                    shutil.copytree(path, dest, dirs_exist_ok=True)
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Copied: {path} → {dest}"
                )
                
                return {
                    "success": True,
                    "operation": "copied",
                    "from": str(path),
                    "to": str(dest),
                    "exists": dest.exists()
                }
            
            elif op_type == 'move':
                dest_path = operation.get('destination', '')
                if not dest_path:
                    raise Exception("Missing destination for move operation")
                
                dest = Path(self.context_engine.resolve_path(dest_path))
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                shutil.move(str(path), str(dest))
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Moved: {path} → {dest}"
                )
                
                return {
                    "success": True,
                    "operation": "moved",
                    "from": str(path),
                    "to": str(dest),
                    "exists": dest.exists()
                }
            
            else:
                raise Exception(f"Unknown file operation: {op_type}")
                
        except json.JSONDecodeError as e:
            self._log_execution("FILE_OPERATION_JSON_ERROR", {"error": str(e), "text": op_text})
            raise Exception(f"Failed to parse file operation JSON: {str(e)}")
        except Exception as e:
            self._log_execution("FILE_OPERATION_ERROR", {"error": str(e)})
            raise Exception(f"File operation error: {str(e)}")
    
    def _take_screenshot(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot with context-aware saving"""
        
        try:
            # Generate filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
            # Use Pictures directory or Desktop as fallback
            pictures_dir = os.path.join(context.get('home'), "Pictures")
            if os.path.exists(pictures_dir):
                filepath = Path(pictures_dir) / filename
            else:
                filepath = Path(context.get('desktop')) / filename
            
            filepath.parent.mkdir(exist_ok=True)
            
            # Take screenshot
            self._send_update(
                AgentStatus.EXECUTING,
                f"📸 Capturing screenshot..."
            )
            
            # Try multiple methods in order of preference
            screenshot_taken = False
            error_msg = ""
            
            # Method 1: Try pyscreenshot with childprocess=False (direct)
            try:
                import pyscreenshot as ImageGrab
                screenshot = ImageGrab.grab(childprocess=False)
                screenshot.save(str(filepath))
                screenshot_taken = True
            except Exception as e1:
                error_msg = f"pyscreenshot failed: {str(e1)}"
                
                # Method 2: Try using gnome-screenshot command
                try:
                    result = subprocess.run(
                        ['gnome-screenshot', '-f', str(filepath)],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and filepath.exists():
                        screenshot_taken = True
                    else:
                        error_msg += f" | gnome-screenshot failed: {result.stderr}"
                except FileNotFoundError:
                    error_msg += " | gnome-screenshot not installed"
                except Exception as e2:
                    error_msg += f" | gnome-screenshot error: {str(e2)}"
                
                # Method 3: Try using scrot command
                if not screenshot_taken:
                    try:
                        result = subprocess.run(
                            ['scrot', str(filepath)],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and filepath.exists():
                            screenshot_taken = True
                        else:
                            error_msg += f" | scrot failed: {result.stderr}"
                    except FileNotFoundError:
                        error_msg += " | scrot not installed"
                    except Exception as e3:
                        error_msg += f" | scrot error: {str(e3)}"
                
                # Method 4: Try ImageMagick's import command
                if not screenshot_taken:
                    try:
                        result = subprocess.run(
                            ['import', '-window', 'root', str(filepath)],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0 and filepath.exists():
                            screenshot_taken = True
                        else:
                            error_msg += f" | imagemagick failed: {result.stderr}"
                    except FileNotFoundError:
                        error_msg += " | imagemagick not installed"
                    except Exception as e4:
                        error_msg += f" | imagemagick error: {str(e4)}"
            
            if not screenshot_taken:
                raise Exception(f"All screenshot methods failed. {error_msg}\nPlease install one of: gnome-screenshot, scrot, or imagemagick")
            
            # Verify file was created
            if not filepath.exists():
                raise Exception(f"Screenshot file was not created at {filepath}")
            
            file_size_kb = filepath.stat().st_size / 1024
            
            self._send_update(
                AgentStatus.SUCCESS,
                f"✅ Screenshot captured and saved!\n📁 Location: {filepath}\n📏 Size: {file_size_kb:.1f} KB"
            )
            
            self._log_execution("SCREENSHOT", {
                "path": str(filepath),
                "size_kb": file_size_kb,
                "exists": filepath.exists()
            })
            
            return {
                "success": True,
                "operation": "screenshot",
                "message": f"Screenshot saved to {filepath} ({file_size_kb:.1f} KB)",
                "path": str(filepath),
                "exists": filepath.exists(),
                "size": filepath.stat().st_size,
                "size_kb": file_size_kb
            }
            
        except ImportError as ie:
            error_msg = f"Screenshot library not installed: {str(ie)}. Run: pip install pyscreenshot pillow"
            self._log_execution("SCREENSHOT_ERROR", {"error": error_msg})
            raise Exception(error_msg)
        except Exception as e:
            self._log_execution("SCREENSHOT_ERROR", {"error": str(e)})
            raise Exception(f"Screenshot error: {str(e)}")
    
    def _ai_execute(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to figure out how to execute an unknown action with context awareness"""
        
        prompt = f"""You need to accomplish this task: "{action}"

Current System Context:
- Working Directory: {context.get('cwd')}
- Home Directory: {context.get('home')}
- Desktop: {context.get('desktop')}
- OS: {context.get('os')}

Think about how to do this safely. Provide a Python code snippet that:
1. Uses absolute paths (available in context dict)
2. Creates parent directories if needed
3. Handles errors gracefully
4. Returns a result dict with 'success' and relevant info

Available in namespace: os, subprocess, Path, shutil, context

Example for "create file test.txt on desktop":
```python
from pathlib import Path
target = Path(context['desktop']) / 'test.txt'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("")
result = {{"success": True, "path": str(target), "created": True}}
```

Respond with ONLY the Python code, nothing else."""

        try:
            response = self._get_execution_model().generate_content(prompt)
            code = response.text.strip()
            
            # Extract code from markdown
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"🤖 Executing AI-generated solution..."
            )
            
            self._log_execution("AI_EXECUTE", {
                "action": action,
                "code": code[:200]  # Log first 200 chars
            })
            
            # Execute in controlled environment with context
            namespace = {
                'os': os,
                'subprocess': subprocess,
                'Path': Path,
                'shutil': shutil,
                'context': context,
                'result': None
            }
            
            exec(code, namespace)
            result = namespace.get('result')
            
            # If no result was set, try to infer success
            if result is None:
                result = {
                    "success": True,
                    "action": action,
                    "method": "ai_generated_code",
                    "note": "Code executed but no explicit result returned"
                }
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"✅ AI execution completed"
            )
            
            return {
                "success": True,
                "action": action,
                "method": "ai_generated_code",
                "result": result
            }
            
        except Exception as e:
            self._log_execution("AI_EXECUTE_ERROR", {"error": str(e)})
            raise Exception(f"AI execution error: {str(e)}")
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get execution log for debugging"""
        return self.execution_log
    
    def clear_execution_log(self):
        """Clear execution log"""
        self.execution_log = []
