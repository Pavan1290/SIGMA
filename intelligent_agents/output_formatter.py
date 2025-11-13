#!/usr/bin/env python3
"""
Advanced Output Formatter for SIGMA-OS
Transforms raw command output into beautiful, structured, AI-powered responses
"""

import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class OutputType(Enum):
    """Different types of output that need special formatting"""
    FILE_LISTING = "file_listing"
    SYSTEM_INFO = "system_info"
    PROCESS_LIST = "process_list"
    DISK_USAGE = "disk_usage"
    NETWORK_INFO = "network_info"
    TEXT_OUTPUT = "text_output"
    ERROR_OUTPUT = "error_output"
    SUCCESS_MESSAGE = "success_message"
    TABLE_DATA = "table_data"
    JSON_DATA = "json_data"

class OutputFormatter:
    """
    Intelligently formats raw command output into beautiful, structured responses
    """
    
    def __init__(self):
        self.formatters = {
            OutputType.FILE_LISTING: self._format_file_listing,
            OutputType.SYSTEM_INFO: self._format_system_info,
            OutputType.PROCESS_LIST: self._format_process_list,
            OutputType.DISK_USAGE: self._format_disk_usage,
            OutputType.NETWORK_INFO: self._format_network_info,
            OutputType.TEXT_OUTPUT: self._format_text_output,
            OutputType.ERROR_OUTPUT: self._format_error,
            OutputType.SUCCESS_MESSAGE: self._format_success,
            OutputType.TABLE_DATA: self._format_table,
            OutputType.JSON_DATA: self._format_json,
        }
    
    def detect_output_type(self, output: str, command: str = "") -> OutputType:
        """Intelligently detect what type of output this is"""
        output_lower = output.lower()
        command_lower = command.lower()
        
        # File listing detection
        if any(keyword in command_lower for keyword in ['ls', 'list', 'dir', 'files']):
            if 'total' in output_lower or (any(x in output for x in ['drwx', '-rw', 'lrw'])):
                return OutputType.FILE_LISTING
        
        # System info detection
        if any(keyword in command_lower for keyword in ['systemctl', 'uname', 'lsb', 'hostnamectl', 'system', 'info']):
            return OutputType.SYSTEM_INFO
        
        # Process list detection
        if any(keyword in command_lower for keyword in ['ps', 'top', 'process', 'pgrep', 'pstree']):
            return OutputType.PROCESS_LIST
        
        # Disk usage detection
        if any(keyword in command_lower for keyword in ['df', 'disk', 'du', 'usage', 'storage']):
            return OutputType.DISK_USAGE
        
        # Network info detection
        if any(keyword in command_lower for keyword in ['ip', 'ifconfig', 'netstat', 'ping', 'network', 'connection']):
            return OutputType.NETWORK_INFO
        
        # Error detection
        if any(keyword in output_lower for keyword in ['error', 'failed', 'exception', 'traceback', 'not found', 'permission denied']):
            return OutputType.ERROR_OUTPUT
        
        # Success detection
        if any(keyword in output_lower for keyword in ['success', 'completed', 'done', 'ok', 'created', 'deleted']):
            return OutputType.SUCCESS_MESSAGE
        
        # JSON detection
        if output.strip().startswith('{') or output.strip().startswith('['):
            return OutputType.JSON_DATA
        
        return OutputType.TEXT_OUTPUT
    
    def format(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """
        Main entry point - formats any output beautifully
        Returns structured response with metadata, formatted output, and interactive elements
        """
        if not output:
            return self._format_empty_output()
        
        output_type = self.detect_output_type(output, command)
        formatter = self.formatters.get(output_type, self._format_text_output)
        
        try:
            formatted = formatter(output, command, success)
        except Exception as e:
            # Fallback to text formatting if specific formatter fails
            formatted = self._format_text_output(output, command, success)
        
        return formatted
    
    # ==================== FILE LISTING FORMATTER ====================
    def _format_file_listing(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """Format 'ls -la' style file listings into beautiful structured format"""
        lines = output.strip().split('\n')
        
        files = []
        total_line = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('total'):
                total_line = line
                continue
            
            # Parse ls -la format
            parts = line.split()
            if len(parts) >= 9:
                file_data = {
                    "permissions": parts[0],
                    "links": parts[1],
                    "owner": parts[2],
                    "group": parts[3],
                    "size": parts[4],
                    "date": f"{parts[5]} {parts[6]} {parts[7]}",
                    "name": ' '.join(parts[8:]),
                    "is_directory": parts[0].startswith('d'),
                    "is_symlink": parts[0].startswith('l'),
                    "is_executable": 'x' in parts[0],
                    "icon": self._get_file_icon(parts[0], ' '.join(parts[8:]))
                }
                files.append(file_data)
        
        # Calculate stats
        dirs_count = sum(1 for f in files if f["is_directory"])
        files_count = len(files) - dirs_count
        total_size = sum(int(f["size"]) for f in files if f["size"].isdigit())
        
        return {
            "type": "file_listing",
            "success": success,
            "command": command,
            "summary": {
                "total_items": len(files),
                "directories": dirs_count,
                "files": files_count,
                "total_size_bytes": total_size,
                "total_size_human": self._bytes_to_human(total_size)
            },
            "data": files,
            "raw_output": output,
            "visualization": "table",
            "explanation": f"Found {len(files)} items: {dirs_count} directories and {files_count} files. Total size: {self._bytes_to_human(total_size)}",
            "actions": [
                {"type": "open", "label": "Open Directory", "target": "parent_dir"},
                {"type": "refresh", "label": "Refresh", "target": "current_dir"},
            ]
        }
    
    def _get_file_icon(self, permissions: str, filename: str) -> str:
        """Get appropriate icon for file type"""
        if permissions.startswith('d'):
            return "📁"
        elif permissions.startswith('l'):
            return "🔗"
        elif 'x' in permissions:
            return "⚙️"
        elif filename.endswith('.txt'):
            return "📄"
        elif filename.endswith(('.jpg', '.png', '.gif', '.jpeg')):
            return "🖼️"
        elif filename.endswith(('.mp3', '.wav', '.flac')):
            return "🎵"
        elif filename.endswith(('.mp4', '.avi', '.mkv')):
            return "🎬"
        elif filename.endswith(('.zip', '.tar', '.gz', '.rar')):
            return "📦"
        elif filename.endswith('.py'):
            return "🐍"
        elif filename.endswith(('.js', '.jsx', '.ts', '.tsx')):
            return "📜"
        else:
            return "📃"
    
    # ==================== SYSTEM INFO FORMATTER ====================
    def _format_system_info(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """Format system information beautifully"""
        lines = output.strip().split('\n')
        
        info_dict = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info_dict[key.strip()] = value.strip()
        
        return {
            "type": "system_info",
            "success": success,
            "command": command,
            "data": info_dict,
            "visualization": "info_card",
            "explanation": self._generate_system_explanation(info_dict),
            "raw_output": output,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "format": "key-value"
            }
        }
    
    def _generate_system_explanation(self, info_dict: Dict[str, str]) -> str:
        """Generate human-readable explanation of system info"""
        explanations = []
        for key, value in list(info_dict.items())[:3]:
            explanations.append(f"{key}: {value}")
        return " • ".join(explanations)
    
    # ==================== PROCESS LIST FORMATTER ====================
    def _format_process_list(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """Format process lists beautifully"""
        lines = output.strip().split('\n')
        
        processes = []
        headers = []
        
        for idx, line in enumerate(lines):
            if idx == 0:
                headers = line.split()
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                process = {
                    "pid": parts[0] if parts else "N/A",
                    "command": ' '.join(parts[1:]) if len(parts) > 1 else "N/A",
                    "raw": line
                }
                processes.append(process)
        
        return {
            "type": "process_list",
            "success": success,
            "command": command,
            "count": len(processes),
            "data": processes[:10],  # Limit to top 10
            "has_more": len(processes) > 10,
            "total_processes": len(processes),
            "visualization": "list",
            "explanation": f"Currently running {len(processes)} processes. Showing top 10 most recent.",
            "raw_output": output,
        }
    
    # ==================== DISK USAGE FORMATTER ====================
    def _format_disk_usage(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """Format disk usage information beautifully"""
        lines = output.strip().split('\n')
        
        disks = []
        for line in lines[1:]:  # Skip header
            if not line.strip():
                continue
            
            parts = line.split()
            if len(parts) >= 4:
                used = int(parts[1])
                total = int(parts[0])
                used_percent = (used / total * 100) if total > 0 else 0
                
                disk_info = {
                    "filesystem": parts[-1],
                    "size": parts[0],
                    "used": parts[1],
                    "available": parts[2],
                    "usage_percent": round(used_percent, 1),
                    "usage_level": self._get_usage_level(used_percent),
                    "raw": line
                }
                disks.append(disk_info)
        
        total_used = sum(int(d["used"]) for d in disks if d["used"].isdigit())
        total_size = sum(int(d["size"]) for d in disks if d["size"].isdigit())
        
        return {
            "type": "disk_usage",
            "success": success,
            "command": command,
            "data": disks,
            "summary": {
                "total_size": self._bytes_to_human(total_size),
                "total_used": self._bytes_to_human(total_used),
                "total_free": self._bytes_to_human(total_size - total_used),
                "usage_percent": round((total_used / total_size * 100), 1) if total_size > 0 else 0
            },
            "visualization": "progress_bars",
            "explanation": f"Disk usage: {round((total_used / total_size * 100), 1)}% used. {self._bytes_to_human(total_size - total_used)} free space available.",
            "raw_output": output,
            "warning": total_used / total_size > 0.9 if total_size > 0 else False
        }
    
    def _get_usage_level(self, percent: float) -> str:
        """Get usage level label"""
        if percent < 50:
            return "low"
        elif percent < 75:
            return "medium"
        elif percent < 90:
            return "high"
        else:
            return "critical"
    
    # ==================== NETWORK INFO FORMATTER ====================
    def _format_network_info(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """Format network information beautifully"""
        lines = output.strip().split('\n')
        
        network_data = {
            "interfaces": [],
            "raw_lines": lines
        }
        
        current_interface = None
        for line in lines:
            if line and not line[0].isspace():
                current_interface = {
                    "name": line.split()[0] if line.split() else "unknown",
                    "details": {}
                }
                network_data["interfaces"].append(current_interface)
            elif current_interface and ':' in line:
                key, value = line.split(':', 1)
                current_interface["details"][key.strip()] = value.strip()
        
        return {
            "type": "network_info",
            "success": success,
            "command": command,
            "data": network_data["interfaces"],
            "interface_count": len(network_data["interfaces"]),
            "visualization": "info_cards",
            "explanation": f"Found {len(network_data['interfaces'])} network interfaces configured on this system.",
            "raw_output": output,
        }
    
    # ==================== ERROR FORMATTER ====================
    def _format_error(self, output: str, command: str = "", success: bool = False) -> Dict[str, Any]:
        """Format error messages beautifully with helpful suggestions"""
        
        error_type = "unknown_error"
        suggestions = []
        
        output_lower = output.lower()
        
        if "permission denied" in output_lower:
            error_type = "permission_denied"
            suggestions = [
                "Try using 'sudo' command with appropriate permissions",
                "Check file/directory ownership",
                "Verify user group membership"
            ]
        elif "not found" in output_lower or "no such file" in output_lower:
            error_type = "not_found"
            suggestions = [
                "Check the path and filename spelling",
                "Verify the file/directory exists",
                "Try using absolute path instead of relative path"
            ]
        elif "command not found" in output_lower:
            error_type = "command_not_found"
            suggestions = [
                "Check if the command is installed",
                "Verify the command is in your PATH",
                "Try installing the required package"
            ]
        elif "connection refused" in output_lower:
            error_type = "connection_refused"
            suggestions = [
                "Check if the service is running",
                "Verify the port number is correct",
                "Check firewall settings"
            ]
        
        return {
            "type": "error",
            "success": success,
            "command": command,
            "error_type": error_type,
            "message": output.split('\n')[0] if output else "An error occurred",
            "details": output,
            "visualization": "error_alert",
            "suggestions": suggestions,
            "explanation": f"An error occurred: {error_type.replace('_', ' ')}. See suggestions for resolution.",
            "raw_output": output,
            "severity": "high"
        }
    
    # ==================== SUCCESS FORMATTER ====================
    def _format_success(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """Format success messages beautifully"""
        
        return {
            "type": "success",
            "success": success,
            "command": command,
            "message": output.split('\n')[0] if output else "Operation completed successfully!",
            "details": output,
            "visualization": "success_banner",
            "explanation": output if len(output) < 200 else output[:200] + "...",
            "raw_output": output,
            "icon": "✅",
            "timestamp": datetime.now().isoformat()
        }
    
    # ==================== TEXT OUTPUT FORMATTER ====================
    def _format_text_output(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """Format plain text output with basic formatting"""
        
        lines = output.strip().split('\n')
        line_count = len(lines)
        
        return {
            "type": "text",
            "success": success,
            "command": command,
            "content": output,
            "line_count": line_count,
            "preview": '\n'.join(lines[:5]),
            "has_more": line_count > 5,
            "visualization": "code_block",
            "explanation": f"Output contains {line_count} lines of text.",
            "raw_output": output,
            "metadata": {
                "character_count": len(output),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    # ==================== TABLE FORMATTER ====================
    def _format_table(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """Format tabular data"""
        
        lines = output.strip().split('\n')
        headers = []
        rows = []
        
        if lines:
            headers = lines[0].split()
            for line in lines[1:]:
                if line.strip():
                    rows.append(line.split())
        
        return {
            "type": "table",
            "success": success,
            "command": command,
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "visualization": "table",
            "explanation": f"Formatted data as table with {len(headers)} columns and {len(rows)} rows.",
            "raw_output": output,
        }
    
    # ==================== JSON FORMATTER ====================
    def _format_json(self, output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
        """Format JSON data beautifully"""
        
        try:
            data = json.loads(output)
        except:
            data = {"error": "Could not parse JSON"}
        
        return {
            "type": "json",
            "success": success,
            "command": command,
            "data": data,
            "visualization": "json_viewer",
            "explanation": "Formatted output as structured JSON data.",
            "raw_output": output,
            "is_valid": isinstance(data, dict) or isinstance(data, list)
        }
    
    # ==================== EMPTY OUTPUT FORMATTER ====================
    def _format_empty_output(self) -> Dict[str, Any]:
        """Format empty output"""
        return {
            "type": "empty",
            "success": True,
            "message": "Command executed successfully with no output",
            "visualization": "empty_state",
            "explanation": "The command completed without producing any output.",
            "raw_output": ""
        }
    
    # ==================== UTILITY FUNCTIONS ====================
    def _bytes_to_human(self, bytes_val: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"
    
    def _sanitize_output(self, output: str) -> str:
        """Remove ANSI color codes and other escape sequences"""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', output)
    
    def add_ai_insights(self, formatted_response: Dict[str, Any], insights: str = "") -> Dict[str, Any]:
        """Add AI-powered insights and explanations to the response"""
        formatted_response["ai_insights"] = insights or formatted_response.get("explanation", "")
        formatted_response["generated_at"] = datetime.now().isoformat()
        return formatted_response


# Global formatter instance
output_formatter = OutputFormatter()


def format_output(output: str, command: str = "", success: bool = True) -> Dict[str, Any]:
    """Convenience function to format output"""
    return output_formatter.format(output, command, success)
