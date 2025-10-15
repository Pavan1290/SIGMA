#!/usr/bin/env python3
"""
Email Agent - Intelligent email management
Uses Gmail API for reliable email operations
"""

import os
import json
import time
import base64
from pathlib import Path
from typing import Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .agent_core import IntelligentAgent, AgentStatus

class EmailAgent(IntelligentAgent):
    """
    Intelligent agent for email operations using Gmail API
    No Selenium needed - uses official Google API
    """
    
    def __init__(self, update_callback=None):
        super().__init__(
            name="EmailAgent",
            capabilities=[
                "send_email",
                "read_email",
                "search_email",
                "compose_intelligent_emails",
                "handle_attachments"
            ],
            update_callback=update_callback
        )
        self.gmail_service = None
    
    def _init_gmail_api(self):
        """Initialize Gmail API (proper way, not Selenium)"""
        
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/gmail.send']
            creds = None
            
            token_path = Path.home() / '.sigma_gmail_token.json'
            
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Need credentials.json from Google Cloud Console
                    creds_file = Path(__file__).parent.parent / 'credentials.json'
                    if not creds_file.exists():
                        raise Exception("Missing credentials.json - Download from Google Cloud Console")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                token_path.write_text(creds.to_json())
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            return True
            
        except ImportError:
            raise Exception("Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        except Exception as e:
            raise Exception(f"Gmail API init failed: {str(e)}")
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an email operation step"""
        
        tool = step.get('tool', 'auto')
        action = step.get('action', '')
        
        # Initialize Gmail API if needed
        if not self.gmail_service:
            self._send_update(AgentStatus.EXECUTING, "Initializing Gmail API...")
            self._init_gmail_api()
        
        # Let AI decide which operation
        if tool == 'auto':
            tool = self._decide_operation(action, context)
        
        self._send_update(
            AgentStatus.EXECUTING,
            f"Email operation: {tool} - {action}"
        )
        
        if tool == 'send_email':
            return self._send_email(action, context)
        elif tool == 'read_email':
            return self._read_email(action, context)
        elif tool == 'search_email':
            return self._search_email(action, context)
        else:
            # Let AI compose the email intelligently
            return self._ai_compose_and_send(action, context)
    
    def _decide_operation(self, action: str, context: Dict[str, Any]) -> str:
        """Use AI to decide which email operation"""
        
        prompt = f"""Given this email task: "{action}"
Context: {json.dumps(context, indent=2)}

Which operation? Choose from:
- send_email: Send a new email
- read_email: Read existing emails
- search_email: Search for specific emails

Respond with just the operation name."""

        try:
            response = self.execution_model.generate_content(prompt)
            return response.text.strip().lower().replace(' ', '_')
        except:
            return 'send_email'  # Default
    
    def _ai_compose_and_send(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to compose and send email intelligently"""
        
        self._send_update(
            AgentStatus.THINKING,
            "Composing email using AI..."
        )
        
        # Use AI to extract email details and compose content
        prompt = f"""Task: {action}
Context: {json.dumps(context, indent=2)}

Compose a professional email. Provide JSON:
{{
    "to": ["email@example.com"],
    "subject": "email subject",
    "body": "email body content - be professional and clear",
    "tone": "professional|casual|urgent"
}}

If the task mentions a reminder, make it sound professional but friendly.
Extract all email addresses from the task."""

        try:
            response = self.thinking_model.generate_content(prompt)
            email_text = response.text.strip()
            
            if "```json" in email_text:
                email_text = email_text.split("```json")[1].split("```")[0].strip()
            elif "```" in email_text:
                email_text = email_text.split("```")[1].split("```")[0].strip()
            
            email_data = json.loads(email_text)
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"Sending to: {', '.join(email_data['to'])}"
            )
            
            return self._send_email_api(
                to=email_data['to'],
                subject=email_data['subject'],
                body=email_data['body']
            )
            
        except Exception as e:
            raise Exception(f"AI composition failed: {str(e)}")
    
    def _send_email(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using Gmail API"""
        return self._ai_compose_and_send(action, context)
    
    def _send_email_api(self, to: List[str], subject: str, body: str) -> Dict[str, Any]:
        """Actually send the email via Gmail API"""
        
        try:
            message = MIMEMultipart()
            message['To'] = ', '.join(to)
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            send_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            self._send_update(
                AgentStatus.SUCCESS,
                f"✅ Email sent successfully to {', '.join(to)}"
            )
            
            return {
                "success": True,
                "operation": "send_email",
                "to": to,
                "subject": subject,
                "message_id": send_message.get('id')
            }
            
        except Exception as e:
            raise Exception(f"Email send failed: {str(e)}")
    
    def _read_email(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Read emails from Gmail"""
        
        try:
            # Get recent messages
            results = self.gmail_service.users().messages().list(
                userId='me',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            
            return {
                "success": True,
                "operation": "read_email",
                "count": len(messages),
                "messages": messages
            }
            
        except Exception as e:
            raise Exception(f"Read email failed: {str(e)}")
    
    def _search_email(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search emails"""
        
        # Use AI to generate search query
        prompt = f"""Convert this to a Gmail search query: "{action}"

Examples:
- "emails from john" → "from:john"
- "unread emails" → "is:unread"
- "emails with attachments" → "has:attachment"

Respond with just the search query."""

        try:
            response = self.execution_model.generate_content(prompt)
            query = response.text.strip()
            
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=20
            ).execute()
            
            messages = results.get('messages', [])
            
            return {
                "success": True,
                "operation": "search_email",
                "query": query,
                "count": len(messages),
                "messages": messages
            }
            
        except Exception as e:
            raise Exception(f"Email search failed: {str(e)}")
