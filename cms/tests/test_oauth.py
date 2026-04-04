"""Tests for Google OAuth routes (/auth/google, /auth/callback)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_httpx_post(status_code=200, json_body=None):
    """Return a mock httpx response for the token endpoint."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {"access_token": "fake-token"}
    return resp


def _mock_httpx_get(status_code=200, json_body=None):
    """Return a mock httpx response for the userinfo endpoint."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {"email": "james@jamesbrannon.co.uk"}
    return resp


# ── /auth/google ──────────────────────────────────────────────────────────────

def test_oauth_google_redirect_to_google(client):
    """GET /auth/google redirects to Google's consent screen with correct params."""
    import app.main as main_mod
    with patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(main_mod, "_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"):
        resp = client.get("/auth/google", follow_redirects=False)

    assert resp.status_code in (302, 307)
    location = resp.headers["location"]
    assert "accounts.google.com" in location
    assert "test-client-id" in location
    assert "openid" in location
    assert "email" in location


def test_oauth_google_stores_state_in_session(client):
    """GET /auth/google stores a state token in the session."""
    import app.main as main_mod
    with patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(main_mod, "_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"):
        resp = client.get("/auth/google", follow_redirects=False)

    assert resp.status_code in (302, 307)
    # state is embedded in the redirect URL
    location = resp.headers["location"]
    assert "state=" in location


# ── /auth/callback ────────────────────────────────────────────────────────────

def test_oauth_callback_error_param_redirects_to_login(client):
    """Callback with ?error= redirects to login with oauth_failed."""
    resp = client.get("/auth/callback?error=access_denied", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "error=oauth_failed" in resp.headers["location"]


def test_oauth_callback_missing_state_redirects_to_login(client):
    """Callback with no matching state in session redirects to login."""
    resp = client.get("/auth/callback?code=abc&state=bad-state", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert "error=invalid_state" in resp.headers["location"]


def test_oauth_callback_token_failure_redirects_to_login(client):
    """Callback where Google returns a bad token response redirects to login."""
    import app.main as main_mod

    # First prime the session with a valid state
    with patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(main_mod, "_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"):
        redirect_resp = client.get("/auth/google", follow_redirects=False)

    location = redirect_resp.headers["location"]
    state = dict(p.split("=", 1) for p in location.split("?", 1)[1].split("&") if "=" in p).get("state", "")

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_ctx.post = AsyncMock(return_value=_mock_httpx_post(status_code=400, json_body={}))

    with patch("app.main.httpx.AsyncClient", return_value=mock_ctx), \
         patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"):
        resp = client.get(f"/auth/callback?code=abc&state={state}", follow_redirects=False)

    assert resp.status_code in (302, 307)
    assert "error=token_failed" in resp.headers["location"]


def test_oauth_callback_disallowed_domain_redirects_to_login(client):
    """Callback with a non-allowed Google domain redirects to login."""
    import app.main as main_mod

    with patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(main_mod, "_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"):
        redirect_resp = client.get("/auth/google", follow_redirects=False)

    location = redirect_resp.headers["location"]
    state = dict(p.split("=", 1) for p in location.split("?", 1)[1].split("&") if "=" in p).get("state", "")

    token_ctx = MagicMock()
    token_ctx.__aenter__ = AsyncMock(return_value=token_ctx)
    token_ctx.__aexit__ = AsyncMock(return_value=False)
    token_ctx.post = AsyncMock(return_value=_mock_httpx_post())

    userinfo_ctx = MagicMock()
    userinfo_ctx.__aenter__ = AsyncMock(return_value=userinfo_ctx)
    userinfo_ctx.__aexit__ = AsyncMock(return_value=False)
    userinfo_ctx.get = AsyncMock(return_value=_mock_httpx_get(
        json_body={"email": "hacker@evil.com"}
    ))

    ctx_iter = iter([token_ctx, userinfo_ctx])

    with patch("app.main.httpx.AsyncClient", side_effect=ctx_iter), \
         patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(main_mod, "_GOOGLE_ALLOWED_DOMAINS", ["jamesbrannon.co.uk"]):
        resp = client.get(f"/auth/callback?code=abc&state={state}", follow_redirects=False)

    assert resp.status_code in (302, 307)
    assert "error=domain_not_allowed" in resp.headers["location"]


def test_oauth_callback_success_sets_session_and_redirects(client):
    """Successful OAuth callback sets session username and redirects to /admin/."""
    import app.main as main_mod

    with patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(main_mod, "_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"):
        redirect_resp = client.get("/auth/google", follow_redirects=False)

    location = redirect_resp.headers["location"]
    state = dict(p.split("=", 1) for p in location.split("?", 1)[1].split("&") if "=" in p).get("state", "")

    token_ctx = MagicMock()
    token_ctx.__aenter__ = AsyncMock(return_value=token_ctx)
    token_ctx.__aexit__ = AsyncMock(return_value=False)
    token_ctx.post = AsyncMock(return_value=_mock_httpx_post())

    userinfo_ctx = MagicMock()
    userinfo_ctx.__aenter__ = AsyncMock(return_value=userinfo_ctx)
    userinfo_ctx.__aexit__ = AsyncMock(return_value=False)
    userinfo_ctx.get = AsyncMock(return_value=_mock_httpx_get(
        json_body={"email": "james@jamesbrannon.co.uk"}
    ))

    ctx_iter = iter([token_ctx, userinfo_ctx])

    with patch("app.main.httpx.AsyncClient", side_effect=ctx_iter), \
         patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(main_mod, "_GOOGLE_ALLOWED_DOMAINS", ["jamesbrannon.co.uk"]):
        resp = client.get(f"/auth/callback?code=abc&state={state}", follow_redirects=False)

    assert resp.status_code in (302, 307)
    assert resp.headers["location"].rstrip("/") == "/admin"


def test_oauth_callback_allowed_alternate_domain(client):
    """Domains in GOOGLE_ALLOWED_DOMAINS beyond the default are also accepted."""
    import app.main as main_mod

    with patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(main_mod, "_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback"):
        redirect_resp = client.get("/auth/google", follow_redirects=False)

    location = redirect_resp.headers["location"]
    state = dict(p.split("=", 1) for p in location.split("?", 1)[1].split("&") if "=" in p).get("state", "")

    token_ctx = MagicMock()
    token_ctx.__aenter__ = AsyncMock(return_value=token_ctx)
    token_ctx.__aexit__ = AsyncMock(return_value=False)
    token_ctx.post = AsyncMock(return_value=_mock_httpx_post())

    userinfo_ctx = MagicMock()
    userinfo_ctx.__aenter__ = AsyncMock(return_value=userinfo_ctx)
    userinfo_ctx.__aexit__ = AsyncMock(return_value=False)
    userinfo_ctx.get = AsyncMock(return_value=_mock_httpx_get(
        json_body={"email": "james@justjam.es"}
    ))

    ctx_iter = iter([token_ctx, userinfo_ctx])

    with patch("app.main.httpx.AsyncClient", side_effect=ctx_iter), \
         patch.object(main_mod, "_GOOGLE_CLIENT_ID", "test-client-id"), \
         patch.object(main_mod, "_GOOGLE_ALLOWED_DOMAINS", ["jamesbrannon.co.uk", "justjam.es"]):
        resp = client.get(f"/auth/callback?code=abc&state={state}", follow_redirects=False)

    assert resp.status_code in (302, 307)
    assert resp.headers["location"].rstrip("/") == "/admin"
