import os
import shutil
import tempfile
import pytest
from fastapi import HTTPException
from apps.api.main import validate_github_params, sanitize_github_error_detail
from intelligence.indexing.code_indexer import CodeIndexer


def test_github_params_security_validation():
    # Valid params
    validate_github_params("vercel", "next.js")
    validate_github_params("ktilak12", "Ai-developers-OS", "apps/api/main.py")

    # Path traversal in owner
    with pytest.raises(HTTPException) as exc_info:
        validate_github_params("../evil", "repo")
    assert exc_info.value.status_code == 400

    # Path traversal in repo
    with pytest.raises(HTTPException) as exc_info:
        validate_github_params("owner", "../../etc/passwd")
    assert exc_info.value.status_code == 400

    # Path traversal in path
    with pytest.raises(HTTPException) as exc_info:
        validate_github_params("owner", "repo", "../../../secret.json")
    assert exc_info.value.status_code == 400

    # Null byte injection in path
    with pytest.raises(HTTPException) as exc_info:
        validate_github_params("owner", "repo", "main.py\0.jpg")
    assert exc_info.value.status_code == 400


def test_token_masking_in_error_details():
    raw_error = "Failed with Bearer ghp_1234567890abcdefghijklmnopqrstuvwxyz and token github_pat_11AAAAAA00000000000000000000000000"
    sanitized = sanitize_github_error_detail(raw_error)
    assert "ghp_" not in sanitized
    assert "github_pat_" not in sanitized
    assert "[REDACTED" in sanitized


def test_code_indexer_directory_jail_and_sensitive_file_shielding():
    temp_dir = tempfile.mkdtemp()
    try:
        # Create normal code file
        code_file = os.path.join(temp_dir, "app.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write("def hello():\n    return 'world'\n")

        # Create sensitive secret file
        secret_file = os.path.join(temp_dir, ".env")
        with open(secret_file, "w", encoding="utf-8") as f:
            f.write("DATABASE_PASSWORD=super_secret_password\n")

        # Create oversized mock file (3MB)
        large_file = os.path.join(temp_dir, "large_generated.py")
        with open(large_file, "w", encoding="utf-8") as f:
            f.write("# comment\n" * 300000)

        indexer = CodeIndexer(temp_dir)
        index = indexer.scan_and_index()

        # Should index app.py
        assert "app.py" in index["file_symbols_map"]

        # Should NOT index .env (sensitive file shield)
        assert ".env" not in index["file_symbols_map"]

        # Should NOT index large_generated.py (exceeds 2MB cap)
        assert "large_generated.py" not in index["file_symbols_map"]
    finally:
        shutil.rmtree(temp_dir)
