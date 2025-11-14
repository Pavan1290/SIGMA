const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const puppeteer = require('puppeteer');

const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Store browser instances
let browser = null;
let page = null;

const wait = (ms = 1000) => new Promise(resolve => setTimeout(resolve, ms));

// Initialize browser
async function initBrowser() {
    if (!browser) {
        console.log('🌐 Launching browser...');
        browser = await puppeteer.launch({
            headless: false,
            ignoreHTTPSErrors: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled'
            ]
        });
        page = await browser.newPage();
        
        // Set user agent to avoid detection
        await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');
        await page.setViewport({ width: 1280, height: 800 });
        
        console.log('✅ Browser ready');
    }
    return { browser, page };
}

// Create a fresh page for each operation (avoids detached frame issues)
async function createNewPage() {
    try {
        const { browser: b } = await initBrowser();
        
        // Check if browser is still connected
        if (!b.isConnected()) {
            console.log('⚠️  Browser disconnected, relaunching...');
            browser = null;
            page = null;
            return await createNewPage();
        }
        
        const newPage = await b.newPage();
    await newPage.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');
        await newPage.setViewport({ width: 1280, height: 800 });
        return newPage;
    } catch (error) {
        console.error('❌ Error creating page:', error.message);
        browser = null;
        page = null;
        return await createNewPage();
    }
}

