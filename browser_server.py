# browser_server.py
from fastmcp import FastMCP
from DrissionPage import ChromiumPage

# Initialize the MCP Server
mcp = FastMCP("DrissionPage-Agent")

@mcp.tool()
def scrape_with_drission(url: str, headless: bool = True) -> str:
    """
    Visits a URL using DrissionPage (undetected) and returns the text content.
    Use this when standard scraping fails or you get blocked.
    """
    page = ChromiumPage()
    try:
        page.get(url)
        # Add your custom logic here (e.g., clicking buttons, handling popups)
        content = page.html
        return content
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        page.quit()

if __name__ == "__main__":
    mcp.run()