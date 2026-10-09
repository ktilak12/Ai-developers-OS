import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from agents.security.agent import SecurityAgent
from agents.security.tools import SecurityTools

client = TestClient(app)


def test_security_scan_endpoint_rejects_invalid_directory():
    # /api/agents/security/scan with a non-existent directory must return 400
    res = client.post("/api/agents/security/scan", json={
        "directory_path": "/invalid/non_existent_dir_xyz"
    })
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_security_rules_endpoint_rejects_invalid_directory():
    # /api/agents/security/rules with a non-existent directory must return 400
    res = client.get("/api/agents/security/rules?directory_path=/invalid/non_existent_dir_xyz")
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_security_scan_endpoint_rejects_file_as_directory():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    temp_file.close()
    try:
        res = client.post("/api/agents/security/scan", json={
            "directory_path": temp_file.name
        })
        assert res.status_code == 400
        assert "not a directory" in res.json()["detail"]
    finally:
        os.unlink(temp_file.name)


def test_security_tools_detect_aws_key():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = SecurityTools(temp_dir)
        content = 'aws_key = "AKIAIOSFODNN7EXAMPLE"'
        findings = tools.scan_content("config.py", content)
        assert any(f["rule_id"] == "SEC-SECRET-001" for f in findings)
        assert any("AWS" in f["rule_name"] for f in findings)
    finally:
        shutil.rmtree(temp_dir)


def test_security_tools_detect_eval():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = SecurityTools(temp_dir)
        content = "result = eval(user_input)"
        findings = tools.scan_content("utils.py", content)
        assert any(f["rule_id"] == "SEC-INJECT-002" for f in findings)
        assert any(f["severity"] == "CRITICAL" for f in findings)
    finally:
        shutil.rmtree(temp_dir)


def test_security_tools_detect_sql_injection():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = SecurityTools(temp_dir)
        content = 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")'
        findings = tools.scan_content("db.py", content)
        assert any(f["rule_id"] == "SEC-SQLI-003" for f in findings)
        assert any(f["severity"] == "CRITICAL" for f in findings)
    finally:
        shutil.rmtree(temp_dir)


def test_security_tools_detect_debug_mode():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = SecurityTools(temp_dir)
        content = "DEBUG = True"
        findings = tools.scan_content("settings.py", content)
        assert any(f["rule_id"] == "SEC-CONFIG-004" for f in findings)
    finally:
        shutil.rmtree(temp_dir)


def test_security_tools_no_findings_on_clean_code():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = SecurityTools(temp_dir)
        content = "def add(a: int, b: int) -> int:\n    return a + b\n"
        findings = tools.scan_content("math_utils.py", content)
        assert findings == []
    finally:
        shutil.rmtree(temp_dir)


def test_security_agent_security_score_formula():
    temp_dir = tempfile.mkdtemp()
    try:
        agent = SecurityAgent(temp_dir)
        # 1 CRITICAL (penalty 30) => score 70
        report = agent._build_security_report(
            raw_findings=[{
                "file": "a.py", "line": 1, "rule_id": "SEC-SECRET-001",
                "severity": "CRITICAL", "rule_name": "Test"
            }],
            scanned_files=["a.py"]
        )
        assert report["security_score"] == 70
        assert report["passed"] is False
        assert report["status"] == "BLOCKED_BY_POLICY"
        assert report["approval_gate"]["merge_allowed"] is False
    finally:
        shutil.rmtree(temp_dir)


def test_security_agent_deduplication():
    temp_dir = tempfile.mkdtemp()
    try:
        agent = SecurityAgent(temp_dir)
        finding = {"file": "a.py", "line": 1, "rule_id": "SEC-SECRET-001", "severity": "CRITICAL", "rule_name": "X"}
        # Feed same finding twice — should appear once in report
        report = agent._build_security_report(
            raw_findings=[finding, finding],
            scanned_files=["a.py"]
        )
        assert report["total_findings_count"] == 1
    finally:
        shutil.rmtree(temp_dir)


def test_security_agent_clean_scan_grade_a():
    temp_dir = tempfile.mkdtemp()
    try:
        agent = SecurityAgent(temp_dir)
        report = agent._build_security_report(raw_findings=[], scanned_files=["safe.py"])
        assert report["security_score"] == 100
        assert report["grade"] == "A"
        assert report["passed"] is True
        assert report["approval_gate"]["merge_allowed"] is True
    finally:
        shutil.rmtree(temp_dir)


def test_security_agent_shannon_entropy_high_for_random_string():
    entropy = SecurityAgent.calculate_shannon_entropy("AKIAIOSFODNN7EXAMPLEabcdefg1234567890")
    assert entropy > 4.0  # High-entropy string


def test_security_agent_shannon_entropy_zero_for_empty():
    entropy = SecurityAgent.calculate_shannon_entropy("")
    assert entropy == 0.0


def test_security_tools_path_traversal_jail_rejection():
    temp_dir = tempfile.mkdtemp()
    try:
        tools = SecurityTools(temp_dir)
        findings = tools.scan_file("../../../etc/passwd")
        assert findings == []
    finally:
        shutil.rmtree(temp_dir)


def test_security_scan_endpoint_rejects_oversized_file_paths():
    res = client.post("/api/agents/security/scan", json={
        "file_paths": [f"file_{i}.py" for i in range(51)]
    })
    assert res.status_code == 400
    assert "exceeds maximum limit" in res.json()["detail"]


def test_security_scan_endpoint_rejects_null_byte_in_file_paths():
    res = client.post("/api/agents/security/scan", json={
        "file_paths": ["app.py\0malicious"]
    })
    assert res.status_code == 400
    assert "null bytes prohibited" in res.json()["detail"]


def test_security_scan_endpoint_rejects_oversized_changes():
    res = client.post("/api/agents/security/scan", json={
        "changes": [{"file_path": f"f{i}.py", "new_content": "x=1"} for i in range(51)]
    })
    assert res.status_code == 400
    assert "exceeds maximum limit" in res.json()["detail"]


def test_security_agent_scan_changes_handles_malformed():
    temp_dir = tempfile.mkdtemp()
    try:
        agent = SecurityAgent(temp_dir)
        # Passing None or non-list or invalid entries must not throw
        rep = agent.scan_changes(None)
        assert rep["status"] == "PASSED"
        rep2 = agent.scan_changes(["not a dict", {"file_path": "a\0b.py", "new_content": "x=1"}])
        assert rep2["scanned_files_count"] == 0
    finally:
        shutil.rmtree(temp_dir)

