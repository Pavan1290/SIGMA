#!/usr/bin/env python3
"""
Web Agent - Intelligent web browsing and automation
Uses Playwright for reliable web automation (better than Selenium)
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from .agent_core import IntelligentAgent, AgentStatus
import asyncio
import threading

# Setup logging
logger = logging.getLogger(__name__)

class WebAgent(IntelligentAgent):
    """
    Intelligent agent for web operations
    Uses Playwright instead of Selenium (more reliable)
    Enhanced with better error handling and robustness
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
                "interact_with_pages",
                "take_screenshot",
                "scroll_page",
                "wait_for_element"
            ],
            update_callback=update_callback
        )
        self.browser = None
        self.page = None
        self._async_pw = None
        self._browser_lock = threading.Lock()
        self.max_retries = 3
        self.timeout = 30000  # 30 seconds in milliseconds
    
    async def _init_browser(self):
        """Initialize Playwright browser with enhanced error handling."""
        try:
            from playwright.async_api import async_playwright
            
            self._send_update(AgentStatus.EXECUTING, "Initializing Playwright browser...")
            self._async_pw = await async_playwright().start()
            
            # Launch browser with headless mode for robustness
            self.browser = await self._async_pw.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # Create a new page with timeout
            self.page = await self.browser.new_page()
            self.page.set_default_timeout(self.timeout)
            
            self._send_update(AgentStatus.EXECUTING, "Browser initialized successfully")
            logger.info("✅ Playwright browser initialized")
            return True
            
        except ImportError:
            error_msg = "Playwright not installed. Run: pip install playwright && playwright install"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Browser init failed: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a web operation step safely
        Wraps async calls for compatibility with sync agent loop
        """
        async def runner():
            return await self._execute_step_async(step, context)

        try:
            # Try to get running loop
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    # We're already in an async context, use thread to avoid blocking
                    result_holder = {}
                    
                    def _thread_run():
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        try:
                            result_holder['value'] = new_loop.run_until_complete(runner())
                        except Exception as e:
                            result_holder['error'] = e
                        finally:
                            new_loop.close()
                    
                    t = threading.Thread(target=_thread_run, daemon=True)
                    t.start()
                    t.join(timeout=300)  # 5 minute timeout
                    
                    if 'error' in result_holder:
                        raise result_holder['error']
                    return result_holder.get('value', {'success': False, 'error': 'Thread timeout'})
                else:
                    return loop.run_until_complete(runner())
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(runner())
                
        except Exception as e:
            logger.error(f"Step execution error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'operation': step.get('action', 'unknown')
            }

    async def _execute_step_async(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute async web operation with retry logic"""
        try:
            # Initialize browser if needed
            if not self.browser:
                self._send_update(AgentStatus.EXECUTING, "Starting browser...")
                await self._init_browser()

            tool = step.get('tool', 'auto')
            action = step.get('action', '')

            if not action:
                return {'success': False, 'error': 'No action specified'}

            self._send_update(AgentStatus.EXECUTING, f"Web action: {action}")

            # Decide tool if auto
            if tool == 'auto':
                tool = self._decide_web_action(action, context)

            logger.info(f"Executing web tool: {tool}")

            # Execute with retry logic
            for attempt in range(self.max_retries):
                try:
                    if tool == 'navigate':
                        return await self._navigate(action, context)
                    elif tool == 'extract':
                        return await self._extract_info(action, context)
                    elif tool == 'interact':
                        return await self._interact(action, context)
                    else:
                        return await self._ai_web_action(action, context)
                        
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed, retrying... ({str(e)})")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise

        except Exception as e:
            logger.error(f"Web step execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'operation': step.get('action', 'unknown')
            }
    
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
        """Navigate to URL with enhanced error handling"""
        try:
            # Use AI to extract URL from action
            prompt = f"""Extract the URL from: "{action}"
If no URL, provide a reasonable default based on the task.
Respond with just the URL, nothing else."""

            try:
                response = self._get_execution_model().generate_content(prompt)
                url = response.text.strip()
            except Exception as e:
                logger.warning(f"AI URL extraction failed: {str(e)}")
                url = action if action.startswith('http') else f"https://{action}"
            
            # Ensure URL has protocol
            if not url.startswith('http'):
                url = 'https://' + url
            
            self._send_update(AgentStatus.EXECUTING, f"Navigating to: {url}")
            logger.info(f"Navigating to: {url}")
            
            # Navigate with timeout
            try:
                response = await self.page.goto(url, wait_until='networkidle', timeout=self.timeout)
                
                title = await self.page.title()
                logger.info(f"✅ Navigated successfully. Title: {title}")
                
                return {
                    "success": True,
                    "operation": "navigate",
                    "url": url,
                    "title": title,
                    "status": response.status if response else "unknown"
                }
                
            except asyncio.TimeoutError:
                logger.warning(f"Navigation timeout for {url}, but page may have loaded partially")
                title = await self.page.title()
                return {
                    "success": True,
                    "operation": "navigate",
                    "url": url,
                    "title": title,
                    "note": "Navigation timeout but page loaded"
                }
            
        except Exception as e:
            error_msg = f"Navigation failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'operation': 'navigate'
            }
    
    async def _extract_info(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from webpage with robust error handling"""
        try:
            self._send_update(AgentStatus.THINKING, "Analyzing page content...")
            
            # Get page content with timeout
            try:
                content = await asyncio.wait_for(self.page.content(), timeout=10)
                visible_text = await asyncio.wait_for(self.page.inner_text('body'), timeout=10)
            except asyncio.TimeoutError:
                logger.warning("Page content extraction timeout")
                content = ""
                visible_text = "Could not extract page content"
            
            # Limit content size for AI processing
            text_preview = visible_text[:5000] if visible_text else ""
            
            # Use AI to extract relevant information
            prompt = f"""From this webpage, extract: "{action}"

Page content (truncated):
{text_preview}

Provide the extracted information in JSON format."""

            try:
                response = self._get_thinking_model().generate_content(prompt)
                info_text = response.text.strip()
                
                # Parse JSON from response
                if "```json" in info_text:
                    info_text = info_text.split("```json")[1].split("```")[0].strip()
                elif "```" in info_text:
                    info_text = info_text.split("```")[1].split("```")[0].strip()
                
                extracted = json.loads(info_text)
                logger.info(f"✅ Extraction successful")
                
                return {
                    "success": True,
                    "operation": "extract",
                    "data": extracted,
                    "url": self.page.url
                }
                
            except json.JSONDecodeError:
                logger.warning("Could not parse AI response as JSON")
                return {
                    "success": True,
                    "operation": "extract",
                    "data": {"raw_response": info_text},
                    "note": "AI response was not valid JSON"
                }
            
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'operation': 'extract'
            }
    
    async def _interact(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Interact with webpage elements with safe code execution"""
        try:
            # Use AI to generate interaction steps
            prompt = f"""Task: {action}
Current page: {self.page.url}

Generate Playwright code to accomplish this. Use:
- page.click('selector')
- page.fill('selector', 'text')
- page.press('selector', 'Enter')
- page.wait_for_selector('selector')
- page.screenshot(path='screenshot.png')

Respond with ONLY Python code using 'page' variable."""

            response = self._get_execution_model().generate_content(prompt)
            code = response.text.strip()
            
            # Extract code block
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            self._send_update(AgentStatus.EXECUTING, f"Executing web interaction...")
            logger.info(f"Executing interaction code:\n{code}")
            
            # Execute the interaction code safely
            namespace = {
                'page': self.page,
                'result': None,
                'asyncio': asyncio,
            }
            
            # Execute with timeout
            try:
                exec(code, namespace)
                result = namespace.get('result')
                logger.info("✅ Interaction completed successfully")
                
                return {
                    "success": True,
                    "operation": "interact",
                    "action": action,
                    "result": result
                }
            except Exception as e:
                logger.error(f"Code execution error: {str(e)}")
                return {
                    'success': False,
                    'error': f"Code execution failed: {str(e)}",
                    'operation': 'interact'
                }
            
        except Exception as e:
            error_msg = f"Interaction failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'operation': 'interact'
            }
    
    async def _ai_web_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Let AI figure out how to do the web action"""
        try:
            prompt = f"""Accomplish this web task: "{action}"
