import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_api_security_response_headers():
    """Verify that every API response includes mandatory OWASP security headers."""
    res = client.get("/")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"


def test_cors_origin_policy():
    """Verify CORS preflight handling for trusted origins."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }
    res = client.options("/", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert res.headers.get("access-control-allow-credentials") == "true"
