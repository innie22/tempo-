import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        
        # Navigate to app
        await page.goto("http://127.0.0.1:8000/index.html")
        await page.wait_for_timeout(1000)
        
        # Sign in as user
        await page.evaluate("""() => {
            if (window.TempoAuth && window.TempoAuth.signInWithCredentials) {
                return window.TempoAuth.signInWithCredentials('user@tempo.test', 'password123');
            }
        }""")
        await page.wait_for_timeout(500)
        
        # Open Ucheck
        await page.evaluate("""() => {
            if (window.TempoMode && window.TempoMode.openUcheck) {
                window.TempoMode.openUcheck();
            }
        }""")
        await page.wait_for_timeout(1000)
        
        # Check current state
        state = await page.evaluate("""() => {
            const header = document.querySelector('header.entry-header');
            const headerDisplay = header ? window.getComputedStyle(header).display : 'none';
            const navLinks = Array.from(document.querySelectorAll('nav a')).map(a => ({
                id: a.id,
                text: a.textContent.trim(),
                href: a.getAttribute('href')
            }));
            const unclearHomeView = document.getElementById('unclear-home-view');
            const hasDuplicateBar = !!(unclearHomeView && unclearHomeView.querySelector('button[title="Return Home"]'));
            const cards = Array.from(document.querySelectorAll('[data-card]')).map(c => c.getAttribute('data-card'));
            return {
                headerDisplay,
                navLinks,
                hasDuplicateBar,
                cards
            };
        }""")
        print("UCheck DOM state:", state)
        
        await page.screenshot(path="C:/Users/YEN NHI/.gemini/antigravity/brain/6baf9c9e-16aa-475f-b2c0-d941b08ac2c6/current_ucheck_screenshot.png", full_page=False)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
