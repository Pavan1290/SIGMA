#!/usr/bin/env python3
"""
Test Email Agent with Langchain & Gmail API
Quick verification script
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    
    try:
        from intelligent_agents import EmailAgent
        print("✅ EmailAgent imported successfully")
    except Exception as e:
        print(f"❌ EmailAgent import failed: {e}")
        return False
    
    try:
        import langchain
        from langchain_openai import ChatOpenAI
        from langchain.memory import ConversationBufferMemory
        print(f"✅ Langchain v{langchain.__version__} imported successfully")
    except Exception as e:
        print(f"⚠️  Langchain import failed: {e}")
        print("   Email agent will work but without Langchain features")
    
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        print("✅ Google API libraries imported successfully")
    except Exception as e:
        print(f"❌ Google API import failed: {e}")
        return False
    
    return True

def test_credentials():
    """Test credentials availability"""
    print("\n🔑 Testing credentials...")
    
    # Check credentials.json
    creds_file = Path(__file__).parent / 'credentials.json'
    if creds_file.exists():
        print(f"✅ credentials.json found")
        import json
        with open(creds_file) as f:
            data = json.load(f)
            if 'installed' in data:
                print(f"   Client ID: {data['installed']['client_id'][:20]}...")
                print(f"   Project: {data['installed']['project_id']}")
    else:
        print(f"❌ credentials.json not found")
        return False
    
    # Check API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OPENAI_API_KEY found ({openai_key[:15]}...)")
    else:
        print("⚠️  OPENAI_API_KEY not found - Langchain features won't work")
    
    google_key = os.getenv('GOOGLE_API_KEY')
    if google_key:
        print(f"✅ GOOGLE_API_KEY found ({google_key[:15]}...)")
    else:
        print("⚠️  GOOGLE_API_KEY not found")
    
    return True

def test_email_agent():
    """Test EmailAgent initialization"""
    print("\n🤖 Testing EmailAgent initialization...")
    
    try:
        from intelligent_agents import EmailAgent
        
        def update_callback(update):
            print(f"   [{update.status.value}] {update.message}")
        
        agent = EmailAgent(update_callback=update_callback)
        print(f"✅ EmailAgent created: {agent.name}")
        print(f"   Capabilities: {', '.join(agent.capabilities[:3])}...")
        
        # Check if Langchain LLM is initialized
        if hasattr(agent, 'langchain_llm') and agent.langchain_llm:
            print("✅ Langchain LLM initialized - advanced email composition available")
        else:
            print("ℹ️  Using standard AI models for email composition")
        
        return True
        
    except Exception as e:
        print(f"❌ EmailAgent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("📧 Email Agent with Langchain & Gmail API - Test Suite")
    print("="*60)
    
    if not test_imports():
        print("\n❌ Import tests failed")
        return
    
    if not test_credentials():
        print("\n❌ Credentials tests failed")
        return
    
    if not test_email_agent():
        print("\n❌ EmailAgent tests failed")
        return
    
    print("\n" + "="*60)
    print("✅ All tests passed! Email agent is ready to use.")
    print("="*60)
    print("\n📝 Usage examples:")
    print("   - Send email: 'Send an email to john@example.com about meeting tomorrow'")
    print("   - Read emails: 'Show me my recent emails'")
    print("   - Search: 'Find emails from sarah about the project'")
    print("\n💡 Start the backend server with: ./start.sh")
    print("   Then use the UI to send email commands to the agent.")

if __name__ == "__main__":
    main()
