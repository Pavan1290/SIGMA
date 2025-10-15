#!/usr/bin/env python3
"""
Web Agent - Intelligent web browsing and automation
Uses Playwright for reliable web automation (better than Selenium)
"""

import os
import json
import time
from typing import Dict, Any, List
from .agent_core import IntelligentAgent, AgentStatus
import asyncio

class WebAgent(IntelligentAgent):
    """
    Intelligent agent for web operations
    Uses Playwright instead of Selenium (more reliable)
    """
    
    def __init__(self, update_callback=None):
        super().__init__(
            name="WebAgent",
            capabilities=[
                "browse_web",
                "extract_information",
                "fill_forms",
                "click_buttons",
                "scrape_data",
                "interact_with_pages"
            ],
            update_callback=update_callback
        )
        self.browser = None
        self.page = None
        self._async_pw = None
    
    async def _init_browser(self):
        """Initialize Playwright browser using async API (compatible with FastAPI/asyncio)."""
        try:
            from playwright.async_api import async_playwright
            self._async_pw = await async_playwright().start()
            self.browser = await self._async_pw.chromium.launch(headless=False)
            self.page = await self.browser.new_page()
            return True
        except ImportError:
            raise Exception("Install Playwright: pip install playwright && playwright install")
        except Exception as e:
            raise Exception(f"Browser init failed: {str(e)}")
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a web operation step; wraps async calls for compatibility with sync agent loop."""
        async def runner():
            return await self._execute_step_async(step, context)

        # Run in existing loop if not running, otherwise spawn a new loop in a thread
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                import threading
                result_holder = {}

                def _thread_run():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result_holder['value'] = new_loop.run_until_complete(runner())
                    finally:
                        new_loop.close()

                t = threading.Thread(target=_thread_run)
                t.start(); t.join()
                return result_holder.get('value')
            else:
                return loop.run_until_complete(runner())
        except RuntimeError:
            # No running loop, safe to asyncio.run
            return asyncio.run(runner())

    async def _execute_step_async(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.browser:
            self._send_update(AgentStatus.EXECUTING, "Starting browser...")
            await self._init_browser()

        tool = step.get('tool', 'auto')
        action = step.get('action', '')

        self._send_update(AgentStatus.EXECUTING, f"Web action: {action}")

        if tool == 'auto':
            tool = self._decide_web_action(action, context)

        if tool == 'navigate':
            return await self._navigate(action, context)
        elif tool == 'extract':
            return await self._extract_info(action, context)
        elif tool == 'interact':
            return await self._interact(action, context)
        else:
            return await self._ai_web_action(action, context)
    
    def _decide_web_action(self, action: str, context: Dict[str, Any]) -> str:
        """Use AI to decide web action type"""
        
        prompt = f"""Web task: "{action}"
Context: {json.dumps(context, indent=2)}

Choose action type:
- navigate: Go to a URL
- extract: Get information from page
- interact: Click, type, fill forms

Respond with just the action type."""

        try:
            response = self._get_execution_model().generate_content(prompt)
            return response.text.strip().lower()
        except:
            return 'navigate'
    
    async def _navigate(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL"""
        
        # Use AI to extract URL from action
        prompt = f"""Extract the URL from: "{action}"
If no URL, provide a reasonable default based on the task.

Respond with just the URL, nothing else."""

        try:
            response = self._get_execution_model().generate_content(prompt)
            url = response.text.strip()
            
            # Ensure URL has protocol
            if not url.startswith('http'):
                url = 'https://' + url
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"Navigating to: {url}"
            )
            
            await self.page.goto(url, wait_until='networkidle')
            
            return {
                "success": True,
                "operation": "navigate",
                "url": url,
                "title": await self.page.title()
            }
            
        except Exception as e:
            raise Exception(f"Navigation failed: {str(e)}")
    
    async def _extract_info(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from webpage"""
        
        try:
            # Get page content
            content = await self.page.content()
            visible_text = await self.page.inner_text('body')
            
            # Use AI to extract relevant information
            prompt = f"""From this webpage, extract: "{action}"

Page content (truncated):
{visible_text[:3000]}

Provide the extracted information in JSON format."""

            response = self._get_thinking_model().generate_content(prompt)
            info_text = response.text.strip()
            
            if "```json" in info_text:
                info_text = info_text.split("```json")[1].split("```")[0].strip()
            elif "```" in info_text:
                info_text = info_text.split("```")[1].split("```")[0].strip()
            
            extracted = json.loads(info_text)
            
            return {
                "success": True,
                "operation": "extract",
                "data": extracted
            }
            
        except Exception as e:
            raise Exception(f"Extraction failed: {str(e)}")
    
    async def _interact(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Interact with webpage elements"""
        
        # Use AI to generate interaction steps
        prompt = f"""Task: {action}
Current page: {self.page.url}

Generate Playwright code to accomplish this. Use:
- page.click('selector')
- page.fill('selector', 'text')
- page.press('selector', 'Enter')
- page.wait_for_selector('selector')

Respond with ONLY Python code using 'page' variable."""

        try:
            response = self._get_execution_model().generate_content(prompt)
            code = response.text.strip()
            
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"Executing web interaction..."
            )
            
            # Execute the interaction code
            namespace = {'page': self.page, 'result': None}
            exec(code, namespace)
            
            return {
                "success": True,
                "operation": "interact",
                "action": action,
                "result": namespace.get('result')
            }
            
        except Exception as e:
            raise Exception(f"Interaction failed: {str(e)}")
    
    async def _ai_web_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Let AI figure out how to do the web action"""
        
        prompt = f"""Accomplish this web task: "{action}"
Current URL: {self.page.url if self.page else 'No page loaded'}
Context: {json.dumps(context, indent=2)}

Provide Playwright code to do this. Use the 'page' object.
Respond with ONLY Python code."""

        try:
            response = self._get_thinking_model().generate_content(prompt)
            code = response.text.strip()
            
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            namespace = {'page': self.page, 'result': None}
            exec(code, namespace)
            
            return {
                "success": True,
                "operation": "ai_web_action",
                "action": action,
                "result": namespace.get('result')
            }
            
        except Exception as e:
            raise Exception(f"AI web action failed: {str(e)}")
    
    def __del__(self):
        """Cleanup browser"""
        if self.browser:
            try:
                # Close asynchronously if open
                try:
                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(self.browser.close())
                    if self._async_pw:
                        self._async_pw.stop()
                except Exception:
                    pass
            except:
                pass
