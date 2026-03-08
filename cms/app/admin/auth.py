import hmac
import os
import time
from collections import defaultdict
from typing import Dict, List

from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import LoginFailed

# ── Rate limiting ──────────────────────────────────────────────────────────────

_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 900  # 15 minutes

_failed_attempts: Dict[str, List[float]] = defaultdict(list)


def _is_blocked(ip: str) -> bool:
    """Return True if this IP has too many recent failed login attempts."""
    now = time.time()
    _failed_attempts[ip] = [t for t in _failed_attempts[ip] if now - t < _WINDOW_SECONDS]
    return len(_failed_attempts[ip]) >= _MAX_ATTEMPTS


def _record_failure(ip: str) -> None:
    """Record a failed login attempt for rate-limiting purposes."""
    _failed_attempts[ip].append(time.time())


# ── Auth provider ──────────────────────────────────────────────────────────────

class SimpleAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        ip = request.client.host if request.client else "unknown"
        if _is_blocked(ip):
            raise LoginFailed("Too many login attempts. Please try again later.")

        admin_user = os.getenv("ADMIN_USER", "admin")
        admin_pass = os.getenv("ADMIN_PASS", "changeme")

        # Constant-time comparison prevents timing attacks
        user_ok = hmac.compare_digest(username, admin_user)
        pass_ok = hmac.compare_digest(password, admin_pass)
        if user_ok and pass_ok:
            request.session.update({"username": username})
            return response
        # Only count failed attempts toward the rate limit
        _record_failure(ip)
        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request: Request) -> bool:
        return bool(request.session.get("username"))

    def get_admin_config(self, request: Request) -> AdminConfig:
        return AdminConfig(app_title="James Brannon CMS")

    def get_admin_user(self, request: Request) -> AdminUser:
        return AdminUser(username=request.session.get("username", ""))

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response
