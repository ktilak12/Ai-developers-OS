import os
from typing import Dict, Any
from mcp.protocol import BaseMCPTool, MCPToolSchema, MCPToolParameter, MCPToolResponse
from agents.browser.tools import BrowserTools

class OpenPageTool(BaseMCPTool):
    name = "open_page"
    description = "Navigate to an application URL in headless browser"
    server = "browser"

    def __init__(self, root_dir: str):
        self.tools = BrowserTools(root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("url", "string", "Destination URL to open (e.g. 'http://localhost:3000/login')", required=True)
            ]
        )

    def execute(self, url: str = "") -> MCPToolResponse:
        from urllib.parse import urlparse
        if not url or not isinstance(url, str):
            return MCPToolResponse(success=False, error="URL must be a non-empty string.", server=self.server, tool_name=self.name)
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ("http", "https"):
            return MCPToolResponse(success=False, error=f"Invalid URL protocol '{parsed.scheme}'. Only http and https are allowed.", server=self.server, tool_name=self.name)
        if parsed.hostname in ("169.254.169.254", "metadata.google.internal"):
            return MCPToolResponse(success=False, error="Access to cloud metadata IP is prohibited.", server=self.server, tool_name=self.name)
        res = self.tools.open_page(url)
        return MCPToolResponse(success=True, data=res, server=self.server, tool_name=self.name)

class ClickElementTool(BaseMCPTool):
    name = "click_element"
    description = "Click a DOM element on current page matching CSS selector"
    server = "browser"

    def __init__(self, root_dir: str):
        self.tools = BrowserTools(root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("selector", "string", "CSS element selector (e.g. 'button[type=submit]')", required=True)
            ]
        )

    def execute(self, selector: str = "") -> MCPToolResponse:
        res = self.tools.click_element(selector)
        return MCPToolResponse(success=True, data=res, server=self.server, tool_name=self.name)

class TypeTextTool(BaseMCPTool):
    name = "type_text"
    description = "Type text into an input field matching CSS selector"
    server = "browser"

    def __init__(self, root_dir: str):
        self.tools = BrowserTools(root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("selector", "string", "CSS input selector (e.g. 'input#email')", required=True),
                MCPToolParameter("text", "string", "Text string to enter", required=True)
            ]
        )

    def execute(self, selector: str = "", text: str = "") -> MCPToolResponse:
        res = self.tools.type_text(selector, text)
        return MCPToolResponse(success=True, data=res, server=self.server, tool_name=self.name)

class CaptureScreenshotTool(BaseMCPTool):
    name = "capture_screenshot"
    description = "Capture visual viewport screenshot artifact of current page state"
    server = "browser"

    def __init__(self, root_dir: str):
        self.tools = BrowserTools(root_dir)

    def get_schema(self) -> MCPToolSchema:
        return MCPToolSchema(
            name=self.name,
            description=self.description,
            server=self.server,
            parameters=[
                MCPToolParameter("name", "string", "Screenshot artifact name label", required=False, default="page_view")
            ]
        )

    def execute(self, name: str = "page_view") -> MCPToolResponse:
        res = self.tools.capture_screenshot(name)
        return MCPToolResponse(success=True, data=res, server=self.server, tool_name=self.name)
