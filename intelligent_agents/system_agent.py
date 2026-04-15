#!/usr/bin/env python3
"""
ULTIMATE SYSTEM AGENT - Fully Advanced & Optimized
Combines fast pattern matching with context-aware AI execution
Supports 150+ system tasks with minimal AI overhead

Features:
- Lightning-fast execution for 150+ common tasks (no AI calls)
- Context-aware engine for intelligent path resolution
- Cross-platform support (Windows, macOS, Linux)
- Smart fallback to AI for complex tasks
- Comprehensive system operations
"""

import os
import json
import time
import re
import subprocess
import shutil
import platform
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from .agent_core import IntelligentAgent, AgentStatus
from .output_formatter import format_output, OutputFormatter

class ContextAwareEngine:
    """
    Advanced Context-Aware Engine that automatically detects and tracks:
    - Operating System details
    - File system paths (Desktop, Documents, Downloads, etc.)
    - System resources (CPU, Memory, Disk)
    - Network information
    - User permissions
    - Environment variables
    - Current working directory
    
    Cross-platform compatible: Windows, macOS, Linux
    """
    def __init__(self):
        # Basic paths
        self.cwd = os.getcwd()
        self.home = str(Path.home())
        
        # Operating system detection
        self.os_type = platform.system()  # Windows, Linux, Darwin (macOS)
        self.os_version = platform.version()
        self.os_release = platform.release()
        self.machine = platform.machine()  # x86_64, ARM64, etc.
        self.processor = platform.processor()
        
        # Platform-specific paths
        self._detect_special_folders()
        
        # Shell detection
        self._detect_shell()
        
        # System resources
        self._detect_system_resources()
        
        # Network information
        self._detect_network_info()
        
        # User information
        self._detect_user_info()
        
        # Environment variables
        self.env_vars = dict(os.environ)
        
        # Permissions
        self._detect_permissions()
        
    def _detect_special_folders(self):
        """Detect common special folders across platforms"""
        if self.os_type == "Windows":
            # Windows paths
            self.desktop = os.path.join(self.home, "Desktop")
            self.documents = os.path.join(self.home, "Documents")
            self.downloads = os.path.join(self.home, "Downloads")
            self.pictures = os.path.join(self.home, "Pictures")
            self.videos = os.path.join(self.home, "Videos")
            self.music = os.path.join(self.home, "Music")
            self.temp = os.environ.get('TEMP', 'C:\\Windows\\Temp')
        else:
            # macOS and Linux paths
            self.desktop = os.path.join(self.home, "Desktop")
            self.documents = os.path.join(self.home, "Documents")
            self.downloads = os.path.join(self.home, "Downloads")
            self.pictures = os.path.join(self.home, "Pictures")
            self.videos = os.path.join(self.home, "Videos")
            self.music = os.path.join(self.home, "Music")
            self.temp = os.environ.get('TMPDIR', '/tmp')
            
    def _detect_shell(self):
        """Detect shell type"""
        if self.os_type == "Windows":
            self.shell = os.environ.get('COMSPEC', 'cmd.exe')
            self.shell_type = "cmd" if "cmd" in self.shell.lower() else "powershell"
        else:
            self.shell = os.environ.get('SHELL', '/bin/bash')
            self.shell_type = os.path.basename(self.shell)
            
    def _detect_system_resources(self):
        """Detect system resources using psutil if available, fallback to basic info"""
        try:
            import psutil
            # CPU
            self.cpu_count = psutil.cpu_count(logical=True)
            self.cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory
            mem = psutil.virtual_memory()
            self.memory_total = mem.total
            self.memory_available = mem.available
            self.memory_percent = mem.percent
            
            # Disk
            disk = psutil.disk_usage('/')
            self.disk_total = disk.total
            self.disk_free = disk.free
            self.disk_percent = disk.percent
        except ImportError:
            # Fallback without psutil
            self.cpu_count = os.cpu_count() or 1
            self.cpu_percent = 0
            self.memory_total = 0
            self.memory_available = 0
            self.memory_percent = 0
            self.disk_total = 0
            self.disk_free = 0
            self.disk_percent = 0
            
    def _detect_network_info(self):
        """Detect network information"""
        import socket
        try:
            self.hostname = socket.gethostname()
            self.local_ip = socket.gethostbyname(self.hostname)
        except:
            self.hostname = "unknown"
            self.local_ip = "127.0.0.1"
            
    def _detect_user_info(self):
        """Detect user information"""
        self.username = os.environ.get('USER') or os.environ.get('USERNAME') or 'unknown'
        self.is_admin = self._check_admin_privileges()
        
    def _check_admin_privileges(self):
        """Check if running with admin/root privileges"""
        try:
            if self.os_type == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False
            
    def _detect_permissions(self):
        """Detect what permissions are available"""
        self.can_write_home = os.access(self.home, os.W_OK)
        self.can_write_desktop = os.access(self.desktop, os.W_OK) if os.path.exists(self.desktop) else False
        self.can_execute_commands = True  # Assume true, will fail if not
        
    def resolve_path(self, path_hint: str) -> str:
        """Intelligently resolve a path from various hints"""
        path_hint = path_hint.strip().strip('"\'')

        # Expand ~ and environment variables first
        expanded = os.path.expanduser(os.path.expandvars(path_hint))

        # If absolute path is explicitly provided, preserve it as-is.
        if os.path.isabs(expanded):
            return expanded
        
        # Handle special keywords
        keywords = {
            'desktop': self.desktop,
            'on desktop': self.desktop,
            'to desktop': self.desktop,
            'documents': self.documents,
            'docs': self.documents,
            'downloads': self.downloads,
            'pictures': self.pictures,
            'videos': self.videos,
            'music': self.music,
            'home': self.home,
            '~': self.home,
            'temp': self.temp,
            'tmp': self.temp
        }
        
        path_lower = expanded.lower().strip()

        # Exact keyword matches (e.g., "desktop", "documents")
        if path_lower in keywords:
            return keywords[path_lower]

        # Prefix keyword + subpath (e.g., "desktop/report.txt", "docs/project")
        for keyword, base_path in keywords.items():
            for sep in ['/', '\\']:
                prefix = f"{keyword}{sep}"
                if path_lower.startswith(prefix):
                    remainder = expanded[len(prefix):].lstrip('/\\')
                    return os.path.join(base_path, remainder) if remainder else base_path

        # Natural-language form near the end (e.g., "... in documents", "... on desktop")
        location_match = re.search(
            r"\b(?:on|in|to)\s+(desktop|documents?|docs|downloads|pictures|videos|music|home|temp|tmp)\b$",
            path_lower,
        )
        if location_match:
            key = location_match.group(1)
            key_map = {
                'document': 'documents',
                'documents': 'documents',
                'docs': 'docs',
            }
            resolved_key = key_map.get(key, key)
            if resolved_key in keywords:
                return keywords[resolved_key]
        
        # If relative, join with cwd
        return os.path.join(self.cwd, expanded)
    
    def get_context(self) -> Dict[str, Any]:
        """Get comprehensive context information for AI agents"""
        return {
            # Paths
            "cwd": self.cwd,
            "home": self.home,
            "desktop": self.desktop,
            "documents": self.documents,
            "downloads": self.downloads,
            "pictures": self.pictures,
            "videos": self.videos,
            "music": self.music,
            "temp": self.temp,
            
            # OS Information
            "os": self.os_type,
            "os_version": self.os_version,
            "os_release": self.os_release,
            "machine": self.machine,
            "processor": self.processor,
            
            # Shell
            "shell": self.shell,
            "shell_type": self.shell_type,
            
            # System Resources
            "cpu_count": self.cpu_count,
            "cpu_percent": self.cpu_percent,
            "memory_total_gb": round(self.memory_total / (1024**3), 2) if self.memory_total else 0,
            "memory_available_gb": round(self.memory_available / (1024**3), 2) if self.memory_available else 0,
            "memory_percent": self.memory_percent,
            "disk_total_gb": round(self.disk_total / (1024**3), 2) if self.disk_total else 0,
            "disk_free_gb": round(self.disk_free / (1024**3), 2) if self.disk_free else 0,
            "disk_percent": self.disk_percent,
            
            # Network
            "hostname": self.hostname,
            "local_ip": self.local_ip,
            
            # User
            "username": self.username,
            "is_admin": self.is_admin,
            
            # Permissions
            "can_write_home": self.can_write_home,
            "can_write_desktop": self.can_write_desktop,
            "can_execute_commands": self.can_execute_commands
        }
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the system context"""
        ctx = self.get_context()
        return f"""
