# 🚀 Atlas-Style Workflow Engine for SIGMA-OS

## Overview

SIGMA-OS now includes an **Atlas-style workflow engine** that breaks down complex tasks into automated multi-step workflows!

## 🎯 What is it?

Just like **Atlas.so**, our workflow engine:
- ✅ Breaks down complex tasks into steps using AI
- ✅ Executes steps in order automatically
- ✅ Passes output from one step to the next
- ✅ Handles retries and error recovery
- ✅ Supports conditional branching
- ✅ Integrates all your agents (Web, Email, System)

## 📋 Example Workflows

### 1. **Research & Email Report**
**Task:** "Research latest AI news and email summary to me"

**What happens:**
1. Search Google for "latest AI news"
2. Extract top 5 headlines
3. Analyze with AI to create summary
4. Send email with findings

### 2. **Web Scraping Pipeline**
**Task:** "Go to Amazon, find best laptops, extract prices, save to file"

**What happens:**
1. Navigate to amazon.com
2. Search for "best laptops"
3. Extract product names and prices
4. Transform data to JSON
5. Save to `laptops.json`

### 3. **Automated Testing**
**Task:** "Test login flow on example.com and take screenshots"

**What happens:**
1. Navigate to example.com/login
2. Type username
3. Type password
4. Click login button
5. Wait for dashboard
6. Take screenshot
7. Verify success

## 🔧 How to Use

### Method 1: Through the UI

Just type complex tasks naturally:

```
"go to github.com, search for python projects, extract top 3, and save to file"
```

The engine automatically detects complex tasks and creates workflows!

### Method 2: Programmatic API

```python
from intelligent_agents.workflow_engine import AtlasWorkflowEngine, Workflow, WorkflowStep

# Initialize engine
engine = AtlasWorkflowEngine(agents=agents)

# Create workflow from natural language
workflow = engine.create_workflow_from_task(
    task="Research Python tutorials and email me summary",
    context={"email": "user@example.com"}
)

# Execute workflow
result = engine.execute_workflow(workflow)

print(f"Workflow completed: {result['success']}")
print(f"Final result: {result['final_result']}")
```

### Method 3: Define Custom Workflows

```python
from intelligent_agents.workflow_engine import Workflow, WorkflowStep

# Create custom workflow
workflow = Workflow(
    workflow_id="research_pipeline",
    name="Research Pipeline",
    description="Automated research and reporting"
)

# Add steps
workflow.add_step(WorkflowStep(
    step_id="step_1",
    action="Search for AI news",
    tool="web_search",
    params={"query": "latest AI developments 2025"}
))

workflow.add_step(WorkflowStep(
    step_id="step_2",
    action="Analyze results",
    tool="llm_analyze",
    params={
        "data": "{{prev_result.data}}",
        "question": "Summarize top 3 developments"
    }
))

workflow.add_step(WorkflowStep(
    step_id="step_3",
    action="Send email report",
    tool="email_send",
    params={
        "to": "me@example.com",
        "subject": "AI News Summary",
        "body": "{{prev_result.analysis}}"
    }
))

# Execute
result = engine.execute_workflow(workflow)
```

## 🛠️ Available Tools

### Web Tools
- `web_navigate` - Navigate to URL
- `web_search` - Search on Google  
- `web_extract` - Extract data from page
- `web_click` - Click element
- `web_type` - Type text
- `web_screenshot` - Take screenshot

### Email Tools
- `email_send` - Send email
- `email_read` - Read emails

### System Tools
- `system_command` - Run system commands
- `file_read` - Read files
- `file_write` - Write files

### Data Tools
- `extract_data` - Extract with regex patterns
- `transform_data` - Transform data (uppercase, lowercase, json_parse)
- `llm_analyze` - Analyze data with AI

## 🔄 Advanced Features

### 1. **Context Passing**

Use `{{prev_result}}` to access previous step output:

```python
WorkflowStep(
    step_id="step_2",
    tool="llm_analyze",
    params={
        "data": "{{prev_result.content}}",  # From previous step
        "question": "Summarize this"
    }
)
```

