#!/usr/bin/env node
/**
 * Screenshot script for Chat History tab
 */

const puppeteer = require('puppeteer-core');

const url = process.argv[2] || 'https://kish-clawdbot-controls-dnc8qwz5o-kishparikh13s-projects.vercel.app';
const output = process.argv[3] || '/data/workspace/dexter-collab/screenshot-chat-history.png';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/usr/bin/chromium',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });
  
  // Wait for page to load
  await new Promise(r => setTimeout(r, 2000));
  
  // Click on the Chat History tab
  await page.evaluate(() => {
    const buttons = document.querySelectorAll('.nav-tab');
    for (const btn of buttons) {
      if (btn.textContent.includes('Chat History')) {
        btn.click();
        break;
      }
    }
  });
  
  // Wait for the chat view to show
  await new Promise(r => setTimeout(r, 1500));
  
  await page.screenshot({ path: output, fullPage: false });
  console.log(`Screenshot saved to ${output}`);
  
  await browser.close();
})();
