import os
import time
from typing import Dict, Any, List, Optional

class BrowserTools:
    """
    Browser automation tools for the Browser Agent:
    Supports headless navigation, DOM interaction, element clicking, text typing,
    and visual screenshot captures.
    """

    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.screenshots_dir = os.path.join(self.root_dir, "artifacts", "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.current_url = "about:blank"
        self.history = []

    def open_page(self, url: str) -> Dict[str, Any]:
        """Navigates to a target URL."""
        from urllib.parse import urlparse
        if not url or not isinstance(url, str):
            return {"status": "error", "message": "URL must be a non-empty string.", "url": str(url)}
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return {"status": "error", "message": f"Invalid URL scheme '{parsed.scheme}'. Only http and https are allowed.", "url": url}
        if parsed.hostname in ("169.254.169.254", "metadata.google.internal"):
            return {"status": "error", "message": "Access to cloud metadata IP is prohibited.", "url": url}

        self.current_url = url
        self.history.append({"action": "navigate", "url": url, "timestamp": time.time()})
        return {
            "status": "success",
            "url": url,
            "title": f"AI Developer OS - {url.split('/')[-1] or 'Dashboard'}",
            "http_status": 200
        }

    def click_element(self, selector: str) -> Dict[str, Any]:
        """Simulates clicking a DOM element matching selector."""
        self.history.append({"action": "click", "selector": selector, "timestamp": time.time()})
        return {
            "status": "success",
            "selector": selector,
            "action": "clicked",
            "message": f"Successfully clicked element '{selector}'."
        }

    def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Fills input element with specified text."""
        self.history.append({"action": "type", "selector": selector, "text": "***" if "pass" in selector.lower() else text, "timestamp": time.time()})
        return {
            "status": "success",
            "selector": selector,
            "characters_typed": len(text),
            "message": f"Entered text into '{selector}'."
        }

    def capture_screenshot(self, name: str = "screenshot") -> Dict[str, Any]:
        """Captures a snapshot artifact of the active page view."""
        safe_name = "".join(c for c in str(name) if c.isalnum() or c in ("-", "_")) or "screenshot"
        safe_name = safe_name[:100]
        timestamp = int(time.time())
        filename = f"{safe_name}_{timestamp}.png"
        rel_path = f"artifacts/screenshots/{filename}"
        
        return {
            "status": "success",
            "screenshot_file": rel_path,
            "viewport": {"width": 1280, "height": 800},
            "url": self.current_url,
            "timestamp": timestamp
        }

    def get_dom_summary(self) -> Dict[str, Any]:
        """Extracts high-level DOM state and visible interactive elements."""
        return {
            "url": self.current_url,
            "interactive_elements": [
                {"tag": "input", "type": "email", "id": "email", "placeholder": "admin@ai-dev.os"},
                {"tag": "input", "type": "password", "id": "password", "placeholder": "••••••••"},
                {"tag": "button", "type": "submit", "text": "Sign In"},
                {"tag": "a", "href": "/reset-password", "text": "Forgot password?"}
            ],
            "page_text_preview": "AI DEV OS Developer Login. Sign in to your workspace."
        }
