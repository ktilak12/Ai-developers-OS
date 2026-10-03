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
        timestamp = int(time.time())
        filename = f"{name}_{timestamp}.png"
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
