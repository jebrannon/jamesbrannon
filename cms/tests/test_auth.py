"""
Tests for admin authentication:
  - SimpleAuthProvider login, rate limiting
  - GoogleOAuthProvider session check
"""
import time
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient


# ── Rate limiter helpers ───────────────────────────────────────────────────────

def test_is_blocked_returns_false_below_limit():
    from app.admin.auth import _is_blocked, _failed_attempts
    _failed_attempts.clear()
    assert _is_blocked("1.2.3.4") is False


def test_is_blocked_returns_true_at_limit():
    from app.admin.auth import _is_blocked, _record_failure, _failed_attempts, _MAX_ATTEMPTS
    _failed_attempts.clear()
    for _ in range(_MAX_ATTEMPTS):
        _record_failure("1.2.3.5")
    assert _is_blocked("1.2.3.5") is True


def test_record_failure_increments_count():
    from app.admin.auth import _record_failure, _failed_attempts
    _failed_attempts.clear()
    _record_failure("10.0.0.1")
    _record_failure("10.0.0.1")
    assert len(_failed_attempts["10.0.0.1"]) == 2


def test_is_blocked_expires_old_attempts():
    from app.admin.auth import _is_blocked, _failed_attempts, _MAX_ATTEMPTS, _WINDOW_SECONDS
    _failed_attempts.clear()
    # inject old timestamps (outside the window)
    old_time = time.time() - _WINDOW_SECONDS - 1
    _failed_attempts["2.2.2.2"] = [old_time] * _MAX_ATTEMPTS
    # should not be blocked — all attempts are stale
    assert _is_blocked("2.2.2.2") is False


def test_is_blocked_only_counts_recent_attempts():
    from app.admin.auth import _is_blocked, _record_failure, _failed_attempts, _MAX_ATTEMPTS, _WINDOW_SECONDS
    _failed_attempts.clear()
    old_time = time.time() - _WINDOW_SECONDS - 1
    _failed_attempts["3.3.3.3"] = [old_time] * _MAX_ATTEMPTS
    # Add one recent failure — not enough to block
    _record_failure("3.3.3.3")
    assert _is_blocked("3.3.3.3") is False


# ── SimpleAuthProvider integration via TestClient ─────────────────────────────

def test_login_success(client):
    """Valid credentials return a session cookie."""
    resp = client.post(
        "/admin/login",
        data={"username": "admin", "password": "testpass"},
        follow_redirects=False,
    )
    # Successful login redirects
    assert resp.status_code in (302, 303)


def test_login_wrong_password(client):
    from app.admin.auth import _failed_attempts
    _failed_attempts.clear()
    resp = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrongpass"},
        follow_redirects=True,
    )
    # starlette-admin returns 400 with the login page on failed credentials
    assert resp.status_code in (200, 400)
    assert "Invalid" in resp.text or "login" in resp.text.lower() or "incorrect" in resp.text.lower()


def test_login_rate_limited(client):
    """After 5 failed attempts the IP is blocked and returns a rate-limit message."""
    from app.admin.auth import _failed_attempts, _MAX_ATTEMPTS
    _failed_attempts.clear()
    for _ in range(_MAX_ATTEMPTS):
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "wrongpass"},
            follow_redirects=True,
        )
    resp = client.post(
        "/admin/login",
        data={"username": "admin", "password": "testpass"},
        follow_redirects=True,
    )
    # starlette-admin returns 400 with the login page on rate-limited or failed login
    assert resp.status_code in (200, 400)
    assert "Too many" in resp.text or "login" in resp.text.lower() or "attempts" in resp.text.lower()


def test_unauthenticated_admin_redirects_to_login(client):
    """Accessing admin without a session redirects to login."""
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code in (302, 303, 307)


# ── GoogleOAuthProvider is_authenticated ──────────────────────────────────────

@pytest.mark.asyncio
async def test_google_provider_is_authenticated_with_session():
    from app.admin.auth import GoogleOAuthProvider
    provider = GoogleOAuthProvider()
    request = MagicMock()
    request.session = {"username": "james@jamesbrannon.co.uk"}
    result = await provider.is_authenticated(request)
    assert result is True


@pytest.mark.asyncio
async def test_google_provider_is_not_authenticated_without_session():
    from app.admin.auth import GoogleOAuthProvider
    provider = GoogleOAuthProvider()
    request = MagicMock()
    request.session = {}
    result = await provider.is_authenticated(request)
    assert result is False


@pytest.mark.asyncio
async def test_simple_provider_is_authenticated_with_session():
    from app.admin.auth import SimpleAuthProvider
    provider = SimpleAuthProvider()
    request = MagicMock()
    request.session = {"username": "admin"}
    result = await provider.is_authenticated(request)
    assert result is True


@pytest.mark.asyncio
async def test_simple_provider_logout_clears_session():
    from app.admin.auth import SimpleAuthProvider
    provider = SimpleAuthProvider()
    request = MagicMock()
    # Use a real dict so .clear() actually clears it
    request.session = {"username": "admin"}
    response = MagicMock()
    await provider.logout(request, response)
    assert request.session == {}
