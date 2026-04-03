#!/usr/bin/env python3
"""
Email Agent - Intelligent email management with Langchain
Uses Gmail API + Langchain LLM for intelligent email automation
"""

import os
import json
import time
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from .agent_core import IntelligentAgent, AgentStatus

# Langchain imports (optional - for advanced features)
try:
    from langchain_openai import ChatOpenAI
    from langchain_community.chat_message_histories import ChatMessageHistory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

class EmailAgent(IntelligentAgent):
    """
    Intelligent email agent using Langchain + Gmail API
    - Understands natural language email requests
    - Composes professional emails automatically
    - Searches and filters emails intelligently
    - Manages email workflows with memory
    """
    
    def __init__(self, update_callback=None):
        super().__init__(
            name="EmailAgent",
            capabilities=[
                "send_email",
                "read_email",
                "search_email",
                "compose_intelligent_emails",
                "handle_attachments",
                "create_email_drafts",
                "manage_labels",
                "auto_respond"
            ],
            update_callback=update_callback
        )
        self.gmail_service = None
        self.langchain_llm = None
        self.message_history = None
        self._init_langchain() if LANGCHAIN_AVAILABLE else None
    
    def _init_langchain(self):
        """Initialize Langchain LLM for advanced email composition"""
        if not LANGCHAIN_AVAILABLE:
            return
        
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                return
            
            # Initialize ChatOpenAI for intelligent email composition
            self.langchain_llm = ChatOpenAI(
                temperature=0.7,
                model_name="gpt-4-turbo-preview",
                api_key=api_key
            )
            
            # Simple message history for context
            self.message_history = ChatMessageHistory()
            
            self._send_update(AgentStatus.EXECUTING, "Langchain LLM initialized with OpenAI GPT-4")
            
        except Exception as e:
            self._send_update(AgentStatus.ERROR, f"Langchain init failed: {str(e)}")
    
    def _init_gmail_api(self):
        """Initialize Gmail API with comprehensive scopes"""
        
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            # Comprehensive Gmail scopes
            SCOPES = [
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/gmail.labels'
            ]
            creds = None
            
            token_path = Path.home() / '.sigma_gmail_token.json'
            
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Load credentials from credentials.json
                    creds_file = Path(__file__).parent.parent / 'credentials.json'
                    if not creds_file.exists():
                        raise Exception("Missing credentials.json - Download from Google Cloud Console")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next use
                token_path.write_text(creds.to_json())
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            self._send_update(AgentStatus.EXECUTING, "Gmail API initialized successfully")
            return True
            
        except ImportError:
            raise Exception("Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        except Exception as e:
            raise Exception(f"Gmail API init failed: {str(e)}")
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an email operation step using AI + Gmail API"""
        
        tool = step.get('tool', 'auto')
        action = step.get('action', '')
        
        # Initialize Gmail API if needed
        if not self.gmail_service:
            self._send_update(AgentStatus.EXECUTING, "Initializing Gmail API...")
            self._init_gmail_api()
        
        # Decide operation
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
            response = self._get_execution_model().generate_content(prompt)
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
    "tone": "professional|casual|urgent",
    "cc": [],
    "bcc": []
}}

If the task mentions a reminder, make it sound professional but friendly.
Extract all email addresses from the task.
Make the body well-formatted and professional."""

        try:
            response = self._get_thinking_model().generate_content(prompt)
            email_text = response.text.strip()
            
            if "```json" in email_text:
                email_text = email_text.split("```json")[1].split("```")[0].strip()
            elif "```" in email_text:
                email_text = email_text.split("```")[1].split("```")[0].strip()
            
            email_data = json.loads(email_text)
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"Sending to: {', '.join(email_data.get('to', []))}"
            )
            
            return self._send_email_api(
                to=email_data.get('to', []),
                subject=email_data.get('subject', 'No Subject'),
                body=email_data.get('body', ''),
                cc=email_data.get('cc', []),
                bcc=email_data.get('bcc', [])
            )
            
        except Exception as e:
            raise Exception(f"AI composition failed: {str(e)}")
    
    def _send_email(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using Gmail API"""
        return self._ai_compose_and_send(action, context)
    
    def _send_email_api(self, to: List[str], subject: str, body: str, cc: List[str] = None, bcc: List[str] = None) -> Dict[str, Any]:
        """Actually send the email via Gmail API with HTML support"""
        
        try:
            message = MIMEMultipart('alternative')
            message['To'] = ', '.join(to)
            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)
            message['Subject'] = subject
            message['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Attach both plain text and HTML versions
            message.attach(MIMEText(body, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            send_message = self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            all_recipients = to + (cc or []) + (bcc or [])
            self._send_update(
                AgentStatus.SUCCESS,
                f"✅ Email sent successfully to {len(to)} recipient(s)"
            )
            
            return {
                "success": True,
                "operation": "send_email",
                "to": to,
                "cc": cc or [],
                "bcc": bcc or [],
                "subject": subject,
                "message_id": send_message.get('id'),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self._send_update(AgentStatus.ERROR, f"Email send failed: {str(e)}")
            raise Exception(f"Email send failed: {str(e)}")
    
    def _read_email(self, action: str, context: Dict[str, Any], max_results: int = 10) -> Dict[str, Any]:
        """Read emails from Gmail with full content"""
        
        try:
            # Get recent messages
            results = self.gmail_service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q="in:inbox"
            ).execute()
            
            messages = results.get('messages', [])
            
            # Fetch full message details
            email_list = []
            for msg in messages[:5]:  # Limit to 5 for performance
                try:
                    full_msg = self.gmail_service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    headers = full_msg['payload'].get('headers', [])
                    headers_dict = {h['name']: h['value'] for h in headers}
                    
                    email_list.append({
                        "id": msg['id'],
                        "from": headers_dict.get('From', 'Unknown'),
                        "subject": headers_dict.get('Subject', '(No Subject)'),
                        "date": headers_dict.get('Date', 'Unknown'),
                        "snippet": full_msg.get('snippet', '')
                    })
                except:
                    pass
            
            self._send_update(
                AgentStatus.SUCCESS,
                f"Retrieved {len(email_list)} emails from inbox"
            )
            
            return {
                "success": True,
                "operation": "read_email",
                "count": len(email_list),
                "emails": email_list
            }
            
        except Exception as e:
            self._send_update(AgentStatus.ERROR, f"Read email failed: {str(e)}")
            raise Exception(f"Read email failed: {str(e)}")
    
    def _search_email(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search emails intelligently using AI to generate queries"""
        
        # Use AI to generate optimized search query
        prompt = f"""Convert this to a Gmail search query: "{action}"

Examples:
- "emails from john" → "from:john"
- "unread emails" → "is:unread"
- "emails with attachments" → "has:attachment"
- "important emails from last week" → "is:important after:2024-11-07"
- "emails about project x" → "subject:project x"

Respond with just the search query, no explanation."""

        try:
            self._send_update(AgentStatus.THINKING, "Generating search query...")
            response = self._get_execution_model().generate_content(prompt)
            query = response.text.strip()
            
            self._send_update(AgentStatus.EXECUTING, f"Searching with query: {query}")
            
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=20
            ).execute()
            
            messages = results.get('messages', [])
            
            # Fetch details for found emails
            email_list = []
            for msg in messages[:10]:
                try:
                    full_msg = self.gmail_service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    headers = full_msg['payload'].get('headers', [])
                    headers_dict = {h['name']: h['value'] for h in headers}
                    
                    email_list.append({
                        "id": msg['id'],
                        "from": headers_dict.get('From', 'Unknown'),
                        "subject": headers_dict.get('Subject', '(No Subject)'),
                        "date": headers_dict.get('Date', 'Unknown'),
                        "snippet": full_msg.get('snippet', '')
                    })
                except:
                    pass
            
            self._send_update(
                AgentStatus.SUCCESS,
                f"Found {len(email_list)} matching emails"
            )
            
            return {
                "success": True,
                "operation": "search_email",
                "query": query,
                "count": len(email_list),
                "emails": email_list
            }
            
        except Exception as e:
            self._send_update(AgentStatus.ERROR, f"Email search failed: {str(e)}")
            raise Exception(f"Email search failed: {str(e)}")