🖥️  System: {ctx['os']} {ctx['os_release']} ({ctx['machine']})
👤 User: {ctx['username']} {'(Admin)' if ctx['is_admin'] else ''}
📁 Desktop: {ctx['desktop']}
💻 CPU: {ctx['cpu_count']} cores @ {ctx['cpu_percent']}%
💾 RAM: {ctx['memory_available_gb']}GB / {ctx['memory_total_gb']}GB ({ctx['memory_percent']}% used)
💿 Disk: {ctx['disk_free_gb']}GB / {ctx['disk_total_gb']}GB free
🌐 Network: {ctx['hostname']} ({ctx['local_ip']})
""".strip()
    
    def set_cwd(self, new_cwd: str):
        """Update current working directory"""
        if os.path.isdir(new_cwd):
            self.cwd = new_cwd
            os.chdir(new_cwd)
            return True
        return False

class SystemAgent(IntelligentAgent):
    """
    ULTIMATE INTELLIGENT SYSTEM AGENT
    - Fast pattern matching for 150+ common tasks (instant execution)
    - Context-aware AI execution for complex tasks
    - Cross-platform support
    - Comprehensive system operations
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
                "context_aware_execution",
                "fast_pattern_matching",
                "network_operations",
                "git_operations",
                "package_management"
            ],
            update_callback=update_callback
        )
        
        # Initialize context-aware engine
        self.context_engine = ContextAwareEngine()
        
        # Execution log for debugging
        self.execution_log = []
        
        # Quick access to common paths
        self.home = self.context_engine.home
        self.desktop = self.context_engine.desktop
        self.documents = self.context_engine.documents
        self.downloads = self.context_engine.downloads
        self.cwd = self.context_engine.cwd
        self.os_type = self.context_engine.os_type
    
    def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task with optimized performance - try fast path first"""
        try:
            self._send_update(AgentStatus.EXECUTING, f"Processing: {task}")
            
            # FAST PATH: Pattern matching for 150+ common tasks (NO AI)
            result = self._quick_execute(task, context or {})
            
            if result:
                self._send_update(AgentStatus.SUCCESS, "Task completed instantly")
                return result
            
            # SMART PATH: Use AI for complex tasks
            self._send_update(AgentStatus.THINKING, "Analyzing complex task...")
            return self._smart_execute(task, context)
            
        except Exception as e:
            self._send_update(AgentStatus.ERROR, str(e))
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _quick_execute(self, task: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """⚡ FAST EXECUTION - 150+ tasks with NO AI calls"""
        
        task_lower = task.lower()
        full_context = {**self.context_engine.get_context(), **context}

        # ========== CREATE INTENT (PRIORITY) ==========
        # Handle creation requests before generic keyword handlers like list/tree/top,
        # otherwise names such as "Tree", "list", or "top" can trigger wrong tools.
        if 'create' in task_lower:
            folder_intent = bool(re.search(r"\b(folder|directory|dir|mkdir)\b", task_lower))
            file_intent = bool(re.search(r"\b(file|document|txt|md|json|yaml|yml|py|js|ts|csv|log)\b", task_lower))

            if folder_intent:
                dirname = self._extract_filename(task)
                if dirname:
                    target_dir = self._extract_target_directory(task_lower)
                    dirpath = self._build_target_path(dirname, target_dir)
                    return self._create_directory_fast(dirpath, task)

            if file_intent:
                filename = self._extract_filename(task)
                if filename:
                    # Normalize explicit text-file requests to .txt when no extension is provided.
                    if 'text file' in task_lower and not Path(filename).suffix:
                        filename = f"{filename}.txt"
                    target_dir = self._extract_target_directory(task_lower)
                    filepath = self._build_target_path(filename, target_dir)
                    return self._create_file_fast(filepath, task)
        
        # ========== SCREENSHOTS (10+ variations) ==========
        if any(word in task_lower for word in ['screenshot', 'screen capture', 'screen grab', 'capture screen', 'picture of screen', 'snap screen']):
            return self._take_screenshot_fast(full_context)

        # ========== THEME / APPEARANCE (detect / set) ==========
        if any(word in task_lower for word in ['dark mode', 'light mode', 'switch to dark', 'switch to light', 'turn on dark mode', 'turn off dark mode', 'set theme', 'current theme', 'what theme']):
            # detect intent
            if any(word in task_lower for word in ['current theme', 'what theme', 'which theme', 'show theme']):
                return {'success': True, 'result': self._detect_theme()}

            if any(word in task_lower for word in ['dark mode', 'switch to dark', 'turn on dark', 'enable dark']):
                res = self._set_theme('dark')
                return {'success': bool(res.get('success')), 'result': res}

            if any(word in task_lower for word in ['light mode', 'switch to light', 'turn off dark', 'disable dark', 'enable light']):
                res = self._set_theme('light')
                return {'success': bool(res.get('success')), 'result': res}

        # ========== HEALTH CHECK / DIAGNOSTICS ==========
        if any(word in task_lower for word in ['health check', 'diagnose', 'diagnostics', 'system check', 'system diagnose', 'run health check']) \
            and not ('create' in task_lower and any(w in task_lower for w in ['file', 'code', 'script'])):
            return self.health_check(full_context)

        if any(word in task_lower for word in ['monitor system', 'start monitoring', 'start monitor']):
            # start background monitor with default callback that sends updates
            monitor = self.monitor_system(interval= int(full_context.get('monitor_interval', 60)), callback=self._send_update)
            return {'success': True, 'message': 'monitor_started', 'monitor': True}

        if any(word in task_lower for word in ['stop monitoring', 'stop monitor', 'shutdown monitor']):
            # Best-effort: no global registry here; instruct user how to stop if they started one manually
            return {'success': False, 'message': 'stop monitoring not implemented for anonymous monitors; store stop_flag from monitor_system return value to stop it'}
        
        # ========== DIRECTORY LISTING (20+ variations) ==========
        if any(word in task_lower for word in ['list', 'ls', 'show files', 'display files', 'view files', 'see files', 'what files', 'files in']):
            if 'desktop' in task_lower:
                return self._shell_fast(f"ls -lah {self.desktop}", task)
            elif 'download' in task_lower:
                return self._shell_fast(f"ls -lah {self.home}/Downloads", task)
            elif 'document' in task_lower:
                return self._shell_fast(f"ls -lah {self.home}/Documents", task)
            elif 'picture' in task_lower or 'image' in task_lower:
                return self._shell_fast(f"ls -lah {self.home}/Pictures", task)
            elif 'video' in task_lower or 'movie' in task_lower:
                return self._shell_fast(f"ls -lah {self.home}/Videos", task)
            elif 'music' in task_lower or 'audio' in task_lower:
                return self._shell_fast(f"ls -lah {self.home}/Music", task)
            elif 'home' in task_lower:
                return self._shell_fast(f"ls -lah {self.home}", task)
            elif 'root' in task_lower and self.os_type != "Windows":
                return self._shell_fast("ls -lah /", task)
            else:
                return self._shell_fast(f"ls -lah {self.cwd}", task)
        
        # ========== FILE TREE (5+ variations) ==========
        if any(word in task_lower for word in ['tree', 'directory tree', 'folder structure']):
            if shutil.which('tree'):
                return self._shell_fast(f"tree -L 2 {self.cwd}", task)
            else:
                return self._shell_fast(f"find {self.cwd} -maxdepth 2 -type d", task)
        
        # ========== DISK OPERATIONS (15+ variations) ==========
        if any(word in task_lower for word in ['disk space', 'disk usage', 'free space', 'storage', 'how much space', 'check disk']):
            return self._shell_fast("df -h", task)
        
        if any(word in task_lower for word in ['disk free', 'space available', 'free disk']):
            return self._shell_fast("df -h | grep -v tmpfs | grep -v udev", task)
        
        if 'folder size' in task_lower or 'directory size' in task_lower:
            return self._shell_fast(f"du -sh {self.cwd}/*", task)
        
        # ========== MEMORY OPERATIONS (10+ variations) ==========
        if any(word in task_lower for word in ['memory', 'ram', 'free memory', 'memory usage', 'check memory']):
            if self.os_type == "Linux":
                return self._shell_fast("free -h", task)
            elif self.os_type == "Darwin":
                return self._shell_fast("vm_stat", task)
            else:
                return self._shell_fast("wmic OS get TotalVisibleMemorySize,FreePhysicalMemory", task)
        
        # ========== CPU & PROCESS OPERATIONS (30+ variations) ==========
        if any(word in task_lower for word in ['cpu usage', 'cpu load', 'processor usage', 'check cpu']):
            if self.os_type == "Linux":
                return self._shell_fast("top -bn1 | head -20", task)
            else:
                return self._shell_fast("ps aux | head -20", task)
        
        if any(word in task_lower for word in ['running process', 'list process', 'show process', 'active process', 'what\'s running']):
            if self.os_type == "Windows":
                return self._shell_fast("tasklist", task)
            else:
                return self._shell_fast("ps aux", task)
        
        if any(word in task_lower for word in ['kill process', 'stop process', 'terminate']):
            words = task_lower.split()
            for i, word in enumerate(words):
                if word in ['kill', 'stop', 'terminate'] and i + 1 < len(words):
                    target = words[i + 1]
                    if target.isdigit():
                        return self._shell_fast(f"kill {target}", task)
                    else:
                        return self._shell_fast(f"pkill {target}", task)
        
        if re.search(r"\b(top|htop)\b", task_lower):
            return self._shell_fast("ps aux --sort=-%mem | head -20", task)
        
        # ========== NETWORK OPERATIONS (20+ variations) ==========
        if any(word in task_lower for word in ['ip address', 'my ip', 'network address', 'what is my ip', 'show ip']):
            if self.os_type == "Linux":
                return self._shell_fast("ip addr show | grep inet", task)
            elif self.os_type == "Darwin":
                return self._shell_fast("ifconfig | grep inet", task)
            else:
                return self._shell_fast("ipconfig", task)
        
        if any(word in task_lower for word in ['ping', 'test connection', 'check connection', 'network connectivity', 'check network', 'connectivity test']):
            target = 'google.com'
            words = task_lower.split()
            for word in words:
                if '.' in word and word not in ['ping', 'test', 'check']:
                    target = word
                    break
            return self._shell_fast(f"ping -c 4 {target}", task)
        
        if any(word in task_lower for word in ['network interface', 'network card', 'network device']):
            if self.os_type == "Linux":
                return self._shell_fast("ip link show", task)
            else:
                return self._shell_fast("ifconfig", task)
        
        if any(word in task_lower for word in ['open port', 'listening port', 'network port']):
            if self.os_type == "Linux":
                return self._shell_fast("ss -tulpn", task)
            else:
                return self._shell_fast("netstat -an", task)
        
        # ========== TIME & DATE (10+ variations) ==========
        if any(word in task_lower for word in ['time', 'date', 'current time', 'what time', 'clock', 'calendar']):
            return self._shell_fast("date", task)
        
        if 'uptime' in task_lower or 'how long' in task_lower:
            return self._shell_fast("uptime", task)
        
        # ========== PATH OPERATIONS (15+ variations) ==========
        if any(word in task_lower for word in ['pwd', 'working directory', 'current directory', 'current folder', 'where am i', 'current path']):
            return self._shell_fast("pwd", task)
        
        if any(word in task_lower for word in ['change directory', 'cd ', 'go to', 'navigate to']):
            words = task_lower.split()
            for i, word in enumerate(words):
                if word in ['to', 'into'] and i + 1 < len(words):
                    target = words[i + 1]
                    if target == 'desktop':
                        self.context_engine.set_cwd(self.desktop)
                        return self._shell_fast(f"cd {self.desktop} && pwd", task)
                    elif target == 'home':
                        self.context_engine.set_cwd(self.home)
                        return self._shell_fast(f"cd {self.home} && pwd", task)
                    break
        
        # ========== FILE OPERATIONS (40+ variations) ==========
        if any(word in task_lower for word in ['read file', 'cat ', 'show file', 'display file', 'view file', 'open file']):
            filename = self._extract_filename(task)
            if filename:
                target_dir = self._extract_target_directory(task_lower)
                filepath = self._build_target_path(filename, target_dir)
                return self._shell_fast(f"cat {filepath}", task)

        if any(word in task_lower for word in ['delete file', 'remove file', 'rm file']):
            filename = self._extract_filename(task)
            if filename:
                target_dir = self._extract_target_directory(task_lower)
                filepath = self._build_target_path(filename, target_dir)
                return self._shell_fast(f"rm -f {filepath}", task)
        
        if 'touch' in task_lower:
            filename = self._extract_filename(task)
            if filename:
                filepath = os.path.join(self.cwd, filename)
                return self._shell_fast(f"touch {filepath}", task)
        
        # ========== FILE SEARCH (25+ variations) ==========
        if any(word in task_lower for word in ['find', 'search', 'locate', 'look for']):
            if '*.txt' in task or '.txt' in task_lower:
                return self._shell_fast(f"find {self.home} -name '*.txt' -type f 2>/dev/null | head -30", task)
            elif '*.py' in task or '.py' in task_lower:
                return self._shell_fast(f"find {self.home} -name '*.py' -type f 2>/dev/null | head -30", task)
            elif '*.js' in task or '.js' in task_lower:
                return self._shell_fast(f"find {self.home} -name '*.js' -type f 2>/dev/null | head -30", task)
            elif '*.md' in task or '.md' in task_lower or 'markdown' in task_lower:
                return self._shell_fast(f"find {self.home} -name '*.md' -type f 2>/dev/null | head -30", task)
            elif '*.json' in task or '.json' in task_lower:
                return self._shell_fast(f"find {self.home} -name '*.json' -type f 2>/dev/null | head -30", task)
            elif '*.pdf' in task or '.pdf' in task_lower:
                return self._shell_fast(f"find {self.home} -name '*.pdf' -type f 2>/dev/null | head -30", task)
            elif '*.zip' in task or '.zip' in task_lower:
                return self._shell_fast(f"find {self.home} -name '*.zip' -type f 2>/dev/null | head -30", task)
            else:
                words = task_lower.split()
                for i, word in enumerate(words):
                    if word in ['find', 'search', 'locate'] and i + 1 < len(words):
                        term = words[i + 1].strip('"\'')
                        return self._shell_fast(f"find {self.home} -iname '*{term}*' 2>/dev/null | head -30", task)
        
        # ========== SYSTEM INFO (30+ variations) ==========
        if any(word in task_lower for word in ['system info', 'system information', 'uname', 'os info', 'about system']):
            return self._shell_fast("uname -a", task)
        
        if any(word in task_lower for word in ['hostname', 'computer name', 'machine name']):
            return self._shell_fast("hostname", task)
        
        if any(word in task_lower for word in ['kernel', 'kernel version']):
            return self._shell_fast("uname -r", task)
        
        if any(word in task_lower for word in ['environment', 'env variable', 'environment variable']):
            return self._shell_fast("env | sort", task)
        
        if any(word in task_lower for word in ['who am i', 'whoami', 'current user', 'logged in']):
            return self._shell_fast("whoami", task)
        
        if 'users' in task_lower or 'logged users' in task_lower:
            return self._shell_fast("who", task)
        
        # ========== PACKAGE MANAGEMENT (20+ variations) ==========
        if self.os_type == "Linux":
            if any(word in task_lower for word in ['apt update', 'update packages', 'update system']):
                return self._shell_fast("sudo apt update", task)
            
            if any(word in task_lower for word in ['apt upgrade', 'upgrade packages', 'upgrade system']):
                return self._shell_fast("sudo apt upgrade -y", task)
            
            if 'apt install' in task_lower or 'install package' in task_lower:
                words = task_lower.split()
                for i, word in enumerate(words):
                    if word in ['install'] and i + 1 < len(words):
                        package = words[i + 1]
                        return self._shell_fast(f"sudo apt install -y {package}", task)
            
            if 'apt remove' in task_lower or 'uninstall' in task_lower:
                words = task_lower.split()
                for i, word in enumerate(words):
                    if word in ['remove', 'uninstall'] and i + 1 < len(words):
                        package = words[i + 1]
                        return self._shell_fast(f"sudo apt remove -y {package}", task)
        
        # ========== GIT OPERATIONS (20+ variations) ==========
        if 'git status' in task_lower or 'git st' in task_lower:
            return self._shell_fast("git status", task)
        
        if 'git log' in task_lower or 'git history' in task_lower:
            return self._shell_fast("git log --oneline -10", task)
        
        if 'git branch' in task_lower or 'git branches' in task_lower:
            return self._shell_fast("git branch -a", task)
        
        if 'git diff' in task_lower:
            return self._shell_fast("git diff", task)
        
        if 'git pull' in task_lower:
            return self._shell_fast("git pull", task)
        
        if 'git push' in task_lower:
            return self._shell_fast("git push", task)
        
        # ========== PYTHON OPERATIONS (15+ variations) ==========
        if 'python version' in task_lower or 'python --version' in task_lower:
            return self._shell_fast("python3 --version", task)
        
        if 'pip list' in task_lower or 'pip freeze' in task_lower:
            return self._shell_fast("pip3 list", task)
        
        if 'pip install' in task_lower:
            words = task_lower.split()
            for i, word in enumerate(words):
                if word == 'install' and i + 1 < len(words):
                    package = words[i + 1]
                    return self._shell_fast(f"pip3 install {package}", task)
        
        # ========== TEXT PROCESSING (15+ variations) ==========
        if 'echo' in task_lower:
            if 'echo' in task:
                text = task.split('echo', 1)[1].strip().strip('"\'')
                return self._shell_fast(f"echo '{text}'", task)
        
        if 'head' in task_lower or 'first lines' in task_lower:
            filename = self._extract_filename(task)
            if filename:
                return self._shell_fast(f"head -20 {filename}", task)
        
        if 'tail' in task_lower or 'last lines' in task_lower:
            filename = self._extract_filename(task)
            if filename:
                return self._shell_fast(f"tail -20 {filename}", task)
        
        if 'wc' in task_lower or 'count lines' in task_lower or 'line count' in task_lower:
            filename = self._extract_filename(task)
            if filename:
                return self._shell_fast(f"wc -l {filename}", task)
        
        # ========== CLEAR/CLEAN (5+ variations) ==========
        if any(word in task_lower for word in ['clear screen', 'clear terminal', 'cls']):
            return self._shell_fast("clear", task)
        
        # No fast match - use AI
        return None
    
    def _shell_fast(self, command: str, original_task: str) -> Dict[str, Any]:
        """Execute shell command quickly and format output"""
        try:
            print(f"\n⚡ FAST EXECUTION:", flush=True)
            print(f"   Task: {original_task}", flush=True)
            print(f"   Command: $ {command}", flush=True)
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.cwd
            )
            
            output = result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
            success = result.returncode == 0
            
            print(f"   Exit Code: {result.returncode}", flush=True)
            
            if success:
                formatted = format_output(output, command, success)
                display = formatted.get("explanation", output if output else "Command completed")
            else:
                display = f"Command failed: {output}"
            
            return {
                "success": success,
                "results": [{
                    "command": command,
                    "output": output,
                    "exit_code": result.returncode,
                    "success": success
                }],
                "task": original_task,
                "plan": {
                    "understanding": "Fast execution",
                    "approach": "Direct command",
                    "steps": [{"step": 1, "action": command, "tool": "shell", "expected_outcome": "Output"}]
                },
                "formatted_output": display
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _take_screenshot_fast(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fast screenshot capture"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            
            pictures_dir = os.path.join(self.home, "Pictures")
            if os.path.exists(pictures_dir):
                filepath = Path(pictures_dir) / filename
            else:
                filepath = Path(self.desktop) / filename
            
            filepath.parent.mkdir(exist_ok=True)
            
            self._send_update(AgentStatus.EXECUTING, "📸 Capturing screenshot...")
            
            screenshot_taken = False
            error_msg = ""
            
            # Try multiple screenshot methods
            methods = [
                (['gnome-screenshot', '-f', str(filepath)], 'gnome-screenshot'),
                (['scrot', str(filepath)], 'scrot'),
                (['import', '-window', 'root', str(filepath)], 'imagemagick'),
            ]
            
            for cmd, method_name in methods:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 and filepath.exists():
                        screenshot_taken = True
                        break
                except (FileNotFoundError, Exception) as e:
                    error_msg += f" | {method_name}: {str(e)}"
            
            if not screenshot_taken:
                raise Exception(f"Screenshot failed. Install: gnome-screenshot, scrot, or imagemagick")
            
            file_size_kb = filepath.stat().st_size / 1024
            
            return {
                "success": True,
                "operation": "screenshot",
                "message": f"Screenshot saved to {filepath} ({file_size_kb:.1f} KB)",
                "path": str(filepath),
                "exists": filepath.exists(),
                "size_kb": file_size_kb,
                "results": [{"command": "screenshot", "output": f"Saved to {filepath}", "success": True}],
                "task": "Take screenshot"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}
    
    def _create_file_fast(self, filepath: str, original_task: str) -> Dict[str, Any]:
        """Create file quickly, optionally with inferred content from natural-language task."""
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            inferred_content = self._infer_file_content_from_task(original_task, filepath)

            task_lower = original_task.lower()
            code_request = bool(re.search(r"\b(add|write|implement|create|generate|build)\b", task_lower)) and (
                bool(re.search(r"\b(code|script|program)\b", task_lower))
                or bool(re.search(r"add\s+.+\s+(?:in it|on it|to it)", task_lower))
                or Path(filepath).suffix.lower() in {
                    ".py", ".js", ".ts", ".java", ".c", ".cpp", ".cc", ".cxx", ".cs",
                    ".go", ".rs", ".php", ".rb", ".kt", ".swift", ".sh", ".bash", ".html",
                    ".css", ".sql", ".json", ".yml", ".yaml", ".md", ".ex", ".exs"
                }
            )

            if code_request and not inferred_content:
                # One additional direct model attempt to avoid blank/stale files.
                language_hint = Path(filepath).suffix.lstrip('.').lower() or "text"
                inferred_content = self._generate_code_dynamically(
                    task=original_task,
                    filepath=filepath,
                    language=language_hint,
                    topic="general"
                )

            if inferred_content:
                Path(filepath).write_text(inferred_content)
                output_msg = f"File created with content: {filepath}"
                command_msg = f"create+write file {filepath}"
            else:
                if code_request:
                    # Clear stale content if file existed and model returned no code.
                    Path(filepath).write_text("")
                    output_msg = f"File created but model returned no code: {filepath}"
                    command_msg = f"create file (empty after model miss) {filepath}"
                else:
                    Path(filepath).touch(exist_ok=True)
                    output_msg = f"File created: {filepath}"
                    command_msg = f"create file {filepath}"
            
            return {
                "success": True,
                "results": [{"command": command_msg, "output": output_msg, "success": True}],
                "task": original_task,
                "plan": {"understanding": f"Create file at {filepath}"},
                "path": filepath,
                "content_written": bool(inferred_content),
                "bytes_written": len(inferred_content) if inferred_content else 0
            }
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}

    def _infer_file_content_from_task(self, task: str, filepath: str) -> str:
        """Infer file content from quick-path natural language requests.

        This keeps fast execution while handling prompts like:
        "Create new.txt and add python code in it".
        """
        task_lower = task.lower()

        def _generate_plain_text_lines(topic: str, line_count: int) -> str:
            topic = (topic or "nature").strip().strip('.,;:')
            topic_cap = topic[:1].upper() + topic[1:] if topic else "Nature"
            lines = []
            for i in range(1, line_count + 1):
                lines.append(
                    f"{i}. {topic_cap} teaches balance, beauty, and resilience through every season and landscape."
                )
            return "\n".join(lines) + "\n"

        # Respect explicit empty-file intent
        if any(phrase in task_lower for phrase in ["empty file", "blank file", "without content"]):
            return ""

        # Plain-text writing requests (non-code), e.g.:
        # "create a text file named nature and write 100 lines about nature"
        line_request = re.search(r"\bwrite\s+(\d{1,4})\s+lines?\s+about\s+(.+)$", task, flags=re.IGNORECASE)
        if line_request and not re.search(r"\b(code|script|program)\b", task_lower):
            line_count = max(1, min(500, int(line_request.group(1))))
            topic = line_request.group(2)
            topic = re.split(
                r"\s+(?:in|on|to)\s+(?:the\s+)?(?:file|folder|directory|desktop|documents?|downloads?|home|cwd|current\s+directory)\b",
                topic,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip()
            return _generate_plain_text_lines(topic, line_count)

        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".kt": "kotlin",
            ".swift": "swift",
            ".sh": "bash",
            ".bash": "bash",
            ".html": "html",
            ".css": "css",
            ".sql": "sql",
            ".json": "json",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".md": "markdown",
            ".ex": "elixir",
            ".exs": "elixir",
        }

        # If user asked to add/write code, infer requested language from prompt.
        language_cues = {
            "python": ["python"],
            "javascript": ["javascript", "node"],
            "typescript": ["typescript"],
            "java": [" java ", "java code"],
            "c": [" c code", " language c"],
            "cpp": ["c++", "cpp"],
            "csharp": ["c#", "csharp", "dotnet"],
            "go": ["golang", "go code", " go "],
            "rust": ["rust"],
            "php": ["php"],
            "ruby": ["ruby"],
            "kotlin": ["kotlin"],
            "swift": ["swift"],
            "bash": ["bash", "shell", "sh script"],
            "html": ["html"],
            "css": ["css"],
            "sql": ["sql", "database query"],
            "json": ["json"],
            "yaml": ["yaml"],
            "markdown": ["markdown"],
            "elixir": ["elixir"],
        }

        def _extract_requested_language() -> Optional[str]:
            normalized = f" {task_lower} "

            patterns = [
                r"(?:add|write|generate|create)\s+([a-z0-9#+._-]{2,30})\s+(?:code|script|program)",
                r"(?:in|using|with)\s+([a-z0-9#+._-]{2,30})\s+(?:code|script|program)",
                r"([a-z0-9#+._-]{2,30})\s+(?:code|script|program)",
            ]

            for pattern in patterns:
                m = re.search(pattern, normalized)
                if m:
                    token = m.group(1).strip().lower().strip('.,;:!?')
                    if token not in {'a', 'an', 'the', 'some', 'any'}:
                        return token
            return None

        def _detect_language() -> str:
            normalized = f" {task_lower} "

            def _cue_in_text(cue: str) -> bool:
                cue = cue.strip().lower()
                if not cue:
                    return False
                if re.fullmatch(r"[a-z0-9]+", cue):
                    return bool(re.search(rf"\b{re.escape(cue)}\b", normalized))
                return cue in normalized

            for lang, cues in language_cues.items():
                if any(_cue_in_text(cue) for cue in cues):
                    return lang

            return ext_map.get(Path(filepath).suffix.lower(), "python")

        requested_language = _extract_requested_language()
        language = requested_language or _detect_language()

        generic_code_cues = [
            "add code",
            "write code",
            "with code",
            "code in it",
            "add a code",
        ]

        action_verbs = ["add", "write", "implement", "create", "make", "build", "generate"]
        has_code_extension = Path(filepath).suffix.lower() in ext_map

        wants_code = any(cue in task_lower for cue in generic_code_cues) or any(
            cue in f" {task_lower} "
            for cues in language_cues.values()
            for cue in cues
        ) or (
            bool(requested_language) and any(token in task_lower for token in ["code", "script", "program"])
        ) or (
            has_code_extension and any(v in task_lower for v in action_verbs)
        ) or bool(re.search(r"add\s+.+\s+(?:in it|on it|to it)", task_lower))

        def _extract_topic() -> str:
            normalized = task_lower
            if any(word in normalized for word in ["network", "socket", "http", "api", "client", "server"]):
                return "network"
            if any(word in normalized for word in ["add two numbers", "sum two numbers", "addition", "add numbers", "sum numbers"]):
                return "arithmetic_add_two_numbers"
            if any(word in normalized for word in ["file", "read", "write", "csv", "json parse"]):
                return "file processing"
            if any(word in normalized for word in ["sort", "search", "algorithm", "dsa", "array"]):
                return "algorithm"

            match = re.search(r"(?:for|about|related to)\s+([a-z0-9 _\-]{3,60})", normalized)
            if match:
                candidate = match.group(1).strip(" .,:;!?")
                candidate = re.sub(r"\b(code|file|script|program|language)\b", "", candidate).strip()
                if candidate:
                    return candidate
            return "general"

        topic = _extract_topic()

        # Prefer explicit fenced code blocks from user prompt.
        fenced_blocks = re.findall(r"```(?:[a-zA-Z0-9_+-]+)?\n([\s\S]*?)```", task)
        if fenced_blocks and any(block.strip() for block in fenced_blocks):
            return fenced_blocks[0].strip() + "\n"

        # If quoted content is present (e.g., write "print('hi')"), prefer that content.
        quoted = re.findall(r'["\']([^"\']{2,2000})["\']', task)
        if quoted and any(keyword in task_lower for keyword in ["write", "add", "content", "code"]):
            for candidate in quoted:
                if os.path.basename(filepath) not in candidate:
                    return candidate

        if wants_code:
            ai_generated = self._generate_code_dynamically(
                task=task,
                filepath=filepath,
                language=language,
                topic=topic
            )
            if ai_generated:
                return ai_generated

            # Model did not return usable code.
            # Return empty so caller can surface/create behavior without static placeholder code.
            return ""

        return ""

    def _generate_code_dynamically(self, task: str, filepath: str, language: str, topic: str) -> str:
        """Generate code content dynamically for any requested language using the execution model."""
        base_prompt = f"""Generate only source code (no markdown fences, no explanation).