async function runWorkflowStep(activePage, step, index) {
    if (!step || !step.type) {
        throw new Error(`Step ${index + 1}: missing required 'type' field`);
    }

    const action = String(step.type).toLowerCase();
    const label = step.label || step.description || action;

    switch (action) {
        case 'navigate':
        case 'goto': {
            if (!step.url) {
                throw new Error(`Step ${index + 1}: 'url' is required for navigate`);
            }
            await activePage.goto(step.url, {
                waitUntil: step.waitUntil || 'networkidle2',
                timeout: step.timeout || 30000
            });
            return {
                type: 'navigate',
                label,
                url: activePage.url(),
                title: await activePage.title()
            };
        }
        case 'waitforselector':
        case 'wait_for_selector':
        case 'waitfor': {
            if (!step.selector) {
                throw new Error(`Step ${index + 1}: 'selector' is required for waitForSelector`);
            }
            await activePage.waitForSelector(step.selector, {
                visible: step.visible ?? true,
                timeout: step.timeout || 15000
            });
            return {
                type: 'waitForSelector',
                label,
                selector: step.selector
            };
        }
        case 'wait':
        case 'pause': {
            const duration = step.ms || step.timeout || step.duration || 1000;
            await wait(duration);
            return {
                type: 'wait',
                label,
                duration
            };
        }
        case 'click': {
            if (!step.selector) {
                throw new Error(`Step ${index + 1}: 'selector' is required for click`);
            }
            if (step.scrollIntoView !== false) {
                await activePage.$eval(step.selector, (el, opts) => {
                    el.scrollIntoView({
                        behavior: opts.behavior || 'smooth',
                        block: opts.block || 'center',
                        inline: opts.inline || 'center'
                    });
                }, step.scrollOptions || {});
            }

            if (step.waitBefore) {
                await wait(step.waitBefore);
            }

            const clickOptions = {};
            if (step.button) clickOptions.button = step.button;
            if (step.clickCount) clickOptions.clickCount = step.clickCount;

            if (step.waitForNavigation) {
                await Promise.all([
                    activePage.waitForNavigation({
                        waitUntil: step.waitUntil || 'networkidle2',
                        timeout: step.timeout || 30000
                    }),
                    activePage.click(step.selector, clickOptions)
                ]);
            } else {
                await activePage.click(step.selector, clickOptions);
            }

            if (step.waitAfter) {
                await wait(step.waitAfter);
            }

            return {
                type: 'click',
                label,
                selector: step.selector
            };
        }
        case 'type': {
            if (!step.selector) {
                throw new Error(`Step ${index + 1}: 'selector' is required for type`);
            }
            if (typeof step.text === 'undefined') {
                throw new Error(`Step ${index + 1}: 'text' is required for type`);
            }

            if (step.clear) {
                await activePage.$eval(step.selector, el => {
                    if (['INPUT', 'TEXTAREA'].includes(el.tagName)) {
                        el.value = '';
                    } else {
                        el.innerHTML = '';
                    }
                });
            }

            if (step.focusFirst) {
                await activePage.focus(step.selector);
            }

            await activePage.type(step.selector, String(step.text), {
                delay: typeof step.delay === 'number' ? step.delay : 20
            });

            return {
                type: 'type',
                label,
                selector: step.selector,
                text: step.text
            };
        }
        case 'select': {
            if (!step.selector || typeof step.value === 'undefined') {
                throw new Error(`Step ${index + 1}: 'selector' and 'value' are required for select`);
            }
            const values = Array.isArray(step.value) ? step.value : [step.value];
            await activePage.select(step.selector, ...values.map(String));
            return {
                type: 'select',
                label,
                selector: step.selector,
                value: values
            };
        }
        case 'hover': {
            if (!step.selector) {
                throw new Error(`Step ${index + 1}: 'selector' is required for hover`);
            }
            await activePage.hover(step.selector);
            return {
                type: 'hover',
                label,
                selector: step.selector
            };
        }
        case 'scroll': {
            if (step.selector) {
                await activePage.$eval(step.selector, (el, opts) => {
                    el.scrollIntoView({
                        behavior: opts.behavior || 'smooth',
                        block: opts.block || 'center',
                        inline: opts.inline || 'center'
                    });
                }, step);
            } else if (step.to) {
                await activePage.evaluate(destination => {
                    if (destination === 'bottom') {
                        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                    } else if (destination === 'top') {
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                }, step.to);
            } else if (step.by) {
                await activePage.evaluate(delta => {
                    window.scrollBy(delta.x || 0, delta.y || 0);
                }, step.by);
            } else {
                await activePage.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }));
            }
            return {
                type: 'scroll',
                label
            };
        }
        case 'extract': {
            if (step.selector) {
                if (step.all) {
                    const values = await activePage.$$eval(step.selector, els => els.map(el => el.innerText.trim()));
                    return {
                        type: 'extract',
                        label,
                        selector: step.selector,
                        values
                    };
                }
                const text = await activePage.$eval(step.selector, el => el.innerText.trim());
                return {
                    type: 'extract',
                    label,
                    selector: step.selector,
                    text
                };
            }
            const content = await activePage.evaluate(() => document.body.innerText);
            return {
                type: 'extract',
                label,
                text: content
            };
        }
        case 'screenshot': {
            if (step.selector) {
                const element = await activePage.$(step.selector);
                if (!element) {
                    throw new Error(`Step ${index + 1}: element not found for selector ${step.selector}`);
                }
                const image = await element.screenshot({ encoding: 'base64' });
                return {
                    type: 'screenshot',
                    label,
                    selector: step.selector,
                    image,
                    format: 'base64'
                };
            }
            const image = await activePage.screenshot({
                fullPage: step.fullPage ?? false,
                encoding: 'base64'
            });
            return {
                type: 'screenshot',
                label,
                image,
                format: 'base64',
                fullPage: step.fullPage ?? false
            };
        }
        case 'evaluate':
        case 'execute': {
            if (!step.script) {
                throw new Error(`Step ${index + 1}: 'script' is required for evaluate`);
            }
            const result = await activePage.evaluate(step.script);
            return {
                type: 'evaluate',
                label,
                result
            };
        }
        default:
            throw new Error(`Unsupported step type: ${step.type}`);
    }
}

// Close browser and reset
async function resetBrowser() {
    if (browser) {
        await browser.close();
        browser = null;
        page = null;
    }
    return await initBrowser();
}

