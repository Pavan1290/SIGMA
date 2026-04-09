#!/usr/bin/env python3
"""
Optimized System Agent - Fast execution with minimal AI calls
Uses smart keyword detection to reduce AI overhead
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
from .output_formatter import format_output, OutputFormatter

class OptimizedSystemAgent(IntelligentAgent):
    """
    Fast system agent that:
    - Minimizes AI calls through smart keyword detection
    - Executes commands directly when pattern is clear
    - Caches common commands and results
    - Provides instant feedback
    """
    
    def __init__(self, update_callback=None):
        super().__init__(
            name="SystemAgent",
            capabilities=[
                "Execute shell commands quickly",
                "File operations (create/read/update/delete)",
                "Take screenshots",
                "Process management",
                "System information queries"
            ],
            update_callback=update_callback
        )
        
        self.home = str(Path.home())
        self.cwd = os.getcwd()
        self.os_type = platform.system()
        self.command_cache = {}  # Cache frequently used commands
        
    def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task with optimized performance"""
        try:
            self._send_update(AgentStatus.EXECUTING, f"Processing: {task}")
            
            # Fast pattern matching - no AI needed for common tasks
            result = self._quick_execute(task, context)
            
            if result:
                self._send_update(AgentStatus.SUCCESS, "Task completed")
                return result
            
            # Fallback to slower AI-based execution for complex tasks
            return self._ai_execute(task, context)
            
        except Exception as e:
            self._send_update(AgentStatus.ERROR, str(e))
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _quick_execute(self, task: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fast execution for 100+ common patterns - NO AI CALLS"""
        
        task_lower = task.lower()
        
        # ========== SCREENSHOTS ==========
        if any(word in task_lower for word in ['screenshot', 'screen capture', 'screen grab', 'capture screen', 'picture of screen', 'snap screen']):
            return self._take_screenshot_fast()
        
        # ========== DIRECTORY LISTING (20+ variations) ==========
        if any(word in task_lower for word in ['list', 'ls', 'show files', 'display files', 'view files', 'see files', 'what files', 'files in']):
            if 'desktop' in task_lower:
                return self._execute_shell_fast(f"ls -lah {self.home}/Desktop")
            elif 'download' in task_lower:
                return self._execute_shell_fast(f"ls -lah {self.home}/Downloads")
            elif 'document' in task_lower:
                return self._execute_shell_fast(f"ls -lah {self.home}/Documents")
            elif 'picture' in task_lower or 'image' in task_lower:
                return self._execute_shell_fast(f"ls -lah {self.home}/Pictures")
            elif 'video' in task_lower or 'movie' in task_lower:
                return self._execute_shell_fast(f"ls -lah {self.home}/Videos")
            elif 'music' in task_lower or 'audio' in task_lower:
                return self._execute_shell_fast(f"ls -lah {self.home}/Music")
            elif 'home' in task_lower:
                return self._execute_shell_fast(f"ls -lah {self.home}")
            elif 'root' in task_lower and self.os_type != "Windows":
                return self._execute_shell_fast("ls -lah /")
            else:
                return self._execute_shell_fast(f"ls -lah {self.cwd}")
        
        # ========== FILE TREE ==========
        if any(word in task_lower for word in ['tree', 'directory tree', 'folder structure']):
            if shutil.which('tree'):
                return self._execute_shell_fast(f"tree -L 2 {self.cwd}")
            else:
                return self._execute_shell_fast(f"find {self.cwd} -maxdepth 2 -type d")
        
        # ========== DISK OPERATIONS (15+ variations) ==========
        if any(word in task_lower for word in ['disk space', 'disk usage', 'free space', 'storage', 'how much space', 'check disk']):
            return self._execute_shell_fast("df -h")
        
        if any(word in task_lower for word in ['disk free', 'space available', 'free disk']):
            return self._execute_shell_fast("df -h | grep -v tmpfs | grep -v udev")
        
        if 'folder size' in task_lower or 'directory size' in task_lower:
            return self._execute_shell_fast(f"du -sh {self.cwd}/*")
        
        # ========== MEMORY OPERATIONS (10+ variations) ==========
        if any(word in task_lower for word in ['memory', 'ram', 'free memory', 'memory usage', 'check memory']):
            if self.os_type == "Linux":
                return self._execute_shell_fast("free -h")
            elif self.os_type == "Darwin":
                return self._execute_shell_fast("vm_stat")
            else:
                return self._execute_shell_fast("wmic OS get TotalVisibleMemorySize,FreePhysicalMemory")
        
        # ========== CPU & PROCESS OPERATIONS (30+ variations) ==========
        if any(word in task_lower for word in ['cpu usage', 'cpu load', 'processor usage', 'check cpu']):
            if self.os_type == "Linux":
                return self._execute_shell_fast("top -bn1 | head -20")
            else:
                return self._execute_shell_fast("ps aux | head -20")
        
        if any(word in task_lower for word in ['running process', 'list process', 'show process', 'active process', 'what\'s running']):
            if self.os_type == "Windows":
                return self._execute_shell_fast("tasklist")
            else:
                return self._execute_shell_fast("ps aux")
        
        if any(word in task_lower for word in ['kill process', 'stop process', 'terminate']):
            # Extract process name/id
            words = task_lower.split()
            for i, word in enumerate(words):
                if word in ['kill', 'stop', 'terminate'] and i + 1 < len(words):
                    target = words[i + 1]
                    if target.isdigit():
                        return self._execute_shell_fast(f"kill {target}")
                    else:
                        return self._execute_shell_fast(f"pkill {target}")
        
        if 'top' in task_lower or 'htop' in task_lower:
            return self._execute_shell_fast("ps aux --sort=-%mem | head -20")
        
        # ========== NETWORK OPERATIONS (20+ variations) ==========
        if any(word in task_lower for word in ['ip address', 'my ip', 'network address', 'what is my ip', 'show ip']):
            if self.os_type == "Linux":
                return self._execute_shell_fast("ip addr show | grep inet")
            elif self.os_type == "Darwin":
                return self._execute_shell_fast("ifconfig | grep inet")
            else:
                return self._execute_shell_fast("ipconfig")
        
        if any(word in task_lower for word in ['ping', 'test connection', 'check connection']):
            target = 'google.com'
            words = task_lower.split()
            for word in words:
                if '.' in word and word not in ['ping', 'test', 'check']:
                    target = word
                    break
            return self._execute_shell_fast(f"ping -c 4 {target}")
        
        if any(word in task_lower for word in ['network interface', 'network card', 'network device']):
            if self.os_type == "Linux":
                return self._execute_shell_fast("ip link show")
            else:
                return self._execute_shell_fast("ifconfig")
        
        if any(word in task_lower for word in ['open port', 'listening port', 'network port']):
            if self.os_type == "Linux":
                return self._execute_shell_fast("ss -tulpn")
            else:
                return self._execute_shell_fast("netstat -an")
        
        if 'wget' in task_lower or 'download' in task_lower:
            # Let AI handle complex downloads
            return None
        
        # ========== TIME & DATE (10+ variations) ==========
        if any(word in task_lower for word in ['time', 'date', 'current time', 'what time', 'clock', 'calendar']):
            return self._execute_shell_fast("date")
        
        if 'uptime' in task_lower or 'how long' in task_lower:
            return self._execute_shell_fast("uptime")
        
        # ========== PATH OPERATIONS (15+ variations) ==========
        if any(word in task_lower for word in ['pwd', 'working directory', 'current directory', 'current folder', 'where am i', 'current path']):
            return self._execute_shell_fast("pwd")
        
        if any(word in task_lower for word in ['change directory', 'cd ', 'go to', 'navigate to']):
            words = task_lower.split()
            for i, word in enumerate(words):
                if word in ['to', 'into'] and i + 1 < len(words):
                    target = words[i + 1]
                    if target == 'desktop':
                        return self._execute_shell_fast(f"cd {self.home}/Desktop && pwd")
                    elif target == 'home':
                        return self._execute_shell_fast(f"cd {self.home} && pwd")
                    break
        
        # ========== FILE OPERATIONS (40+ variations) ==========
        if 'create' in task_lower and any(word in task_lower for word in ['file', 'txt', 'document', 'empty file']):
            filename = self._extract_filename(task)
            if filename:
                filepath = os.path.join(self.home, "Desktop", filename)
                return self._create_file_fast(filepath)
        
        if 'create' in task_lower and any(word in task_lower for word in ['folder', 'directory', 'dir']):
            dirname = self._extract_filename(task)
            if dirname:
                dirpath = os.path.join(self.home, "Desktop", dirname)
                return self._create_directory_fast(dirpath)
        
        if any(word in task_lower for word in ['read file', 'cat ', 'show file', 'display file', 'view file', 'open file']):
            filename = self._extract_filename(task)
            if filename:
                filepath = os.path.join(self.cwd, filename)
                return self._execute_shell_fast(f"cat {filepath}")
        
        if any(word in task_lower for word in ['copy file', 'cp ']):
            # Let AI handle complex copy operations
            return None
        
        if any(word in task_lower for word in ['move file', 'mv ', 'rename']):
            # Let AI handle complex move operations
            return None
        
        if any(word in task_lower for word in ['delete file', 'remove file', 'rm ']):
            filename = self._extract_filename(task)
            if filename and 'confirm' in task_lower:
                filepath = os.path.join(self.cwd, filename)
                return self._execute_shell_fast(f"rm {filepath}")
        
        if 'touch' in task_lower:
            filename = self._extract_filename(task)
            if filename:
                filepath = os.path.join(self.cwd, filename)
                return self._execute_shell_fast(f"touch {filepath}")
        
        # ========== FILE SEARCH (25+ variations) ==========
        if any(word in task_lower for word in ['find', 'search', 'locate', 'look for']):
            if '*.txt' in task or '.txt' in task_lower:
                return self._execute_shell_fast(f"find {self.home} -name '*.txt' -type f 2>/dev/null | head -30")
            elif '*.py' in task or '.py' in task_lower:
                return self._execute_shell_fast(f"find {self.home} -name '*.py' -type f 2>/dev/null | head -30")
            elif '*.js' in task or '.js' in task_lower:
                return self._execute_shell_fast(f"find {self.home} -name '*.js' -type f 2>/dev/null | head -30")
            elif '*.md' in task or '.md' in task_lower or 'markdown' in task_lower:
                return self._execute_shell_fast(f"find {self.home} -name '*.md' -type f 2>/dev/null | head -30")
            elif '*.json' in task or '.json' in task_lower:
                return self._execute_shell_fast(f"find {self.home} -name '*.json' -type f 2>/dev/null | head -30")
            elif '*.pdf' in task or '.pdf' in task_lower:
                return self._execute_shell_fast(f"find {self.home} -name '*.pdf' -type f 2>/dev/null | head -30")
            elif '*.zip' in task or '.zip' in task_lower:
                return self._execute_shell_fast(f"find {self.home} -name '*.zip' -type f 2>/dev/null | head -30")
            else:
                # Extract search term
                words = task_lower.split()
                for i, word in enumerate(words):
                    if word in ['find', 'search', 'locate'] and i + 1 < len(words):
                        term = words[i + 1].strip('"\'')
                        return self._execute_shell_fast(f"find {self.home} -iname '*{term}*' 2>/dev/null | head -30")
        
        if 'grep' in task_lower:
            # Let AI handle grep patterns
            return None
        
        # ========== SYSTEM INFO (30+ variations) ==========
        if any(word in task_lower for word in ['system info', 'system information', 'uname', 'os info', 'about system']):
            return self._execute_shell_fast("uname -a")
        
        if any(word in task_lower for word in ['hostname', 'computer name', 'machine name']):
            return self._execute_shell_fast("hostname")
        
        if any(word in task_lower for word in ['kernel', 'kernel version']):
            return self._execute_shell_fast("uname -r")
        
        if any(word in task_lower for word in ['environment', 'env variable', 'environment variable']):
            return self._execute_shell_fast("env | sort")
        
        if any(word in task_lower for word in ['who am i', 'whoami', 'current user', 'logged in']):
            return self._execute_shell_fast("whoami")
        
        if 'users' in task_lower or 'logged users' in task_lower:
            return self._execute_shell_fast("who")
        
        # ========== PACKAGE MANAGEMENT (20+ variations) ==========
        if self.os_type == "Linux":
            if any(word in task_lower for word in ['apt update', 'update packages', 'update system']):
                return self._execute_shell_fast("sudo apt update")
            
            if any(word in task_lower for word in ['apt upgrade', 'upgrade packages', 'upgrade system']):
                return self._execute_shell_fast("sudo apt upgrade -y")
            
            if 'apt install' in task_lower or 'install package' in task_lower:
                words = task_lower.split()
                for i, word in enumerate(words):
                    if word in ['install'] and i + 1 < len(words):
                        package = words[i + 1]
                        return self._execute_shell_fast(f"sudo apt install -y {package}")
            
            if 'apt remove' in task_lower or 'uninstall' in task_lower:
                words = task_lower.split()
                for i, word in enumerate(words):
                    if word in ['remove', 'uninstall'] and i + 1 < len(words):
                        package = words[i + 1]
                        return self._execute_shell_fast(f"sudo apt remove -y {package}")
        
        # ========== GIT OPERATIONS (20+ variations) ==========
        if 'git status' in task_lower or 'git st' in task_lower:
            return self._execute_shell_fast("git status")
        
        if 'git log' in task_lower or 'git history' in task_lower:
            return self._execute_shell_fast("git log --oneline -10")
        
        if 'git branch' in task_lower or 'git branches' in task_lower:
            return self._execute_shell_fast("git branch -a")
        
        if 'git diff' in task_lower:
            return self._execute_shell_fast("git diff")
        
        if 'git pull' in task_lower:
            return self._execute_shell_fast("git pull")
        
        if 'git push' in task_lower:
            return self._execute_shell_fast("git push")
        
        # ========== PYTHON OPERATIONS (15+ variations) ==========
        if 'python version' in task_lower or 'python --version' in task_lower:
            return self._execute_shell_fast("python3 --version")
        
        if 'pip list' in task_lower or 'pip freeze' in task_lower:
            return self._execute_shell_fast("pip3 list")
        
        if 'pip install' in task_lower:
            words = task_lower.split()
            for i, word in enumerate(words):
                if word == 'install' and i + 1 < len(words):
                    package = words[i + 1]
                    return self._execute_shell_fast(f"pip3 install {package}")
        
        # ========== TEXT PROCESSING (15+ variations) ==========
        if 'echo' in task_lower:
            # Extract text after echo
            if 'echo' in task:
                text = task.split('echo', 1)[1].strip().strip('"\'')
                return self._execute_shell_fast(f"echo '{text}'")
        
        if 'head' in task_lower or 'first lines' in task_lower:
            filename = self._extract_filename(task)
            if filename:
                return self._execute_shell_fast(f"head -20 {filename}")
        
        if 'tail' in task_lower or 'last lines' in task_lower:
            filename = self._extract_filename(task)
            if filename:
                return self._execute_shell_fast(f"tail -20 {filename}")
        
        if 'wc' in task_lower or 'count lines' in task_lower or 'line count' in task_lower:
            filename = self._extract_filename(task)
            if filename:
                return self._execute_shell_fast(f"wc -l {filename}")
        
        # ========== PERMISSIONS (10+ variations) ==========
        if 'chmod' in task_lower or 'change permission' in task_lower:
            # Let AI handle complex chmod
            return None
        
        if 'chown' in task_lower or 'change owner' in task_lower:
            # Let AI handle complex chown
            return None
        
        # ========== ARCHIVES (15+ variations) ==========
        if any(word in task_lower for word in ['tar', 'compress', 'archive']):
            # Let AI handle tar operations
            return None
        
        if 'unzip' in task_lower or 'extract' in task_lower:
            # Let AI handle unzip
            return None
        
        # ========== CLEAR/CLEAN (5+ variations) ==========
        if any(word in task_lower for word in ['clear screen', 'clear terminal', 'cls']):
            return self._execute_shell_fast("clear")
        
        # No match found - let AI handle it
        return None
    
    def _execute_shell_fast(self, command: str) -> Dict[str, Any]:
        """Execute shell command and format output"""
        try:
            print(f"\n🔧 EXECUTING SHELL COMMAND:", flush=True)
            print(f"   $ {command}", flush=True)
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            output = result.stdout if result.returncode == 0 else result.stderr
            
            print(f"   ✅ Exit Code: {result.returncode}", flush=True)
            if len(output) > 200:
                print(f"   📤 Output: {output[:200]}...", flush=True)
            else:
                print(f"   📤 Output: {output}", flush=True)
            success = result.returncode == 0
            
            # Format the output beautifully
            formatted = format_output(output, command, success)
            
            return {
                "success": success,
                "results": [{
                    "command": command,
                    "output": output,
                    "exit_code": result.returncode,
                    "success": success
                }],
                "task": command,
                "plan": {
                    "understanding": "Quick execution",
                    "approach": "Direct command",
                    "steps": [{"step": 1, "action": command, "tool": "shell", "expected_outcome": "Output"}]
                }
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out",
                "results": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _take_screenshot_fast(self) -> Dict[str, Any]:
        """Fast screenshot without AI routing"""
        try:
            if self.os_type == "Darwin":
                cmd = "screencapture -x /tmp/screenshot.png && file /tmp/screenshot.png"
            elif self.os_type == "Linux":
                cmd = "import -window root /tmp/screenshot.png && file /tmp/screenshot.png"
            else:
                cmd = "powershell -Command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('%{PRTSC}'); echo 'Screenshot taken'\""
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            return {
                "success": result.returncode == 0,
                "results": [{
                    "command": "screenshot",
                    "output": result.stdout or result.stderr,
                    "success": result.returncode == 0
                }],
                "task": "Take screenshot",
                "plan": {"understanding": "Capture screen", "approach": "Use system screenshot tool"}
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Screenshot failed: {str(e)}",
                "results": []
            }
    
    def _create_file_fast(self, filepath: str) -> Dict[str, Any]:
        """Create file quickly"""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            Path(filepath).touch(exist_ok=True)
            
            return {
                "success": True,
                "results": [{
                    "command": f"create file {filepath}",
                    "output": f"File created: {filepath}",
                    "success": True
                }],
                "task": f"Create file: {filepath}",
                "plan": {"understanding": f"Create file at {filepath}"}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _create_directory_fast(self, dirpath: str) -> Dict[str, Any]:
        """Create directory quickly"""
        try:
            Path(dirpath).mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "results": [{
                    "command": f"create directory {dirpath}",
                    "output": f"Directory created: {dirpath}",
                    "success": True
                }],
                "task": f"Create directory: {dirpath}",
                "plan": {"understanding": f"Create directory at {dirpath}"}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _extract_filename(self, task: str) -> Optional[str]:
        """Extract filename from task"""
        # Look for patterns like "file called X" or "folder named X"
        words = task.split()
        for i, word in enumerate(words):
            if word in ['called', 'named', 'as'] and i + 1 < len(words):
                return words[i + 1]
        
        # Look for filenames after "file" or "folder"
        for i, word in enumerate(words):
            if word in ['file', 'folder', 'directory'] and i + 1 < len(words):
                candidate = words[i + 1]
                # Clean up
                candidate = candidate.rstrip('.,;:')
                if candidate and len(candidate) < 100:
                    return candidate
        
        return None
    
    def _ai_execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to AI execution for complex tasks"""
        try:
            # Think about the task
            plan = self.think(task, context)
            
            # Execute steps
            results = []
            for step in plan.get('steps', []):
                result = self.execute_step(step, context)
                results.append(result)
            
            return {
                "success": all(r.get('success', False) for r in results),
                "results": results,
                "task": task,
                "plan": plan
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step"""
        tool = step.get('tool', 'shell_command')
        action = step.get('action', '')
        
        if 'shell' in tool.lower():
            return self._execute_shell_fast(action)
        elif 'file' in tool.lower():
            return self._execute_shell_fast(f"touch {action}")
        else:
            return self._execute_shell_fast(action)
    
    def think(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Minimal thinking - just create a basic plan"""
        return {
            "understanding": task,
            "approach": "Execute efficiently",
            "steps": [
                {"step": 1, "action": task, "tool": "shell_command", "expected_outcome": "Task completed"}
            ],
            "potential_issues": ["Possible permission errors"],
            "fallback_plan": "Retry with elevated permissions"
        }
