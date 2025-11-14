#!/usr/bin/env python3
"""
Web Agent - Intelligent web browsing and automation
Uses Puppeteer (Node.js) for reliable web automation
"""

import os
import json
import time
import re
import requests
from urllib.parse import urlparse
from typing import Dict, Any, List, Optional, Tuple
from .agent_core import IntelligentAgent, AgentStatus

class WebAgent(IntelligentAgent):
    """
    Intelligent agent for web operations
    Uses Puppeteer service (Node.js) for web automation
    """
    
    def __init__(self, update_callback=None):
        super().__init__(
            name="WebAgent",
            capabilities=[
                "browse_web",
                "search_google",
                "extract_information",
                "fill_forms",
                "click_buttons",
                "scrape_data",
                "interact_with_pages",
                "take_screenshots"
            ],
            update_callback=update_callback
        )
        self.puppeteer_url = "http://localhost:3001"
        self.browser_active = False
        self._nav_keywords = [
            'visit', 'open', 'go to', 'navigate to', 'load', 'launch', 'access'
        ]
        self._search_keywords = [
            'search', 'find', 'look for', 'look up', 'google'
        ]
        self._extraction_keywords = [
            'extract', 'get', 'scrape', 'read', 'information', 'price',
            'list', 'summarize', 'tell', 'show', 'report', 'starting',
            'details', 'difference', 'compare', 'titles', 'results'
        ]
        self._interaction_keywords = [
            'click', 'type', 'fill', 'enter', 'submit', 'sign in', 'login',
            'log in', 'add to cart', 'select', 'choose', 'filter'
        ]

    def _finalize_result(
        self,
        task: str,
        result: Dict[str, Any],
        *,
        summary: str = None,
        response: str = None,
        formatted_results: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Attach common metadata to agent responses."""

        if not isinstance(result, dict):
            return {
                "success": False,
                "task": task,
                "data": result,
                "response": str(result)
            }

        result.setdefault("task", task)

        if formatted_results is not None:
            existing = result.get("results")
            if isinstance(existing, list) and existing and existing is not formatted_results:
                result["results"] = existing + formatted_results
            else:
                result["results"] = formatted_results

        if summary:
            result["summary"] = summary

        if response:
            result["response"] = response

        # Provide sensible fallbacks so UI always has something to show
        if "summary" not in result and result.get("message"):
            result["summary"] = result["message"]

        if "response" not in result:
            if result.get("summary"):
                result["response"] = result["summary"]
            elif result.get("message"):
                result["response"] = result["message"]

        existing_results = result.get("results")
        if existing_results is None:
            result["results"] = []
        elif not isinstance(existing_results, list):
            result["results"] = [existing_results]

        return result

    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if any keyword is present in the text."""
        if not text:
            return False
        return any(keyword in text for keyword in keywords)

    def _extract_followup_instruction(self, task: str) -> str:
        """Build a follow-up extraction instruction after navigation."""
        if not task:
            return ''

        lowered = task.lower()
        connectors = [' and then ', ' then ', ' & ', ' plus ', ' also ', ' afterwards ', ' followed by ', ' as well as ', ' next, ']

        for connector in connectors:
            index = lowered.find(connector)
            if index != -1:
                first = task[:index]
                second = task[index + len(connector):]
                if self._contains_keywords(first.lower(), self._nav_keywords) and second.strip():
                    return second.strip()

        # Fallback: remove common navigation phrases at the start
        navigation_patterns = [
            r'^\s*visit\s+[^,;]+',
            r'^\s*go to\s+[^,;]+',
            r'^\s*open\s+[^,;]+',
            r'^\s*navigate to\s+[^,;]+'
        ]

        cleaned = task
        for pattern in navigation_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE).strip()

        if cleaned:
            return cleaned

        return task

    def _derive_site_search_query(self, task: str) -> Tuple[bool, Optional[str]]:
        """Determine if the task needs an on-site search and extract the query."""

        task_lower = task.lower() if task else ''
        search_cues = [
            'price', 'cost', 'find', 'search', 'look for',
            'tell me', 'show me', 'get me', 'what is', 'how much'
        ]

        needs_search_on_site = any(keyword in task_lower for keyword in search_cues)
        search_query = None

        if not needs_search_on_site:
            return False, None

        try:
            prompt = f"""Task: "{task}"

This task wants to visit a website and find specific information.
Extract ONLY what needs to be searched/found on that website.

Examples:
- "visit amazon and tell starting price of speakers" → "speakers"
- "go to wikipedia and find info about python" → "python"  
- "open ebay and show laptop prices" → "laptop"

Extract the search query (just the item/topic, 1-3 words):"""

            response = self._get_execution_model().generate_content(prompt)
            search_query = response.text.strip().strip('"').strip("'")

            if search_query:
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"🎯 Detected search query: '{search_query}'"
                )
            else:
                needs_search_on_site = False
        except Exception as e:
            self._send_update(
                AgentStatus.EXECUTING,
                f"⚠️ Could not extract search query: {e}"
            )
            needs_search_on_site = False
            search_query = None

        return needs_search_on_site, search_query

    def _handle_navigation_and_extraction(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a page and immediately extract requested information."""
        
        needs_search_on_site, search_query = self._derive_site_search_query(task)
        
        self._send_update(
            AgentStatus.EXECUTING,
            "🔗 Step 1/2: Navigating to website..."
        )
        
        navigation = self._navigate(task, context)
        if not navigation.get('success'):
            return navigation

        context = dict(context or {})
        context['current_url'] = navigation.get('url')

        if search_query and needs_search_on_site:
            self._send_update(
                AgentStatus.EXECUTING,
                f"🔍 Searching for '{search_query}' directly on homepage..."
            )
            
            try:
                # Interact with the homepage search bar
                context['current_task'] = task
                search_result = self._interact(f"search {search_query}", context)
                
                if search_result.get('success'):
                    self._send_update(
                        AgentStatus.EXECUTING,
                        f"✅ Extracting results for '{search_query}' from homepage..."
                    )
                    extraction_instruction = self._extract_followup_instruction(task)
                    extraction = self._extract_info(extraction_instruction or task, context)

                    if extraction.get('success'):
                        return {
                            "success": True,
                            "operation": "navigate+extract",
                            "navigation": navigation,
                            "extraction": extraction,
                            "summary": extraction.get('summary'),
                            "response": extraction.get('response'),
                            "results": extraction.get('results'),
                            "message": extraction.get('message')
                        }
            except Exception as e:
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"⚠️ Homepage search failed: {e}, extracting from current page..."
                )

        self._send_update(
            AgentStatus.EXECUTING,
            "📄 Extracting requested information from homepage..."
        )
        
        extraction_instruction = self._extract_followup_instruction(task)
        extraction = self._extract_info(extraction_instruction or task, context)

        if not extraction.get('success'):
            error_message = extraction.get('message') or extraction.get('data') or 'Extraction failed after navigation'
            return {
                "success": False,
                "operation": "navigate+extract",
                "navigation": navigation,
                "error": error_message,
                "message": error_message,
                "results": navigation.get('results', [])
            }

        combined_results = list(navigation.get('results', []) or [])
        combined_results.extend(extraction.get('results', []) or [])

        summary = extraction.get('summary') or navigation.get('summary')
        response = extraction.get('response') or summary

        return {
            "success": True,
            "operation": "navigate+extract",
            "navigation": navigation,
            "extraction": extraction,
            "summary": summary,
            "response": response,
            "results": combined_results,
            "message": extraction.get('message') or navigation.get('message')
        }

    def _handle_navigation_search_and_screenshot(
        self,
        task: str,
        context: Dict[str, Any],
        allow_site_search: bool
    ) -> Dict[str, Any]:
        """Navigate to a page, optionally search, then capture a screenshot."""

        needs_search_on_site, search_query = (False, None)
        if allow_site_search:
            needs_search_on_site, search_query = self._derive_site_search_query(task)

        has_search_step = bool(needs_search_on_site and search_query)
        step_total = 3 if has_search_step else 2

        self._send_update(
            AgentStatus.EXECUTING,
            f"🔗 Step 1/{step_total}: Navigating to website..."
        )

        navigation = self._navigate(task, context)
        if not navigation.get('success'):
            return navigation

        working_context = dict(context or {})
        working_context['current_url'] = navigation.get('url')
        working_context['current_task'] = task

        search_result = None
        if has_search_step:
            self._send_update(
                AgentStatus.EXECUTING,
                f"🔍 Step 2/{step_total}: Searching for '{search_query}' on site..."
            )

            try:
                search_result = self._interact(f"search {search_query}", working_context)
                if not search_result.get('success'):
                    error_text = search_result.get('error') or search_result.get('message') or 'search failed'
                    self._send_update(
                        AgentStatus.EXECUTING,
                        f"⚠️ Site search issue: {error_text}. Continuing to screenshot..."
                    )
                    search_result = None
                else:
                    time.sleep(1.0)
            except Exception as e:
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"⚠️ Site search failed ({e}). Continuing to screenshot..."
                )
                search_result = None

        final_step_label = f"📸 Step {step_total}/{step_total}: Capturing screenshot..."
        self._send_update(AgentStatus.EXECUTING, final_step_label)

        try:
            screenshot = self._take_screenshot(task, working_context)
        except Exception as screenshot_error:
            error_message = str(screenshot_error)
            return {
                "success": False,
                "operation": "navigate+search+screenshot",
                "navigation": navigation,
                "error": error_message,
                "message": error_message,
                "results": navigation.get('results', [])
            }

        combined_results: List[Dict[str, Any]] = []
        combined_results.extend(navigation.get('results', []) or [])
        if search_result:
            combined_results.extend(search_result.get('results', []) or [])
        combined_results.extend(screenshot.get('results', []) or [])

        summary = screenshot.get('summary') or screenshot.get('message')
        response = screenshot.get('response') or summary

        return {
            "success": True,
            "operation": "navigate+search+screenshot",
            "navigation": navigation,
            "search": search_result,
            "screenshot": screenshot,
            "summary": summary,
            "response": response,
            "results": combined_results,
            "message": screenshot.get('message') or navigation.get('message')
        }
    
    def _check_puppeteer_service(self) -> bool:
        """Check if Puppeteer service is running"""
        try:
            response = requests.get(f"{self.puppeteer_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def run(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Override base run() method with simpler, direct keyword-based routing
        Avoids complex AI planning for web tasks - most are straightforward
        """
        self._send_update(
            AgentStatus.THINKING,
            f"Processing web task: {task}"
        )
        
        try:
            # Check Puppeteer service
            if not self._check_puppeteer_service():
                return self._finalize_result(task, {
                    "success": False,
                    "data": "⚠️ Puppeteer service not running",
                    "message": "Please run 'bash start.sh' to start all services including Puppeteer web automation."
                })
            
            task_lower = task.lower()
            
            needs_navigation = self._contains_keywords(task_lower, self._nav_keywords)
            needs_search = self._contains_keywords(task_lower, self._search_keywords)
            needs_extraction = self._contains_keywords(task_lower, self._extraction_keywords)
            needs_interaction = self._contains_keywords(task_lower, self._interaction_keywords)
            needs_screenshot = any(word in task_lower for word in ['screenshot', 'capture', 'image', 'picture'])

            if self._should_use_workflow(task_lower):
                self._send_update(AgentStatus.EXECUTING, "⚙️ Planning advanced automation...")
                workflow_result = self._run_workflow(task, context)
                return self._finalize_result(task, workflow_result)
            
            # Direct keyword-based routing - FAST and ACCURATE
            # Screenshot workflows before plain navigation
            if needs_navigation and needs_screenshot:
                self._send_update(AgentStatus.EXECUTING, "📸 Navigating, searching, and capturing screenshot...")
                screenshot_flow = self._handle_navigation_search_and_screenshot(task, context, needs_search)
                return self._finalize_result(task, screenshot_flow)

            # Check for combined navigation + extraction next
            if needs_navigation and needs_extraction and not needs_interaction and not needs_screenshot:
                self._send_update(AgentStatus.EXECUTING, "🔗 Navigating and extracting...")
                combined_result = self._handle_navigation_and_extraction(task, context)
                return self._finalize_result(task, combined_result)

            elif needs_navigation:
                # NAVIGATION ONLY - Extract URL and navigate directly
                self._send_update(AgentStatus.EXECUTING, "🔗 Navigating to website...")
                navigation = self._navigate(task, context)
                return self._finalize_result(task, navigation)
            
            elif needs_search:
                # SEARCH - Extract query and search
                self._send_update(AgentStatus.EXECUTING, "🔍 Searching...")
                search = self._search_google(task, context)
                return self._finalize_result(task, search)
            
            elif needs_extraction:
                # EXTRACTION - Get content from current page
                self._send_update(AgentStatus.EXECUTING, "📄 Extracting content...")
                extracted = self._extract_info(task, context)
                return self._finalize_result(task, extracted)
            
            elif needs_interaction:
                # INTERACTION - Click buttons, type in forms
                self._send_update(AgentStatus.EXECUTING, "👆 Interacting with page...")
                interaction = self._interact(task, context)
                return self._finalize_result(task, interaction)
            
            elif needs_screenshot:
                # SCREENSHOT - Take a screenshot
                self._send_update(AgentStatus.EXECUTING, "📸 Taking screenshot...")
                screenshot = self._take_screenshot(task, context)
                return self._finalize_result(task, screenshot)
            
            else:
                # FALLBACK - Try search as default
                self._send_update(AgentStatus.EXECUTING, "🔍 Searching (default)...")
                fallback_search = self._search_google(task, context)
                return self._finalize_result(task, fallback_search)
        
        except Exception as e:
            self._send_update(AgentStatus.ERROR, f"Task failed: {str(e)}")
            return self._finalize_result(task, {
                "success": False,
                "data": f"Error: {str(e)}",
                "message": f"Error: {str(e)}"
            })

    def _should_use_workflow(self, text: str) -> bool:
        """Detect whether the task needs multi-step automation"""
        if not text:
            return False
        normalized = text.lower()

        multi_step_connectors = [' and then ', ' then ', ' after ', ' afterwards ', 'next,', 'followed by', ' step ', ' as well as ', ' & ']
        if any(connector in normalized for connector in multi_step_connectors):
            return True

        workflow_keywords = [
            'log in', 'login', 'sign in', 'sign-in', 'sign up', 'signup', 'register',
            'fill out', 'fill the form', 'fill form', 'submit the form', 'submit form',
            'complete the form', 'multi-step', 'multi step', 'automation', 'workflow',
            'checkout', 'purchase', 'add to cart', 'book a', 'book the', 'reservation',
            'schedule', 'upload', 'download', 'form submission', 'apply for', 'payment',
            'compare', 'price difference', 'first two', 'first five', 'list the first'
        ]

        for keyword in workflow_keywords:
            if re.search(rf'\b{re.escape(keyword)}\b', normalized):
                return True

        return False

    def _run_workflow(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan and execute a multi-step automation workflow"""
        self._send_update(AgentStatus.THINKING, "🧠 Planning workflow steps")

        workflow_prompt = f"""You are an expert browser automation planner.
Convert the user's request into a STRICT JSON workflow that Puppeteer can execute.

Task: "{task}"

Supported step types:
- navigate: {{"type": "navigate", "url": "https://example.com", "waitUntil": "networkidle2"}}
- waitForSelector: {{"type": "waitForSelector", "selector": "#id", "timeout": 10000}}
- click: {{"type": "click", "selector": "button.submit", "waitForNavigation": true}}
- type: {{"type": "type", "selector": "input[name=email]", "text": "hello", "clear": true}}
- select: {{"type": "select", "selector": "select#role", "value": "admin"}}
- wait: {{"type": "wait", "ms": 1500}}
- hover: {{"type": "hover", "selector": "#menu"}}
- scroll: {{"type": "scroll", "selector": "#footer"}}
- extract: {{"type": "extract", "selector": "div.price"}}
- screenshot: {{"type": "screenshot", "fullPage": true}}
- evaluate: {{"type": "evaluate", "script": "return document.title;"}}

Rules:
1. ALWAYS return valid JSON that can be parsed by json.loads (double quotes only, no trailing commas, no comments).
2. Include specific CSS selectors when interacting with elements.
3. Add waitForSelector steps before click/type when needed.
4. Include wait steps when the UI needs time to update.
5. Final response MUST be JSON only with this exact structure:
{{
    "steps": [ ... ],
    "summary": "short explanation",
    "waitBetweenSteps": optional milliseconds,
    "closeOnFinish": optional boolean,
    "startNew": optional boolean (default true)
}}
"""

        try:
            response = self._get_thinking_model().generate_content(workflow_prompt)
            plan_text = response.text.strip()

            if "```json" in plan_text:
                plan_text = plan_text.split("```json")[1].split("```")[0].strip()
            elif "```" in plan_text:
                plan_text = plan_text.split("```")[1].split("```")[0].strip()

            plan = json.loads(plan_text)
        except Exception as planning_error:
            fix_prompt = f"""The following workflow JSON could not be parsed. Convert it into valid JSON with the same intent.

---
{plan_text}
---

Return ONLY the corrected JSON."""

            try:
                fix_response = self._get_thinking_model().generate_content(fix_prompt)
                fixed_text = fix_response.text.strip()
                if "```json" in fixed_text:
                    fixed_text = fixed_text.split("```json")[1].split("```")[0].strip()
                elif "```" in fixed_text:
                    fixed_text = fixed_text.split("```")[1].split("```")[0].strip()
                plan = json.loads(fixed_text)
            except Exception:
                raise Exception(f"Could not plan workflow: {str(planning_error)}")

        steps = plan.get('steps', [])
        if not steps:
            raise Exception("Workflow planning returned no steps")

        options = {
            "startNew": plan.get('startNew', True),
            "waitBetweenSteps": plan.get('waitBetweenSteps', 0),
            "closeOnFinish": plan.get('closeOnFinish', False),
            "keepOpen": plan.get('keepOpen', True)
        }

        self._send_update(AgentStatus.EXECUTING, f"⚙️ Executing workflow with {len(steps)} steps")

        try:
            response = requests.post(
                f"{self.puppeteer_url}/workflow",
                json={"steps": steps, "options": options},
                timeout=90
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as workflow_error:
            error_message = str(workflow_error)
            if getattr(workflow_error, "response", None) is not None:
                try:
                    error_payload = workflow_error.response.json()
                    error_message = error_payload.get('error', error_message)
                except Exception:
                    body = workflow_error.response.text
                    error_message = f"{error_message} - {body[:200]}"
            raise Exception(f"Workflow execution failed: {error_message}")

        try:
            result = response.json()
        except ValueError as json_error:
            raise Exception(f"Invalid workflow response: {str(json_error)}")

        if not result.get('success'):
            error_message = result.get('error', 'Unknown workflow error')
            raise Exception(error_message)

        steps_result = result.get('steps', [])
        formatted_results = []
        extracted_payloads = []

        for idx, step_info in enumerate(steps_result, start=1):
            label = step_info.get('label') or step_info.get('type') or f"Step {idx}"
            status = 'Success' if step_info.get('success') else 'Failed'
            pieces = [f"{idx}. {label}: {status}"]

            if step_info.get('error'):
                pieces.append(f"Reason: {step_info['error']}")

            result_payload = step_info.get('result') or {}
            selector = result_payload.get('selector') or step_info.get('selector')
            if selector:
                pieces.append(f"Selector: {selector}")

            formatted_results.append({
                "output": " — ".join(pieces)
            })

            if step_info.get('success') and isinstance(result_payload, dict):
                if result_payload.get('type') == 'extract':
                    if result_payload.get('values'):
                        extracted_payloads.append("\n".join(result_payload['values']))
                    elif result_payload.get('text'):
                        extracted_payloads.append(result_payload['text'])

        for idx, step_info in enumerate(steps_result, start=1):
            status_icon = '✅' if step_info.get('success') else '⚠️'
            step_label = step_info.get('label') or step_info.get('type') or f'step {idx}'
            self._send_update(
                AgentStatus.EXECUTING,
                f"{status_icon} Step {idx}: {step_label}"
            )

        final_state = result.get('final', {})
        summary = plan.get('summary') or plan.get('notes') or ''

        if final_state.get('url') or final_state.get('title'):
            final_label = final_state.get('title') or final_state.get('url')
            formatted_results.append({
                "output": f"Final page: {final_label}"
            })

        response_text = summary.strip()

        if extracted_payloads:
            extraction_preview = "\n\n".join(extracted_payloads)[:3000]
            summary_prompt = f"""You executed this browser workflow for the task: "{task}".

Data captured:
{extraction_preview}

Provide a concise summary of the key findings or data points. Keep it under 8 sentences."""

            try:
                summary_response = self._get_thinking_model().generate_content(summary_prompt)
                ai_summary = summary_response.text.strip()
                if ai_summary:
                    response_text = ai_summary
            except Exception:
                # Fall back gracefully if model summarization fails
                if not response_text:
                    response_text = "Workflow completed. Review extracted data in the details."

        if not response_text:
            response_text = 'Workflow completed'

        if not summary:
            summary = response_text

        self._send_update(AgentStatus.SUCCESS, summary)

        return {
            "success": True,
            "operation": "workflow",
            "summary": summary,
            "steps": steps_result,
            "final": final_state,
            "response": response_text,
            "results": formatted_results,
            "extracted_data": extracted_payloads
        }
    
    def execute_step(self, step: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a web operation step"""
        
        # Check if Puppeteer service is running
        if not self._check_puppeteer_service():
            raise Exception(
                "Puppeteer service not running. Start it with: node puppeteer_service/puppeteer_server.js"
            )
        
        tool = step.get('tool', 'auto')
        action = step.get('action', '')

        self._send_update(AgentStatus.EXECUTING, f"Web action: {action}")

        if tool == 'auto':
            tool = self._decide_web_action(action, context)

        if tool == 'search' or 'search' in action.lower():
            return self._search_google(action, context)
        elif tool == 'navigate':
            return self._navigate(action, context)
        elif tool == 'extract':
            return self._extract_info(action, context)
        elif tool == 'interact':
            return self._interact(action, context)
        elif tool == 'screenshot':
            return self._take_screenshot(action, context)
        else:
            return self._ai_web_action(action, context)
    
    def _decide_web_action(self, action: str, context: Dict[str, Any]) -> str:
        """Use AI to decide web action type"""
        
        # Simple keyword detection for common actions
        action_lower = action.lower()
        
        if any(word in action_lower for word in ['search', 'google', 'find', 'look up']):
            return 'search'
        elif any(word in action_lower for word in ['go to', 'open', 'visit', 'navigate']):
            return 'navigate'
        elif any(word in action_lower for word in ['get', 'extract', 'scrape', 'read']):
            return 'extract'
        elif any(word in action_lower for word in ['click', 'type', 'fill', 'enter']):
            return 'interact'
        elif any(word in action_lower for word in ['screenshot', 'capture', 'image']):
            return 'screenshot'
        
        # Use AI for complex cases
        prompt = f"""Web task: "{action}"

Choose action type:
- search: Search on Google
- navigate: Go to a URL
- extract: Get information from page
- interact: Click, type, fill forms
- screenshot: Take a screenshot

Respond with just the action type."""

        try:
            response = self._get_execution_model().generate_content(prompt)
            return response.text.strip().lower()
        except:
            return 'search'
    
    def _search_google(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search on Google using Puppeteer"""
        
        # Extract search query by removing common search keywords
        query = action.lower()
        
        # Remove common search prefixes
        search_keywords = ['search', 'find', 'google', 'look for', 'search for', 'look up', 'find me', 'get me']
        for keyword in search_keywords:
            if query.startswith(keyword):
                query = query[len(keyword):].strip()
                break
        
        # Clean up
        query = ' '.join(query.split()).strip('"').strip("'").strip()
        
        # If query is very short or same as original, use AI fallback
        if not query or len(query) < 2:
            prompt = f"""Extract the search query from: "{action}"
Return just the search query, nothing else."""
            try:
                response = self._get_execution_model().generate_content(prompt)
                query = response.text.strip().strip('"').strip("'")
            except:
                query = action
        
        self._send_update(
            AgentStatus.EXECUTING,
            f"🔍 Searching for: {query}"
        )
        
        # Call Puppeteer service
        try:
            response = requests.post(
                f"{self.puppeteer_url}/search",
                json={"query": query},
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            if result.get('success'):
                count = result.get('count', 0)
                search_results = result.get('results', []) or []

                formatted_results = []
                summary_lines = []

                for idx, item in enumerate(search_results[:5], start=1):
                    title = item.get('title') or item.get('link') or f"Result {idx}"
                    snippet = (item.get('snippet') or '').strip()
                    line = f"{idx}. {title}"
                    if snippet:
                        line = f"{line} — {snippet}"

                    summary_lines.append(line)
                    formatted_result = {
                        "output": line
                    }
                    if item.get('link'):
                        formatted_result['link'] = item['link']
                    formatted_results.append(formatted_result)

                message = result.get('message') or f"Found {count} results for '{query}'"
                summary_text = message
                if summary_lines:
                    summary_text = "Top results:\n" + "\n".join(summary_lines)
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Found {count} results"
                )
                
                return {
                    "success": True,
                    "operation": "search",
                    "query": query,
                    "search_results": search_results,
                    "results": formatted_results,
                    "count": count,
                    "message": message,
                    "summary": summary_text,
                    "response": summary_text
                }
            else:
                raise Exception(result.get('error', 'Search failed'))
            
        except Exception as e:
            raise Exception(f"Google search failed: {str(e)}")
    
    def _navigate(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL"""
        
    # First try to extract URL using regex
        # Look for URLs in format: domain.com, www.domain.com, https://domain.com
        url_patterns = [
            r'https?://[^\s]+',  # Full URL with protocol
            r'www\.[a-z0-9]+\.[a-z.]+',  # www.domain.com
            r'[a-z0-9]+\.[a-z]{2,}'  # domain.com
        ]
        
        url = None
        for pattern in url_patterns:
            matches = re.findall(pattern, action.lower())
            if matches:
                url = matches[0]
                break
        
        # If no URL found via regex, use AI
        if not url:
            prompt = f"""Extract the website/URL from: "{action}"
Return just the domain or URL, nothing else.
Examples: reddit.com, github.com, google.com"""

            try:
                response = self._get_execution_model().generate_content(prompt)
                url = response.text.strip()
            except:
                url = action.split()[-1]  # Fallback to last word
        
        # Clean up and ensure URL has protocol
        url = url.strip().strip('.')
        if not url.startswith('http'):
            url = 'https://' + url
        
        self._send_update(
            AgentStatus.EXECUTING,
            f"🔗 Opening: {url}"
        )
        
        # Call Puppeteer service
        try:
            result = requests.post(
                f"{self.puppeteer_url}/navigate",
                json={"url": url},
                timeout=30
            ).json()
            
            if result.get('success'):
                final_url = result.get('url') or url
                title = result.get('title')
                message = result.get('message') or f"Successfully navigated to {final_url}"
                summary = title or message
                formatted_results = [{
                    "output": message,
                    "url": final_url,
                    "title": title
                }]
                return {
                    "success": True,
                    "operation": "navigate",
                    "url": final_url,
                    "title": title,
                    "message": message,
                    "summary": summary,
                    "response": message,
                    "results": formatted_results
                }
            else:
                raise Exception(result.get('error', 'Navigation failed'))
            
        except Exception as e:
            error_text = str(e)
            normalized_error = error_text.upper()
            network_hints = [
                'ERR_CERT',
                'SSL',
                'CERTIFICATE',
                'ERR_NAME_NOT_RESOLVED',
                'ERR_CONNECTION',
                'ERR_FAILED'
            ]

            if any(hint in normalized_error for hint in network_hints):
                parsed = urlparse(url)
                host = parsed.netloc or parsed.path.split('/')[0]
                host = host or url
                host = host.replace('https://', '').replace('http://', '')
                host = host.strip('/')

                self._send_update(
                    AgentStatus.EXECUTING,
                    f"⚠️ Navigation issue detected ({error_text}). Searching for the correct site instead..."
                )

                try:
                    fallback_query = host.replace('www.', '') if host else url
                    search_task = f"search {fallback_query} official site"
                    search_result = self._search_google(search_task, context)
                    info_message = (
                        f"Navigation issue detected ({error_text}). "
                        "Provided search results so you can choose the correct link."
                    )
                    search_result["message"] = info_message
                    combined_summary = info_message
                    if search_result.get("summary"):
                        combined_summary = info_message + "\n\n" + search_result["summary"]
                    search_result["summary"] = combined_summary
                    search_result["response"] = combined_summary
                    return search_result
                except Exception as fallback_error:
                    raise Exception(
                        f"Navigation failed due to certificate/domain issue and fallback search also failed: {fallback_error}"
                    ) from fallback_error

            raise Exception(f"Navigation failed: {error_text}")
    
    def _extract_info(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract information from webpage"""
        
        try:
            self._send_update(
                AgentStatus.EXECUTING,
                "Extracting page content..."
            )
            
            # Get page content using Puppeteer with retries to handle navigation churn
            extract_errors = (
                'execution context was destroyed',
                'cannot read properties of null',
                'execution context destroyed'
            )

            max_attempts = 3
            last_error = ''
            result = {}

            for attempt in range(max_attempts):
                response = requests.post(
                    f"{self.puppeteer_url}/extract",
                    json={},
                    timeout=15
                )

                try:
                    result = response.json()
                except ValueError:
                    last_error = 'Invalid JSON response from extract endpoint'
                    result = {}

                if result.get('success'):
                    break

                last_error = result.get('error', 'Extraction failed')

                if attempt < max_attempts - 1 and any(err in last_error.lower() for err in extract_errors):
                    time.sleep(1.5)
                    continue

                raise Exception(last_error)
            
            if not result.get('success'):
                raise Exception(last_error or 'Extraction failed')
            
            page_text = result.get('data', '')
            page_url = result.get('url', '')
            page_title = result.get('title', '')
            
            # Use AI to extract relevant information with enhanced context
            prompt = f"""You are analyzing a webpage to extract specific information.

**User Request:** "{action}"

**Current Page:**
- URL: {page_url}
- Title: {page_title}

**Page Content (first 3000 characters):**
{page_text[:3000]}

**Instructions:**
1. Read the user's request carefully to understand what specific information they want.
2. Analyze the page content to find the relevant data.
3. Extract ONLY the information requested - be specific and concise.
4. If the information is not found, say "Could not find [requested info] on this page."
5. For prices/numbers: include the exact values with currency/units.
6. For lists: provide the actual items/titles requested.
7. Format your response clearly and directly answer what was asked.

Provide your answer now:"""

            response = self._get_thinking_model().generate_content(prompt)
            extracted_info = response.text.strip()

            summary_text = self._summarize_extracted_data(
                action,
                extracted_info,
                page_title,
                page_url,
                page_text
            )

            # If extraction seems generic or unhelpful, note it
            if len(extracted_info) < 50 or 'could not find' in extracted_info.lower():
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"⚠️ Limited info extracted: {extracted_info[:100]}"
                )
            else:
                self._send_update(
                    AgentStatus.EXECUTING,
                    f"✅ Extracted {len(extracted_info)} characters of data"
                )

            detail_preview = extracted_info.strip()
            if len(detail_preview) > 500:
                detail_preview = detail_preview[:497] + "..."

            message = f"Extracted information from {page_title or page_url}"

            return {
                "success": True,
                "operation": "extract",
                "url": page_url,
                "title": page_title,
                "data": extracted_info,
                "summary": summary_text or detail_preview,
                "response": summary_text or extracted_info,
                "results": [{"output": extracted_info}],
                "message": message
            }
            
        except Exception as e:
            raise Exception(f"Extraction failed: {str(e)}")

    def _summarize_extracted_data(
        self,
        task: str,
        extracted_text: str,
        page_title: str = '',
        page_url: str = '',
        raw_page_text: str = ''
    ) -> str:
        """Condense extracted page data into a succinct answer."""

        if not extracted_text:
            return ''

        normalized = extracted_text.strip()
        if not normalized:
            return ''

        lowered = normalized.lower()
        if 'could not find' in lowered and 'on this page' in lowered:
            return normalized

        if len(normalized) <= 180 and 'could not find' not in lowered:
            return normalized

        prompt = f"""You extracted content for the task: "{task}".
Page title: {page_title}
URL: {page_url}

Extracted content:
---
{normalized[:2000]}
---

Provide a concise answer (maximum 3 sentences) that directly satisfies the task.
Include key values such as prices or counts when present.
If the requested information is missing, respond with "Could not find [requested info] on this page.".

Answer:"""

        summary = ''

        try:
            response = self._get_thinking_model().generate_content(prompt)
            summary = response.text.strip()
        except Exception:
            summary = ''

        if summary:
            lowered_summary = summary.lower()
            if 'could not find' not in lowered_summary and len(summary) <= 220:
                return summary

        price_hint = self._find_starting_price(raw_page_text or extracted_text)
        if price_hint:
            snippet = price_hint.get('snippet')
            snippet_text = f" (context: {snippet})" if snippet else ''
            return f"Starting price appears to be {price_hint['display']}.{snippet_text}".strip()

        fallback = summary or normalized[:300]
        return fallback

    def _find_starting_price(self, text: str) -> Dict[str, Any]:
        """Locate a plausible starting price within page text."""

        if not text:
            return {}

        currency_alias = {
            'usd': '$',
            'dollars': '$',
            'eur': '€',
            'euros': '€',
            'gbp': '£',
            'pounds': '£',
            'inr': '₹',
            'rupees': '₹',
            'rs': '₹',
            'rs.': '₹'
        }

        patterns = [
            re.compile(r'(₹|rs\.?|inr|\$|usd|€|eur|£|gbp)\s?(\d[\d,]*)(\.\d+)?', re.IGNORECASE),
            re.compile(r'(\d[\d,]*)(\.\d+)?\s?(usd|dollars|eur|euros|gbp|pounds|inr|rupees|rs\.?)', re.IGNORECASE)
        ]

        candidates: List[Dict[str, Any]] = []

        def _extract_candidate(match, symbol, amount, decimals):
            cleaned_amount = amount.replace(',', '')
            decimal_part = decimals or ''
            try:
                numeric_value = float(f"{cleaned_amount}{decimal_part}")
            except ValueError:
                return

            display_symbol = symbol
            if symbol.lower() in currency_alias:
                display_symbol = currency_alias[symbol.lower()]

            display = f"{display_symbol}{amount}{decimal_part}".replace('$$', '$')

            start = max(match.start() - 80, 0)
            end = min(match.end() + 80, len(text))
            snippet = re.sub(r'\s+', ' ', text[start:end]).strip()

            candidates.append({
                'value': numeric_value,
                'display': display,
                'snippet': snippet
            })

        # Pattern: currency symbol before amount
        for match in patterns[0].finditer(text):
            symbol = match.group(1)
            amount = match.group(2)
            decimals = match.group(3)
            _extract_candidate(match, symbol, amount, decimals)

        # Pattern: amount before currency word
        for match in patterns[1].finditer(text):
            amount = match.group(1)
            decimals = match.group(2)
            symbol_word = match.group(3)
            symbol = currency_alias.get(symbol_word.lower(), symbol_word)
            _extract_candidate(match, symbol, amount, decimals)

        if not candidates:
            return {}

        candidates.sort(key=lambda item: item['value'])
        return candidates[0]
    
    def _interact(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Interact with webpage elements"""
        
        # Predefined logic for homepage search
        if 'search' in action.lower():
            try:
                self._send_update(
                    AgentStatus.EXECUTING,
                    "Typing search query into homepage search bar..."
                )
                
                # Use Puppeteer to type and submit search query
                search_query = action.split('search', 1)[1].strip()

                current_url = (context or {}).get('current_url', '')
                current_task = (context or {}).get('current_task', action.lower())
                domain = ''
                if '//' in current_url:
                    domain = current_url.split('//')[1].split('/')[0]
                
                selectors_by_domain = {
                    'amazon': {
                        'input': [
                            "input[id='twotabsearchtextbox']",
                            "input[name='field-keywords']",
                            "input[type='search']"
                        ],
                        'submit': [
                            "input[id='nav-search-submit-button']",
                            "input[type='submit']"
                        ]
                    },
                    'wikipedia': {
                        'input': [
                            "input[name='search']",
                            "input[id='searchInput']",
                            "input[placeholder*='Search']"
                        ],
                        'submit': [
                            "button[type='submit']",
                            "input[type='submit']",
                            "form#searchform button"
                        ]
                    }
                }

                site_key = ''
                domain_lower = domain.lower()
                for key in selectors_by_domain.keys():
                    if key and key in domain_lower:
                        site_key = key
                        break

                if not site_key:
                    task_lower = current_task.lower()
                    for key in selectors_by_domain.keys():
                        if key and key in task_lower:
                            site_key = key
                            break

                search_selectors = selectors_by_domain.get(site_key, {}).get('input', [
                    "input[type='search']",
                    "input[name='q']"
                ])

                self._send_update(
                    AgentStatus.EXECUTING,
                    f"🌐 Using selector profile '{site_key or 'default'}' for search"
                )

                typed = False
                last_type_error = ''

                for selector in search_selectors:
                    type_result = requests.post(
                        f"{self.puppeteer_url}/type",
                        json={
                            "selector": selector,
                            "text": search_query
                        },
                        timeout=15
                    ).json()

                    if type_result.get('success'):
                        typed = True
                        break

                    last_type_error = type_result.get('error', '')

                if not typed:
                    raise Exception(last_type_error or 'Unable to type into site search box')

                submit_selectors = selectors_by_domain.get(site_key, {}).get('submit', [
                    "input[type='submit']",
                    "button[type='submit']",
                    "button[aria-label*='search']",
                    "button[title*='search']"
                ])

                clicked = False
                last_click_error = ''

                for selector in submit_selectors:
                    submit_payload = {
                        "selector": selector,
                        "waitForNavigation": True
                    }

                    submit_result = requests.post(
                        f"{self.puppeteer_url}/click",
                        json=submit_payload,
                        timeout=25
                    ).json()

                    if submit_result.get('success'):
                        clicked = True
                        break

                    last_click_error = submit_result.get('error', '')

                if not clicked:
                    self._send_update(
                        AgentStatus.EXECUTING,
                        "⌨️ Submitting search by pressing Enter..."
                    )
                    execute_result = requests.post(
                        f"{self.puppeteer_url}/execute",
                        json={
                            "script": "(() => {\n  const active = document.activeElement;\n  if (active && active.dispatchEvent) {\n    const evt = new KeyboardEvent('keydown', {key: 'Enter', keyCode: 13, which: 13, bubbles: true});\n    active.dispatchEvent(evt);\n    const evtUp = new KeyboardEvent('keyup', {key: 'Enter', keyCode: 13, which: 13, bubbles: true});\n    active.dispatchEvent(evtUp);\n  }\n  if (active && active.form) {\n    active.form.submit?.();\n  }\n  return document.activeElement ? 'enter-sent' : 'no-active';\n})()"
                        },
                        timeout=15
                    ).json()

                    if not execute_result.get('success'):
                        raise Exception(last_click_error or execute_result.get('error', 'Unable to submit search form'))
                
                # Wait briefly for dynamic content to populate after navigation
                time.sleep(2.5)
                
                self._send_update(
                    AgentStatus.EXECUTING,
                    "✅ Search query submitted successfully"
                )
                
                return {
                    "success": True,
                    "operation": "interact",
                    "message": "Search query submitted successfully"
                }
            except Exception as e:
                return {
                    "success": False,
                    "operation": "interact",
                    "error": str(e),
                    "message": f"Interaction failed: {str(e)}"
                }
        
        # Default AI-based interaction logic
        prompt = f"""Task: {action}

Determine the interaction needed:
1. If clicking: provide CSS selector to click
2. If typing: provide selector and text to type

Respond in JSON format:
{{
    "type": "click" or "type",
    "selector": "CSS selector",
    "text": "text to type (if type action)"
}}"""

        try:
            response = self._get_execution_model().generate_content(prompt)
            interaction_text = response.text.strip()
            
            if "```json" in interaction_text:
                interaction_text = interaction_text.split("```json")[1].split("```")[0].strip()
            elif "```" in interaction_text:
                interaction_text = interaction_text.split("```")[1].split("```")[0].strip()
            
            interaction = json.loads(interaction_text)
            
            self._send_update(
                AgentStatus.EXECUTING,
                f"Performing {interaction['type']} action..."
            )
            
            # Execute interaction via Puppeteer
            if interaction['type'] == 'click':
                result = requests.post(
                    f"{self.puppeteer_url}/click",
                    json={"selector": interaction['selector']},
                    timeout=15
                ).json()
            elif interaction['type'] == 'type':
                result = requests.post(
                    f"{self.puppeteer_url}/type",
                    json={
                        "selector": interaction['selector'],
                        "text": interaction['text']
                    },
                    timeout=15
                ).json()
            
            if not result.get('success'):
                raise Exception(result.get('error', 'Interaction failed'))
            
            return {
                "success": True,
                "operation": "interact",
                "message": "Interaction completed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "operation": "interact",
                "error": str(e),
                "message": f"Interaction failed: {str(e)}"
            }
    
    def _take_screenshot(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot of the current page"""
        
        try:
            self._send_update(
                AgentStatus.EXECUTING,
                "Taking screenshot..."
            )
            
            result = requests.post(
                f"{self.puppeteer_url}/screenshot",
                json={"fullPage": True},
                timeout=15
            ).json()
            
            if result.get('success'):
                message = "Screenshot captured successfully"
                return {
                    "success": True,
                    "operation": "screenshot",
                    "image": result.get('image'),
                    "format": "base64",
                    "message": message,
                    "summary": message,
                    "response": message,
                    "results": [{
                        "output": message,
                        "image": result.get('image'),
                        "format": "base64"
                    }]
                }
            else:
                raise Exception(result.get('error', 'Screenshot failed'))
            
        except Exception as e:
            raise Exception(f"Screenshot failed: {str(e)}")
    
    def _ai_web_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Let AI figure out how to do the web action"""
        
        # For now, default to search if unclear
        return self._search_google(action, context)