User request: {task}
Target file: {filepath}
Requested language: {language}
Topic intent: {topic}

Requirements:
1. Output must be valid {language} code.
2. Keep it minimal but meaningful for the requested topic.
3. If the topic is unclear, include a practical starter skeleton.
4. Do not include any text outside the code.
"""

        def _extract_code(raw: str) -> str:
            text = (raw or "").strip()
            if not text:
                return ""

            if "```" in text:
                parts = re.findall(r"```(?:[a-zA-Z0-9_+\-#.]*)\n([\s\S]*?)```", text)
                if parts:
                    text = parts[0].strip()
                else:
                    text = text.replace("```", "").strip()

            lines = [ln for ln in text.splitlines() if ln.strip()]
            non_comment = [
                ln for ln in lines
                if not re.match(r"^\s*(#|//|/\*|\*|--)", ln.strip())
            ]
            if not non_comment:
                return ""

            return text + "\n"

        prompts = [
            base_prompt,
            base_prompt + "\nFocus on implementing the main requested behavior directly (for example, if user asks to add two numbers, include that exact logic).",
        ]

        # Execution model first (with retries), then thinking model as fallback.
        for prompt in prompts:
            try:
                response = self._get_execution_model().generate_content(prompt)
                extracted = _extract_code(getattr(response, 'text', ''))
                if extracted:
                    return extracted
            except Exception:
                continue

        for prompt in prompts[:1]:
            try:
                response = self._get_thinking_model().generate_content(prompt)
                extracted = _extract_code(getattr(response, 'text', ''))
                if extracted:
                    return extracted
            except Exception:
                continue

        return ""
    
    def _create_directory_fast(self, dirpath: str, original_task: str) -> Dict[str, Any]:
        """Create directory quickly"""
        try:
            Path(dirpath).mkdir(parents=True, exist_ok=True)
            
            return {
                "success": True,
                "results": [{"command": f"create directory {dirpath}", "output": f"Directory created: {dirpath}", "success": True}],
                "task": original_task,
                "plan": {"understanding": f"Create directory at {dirpath}"}
            }
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}

    # ========== THEME / APPEARANCE HELPERS ==========
    def _detect_theme(self) -> Dict[str, Any]:
        """Detect current system theme (best-effort across platforms). Returns {'theme': 'dark'|'light'|'unknown', 'details': str}
        """
        try:
            if self.os_type == 'Darwin':
                # macOS - use AppleScript to query dark mode
                cmd = ['osascript', '-e', 'tell application "System Events" to tell appearance preferences to get dark mode']
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                out = r.stdout.strip().lower()
                if out in ['true', 'yes']:
                    return {'theme': 'dark', 'details': 'macOS reports Dark Mode'}
                elif out in ['false', 'no']:
                    return {'theme': 'light', 'details': 'macOS reports Light Mode'}
                else:
                    return {'theme': 'unknown', 'details': out}

            elif self.os_type == 'Linux':
                # Try GNOME color-scheme first
                try:
                    r = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'], capture_output=True, text=True, timeout=3)
                    val = r.stdout.strip().strip("'")
                    if 'dark' in val:
                        return {'theme': 'dark', 'details': f'GNOME color-scheme: {val}'}
                except Exception:
                    pass
                # Fallback: check GTK theme name
                try:
                    r = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme'], capture_output=True, text=True, timeout=3)
                    val = r.stdout.strip().strip("'")
                    if val and ('dark' in val.lower() or 'dark' in val):
                        return {'theme': 'dark', 'details': f'GTK theme: {val}'}
                    elif val:
                        return {'theme': 'light', 'details': f'GTK theme: {val}'}
                except Exception:
                    pass
                return {'theme': 'unknown', 'details': 'No GNOME/GTK info available'}

            elif self.os_type == 'Windows':
                # Read registry values for theme (AppsUseLightTheme)
                try:
                    pw = ['powershell', '-NoProfile', '-Command', "(Get-ItemProperty -Path HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme).AppsUseLightTheme"]
                    r = subprocess.run(pw, capture_output=True, text=True, timeout=5)
                    val = r.stdout.strip()
                    if val == '0':
                        return {'theme': 'dark', 'details': 'Windows registry AppsUseLightTheme=0'}
                    elif val == '1':
                        return {'theme': 'light', 'details': 'Windows registry AppsUseLightTheme=1'}
                except Exception:
                    pass
                return {'theme': 'unknown', 'details': 'Unable to read Windows theme setting'}

            else:
                return {'theme': 'unknown', 'details': f'Unsupported OS: {self.os_type}'}
        except Exception as e:
            return {'theme': 'unknown', 'details': str(e)}

    def _set_theme(self, mode: str) -> Dict[str, Any]:
        """Set system theme to 'dark' or 'light' where supported. Best-effort; returns result dict."""
        mode = str(mode).lower()
        if mode not in ['dark', 'light']:
            return {'success': False, 'error': f'Unknown mode: {mode}'}
        try:
            if self.os_type == 'Darwin':
                value = 'true' if mode == 'dark' else 'false'
                cmd = ['osascript', '-e', f'tell application "System Events" to tell appearance preferences to set dark mode to {value}']
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    return {'success': True, 'message': f'macOS set to {mode} mode'}
                return {'success': False, 'error': r.stderr or r.stdout}

            elif self.os_type == 'Linux':
                # Try GNOME color-scheme where supported
                try:
                    val = 'prefer-dark' if mode == 'dark' else 'default'
                    r = subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'color-scheme', val], capture_output=True, text=True, timeout=3)
                    if r.returncode == 0:
                        return {'success': True, 'message': f'GNOME color-scheme set to {val}'}
                except Exception:
                    pass
                # Try changing GTK theme name (best-effort fallback)
                # Do not attempt to guess theme names; inform user how to change manually
                return {'success': False, 'error': 'Setting theme on Linux is DE-specific. Try gsettings or change your GTK/DE theme manually.'}

            elif self.os_type == 'Windows':
                # Set registry keys via PowerShell
                try:
                    val = '0' if mode == 'dark' else '1'
                    cmds = [
                        ['powershell', '-NoProfile', '-Command', f"Set-ItemProperty -Path HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name AppsUseLightTheme -Value {val}"],
                        ['powershell', '-NoProfile', '-Command', f"Set-ItemProperty -Path HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize -Name SystemUsesLightTheme -Value {val}"]
                    ]
                    for c in cmds:
                        r = subprocess.run(c, capture_output=True, text=True, timeout=5)
                        if r.returncode != 0:
                            return {'success': False, 'error': r.stderr or r.stdout}
                    return {'success': True, 'message': f'Windows theme set to {mode} (registry updated)'}
                except Exception as e:
                    return {'success': False, 'error': str(e)}

            else:
                return {'success': False, 'error': f'Unsupported OS: {self.os_type}'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== HEALTH CHECKS & MONITORING ==========
    def health_check(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a set of diagnostic checks and return structured results."""
        ctx = {**self.context_engine.get_context(), **(context or {})}
        checks = []

        # Disk usage
        try:
            r = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=10)
            disk_out = r.stdout.strip()
            # detect partitions above 85%
            critical = []
            for line in disk_out.splitlines()[1:]:
                parts = [p for p in line.split() if p]
                if len(parts) >= 5:
                    try:
                        pct = parts[4]
                        if pct.endswith('%') and int(pct.rstrip('%')) >= 85:
                            critical.append({'mount': parts[5] if len(parts) > 5 else parts[-1], 'usage': pct})
                    except Exception:
                        pass
            status = 'ok' if not critical else 'warning'
            checks.append({'name': 'disk', 'status': status, 'details': disk_out, 'issues': critical})
        except Exception as e:
            checks.append({'name': 'disk', 'status': 'unknown', 'error': str(e)})

        # Memory
        try:
            if self.os_type == 'Linux':
                r = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=5)
                mem_out = r.stdout.strip()
                # parse available memory
                lines = mem_out.splitlines()
                if len(lines) >= 2:
                    vals = lines[1].split()
                    if len(vals) >= 7:
                        avail = int(vals[6])
                        status = 'ok' if avail >= 500 else 'warning'
                    else:
                        status = 'unknown'
                else:
                    status = 'unknown'
                checks.append({'name': 'memory', 'status': status, 'details': mem_out})
            else:
                r = subprocess.run(['vm_stat'] if self.os_type == 'Darwin' else ['wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory'], capture_output=True, text=True, timeout=5)
                checks.append({'name': 'memory', 'status': 'ok', 'details': r.stdout.strip()})
        except Exception as e:
            checks.append({'name': 'memory', 'status': 'unknown', 'error': str(e)})

        # CPU / load
        try:
            if self.os_type == 'Linux':
                r = subprocess.run(['uptime'], capture_output=True, text=True, timeout=5)
                up = r.stdout.strip()
                checks.append({'name': 'cpu', 'status': 'ok', 'details': up})
            else:
                r = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
                checks.append({'name': 'cpu', 'status': 'ok', 'details': r.stdout.strip()[:1000]})
        except Exception as e:
            checks.append({'name': 'cpu', 'status': 'unknown', 'error': str(e)})

        # High memory processes
        try:
            r = subprocess.run(['ps', 'aux', '--sort=-%mem'], capture_output=True, text=True, timeout=5)
            top_procs = '\n'.join(r.stdout.splitlines()[:10])
            checks.append({'name': 'top_processes', 'status': 'ok', 'details': top_procs})
        except Exception as e:
            checks.append({'name': 'top_processes', 'status': 'unknown', 'error': str(e)})

        # Failed systemd services (Linux)
        if self.os_type == 'Linux' and shutil.which('systemctl'):
            try:
                r = subprocess.run(['systemctl', '--failed', '--no-legend'], capture_output=True, text=True, timeout=5)
                failed = r.stdout.strip()
                status = 'ok' if not failed else 'warning'
                checks.append({'name': 'systemd_failed', 'status': status, 'details': failed})
            except Exception as e:
                checks.append({'name': 'systemd_failed', 'status': 'unknown', 'error': str(e)})

        # Recent kernel / journal errors
        try:
            d = subprocess.run(['dmesg', '--level=err,crit,alert,emerg'], capture_output=True, text=True, timeout=5)
            journal_err = d.stdout.strip()[:2000]
            checks.append({'name': 'kernel_errors', 'status': 'ok' if not journal_err else 'warning', 'details': journal_err})
        except Exception:
            # best-effort: journalctl
            try:
                j = subprocess.run(['journalctl', '-p', 'err', '-n', '50', '--no-pager'], capture_output=True, text=True, timeout=5)
                checks.append({'name': 'journal_errors', 'status': 'ok' if not j.stdout.strip() else 'warning', 'details': j.stdout.strip()[:2000]})
            except Exception as e:
                checks.append({'name': 'journal_errors', 'status': 'unknown', 'error': str(e)})

        # Network connectivity
        try:
            r = subprocess.run(['ping', '-c', '2', '8.8.8.8'], capture_output=True, text=True, timeout=8)
            net_ok = r.returncode == 0
            checks.append({'name': 'network', 'status': 'ok' if net_ok else 'warning', 'details': r.stdout.strip() or r.stderr.strip()})
        except Exception as e:
            checks.append({'name': 'network', 'status': 'unknown', 'error': str(e)})

        # Python environment health
        try:
            if shutil.which('pip3'):
                r = subprocess.run(['pip3', 'check'], capture_output=True, text=True, timeout=10)
                pip_out = r.stdout.strip() or r.stderr.strip()
                status = 'ok' if r.returncode == 0 else 'warning'
                checks.append({'name': 'pip_check', 'status': status, 'details': pip_out})
        except Exception as e:
            checks.append({'name': 'pip_check', 'status': 'unknown', 'error': str(e)})

        # Package updates available (apt based)
        if self.os_type == 'Linux' and shutil.which('apt'):
            try:
                r = subprocess.run(['apt', 'list', '--upgradable'], capture_output=True, text=True, timeout=10)
                upg = '\n'.join(r.stdout.splitlines()[:30])
                checks.append({'name': 'apt_upgradable', 'status': 'ok', 'details': upg})
            except Exception as e:
                checks.append({'name': 'apt_upgradable', 'status': 'unknown', 'error': str(e)})

        # Compose summary
        summary = {'success': True, 'checks': checks}
        # add simple scoring
        severity = 'ok'
        for c in checks:
            if c.get('status') == 'warning':
                severity = 'warning'
            if c.get('status') == 'critical':
                severity = 'critical'
                break
        summary['severity'] = severity
        return summary

    def monitor_system(self, interval: int = 60, callback=None):
        """Run health_check periodically in a background thread. Callback receives the health summary."""
        stop_flag = {'stop': False}

        def _loop():
            while not stop_flag['stop']:
                try:
                    res = self.health_check()
                    if callback:
                        try:
                            callback(res)
                        except Exception:
                            pass
                    else:
                        # send update to UI if available
                        self._send_update(AgentStatus.EXECUTING, f"Monitor: {res.get('severity')}")
                except Exception:
                    pass
                time.sleep(interval)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        return {'success': True, 'message': 'monitor_started', 'thread': t, 'stop_flag': stop_flag}

    
    def _extract_filename(self, task: str) -> Optional[str]:
        """Extract file/folder name from natural language task text."""
        text = (task or "").strip()
        if not text:
            return None

        def _clean_candidate(raw: str) -> str:
            candidate = (raw or "").strip().strip('"\'').rstrip('.,;:')
            # Remove chained instruction clauses that are not part of file/folder name.
            candidate = re.split(
                r"\s+(?:and|then)\s+(?:write|add|include|put|insert|with|about)\b",
                candidate,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0].strip()
            candidate = re.sub(r"^as\s+", "", candidate, flags=re.IGNORECASE)
            return candidate

        # Prefer quoted target names: create file "my note.txt"
        quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
        for pair in quoted:
            candidate = _clean_candidate(pair[0] or pair[1] or "")
            if candidate:
                return candidate

        stop_location = r"\s+(?:on|in|at|to)\s+(?:the\s+)?(?:desktop|documents?|downloads?|home|current\s+directory|cwd)\b"
        name_until_location_or_end = rf"(.+?)(?={stop_location}|$)"

        patterns = [
            rf"(?:called|named(?:\s+as)?|as)\s+{name_until_location_or_end}",
            rf"(?:file|folder|directory|dir)\s+{name_until_location_or_end}",
            rf"create\s+(?:a\s+|an\s+)?(?:new\s+)?(?:file|folder|directory|dir)\s+{name_until_location_or_end}",
        ]

        for pattern in patterns:
            m = re.search(pattern, text, flags=re.IGNORECASE)
            if m:
                candidate = _clean_candidate(m.group(1))
                if candidate and len(candidate) < 255:
                    return candidate

        # Fallback: pick a token that looks like a filename.
        tokens = [tok.strip('"\'').rstrip('.,;:') for tok in text.split()]
        for tok in tokens:
            if not tok:
                continue
            if re.search(r"\.[a-zA-Z0-9]{1,10}$", tok):
                return tok

        return None

    def _extract_target_directory(self, task_lower: str) -> str:
        """Resolve destination directory from user phrasing for quick create operations."""
        if re.search(r"\b(?:on|in|to)\s+(?:the\s+)?desktop\b", task_lower):
            return self.desktop
        if re.search(r"\b(?:on|in|to)\s+(?:the\s+)?(?:documents?|docs)\b", task_lower):
            return self.documents
        if re.search(r"\b(?:on|in|to)\s+(?:the\s+)?downloads?\b", task_lower):
            return self.downloads
        if re.search(r"\b(?:on|in|to)\s+(?:the\s+)?home(?:\s+directory)?\b", task_lower):
            return self.home
        if re.search(r"\b(?:on|in|to)\s+(?:the\s+)?(?:current\s+directory|cwd|here)\b", task_lower):
            return self.cwd
        return self.desktop

    def _build_target_path(self, name_or_path: str, target_dir: str) -> str:
        """Build an absolute target path for quick create operations."""
        candidate = (name_or_path or "").strip()
        if not candidate:
            return target_dir

        # Keep explicit absolute/home/dot-relative paths as user intent.
        if (
            candidate.startswith('~')
            or os.path.isabs(candidate)
            or candidate.startswith('./')
            or candidate.startswith('../')
            or candidate.startswith('.\\')
            or candidate.startswith('..\\')
        ):
            return self.context_engine.resolve_path(candidate)

        # For relative names (including nested paths like project/tree.txt),
        # honor the detected destination directory.
        if '/' in candidate or '\\' in candidate:
            return os.path.join(target_dir, candidate.lstrip('/\\'))

        return os.path.join(target_dir, candidate)
    
    def _smart_execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Smart AI-powered execution for complex tasks"""
        try:
            full_context = {**self.context_engine.get_context(), **(context or {})}
            
            # Think about the task
            plan = self.think(task, full_context)
            
            # Execute steps
            results = []
            for step in plan.get('steps', []):
                result = self.execute_step(step, full_context)
                results.append(result)
            
            return {
                "success": all(r.get('success', False) for r in results),
                "results": results,
                "task": task,
                "plan": plan
            }
        except Exception as e:
            return {"success": False, "error": str(e), "results": []}
    
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
    
    def think(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhanced thinking with specific tool selection guidance for SystemAgent"""
        self._send_update(
            AgentStatus.THINKING,
            f"Analyzing task: {task}",
            thinking_process="Breaking down the task with system context..."
        )
        
        # Build context-aware prompt with tool guidance
        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context, indent=2)}"
        
        sys_context = self.context_engine.get_context()
        
        prompt = f"""You are SystemAgent with comprehensive system awareness.

Task: {task}
{context_str}

System Context:
- OS: {sys_context['os']} {sys_context['os_release']}
- Desktop: {sys_context['desktop']}
- Current Dir: {sys_context['cwd']}
- Shell: {sys_context['shell_type']}

CRITICAL TOOL SELECTION RULES:
1. **shell_command** - Use for:
   - Listing files/directories (ls, dir, find)
   - Checking system status (ps, df, free, uptime)
   - Searching/finding (grep, find)
   - Viewing file contents (cat, head, tail)
   - ANY command that reads/displays information
   
2. **file_operation** - Use ONLY for:
   - Creating new files (touch, echo >)
   - Creating new folders (mkdir)
   - Modifying file contents
   - Deleting files/folders
   
3. **screenshot** - Use for:
   - Taking screenshots
   - Screen capture
   - Capturing screen

EXAMPLES:
- "list files in desktop" → shell_command (use ls)
- "show files" → shell_command (use ls)
- "create file.txt" → file_operation (create new file)
- "take screenshot" → screenshot

Provide execution plan in JSON:
{{
    "understanding": "What the user wants",
    "approach": "How to accomplish it",
    "steps": [
        {{"step": 1, "action": "list files in {sys_context['desktop']}", "tool": "shell_command", "expected_outcome": "display file list"}},
    ],
    "potential_issues": ["permission errors"],
    "fallback_plan": "retry with different approach"
}}

CRITICAL: For "{task}" - if it's about LISTING/SHOWING/DISPLAYING → MUST use shell_command, NOT file_operation!"""

        try:
            response = self._get_thinking_model().generate_content(prompt)
            thinking_text = response.text
            
            # Extract JSON from response
            if "```json" in thinking_text:
                thinking_text = thinking_text.split("```json")[1].split("```")[0].strip()
            elif "```" in thinking_text:
                thinking_text = thinking_text.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(thinking_text)
            
            # Force correct tool selection for common cases
            for step in plan.get('steps', []):
                action_lower = step.get('action', '').lower()
                # Override if AI chose wrong tool
                if any(word in action_lower for word in ['list', 'show', 'display', 'find', 'check', 'view']):
                    if step.get('tool') == 'file_operation':
                        step['tool'] = 'shell_command'
                        print(f"[SYSTEM AGENT] AUTO-CORRECTED: Changed file_operation → shell_command for: {step.get('action')}")
            
            self._send_update(
                AgentStatus.THINKING,
                f"Plan created with {len(plan.get('steps', []))} steps",
                thinking_process=plan.get('understanding', ''),
                progress=20
            )
            
            return plan
            
        except Exception as e:
            self._send_update(
                AgentStatus.ERROR,
                f"Thinking failed: {str(e)}",
                thinking_process=f"Error during planning: {str(e)}"
            )
            # Fallback plan for listing
            if any(word in task.lower() for word in ['list', 'show', 'display']):
                return {
                    "understanding": task,
                    "approach": "Use shell command to list files",
                    "steps": [{"step": 1, "action": task, "tool": "shell_command", "expected_outcome": "File list displayed"}],
                    "potential_issues": ["Permission errors"],
                    "fallback_plan": "Retry with elevated permissions"
                }
            return {
                "understanding": task,
                "approach": "Direct execution",
                "steps": [{"step": 1, "action": task, "tool": "auto", "expected_outcome": "Task completed"}],
                "potential_issues": ["Unknown"],
                "fallback_plan": "Retry with different approach"
            }
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a system operation step with enhanced context awareness"""
        
        tool = step.get('tool', 'auto')
        action = step.get('action', '')
        action_key = str(action).strip().lower()
        
        # Merge context with engine context
        full_context = {**self.context_engine.get_context(), **(context or {})}

        # Direct plan action handlers (bypass tool inference)
        if action_key == 'create_file':
            path = step.get('path')
            if not path:
                raise ValueError("create_file step requires 'path'")
            return self._create_file_step(path, full_context)

        if action_key == 'write_file':
            path = step.get('path')
            if not path:
                raise ValueError("write_file step requires 'path'")
            content = step.get('content', '')
            return self._write_file_step(path, content, full_context)
        
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

    def _create_file_step(self, path_hint: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create file for explicit plan step actions."""
        path = Path(self.context_engine.resolve_path(str(path_hint)))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        return {
            "success": True,
            "operation": "create_file",
            "path": str(path),
            "exists": path.exists()
        }

    def _write_file_step(self, path_hint: str, content: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Write file content for explicit plan step actions."""
        path = Path(self.context_engine.resolve_path(str(path_hint)))
        path.parent.mkdir(parents=True, exist_ok=True)
        text_content = "" if content is None else str(content)
        if not text_content.strip():
            # If planner omitted content, infer from original command/language intent.
            source_task = str(context.get('command') or context.get('task') or 'write code')
            text_content = self._infer_file_content_from_task(source_task, str(path))
        path.write_text(text_content)
        return {
            "success": True,
            "operation": "write_file",
            "path": str(path),
            "bytes_written": len(text_content)
        }
    
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
                # Format output beautifully using AI-powered formatter
                formatted_response = format_output(output, command, success=True)
                display_output = formatted_response.get("explanation", output if output else "(command completed with no output)")
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Success\n\n{display_output}"
                )
                
                return {
                    "success": True,
                    "command": command,
                    "output": output,
                    "formatted_response": formatted_response,
                    "formatted_output": display_output,
                    "error": error if error else None,
                    "action": action,
                    "exit_code": 0,
                    "message": f"Command executed successfully:\n{display_output}"
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
                if not content:
                    # Fallback inference for prompts like:
                    # "create file X and add <language> code"
                    content = self._infer_file_content_from_task(action, str(path))
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
            
            # Method 1: Try PIL/Pillow ImageGrab
            try:
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
                screenshot.save(str(filepath))
                screenshot_taken = True
            except Exception as e1:
                error_msg = f"PIL ImageGrab failed: {str(e1)}"
                
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
