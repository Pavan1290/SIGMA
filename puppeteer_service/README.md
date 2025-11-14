# Puppeteer Web Automation Service

This service provides web automation capabilities for SIGMA-OS using Puppeteer (Node.js).

## Features

- 🔍 **Google Search** - Search and extract results
- 🌐 **Web Navigation** - Visit any URL
- 📝 **Content Extraction** - Extract text from pages
- 👆 **Element Interaction** - Click buttons, fill forms
- ⌨️ **Text Input** - Type into input fields
- 📸 **Screenshots** - Capture page screenshots
- ⚡ **Custom JavaScript** - Execute custom scripts

## API Endpoints

All endpoints are available at `http://localhost:3001`

### Health Check
```
GET /health
```

### Search Google
```
POST /search
Body: { "query": "your search query" }
```

### Navigate to URL
```
POST /navigate
Body: { "url": "https://example.com" }
```

### Extract Text
```
POST /extract
Body: { "selector": ".classname" } // optional
```

### Click Element
```
POST /click
Body: { "selector": "button.submit" }
```

### Type Text
```
POST /type
Body: { "selector": "input#search", "text": "hello world" }
```

### Take Screenshot
```
POST /screenshot
Body: { "fullPage": true }
```

### Execute JavaScript
```
POST /execute
Body: { "script": "return document.title;" }
```

## Usage from Python

The `WebAgent` class automatically uses the Puppeteer service:

```python
from intelligent_agents.web_agent import WebAgent

agent = WebAgent()

# Search Google
result = agent.run("search for Python tutorials")

# Navigate to a website
result = agent.run("go to github.com")

# Extract information
result = agent.run("get the page title")
```

## Standalone Usage

You can also start the Puppeteer service independently:

```bash
node puppeteer_service/puppeteer_server.js
```

Then make HTTP requests directly:

```bash
# Search Google
curl -X POST http://localhost:3001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "puppeteer tutorial"}'

# Navigate to URL
curl -X POST http://localhost:3001/navigate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.github.com"}'
```

## Configuration

Edit `puppeteer_service/puppeteer_server.js` to change:

- **Port**: Change `PORT` constant (default: 3001)
- **Headless Mode**: Set `headless: true` for background operation
- **Browser Args**: Modify launch arguments for custom configuration

## Troubleshooting

### Service not starting
```bash
# Make sure Node.js and npm are installed
node --version
npm --version

# Install dependencies
npm install puppeteer express cors body-parser
```

### Chrome/Chromium not found
```bash
# Puppeteer will download Chromium automatically
# Or use system Chrome:
export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
export PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome
```

### Connection refused
- Make sure the service is running: `node puppeteer_service/puppeteer_server.js`
- Check if port 3001 is available: `lsof -i :3001`
