# Web Automation with Puppeteer - Quick Start Guide

## 🎯 What You Can Do Now

Your SIGMA-OS agent can now perform web automation tasks like:

- **Search the web** - "search Google for latest AI news"
- **Visit websites** - "go to github.com"
- **Extract information** - "get the page title"
- **Take screenshots** - "take a screenshot of the page"
- **Interact with pages** - "click the login button"

## 🚀 How to Use

### 1. Start the System

Run the startup script which now includes the Puppeteer service:

```bash
./start.sh
```

This will start:
- ✅ Puppeteer automation service (port 3001)
- ✅ Python backend (port 5000)
- ✅ React frontend (port 5173)

### 2. Use Web Automation in Your Agent

Open your browser at `http://localhost:5173` and try these commands:

```
"search Google for Python tutorials"
"find latest news about AI"
"go to wikipedia.org"
"search for best programming languages 2024"
```

### 3. Test Manually (Optional)

Test the web agent separately:

```bash
source .venv/bin/activate
python test_web_agent.py
```

## 📋 Example Commands

Here are some example commands you can give to your agent:

1. **Web Search**
   - "search for machine learning courses"
   - "find information about quantum computing"
   - "look up python documentation"

2. **Website Navigation**
   - "open github.com"
   - "visit reddit.com"
   - "go to stackoverflow.com"

3. **Information Extraction**
   - "get the title of the current page"
   - "extract all links from this page"
   - "read the main content"

4. **Advanced Workflows**
   - "log in to flipkart.com with my email and show the dashboard"
   - "visit amazon, add the first two mobiles to compare, and summarize the price difference"
   - "open hacker news, filter posts from today, and capture a screenshot of the top story"
   - "go to netflix, search for sci-fi movies, and list the first five titles"
   - "load github, search for sigma project issues, and extract the open issues list"

## 🔧 Advanced Usage

### Direct API Calls

The Puppeteer service runs on `http://localhost:3001`. You can make direct API calls:

```bash
# Search Google
curl -X POST http://localhost:3001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "web automation"}'

# Navigate to URL
curl -X POST http://localhost:3001/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com"}'
```

### Python Integration

Use the WebAgent directly in your Python code:

```python
from intelligent_agents.web_agent import WebAgent

agent = WebAgent()

# Search Google
result = agent.run("search for AI news")
print(result)

# Navigate to a site
result = agent.run("go to example.com")
print(result)
```

### Automation Workflows (Multi-step)

You can now run complex sequences (navigate → wait → type → click) with a single call.

```bash
curl -X POST http://localhost:3001/workflow \
   -H "Content-Type: application/json" \
   -d '{
      "steps": [
         {"type": "navigate", "url": "https://example.com/login"},
         {"type": "waitForSelector", "selector": "input[name=email]"},
         {"type": "type", "selector": "input[name=email]", "text": "user@example.com", "clear": true},
         {"type": "type", "selector": "input[name=password]", "text": "supers3cret", "clear": true},
         {"type": "click", "selector": "button[type=submit]", "waitForNavigation": true},
         {"type": "screenshot", "fullPage": true}
      ],
      "options": {"startNew": true, "waitBetweenSteps": 250}
   }'
```

Or let the agent figure out the workflow for you:

```
"log in to example.com with my email and take a screenshot of the dashboard"
"fill out the contact form on example.org with sample data"
"go to demoqa.com, add an item to cart, and capture the order summary"
```

## 🎨 Headless vs Visible Mode

By default, the browser runs in **visible mode** so you can see what's happening.

To run in **headless mode** (background), edit `puppeteer_service/puppeteer_server.js`:

```javascript
browser = await puppeteer.launch({
    headless: true,  // Change to true
    // ...
});
```

## 🐛 Troubleshooting

### "Puppeteer service not running" error

Start the service manually:
```bash
node puppeteer_service/puppeteer_server.js
```

### Chrome not found

Install Chrome or Chromium:
```bash
# Ubuntu/Debian
sudo apt install chromium-browser

# Or let Puppeteer download it
npx puppeteer browsers install chrome
```

### Port already in use

Check if something is using port 3001:
```bash
lsof -i :3001
kill -9 <PID>
```

## 📚 More Information

See `puppeteer_service/README.md` for detailed API documentation.
