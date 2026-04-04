import hmac
import os
import time
from collections import defaultdict
from typing import Dict, List

from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminConfig, AdminUser, AuthProvider
from starlette_admin.exceptions import LoginFailed

# ── Rate limiting (SimpleAuthProvider only) ────────────────────────────────────

_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 900  # 15 minutes

_failed_attempts: Dict[str, List[float]] = defaultdict(list)


def _is_blocked(ip: str) -> bool:
    """Return True if this IP has too many recent failed login attempts."""
    now = time.time()
    _failed_attempts[ip] = [t for t in _failed_attempts[ip] if now - t < _WINDOW_SECONDS]
    return len(_failed_attempts[ip]) >= _MAX_ATTEMPTS


def _record_failure(ip: str) -> None:
    _failed_attempts[ip].append(time.time())


# ── Username / password provider (local dev fallback) ──────────────────────────

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

        admin_user = os.getenv("ADMIN_USER", "")
        admin_pass = os.getenv("ADMIN_PASS", "")

        user_ok = hmac.compare_digest(username, admin_user)
        pass_ok = hmac.compare_digest(password, admin_pass)
        if user_ok and pass_ok:
            request.session.update({"username": username})
            return response
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


# ── Google OAuth provider ──────────────────────────────────────────────────────

class GoogleOAuthProvider(AuthProvider):
    """
    Auth provider that delegates to Google OAuth 2.0.
    Restricts access to accounts on GOOGLE_ALLOWED_DOMAINS.
    Falls back to showing a "Sign in with Google" button on the login page.
    """

    async def render_login(self, request: Request, admin) -> Response:
        """Override to inject use_google_oauth=True into the login template context."""
        error = request.query_params.get("error")
        error_messages = {
            "oauth_failed": "Google sign-in failed. Please try again.",
            "token_failed": "Could not retrieve access token from Google.",
            "domain_not_allowed": "Your Google account domain is not authorised.",
            "invalid_state": "Invalid OAuth state. Please try again.",
        }
        return admin.templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "_is_login_path": True,
                "use_google_oauth": True,
                "error": error_messages.get(error) if error else None,
            },
        )

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        # Standard form submission is not used with Google OAuth
        raise LoginFailed("Use the Sign in with Google button.")

    async def is_authenticated(self, request: Request) -> bool:
        return bool(request.session.get("username"))

    def get_admin_config(self, request: Request) -> AdminConfig:
        return AdminConfig(app_title="James Brannon CMS")

    def get_admin_user(self, request: Request) -> AdminUser:
        return AdminUser(username=request.session.get("username", ""))

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response
