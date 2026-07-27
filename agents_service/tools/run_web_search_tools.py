import asyncio
import json
import os
from pathlib import Path
from typing import Any

# Load .env file manually to configure TAVILY_API_KEY
env_path = Path(__file__).resolve().parents[2] / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

# Now import the tools after environment variables are set
from agents_service.tools.web_search_tools import web_search, extract_page, crawl_page


async def run_and_save():
    output_path = Path(__file__).parent / "search_results.txt"
    print(f"Running web search tools and saving results to {output_path}...")

    # 1. Test web_search
    query = "Memory and Context in AI agents"
    print(f"Running web_search with query: '{query}'...")
    web_search_res = await web_search(query=query)

    # 2. Test extract_page with multiple URLs
    urls = [
        "https://www.python.org",
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
    ]
    print(f"Running extract_page with URLs: {urls}...")
    extract_page_res = await extract_page(urls=urls, extract_depth="basic")

    # 3. Test crawl_page with a limit of 1 to keep it fast
    crawl_url = "https://www.python.org"
    print(f"Running crawl_page with URL: '{crawl_url}' (limit=1)...")
    crawl_page_res = await crawl_page(url=crawl_url, limit=1)

    # Format the results into a text file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=== web_search ===\n")
        if isinstance(web_search_res, dict):
            f.write(json.dumps(web_search_res, indent=2))
        else:
            f.write(json.dumps([res.__dict__ for res in web_search_res], indent=2))
        f.write("\n\n")

        f.write("=== extract_page ===\n")
        if isinstance(extract_page_res, dict):
            f.write(json.dumps(extract_page_res, indent=2))
        else:
            f.write(json.dumps([res.__dict__ for res in extract_page_res], indent=2))
        f.write("\n\n")

        f.write("=== crawl_page ===\n")
        if isinstance(crawl_page_res, dict):
            f.write(json.dumps(crawl_page_res, indent=2))
        else:
            f.write(json.dumps([res.__dict__ for res in crawl_page_res], indent=2))
        f.write("\n")

    print("Done! Results written successfully.")


if __name__ == "__main__":
    asyncio.run(run_and_save())