### 2. **Conditional Execution**

Steps can have conditions:

```python
WorkflowStep(
    step_id="send_alert",
    tool="email_send",
    condition="if prev_result.success and prev_result.count > 10",
    params={"to": "alert@example.com", "subject": "Alert!"}
)
```

### 3. **Automatic Retries**

Each step retries automatically on failure:

```python
WorkflowStep(
    step_id="flaky_step",
    tool="web_navigate",
    retry_count=5  # Will retry up to 5 times
)
```

### 4. **Error Recovery**

Workflows handle failures gracefully:
- Exponential backoff between retries
- Detailed error logging
- Partial workflow results available

## 📊 Workflow Status

Monitor workflow execution:

```python
result = engine.execute_workflow(workflow)

# Check status
print(result['workflow']['status'])  # completed, failed, running

# Get step details
for step in result['workflow']['steps']:
    print(f"{step['step_id']}: {step['status']}")
    if step['error']:
        print(f"  Error: {step['error']}")

# Execution time
print(f"Completed in: {result['execution_time']}s")
```

## 🎨 Real-World Examples

### E-commerce Price Monitoring

```python
workflow = engine.create_workflow_from_task(
    "Go to Amazon, search for 'gaming laptop', extract top 5 products with prices, "
    "compare with last week's data, and email me if any price dropped"
)
```

**Generated workflow:**
1. Navigate to amazon.com
2. Search for "gaming laptop"
3. Extract product data
4. Read last week's prices from file
5. Compare prices
6. Conditional: If price drop detected
7. Send email alert

### Daily News Digest

```python
workflow = engine.create_workflow_from_task(
    "Search for tech news from today, extract headlines, "
    "summarize with AI, and email me daily digest"
)
```

**Generated workflow:**
1. Search Google for "tech news today"
2. Extract top 10 headlines
3. AI analysis to create summary
4. Format as HTML email
5. Send email digest

### Automated Testing

```python
workflow = engine.create_workflow_from_task(
    "Test login on staging.example.com with test credentials, "
    "verify dashboard loads, take screenshot, and save test report"
)
```

**Generated workflow:**
1. Navigate to staging.example.com/login
2. Type test username
3. Type test password
4. Click login
5. Wait for dashboard element
6. Take screenshot
7. Verify success
8. Write test report to file

## 🚀 Integration with Existing Features

The workflow engine integrates seamlessly:

- **Web Agent**: All Puppeteer automation available
- **Email Agent**: Gmail API + Langchain
- **System Agent**: 150+ system operations
- **LLM Models**: Groq, Gemini, OpenAI for AI steps

## 📝 Custom Tool Registration

Add your own tools:

```python
def my_custom_tool(params, context):
    # Your logic here
    result = do_something(params['input'])
    return {
        "success": True,
        "result": result
    }

# Register
engine.register_tool("my_tool", my_custom_tool)

# Use in workflow
workflow.add_step(WorkflowStep(
    step_id="custom_step",
    tool="my_tool",
    params={"input": "data"}
))
```

## 🎯 Best Practices

1. **Keep steps atomic** - Each step should do one thing
2. **Use descriptive names** - Make workflows self-documenting
3. **Handle errors** - Add fallback steps
4. **Test incrementally** - Test each step before chaining
5. **Use context** - Pass data between steps efficiently

## 🐛 Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View step execution:
- Start time and end time for each step
- Attempt count for retries
- Error messages
- Result data

## 🌟 Coming Soon

- [ ] Scheduled workflows (cron-like)
- [ ] Webhooks to trigger workflows
- [ ] Workflow templates library
- [ ] Visual workflow builder
- [ ] Parallel step execution
- [ ] Workflow versioning

## 💡 Tips

**Complex multi-step tasks?** Let the AI create the workflow!

Instead of manual steps, just describe what you want:

```
"Monitor Hacker News, extract top story, read the article, 
summarize with AI, and post to Slack"
```

The engine figures out all the steps automatically! 🎉

---

**This is Atlas-level automation, built into SIGMA-OS!** 🚀
