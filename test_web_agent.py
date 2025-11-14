#!/usr/bin/env python3
"""
Test script for Puppeteer-based web automation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from intelligent_agents.web_agent import WebAgent

def test_web_search():
    """Test Google search functionality"""
    print("\n🧪 Testing Web Agent with Puppeteer...")
    print("=" * 60)
    
    agent = WebAgent()
    
    # Test 1: Search Google
    print("\n📝 Test 1: Search Google for 'Python programming'")
    result = agent.run("search google for Python programming")
    
    if result['success']:
        print("✅ Search successful!")
        raw_results = result.get('search_results', [])
        if raw_results:
            print(f"Found {result.get('count', len(raw_results))} results")
            for i, item in enumerate(raw_results[:3], 1):
                title = item.get('title') or 'Untitled result'
                link = item.get('link') or 'No URL provided'
                print(f"\n{i}. {title}")
                print(f"   {link}")
        else:
            print("No detailed results returned; response:")
            print(result.get('response'))
    else:
        print(f"❌ Search failed: {result.get('error')}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_web_search()
