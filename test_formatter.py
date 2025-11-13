#!/usr/bin/env python3
"""
Test script for the Output Formatter
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from intelligent_agents.output_formatter import format_output

# Test data
test_cases = [
    {
        "name": "File Listing",
        "command": "ls -la",
        "output": """total 48
drwxr-xr-x 10 user user 4096 Nov 13 22:32 .
drwxr-xr-x 33 user user 4096 Nov 13 22:50 ..
drwxrwxr-x  3 user user 4096 Nov 13 09:45 .git
-rw-r--r--  1 user user 1024 Nov 13 10:00 README.md
-rw-r--r--  1 user user 2048 Nov 13 11:30 setup.py
drwxrwxr-x  5 user user 4096 Nov 13 14:20 src
-rwxr-xr-x  1 user user 512 Nov 13 15:45 script.sh
lrwxrwxrwx  1 user user   15 Nov 13 16:00 link -> /usr/local/bin"""
    },
    {
        "name": "Disk Usage",
        "command": "df -h",
        "output": """Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1       100G   85G   15G  85% /
tmpfs           8.0G     0  8.0G   0% /dev/shm
/dev/sdb1       500G  250G  250G  50% /home"""
    },
    {
        "name": "System Info",
        "command": "uname -a",
        "output": """Linux hostname 5.15.0-56-generic #62-Ubuntu SMP Tue Nov 1 09:26:06 UTC 2022 x86_64 GNU/Linux
Architecture: x86_64
CPU op-mode(s): 32-bit, 64-bit"""
    },
    {
        "name": "Error Output",
        "command": "cat nonexistent.txt",
        "output": "cat: nonexistent.txt: No such file or directory",
        "success": False
    },
    {
        "name": "Success Message",
        "command": "touch test.txt",
        "output": "File created successfully",
        "success": True
    }
]

print("=" * 70)
print("OUTPUT FORMATTER TEST SUITE")
print("=" * 70)
print()

for test in test_cases:
    print(f"\n📝 Test: {test['name']}")
    print(f"   Command: {test['command']}")
    print("-" * 70)
    
    result = format_output(
        test['output'],
        test['command'],
        test.get('success', True)
    )
    
    print(f"   Type: {result.get('type')}")
    print(f"   Success: {result.get('success')}")
    
    # Display relevant information based on type
    if result.get('type') == 'file_listing':
        summary = result.get('summary', {})
        print(f"   📁 Items: {summary.get('total_items', 0)}")
        print(f"   📊 Directories: {summary.get('directories', 0)}")
        print(f"   📄 Files: {summary.get('files', 0)}")
        print(f"   💾 Total Size: {summary.get('total_size_human', 'N/A')}")
        print(f"   ✨ Explanation: {result.get('explanation', 'N/A')}")
        
    elif result.get('type') == 'disk_usage':
        summary = result.get('summary', {})
        print(f"   📊 Usage: {summary.get('usage_percent', 0)}%")
        print(f"   💾 Used: {summary.get('total_used', 'N/A')}")
        print(f"   🎯 Free: {summary.get('total_free', 'N/A')}")
        print(f"   ✨ Explanation: {result.get('explanation', 'N/A')}")
        
    elif result.get('type') == 'system_info':
        print(f"   🖥️ Data points: {len(result.get('data', {}))}")
        print(f"   ✨ Explanation: {result.get('explanation', 'N/A')}")
        
    elif result.get('type') == 'error':
        print(f"   ⚠️ Error Type: {result.get('error_type', 'unknown')}")
        print(f"   💡 Suggestions: {len(result.get('suggestions', []))}")
        print(f"   ✨ Explanation: {result.get('explanation', 'N/A')}")
        
    elif result.get('type') == 'success':
        print(f"   ✅ Message: {result.get('message', 'N/A')}")
        print(f"   ✨ Explanation: {result.get('explanation', 'N/A')}")
    
    # Show full JSON for debugging
    print(f"\n   📦 Full Response (JSON):")
    print(json.dumps(result, indent=2)[:500] + "...")

print("\n" + "=" * 70)
print("✅ All tests completed!")
print("=" * 70)
