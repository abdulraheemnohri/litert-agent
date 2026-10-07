"""Browser tool (Playwright wrapper with fallback)."""

from litert_agent.tools.base import BaseTool, ToolResult


class BrowserTool(BaseTool):
    name = "browser"
    description = "Browser automation with Playwright"

    async def execute(self, action: str = "navigate", url: str = "", **kwargs) -> ToolResult:
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url)
                title = await page.title()
                content = await page.content()
                await browser.close()
                return ToolResult(
                    success=True,
                    output=f"Title: {title}\nLength: {len(content)}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Browser execution failed: {str(e)}. (Ensure playwright dependencies are installed)"
            )