// Close browser
async function closeBrowser() {
    if (browser) {
        await browser.close();
        browser = null;
        page = null;
        console.log('🔒 Browser closed');
    }
}

// Health check
app.get('/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        browserActive: browser !== null,
        service: 'puppeteer-automation'
    });
});

// Navigate to URL
app.post('/navigate', async (req, res) => {
    let newPage = null;
    try {
        const { url, waitUntil = 'networkidle2' } = req.body;
        
        if (!url) {
            return res.status(400).json({ error: 'URL is required' });
        }

        // Create a fresh page for this operation
        newPage = await createNewPage();
        
        console.log(`🔗 Navigating to: ${url}`);
        await newPage.goto(url, { waitUntil, timeout: 30000 });
        
        const title = await newPage.title();
        const currentUrl = newPage.url();
        
        // Store the page for potential future operations
        page = newPage;
        
        res.json({
            success: true,
            operation: 'navigate',
            url: currentUrl,
            title: title,
            message: `Navigated to ${title}`
        });
    } catch (error) {
        console.error('❌ Navigation error:', error.message);
        
        // Close the page on error
        if (newPage) {
            try {
                await newPage.close();
            } catch (e) {
                // Ignore
            }
        }
        
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Extract text from page
app.post('/extract', async (req, res) => {
    try {
        const { selector, extractAll = false } = req.body;

        if (!page) {
            return res.status(400).json({ error: 'No page loaded. Navigate first.' });
        }

        let data;
        
        if (selector) {
            if (extractAll) {
                data = await page.$$eval(selector, elements => 
                    elements.map(el => el.textContent.trim())
                );
            } else {
                data = await page.$eval(selector, el => el.textContent.trim());
            }
        } else {
            // Get all visible text
            data = await page.evaluate(() => document.body.innerText);
        }

        const title = await page.title();
        const url = page.url();

        res.json({
            success: true,
            operation: 'extract',
            url: url,
            title: title,
            data: data
        });
    } catch (error) {
        console.error('❌ Extraction error:', error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Search on Google - IMPROVED VERSION
app.post('/search', async (req, res) => {
    let searchPage = null;
    try {
        const { query } = req.body;
        
        if (!query) {
            return res.status(400).json({ error: 'Search query is required' });
        }

        // Create a fresh page for search
        searchPage = await createNewPage();
        
        console.log(`🔍 Searching for: ${query}`);
        
        try {
            // Navigate to Google
            await searchPage.goto('https://www.google.com', { 
                waitUntil: 'networkidle0',
                timeout: 15000 
            });
            
            // Wait a bit for any popups/consent forms
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Try to accept cookies if the button exists
            try {
                const acceptButton = await searchPage.$('button[id*="accept"], button[id*="agree"], #L2AGLb');
                if (acceptButton) {
                    await acceptButton.click();
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            } catch (e) {
                // Cookie button not found, continue
            }
            
            // Wait for search input
            await searchPage.waitForSelector('textarea[name="q"], input[name="q"]', { timeout: 5000 });
            
            // Type search query
            await searchPage.type('textarea[name="q"], input[name="q"]', query);
            await searchPage.keyboard.press('Enter');
            
            // Wait for results - try multiple selectors
            try {
                await searchPage.waitForSelector('#search, #rso, .g', { timeout: 10000 });
            } catch (e) {
                console.log('⚠️  Using alternative wait strategy');
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
            
            // Extract search results
            const results = await searchPage.evaluate(() => {
                const items = [];
                
                // Try multiple selectors for search results
                const searchResults = document.querySelectorAll('#search .g, #rso .g, .v7W49e');
                
                searchResults.forEach((result, index) => {
                    if (index < 10) {
                        const titleElement = result.querySelector('h3');
                        const linkElement = result.querySelector('a');
                        const snippetElement = result.querySelector('.VwiC3b, .lyLwlc, .s3v9rd');
                        
                        if (titleElement && linkElement && linkElement.href) {
                            items.push({
                                title: titleElement.textContent,
                                link: linkElement.href,
                                snippet: snippetElement ? snippetElement.textContent : ''
                            });
                        }
                    }
                });
                
                return items;
            });
            
            res.json({
                success: true,
                operation: 'search',
                query: query,
                results: results,
                count: results.length,
                message: `Browser stays open for you to explore!`
            });
            
            // Keep the page open (don't close it)
            page = searchPage;
            
        } catch (innerError) {
            console.error('❌ Search error:', innerError.message);
            
            // Close the search page on error
            if (searchPage) {
                try {
                    await searchPage.close();
                } catch (e) {
                    // Ignore
                }
            }
            
            throw innerError;
        }
        
    } catch (error) {
        console.error('❌ Search error:', error.message);
        
        // Close page on error
        if (searchPage) {
            try {
                await searchPage.close();
            } catch (e) {
                // Ignore
            }
        }
        
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Advanced workflow automation
app.post('/workflow', async (req, res) => {
    let workflowPage = page;
    let stepResults = [];
    let workflowOptions = {};
    let startNew = false;
    let continueOnError = false;
    let waitBetweenSteps = 0;
    let closeOnFinish = false;
    let keepOpen = true;
    let closeOnError = false;

    try {
        const { steps, options } = req.body;

        if (!Array.isArray(steps) || steps.length === 0) {
            return res.status(400).json({ error: 'Steps array is required' });
        }

        workflowOptions = options || {};

        startNew = workflowOptions.startNew ?? false;
        continueOnError = workflowOptions.continueOnError ?? false;
        waitBetweenSteps = workflowOptions.waitBetweenSteps ?? 0;
        closeOnFinish = workflowOptions.closeOnFinish ?? false;
        keepOpen = workflowOptions.keepOpen ?? true;
        closeOnError = workflowOptions.closeOnError ?? false;

        if (startNew || !workflowPage) {
            workflowPage = await createNewPage();
        }

        console.log(`🛠️  Running workflow with ${steps.length} steps`);

        for (let i = 0; i < steps.length; i++) {
            const step = steps[i] || {};
            try {
                const result = await runWorkflowStep(workflowPage, step, i);
                stepResults.push({
                    index: i,
                    success: true,
                    type: result.type,
                    label: result.label,
                    result
                });

                if (waitBetweenSteps > 0) {
                    await wait(waitBetweenSteps);
                }
            } catch (stepError) {
                console.error(`⚠️  Workflow step ${i + 1} failed:`, stepError.message);
                const errorInfo = {
                    index: i,
                    success: false,
                    type: step.type,
                    label: step.label || step.description || step.type,
                    error: stepError.message
                };
                stepResults.push(errorInfo);

                if (!continueOnError) {
                    throw {
                        message: stepError.message,
                        stepResults,
                        stepIndex: i
                    };
                }
            }
        }

        const finalInfo = {
            url: workflowPage.url(),
            title: await workflowPage.title()
        };

        if (closeOnFinish) {
            try {
                await workflowPage.close();
            } catch (error) {
                console.warn('⚠️  Unable to close page after workflow:', error.message);
            }
            if (page === workflowPage) {
                page = null;
            }
        } else if (keepOpen) {
            page = workflowPage;
        }

        res.json({
            success: true,
            operation: 'workflow',
            steps: stepResults,
            final: finalInfo
        });
    } catch (error) {
        const message = error.message || 'Workflow failed';
        stepResults = error.stepResults || stepResults;

    if (workflowPage && closeOnError) {
            try {
                await workflowPage.close();
                if (page === workflowPage) {
                    page = null;
                }
            } catch (closeError) {
                console.warn('⚠️  Unable to close page after workflow error:', closeError.message);
            }
        }

        res.status(500).json({
            success: false,
            error: message,
            steps: stepResults
        });
    }
});

// Click element
app.post('/click', async (req, res) => {
    try {
        const { selector, waitForNavigation = false } = req.body;
        
        if (!selector) {
            return res.status(400).json({ error: 'Selector is required' });
        }

        if (!page) {
            return res.status(400).json({ error: 'No page loaded. Navigate first.' });
        }

        console.log(`👆 Clicking: ${selector}`);
        
        if (waitForNavigation) {
            await Promise.all([
                page.waitForNavigation({ waitUntil: 'networkidle2' }),
                page.click(selector)
            ]);
        } else {
            await page.click(selector);
        }

        res.json({
            success: true,
            operation: 'click',
            selector: selector
        });
    } catch (error) {
        console.error('❌ Click error:', error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Type text
app.post('/type', async (req, res) => {
    try {
        const { selector, text, delay = 0 } = req.body;
        
        if (!selector || !text) {
            return res.status(400).json({ error: 'Selector and text are required' });
        }

        if (!page) {
            return res.status(400).json({ error: 'No page loaded. Navigate first.' });
        }

        console.log(`⌨️  Typing into: ${selector}`);
        await page.type(selector, text, { delay });

        res.json({
            success: true,
            operation: 'type',
            selector: selector
        });
    } catch (error) {
        console.error('❌ Type error:', error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Take screenshot
app.post('/screenshot', async (req, res) => {
    try {
        const { fullPage = false, selector = null } = req.body;

        if (!page) {
            return res.status(400).json({ error: 'No page loaded. Navigate first.' });
        }

        console.log(`📸 Taking screenshot`);
        
        let screenshot;
        if (selector) {
            const element = await page.$(selector);
            screenshot = await element.screenshot({ encoding: 'base64' });
        } else {
            screenshot = await page.screenshot({ 
                fullPage: fullPage,
                encoding: 'base64'
            });
        }

        res.json({
            success: true,
            operation: 'screenshot',
            image: screenshot,
            format: 'base64'
        });
    } catch (error) {
        console.error('❌ Screenshot error:', error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Execute custom JavaScript
app.post('/execute', async (req, res) => {
    try {
        const { script } = req.body;
        
        if (!script) {
            return res.status(400).json({ error: 'Script is required' });
        }

        if (!page) {
            return res.status(400).json({ error: 'No page loaded. Navigate first.' });
        }

        console.log(`⚡ Executing custom script`);
        const result = await page.evaluate(script);

        res.json({
            success: true,
            operation: 'execute',
            result: result
        });
    } catch (error) {
        console.error('❌ Execute error:', error.message);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get page info
app.get('/page-info', async (req, res) => {
    try {
        if (!page) {
            return res.status(400).json({ error: 'No page loaded' });
        }

        const title = await page.title();
        const url = page.url();
        const content = await page.content();

        res.json({
            success: true,
            title: title,
            url: url,
            contentLength: content.length
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Close browser
app.post('/close', async (req, res) => {
    try {
        await closeBrowser();
        res.json({
            success: true,
            operation: 'close'
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down...');
    await closeBrowser();
    process.exit(0);
});

process.on('SIGTERM', async () => {
    await closeBrowser();
    process.exit(0);
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Puppeteer Automation Service running on http://localhost:${PORT}`);
    console.log(`📋 Available endpoints:`);
    console.log(`   POST /navigate - Navigate to URL`);
    console.log(`   POST /search - Search on Google`);
    console.log(`   POST /extract - Extract text from page`);
    console.log(`   POST /click - Click element`);
    console.log(`   POST /type - Type text`);
    console.log(`   POST /screenshot - Take screenshot`);
    console.log(`   POST /execute - Execute custom JavaScript`);
    console.log(`   GET  /page-info - Get current page info`);
    console.log(`   POST /close - Close browser`);
    console.log(`   GET  /health - Health check`);
});
