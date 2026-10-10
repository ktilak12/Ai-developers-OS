import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from agents.browser.agent import BrowserAgent
from agents.browser.tools import BrowserTools

client = TestClient(app)


def test_browser_verify_endpoint_rejects_invalid_directory():
    res = client.post("/api/agents/browser/verify", json={
        "directory_path": "/invalid/non_existent_dir_xyz",
        "start_url": "http://localhost:3000/login"
    })
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_browser_verify_endpoint_rejects_dangerous_protocols():
    res = client.post("/api/agents/browser/verify", json={
        "start_url": "file:///etc/passwd"
    })
    assert res.status_code == 400
    assert "Only http and https are allowed" in res.json()["detail"]


def test_browser_verify_endpoint_rejects_cloud_metadata_ip():
    res = client.post("/api/agents/browser/verify", json={
        "start_url": "http://169.254.169.254/latest/meta-data"
    })
    assert res.status_code == 400
    assert "cloud metadata" in res.json()["detail"]


def test_browser_verify_endpoint_rejects_oversized_task_name():
    res = client.post("/api/agents/browser/verify", json={
        "task_name": "x" * 201
    })
    assert res.status_code == 400
    assert "exceeds maximum length" in res.json()["detail"]


def test_browser_verify_endpoint_rejects_oversized_steps():
    res = client.post("/api/agents/browser/verify", json={
        "steps": [{"action": "navigate", "url": "http://localhost:3000"}] * 51
    })
    assert res.status_code == 400
    assert "exceeds maximum limit" in res.json()["detail"]


def test_browser_tools_sanitizes_screenshot_filename():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = BrowserTools(temp_dir)
        res = tools.capture_screenshot(name="../../../evil_escape")
        assert res["status"] == "success"
        # Must not contain traversal dots or slashes
        assert ".." not in res["screenshot_file"]
        assert "evil_escape" in res["screenshot_file"]
    finally:
        shutil.rmtree(temp_dir)


def test_browser_tools_rejects_file_protocol():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = BrowserTools(temp_dir)
        res = tools.open_page("file:///etc/shadow")
        assert res["status"] == "error"
        assert "Only http and https are allowed" in res["message"]
    finally:
        shutil.rmtree(temp_dir)


def test_browser_agent_executes_valid_flow():
    temp_dir = tempfile.mkdtemp()
    try:
        agent = BrowserAgent(temp_dir)
        res = agent.verify_flow(task_name="Verify Dashboard", start_url="http://localhost:3000/dashboard")
        assert res["status"] == "PASSED"
        assert res["total_steps_executed"] > 0
        assert "screenshot_artifact" in res
    finally:
        shutil.rmtree(temp_dir)


def test_browser_agent_marks_failed_flow_when_step_errors():
    temp_dir = tempfile.mkdtemp()
    try:
        agent = BrowserAgent(temp_dir)
        # Passing an invalid protocol step should cause verify_flow to return FAILED
        steps = [
            {"action": "navigate", "url": "ftp://malicious.com"},
            {"action": "click", "selector": "button"}
        ]
        res = agent.verify_flow(task_name="Failing Journey", start_url="ftp://malicious.com", steps=steps)
        assert res["status"] == "FAILED"
        assert "failed" in res["observation"].lower()
    finally:
        shutil.rmtree(temp_dir)


def test_browser_verify_endpoint_rejects_null_bytes():
    res1 = client.post("/api/agents/browser/verify", json={
        "task_name": "Login\0Injection"
    })
    assert res1.status_code == 400
    assert "Null bytes are prohibited" in res1.json()["detail"]

    res2 = client.post("/api/agents/browser/verify", json={
        "start_url": "http://localhost:3000/\0test"
    })
    assert res2.status_code == 400
    assert "Null bytes are prohibited" in res2.json()["detail"]


def test_browser_verify_endpoint_rejects_non_dict_steps():
    res = client.post("/api/agents/browser/verify", json={
        "steps": ["invalid_string_step"]
    })
    assert res.status_code in (400, 422)


def test_browser_tools_handles_none_text_safely():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = BrowserTools(temp_dir)
        res = tools.type_text("input#username", None)
        assert res["status"] == "success"
        assert res["characters_typed"] == 0
    finally:
        shutil.rmtree(temp_dir)


def test_browser_tools_rejects_null_bytes_and_empty_selectors():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = BrowserTools(temp_dir)
        res_url = tools.open_page("http://example.com/\0evil")
        assert res_url["status"] == "error"
        assert "Null bytes" in res_url["message"]

        res_sel = tools.click_element("btn\0evil")
        assert res_sel["status"] == "error"
        assert "Null bytes" in res_sel["message"]

        res_empty = tools.click_element("   ")
        assert res_empty["status"] == "error"
        assert "non-empty string" in res_empty["message"]
    finally:
        shutil.rmtree(temp_dir)

