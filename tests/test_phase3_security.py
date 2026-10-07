import os
import tempfile
import shutil
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api.main import app, validate_safe_directory
from intelligence.retrieval.symbol_search import SymbolSearchEngine
from intelligence.parser.code_parser import CodeParser

client = TestClient(app)


def test_symbol_search_query_sanitization_and_length_capping():
    mock_index = {
        "functions": [{"name": "authenticate_user", "file": "auth.py"}],
        "classes": [{"name": "AuthService", "file": "auth_service.py"}],
        "components": [{"name": "LoginForm", "file": "components/Login.tsx"}],
        "routes": [{"path": "/api/auth/login", "file": "routes/auth.py"}],
        "models": [{"name": "UserModel", "file": "models/user.py"}]
    }
    engine = SymbolSearchEngine(mock_index)

    # Empty query
    res_empty = engine.search("")
    assert res_empty["relevant_files"] == []
    assert "Empty search query" in res_empty["answer_summary"]

    # Whitespace and control character query
    res_ctrl = engine.search("  \x00\x08auth\x1b  ")
    assert len(res_ctrl["matched_functions"]) > 0
    assert res_ctrl["query"] == "auth"

    # Excessively long query (>200 chars)
    long_query = "search_" + "a" * 300
    res_long = engine.search(long_query)
    assert len(res_long["query"]) <= 200


def test_symbol_search_result_limits():
    # Large mock index with 150 functions
    mock_index = {
        "functions": [{"name": f"func_{i}", "file": f"file_{i}.py"} for i in range(150)],
        "classes": [],
        "components": [],
        "routes": [],
        "models": []
    }
    engine = SymbolSearchEngine(mock_index)

    # Default limit should cap results at 50
    res_default = engine.search("func")
    assert len(res_default["matched_functions"]) == 50
    assert len(res_default["relevant_files"]) == 50

    # Custom limit capped at 100
    res_custom = engine.search("func", max_results=80)
    assert len(res_custom["matched_functions"]) == 80

    # Upper bound cap at 100
    res_overflow = engine.search("func", max_results=500)
    assert len(res_overflow["matched_functions"]) <= 100


def test_code_parser_robustness_and_size_guard():
    # 1. Malformed Python syntax should gracefully fallback to regex extraction without raising unhandled exceptions
    malformed_code = """
    def valid_function():
        pass
    def broken_func(
    class BrokenClass:::
    """
    symbols = CodeParser.parse_python(malformed_code, "test.py")
    assert any(f["name"] == "valid_function" for f in symbols["functions"])

    # 2. Oversized file (>2MB) should be safely rejected
    huge_code = "def huge(): pass\n" * 200000
    symbols_huge = CodeParser.parse_python(huge_code, "huge.py")
    assert symbols_huge["functions"] == []

    # 3. TypeScript parsing resilience
    ts_code = """
    import { useState } from 'react';
    export const fetchUserData = async () => {};
    export default function DashboardWidget() { return <div />; }
    class AuthManager {}
    """
    ts_symbols = CodeParser.parse_typescript(ts_code, "src/components/DashboardWidget.tsx")
    assert "react" in ts_symbols["imports"]
    assert any(f["name"] == "fetchUserData" for f in ts_symbols["functions"])
    assert "DashboardWidget" in ts_symbols["components"]
    assert any(c["name"] == "AuthManager" for c in ts_symbols["classes"])


def test_validate_safe_directory():
    # Valid directory
    temp_dir = tempfile.mkdtemp()
    try:
        resolved = validate_safe_directory(temp_dir)
        assert os.path.exists(resolved)

        # Non-existent directory
        with pytest.raises(HTTPException) as exc_info:
            validate_safe_directory(os.path.join(temp_dir, "non_existent_folder_xyz"))
        assert exc_info.value.status_code == 400

        # Null byte in path
        with pytest.raises(HTTPException) as exc_info:
            validate_safe_directory(f"{temp_dir}\0secret")
        assert exc_info.value.status_code == 400
    finally:
        shutil.rmtree(temp_dir)


def test_intelligence_api_endpoints_validation():
    # /api/intelligence/search query parameter bounds
    res_search_valid = client.get("/api/intelligence/search?query=auth")
    assert res_search_valid.status_code == 200

    # /api/intelligence/search empty query should fail validation
    res_search_invalid = client.get("/api/intelligence/search?query=")
    assert res_search_invalid.status_code == 422  # Unprocessable Entity (min_length=1)

    # /api/intelligence/index with invalid directory
    res_index_invalid = client.post("/api/intelligence/index", json={"directory_path": "/non/existent/path/xyz123"})
    assert res_index_invalid.status_code == 400
