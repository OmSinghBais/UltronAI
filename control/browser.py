"""
ATLAS — Browser Control Module
Provides Playwright wrappers for browser automation:
- navigate(url: str, headless: bool = True) -> dict
- search(query: str, engine: str = "google", headless: bool = True) -> dict
- fill_form(url: str, selector: str, value: str, submit: bool = False, headless: bool = True) -> dict
- read_page(url: str, headless: bool = True) -> dict
"""

import urllib.parse
from typing import Any, Dict, Optional

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


def _format_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def navigate(url: str, headless: bool = True) -> Dict[str, Any]:
    """
    Navigates to the specified URL using Playwright.
    """
    if not url or not url.strip():
        return {"status": "error", "error": "URL cannot be empty"}

    action_name = "navigate"
    target_url = _format_url(url)

    if sync_playwright is None:
        return {"status": "error", "error": "playwright module is not installed"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            response = page.goto(target_url, timeout=30000)
            page_title = page.title()
            final_url = page.url
            status_code = response.status if response else 200
            browser.close()

            return {
                "status": "ok",
                "action": action_name,
                "data": {
                    "url": final_url,
                    "title": page_title,
                    "status_code": status_code,
                },
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to navigate to '{target_url}': {str(e)}",
        }


def search(
    query: str, engine: str = "google", headless: bool = True
) -> Dict[str, Any]:
    """
    Performs a web search on Google, Bing, or DuckDuckGo.
    """
    if not query or not query.strip():
        return {"status": "error", "error": "Search query cannot be empty"}

    action_name = "search"
    query_str = query.strip()
    encoded_query = urllib.parse.quote_plus(query_str)

    engines = {
        "google": f"https://www.google.com/search?q={encoded_query}",
        "bing": f"https://www.bing.com/search?q={encoded_query}",
        "duckduckgo": f"https://duckduckgo.com/?q={encoded_query}",
    }

    engine_key = engine.lower().strip()
    if engine_key not in engines:
        return {
            "status": "error",
            "error": f"Unsupported search engine '{engine}'. Choose from: {list(engines.keys())}",
        }

    search_url = engines[engine_key]
    nav_res = navigate(search_url, headless=headless)
    if nav_res["status"] == "ok":
        nav_res["action"] = action_name
        nav_res["data"]["query"] = query_str
        nav_res["data"]["engine"] = engine_key

    return nav_res


def fill_form(
    url: str,
    selector: str,
    value: str,
    submit: bool = False,
    headless: bool = True,
) -> Dict[str, Any]:
    """
    Navigates to URL and fills the input form field specified by selector with value.
    """
    if not url or not url.strip():
        return {"status": "error", "error": "URL cannot be empty"}
    if not selector or not selector.strip():
        return {"status": "error", "error": "Selector cannot be empty"}
    if value is None:
        return {"status": "error", "error": "Value cannot be None"}

    action_name = "fill_form"
    target_url = _format_url(url)

    if sync_playwright is None:
        return {"status": "error", "error": "playwright module is not installed"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.goto(target_url, timeout=30000)
            page.fill(selector, value)

            if submit:
                page.press(selector, "Enter")

            page_title = page.title()
            final_url = page.url
            browser.close()

            return {
                "status": "ok",
                "action": action_name,
                "data": {
                    "url": final_url,
                    "title": page_title,
                    "selector": selector,
                    "filled_value": value,
                    "submitted": submit,
                },
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to fill form field '{selector}': {str(e)}",
        }


def read_page(url: str, headless: bool = True) -> Dict[str, Any]:
    """
    Navigates to URL and reads visible page title, metadata, and body text.
    """
    if not url or not url.strip():
        return {"status": "error", "error": "URL cannot be empty"}

    action_name = "read_page"
    target_url = _format_url(url)

    if sync_playwright is None:
        return {"status": "error", "error": "playwright module is not installed"}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.goto(target_url, timeout=30000)

            page_title = page.title()
            final_url = page.url
            body_text = page.inner_text("body")
            browser.close()

            return {
                "status": "ok",
                "action": action_name,
                "data": {
                    "url": final_url,
                    "title": page_title,
                    "content": body_text[:5000] if body_text else "",
                    "content_length": len(body_text) if body_text else 0,
                },
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to read page '{target_url}': {str(e)}",
        }
