#!/usr/bin/env python3
"""Quick test of Email Agent"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from intelligent_agents import EmailAgent

def test_email_agent():
    print("🧪 Testing Email Agent...\n")
    
    agent = EmailAgent()
    
    try:
        print("✅ EmailAgent initialized successfully!")
        print(f"   Capabilities: {', '.join(agent.capabilities)}")
        
        # Try to initialize Gmail API
        print("\n🔐 Testing Gmail API connection...")
        agent._init_gmail_api()
        print("✅ Gmail API connected!")
        print("✅ Credentials verified!")
        print("\n📧 Email Agent is READY TO USE!")
        print("\nNext step: ./start.sh")
        print("Then try: 'send email to someone@example.com about test'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check credentials.json exists in project root")
        print("2. Verify Google Cloud project has Gmail API enabled")
        print("3. Check OAuth credentials are set up correctly")
        return False

if __name__ == "__main__":
    success = test_email_agent()
    sys.exit(0 if success else 1)
