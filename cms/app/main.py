import logging
import os
import secrets as _secrets
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv

load_dotenv()  # Must run before any app-module imports that read os.getenv at module level

import httpx
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.base import BaseAdmin as Admin
from starlette_admin.views import DropDown, Link

from .admin.auth import GoogleOAuthProvider, SimpleAuthProvider
from .admin.views import (
    BlogSettingsView, BrandView, CategoryView, DashboardView,
    PageView, PostView, ProfileView, SeoView, STATIC_DIR,
)
from .db import create_table_if_not_exists
from .routers import categories, pages, posts, settings

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "msg": "%(message)s"}',
)

logger = logging.getLogger(__name__)

ADMIN_TEMPLATES_DIR = Path(__file__).parent / "admin" / "templates"

_DEFAULT_SECRET_KEY = "dev-secret-key-change-in-production"
_SECRET_KEY = os.getenv("SECRET_KEY", _DEFAULT_SECRET_KEY)

# Fail fast if running with the default insecure key outside of local dev.
# Local dev is detected by the presence of DYNAMODB_ENDPOINT (points at moto).
_IS_LOCAL_DEV = bool(os.getenv("DYNAMODB_ENDPOINT"))
if not _IS_LOCAL_DEV and _SECRET_KEY == _DEFAULT_SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set or is using the insecure default. "
        "Set a strong SECRET_KEY in your environment before deploying."
    )

# ── Google OAuth ──────────────────────────────────────────────────────────────
_GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
_GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
_GOOGLE_ALLOWED_DOMAINS = [
    d.strip()
    for d in os.getenv("GOOGLE_ALLOWED_DOMAINS", "jamesbrannon.co.uk").split(",")
    if d.strip()
]
_OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback")
_USE_GOOGLE_OAUTH = bool(_GOOGLE_CLIENT_ID)

_DEV_CREDENTIAL_VALUES = {"", "admin", "changeme"}
_ADMIN_USER = os.getenv("ADMIN_USER", "")
_ADMIN_PASS = os.getenv("ADMIN_PASS", "")
if not _IS_LOCAL_DEV and not _USE_GOOGLE_OAUTH and (
    _ADMIN_USER in _DEV_CREDENTIAL_VALUES or _ADMIN_PASS in _DEV_CREDENTIAL_VALUES
):
    raise RuntimeError(
        "ADMIN_USER and ADMIN_PASS must be set to non-default values outside of local dev."
    )

if not _IS_LOCAL_DEV and not os.getenv("S3_BUCKET"):
    raise RuntimeError(
        "S3_BUCKET must be set in production. "
        "Image uploads will fail without a configured S3 bucket."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table_if_not_exists()
    from .services.image import ensure_s3_bucket_exists
    ensure_s3_bucket_exists()
    yield


app = FastAPI(
    title="James Brannon CMS",
    description="Content API and admin for jamesbrannon.co.uk",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# In production the frontend is served from the same CloudFront distribution,
# so the origin will match. Add the production domain here when deploying.
_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["content-type"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=_SECRET_KEY,
    https_only=not _IS_LOCAL_DEV,
    same_site="strict",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if not _IS_LOCAL_DEV:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── Global error handler ───────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# ── Static files (favicons and other uploaded assets) ─────────────────────────
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── Public content API ────────────────────────────────────────────────────────
app.include_router(posts.router, prefix="/api")
app.include_router(pages.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


# ── Admin UI (/admin) ─────────────────────────────────────────────────────────
_auth_provider = GoogleOAuthProvider() if _USE_GOOGLE_OAUTH else SimpleAuthProvider()

admin = Admin(
    title="James Brannon CMS",
    auth_provider=_auth_provider,
    templates_dir=str(ADMIN_TEMPLATES_DIR),
    index_view=DashboardView(),
    logo_url="/static/admin-logo.svg",
    login_logo_url="/static/admin-logo.svg",
)
admin.add_view(Link(label="Dashboard", icon="fa fa-home", url="/admin/", target="_self"))
admin.add_view(DropDown(
    "Blog",
    icon="fa fa-pencil",
    views=[
        Link(label="New Post", icon="fa fa-plus", url="/admin/post/create", target="_self"),
        PostView(),
        CategoryView(),
        BlogSettingsView(),
    ],
))
admin.add_view(ProfileView())
admin.add_view(PageView())
admin.add_view(SeoView())
admin.add_view(BrandView())
admin.mount_to(app)


# ── Google OAuth routes ───────────────────────────────────────────────────────

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@app.get("/auth/google")
async def oauth_google_redirect(request: Request) -> RedirectResponse:
    """Initiate Google OAuth flow — redirects to Google's consent screen."""
    state = _secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    params = {
        "client_id": _GOOGLE_CLIENT_ID,
        "redirect_uri": _OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return RedirectResponse(url=f"{_GOOGLE_AUTH_URL}?{urlencode(params)}")


@app.get("/auth/callback")
async def oauth_callback(request: Request) -> RedirectResponse:
    """Handle Google OAuth callback — verify state, exchange code, set session."""
    if request.query_params.get("error"):
        return RedirectResponse(url="/admin/login?error=oauth_failed")

    state = request.query_params.get("state")
    if not state or state != request.session.pop("oauth_state", None):
        return RedirectResponse(url="/admin/login?error=invalid_state")

    code = request.query_params.get("code")
    async with httpx.AsyncClient() as http:
        token_resp = await http.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": _GOOGLE_CLIENT_ID,
                "client_secret": _GOOGLE_CLIENT_SECRET,
                "redirect_uri": _OAUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    if token_resp.status_code != 200:
        return RedirectResponse(url="/admin/login?error=token_failed")

    access_token = token_resp.json().get("access_token")
    if not access_token:
        return RedirectResponse(url="/admin/login?error=token_failed")

    async with httpx.AsyncClient() as http:
        userinfo_resp = await http.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if userinfo_resp.status_code != 200:
        return RedirectResponse(url="/admin/login?error=oauth_failed")

    userinfo = userinfo_resp.json()
    email = userinfo.get("email", "")
    domain = email.split("@")[-1] if "@" in email else ""

    if domain not in _GOOGLE_ALLOWED_DOMAINS:
        return RedirectResponse(url="/admin/login?error=domain_not_allowed")

    request.session["username"] = email
    return RedirectResponse(url="/admin/")


@app.post("/api/preview-svg")
async def preview_svg(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """Auth-gated SVG preview — runs dark-mode injection and returns a data URL. Nothing is saved."""
    if not request.session.get("username"):
        return JSONResponse({"error": "Unauthorized"}, status_code=403)

    content = await file.read()
    if not content.lstrip().startswith(b"<"):
        return JSONResponse({"error": "Invalid SVG"}, status_code=400)

    import asyncio, base64
    from .services.image import _inject_dark_mode
    await asyncio.sleep(1)
    processed = _inject_dark_mode(content)
    data_url = "data:image/svg+xml;base64," + base64.b64encode(processed).decode()
    return JSONResponse({"preview": data_url})


@app.post("/api/upload-image")
async def upload_block_image(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """Auth-gated image upload for the block editor media slots."""
    if not request.session.get("username"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    from app.services.image import save_block_image
    content = await file.read()
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if not ext:
        ext = ".jpg"
    url = save_block_image(content, str(uuid.uuid4())[:8], ext)
    return JSONResponse({"url": url})


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