Current URL: {self.page.url if self.page else 'No page loaded'}
Context: {json.dumps(context, indent=2) if context else '{}'}

Provide Playwright code to do this. Use the 'page' object.
Respond with ONLY Python code."""

            response = self._get_thinking_model().generate_content(prompt)
            code = response.text.strip()
            
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            namespace = {'page': self.page, 'result': None, 'asyncio': asyncio}
            exec(code, namespace)
            
            logger.info("✅ AI web action completed successfully")
            
            return {
                "success": True,
                "operation": "ai_web_action",
                "action": action,
                "result": namespace.get('result')
            }
            
        except Exception as e:
            error_msg = f"AI web action failed: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'operation': 'ai_web_action'
            }
    
    def __del__(self):
        """Cleanup browser resources"""
        if self.browser:
            try:
                # Schedule cleanup in event loop
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Can't await in __del__, just log warning
                        logger.warning("Browser cleanup deferred (event loop still running)")
                    else:
                        loop.run_until_complete(self._cleanup())
                except Exception as e:
                    logger.warning(f"Could not cleanup browser in event loop: {e}")
                    
                # Try synchronous cleanup
                self._cleanup_sync()
            except Exception as e:
                logger.error(f"Error during browser cleanup: {e}")
    
    async def _cleanup(self):
        """Async browser cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self._async_pw:
                await self._async_pw.stop()
            logger.info("✅ Browser cleaned up")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def _cleanup_sync(self):
        """Synchronous browser cleanup attempt"""
        try:
            self.browser = None
            self.page = None
            self._async_pw = None
        except Exception:
            pass
