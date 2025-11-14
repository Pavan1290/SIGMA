#!/usr/bin/env python3
"""
Quick Demo: Email Agent with Langchain & Gmail API
Test sending an email
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from intelligent_agents import EmailAgent

def demo_send_email():
    """Demo: Send an email"""
    
    print("="*60)
    print("📧 Email Agent Demo - Send Email")
    print("="*60)
    
    def update_callback(update):
        print(f"[{update.status.value.upper()}] {update.message}")
    
    # Create email agent
    agent = EmailAgent(update_callback=update_callback)
    
    # Example: Send email (you can modify this)
    print("\n🚀 Sending test email...")
    print("Note: Update the email address below to test!\n")
    
    result = agent.run(
        task="Send an email to your-email@example.com with subject 'Test from SIGMA Email Agent' and body 'Hi! This is a test email sent using the SIGMA Email Agent with Gmail API and AI. The agent can compose professional emails automatically. Best regards, SIGMA AI Assistant'",
        context={}
    )
    
    print("\n" + "="*60)
    if result.get('success'):
        print("✅ Email sent successfully!")
        print(f"Results: {result}")
    else:
        print("❌ Email failed:")
        print(f"Error: {result.get('error')}")
    print("="*60)

if __name__ == "__main__":
    print("\n⚠️  Before running this demo:")
    print("1. Make sure you have credentials.json in the project root")
    print("2. Make sure OPENAI_API_KEY is set in .env")
    print("3. Update the email address in the code")
    print("4. The first time will open a browser for Gmail OAuth")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
        demo_send_email()
    except KeyboardInterrupt:
        print("\n\n❌ Demo cancelled")
