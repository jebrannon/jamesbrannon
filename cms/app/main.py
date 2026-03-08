import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.base import BaseAdmin as Admin
from starlette_admin.views import DropDown, Link

from .admin.auth import SimpleAuthProvider
from .admin.views import (
    BlogSettingsView, BrandView, CategoryView, DashboardView,
    PageView, PostView, ProfileView, SeoView, STATIC_DIR,
)
from .db import create_table_if_not_exists
from .routers import categories, pages, posts, settings

load_dotenv()

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table_if_not_exists()
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
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=_SECRET_KEY,
)

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
admin = Admin(
    title="James Brannon CMS",
    auth_provider=SimpleAuthProvider(),
    templates_dir=str(ADMIN_TEMPLATES_DIR),
    index_view=DashboardView(),
    logo_url="/static/admin-logo.svg",
    login_logo_url="/static/admin-logo.svg",
)
admin.add_view(Link(label="Dashboard", icon="fa fa-home", url="/admin/", target="_self"))
admin.add_view(DropDown(
    "Blog",
    icon="fa fa-pencil",
    views=[PostView(), CategoryView(), BlogSettingsView()],
))
admin.add_view(ProfileView())
admin.add_view(PageView())
admin.add_view(SeoView())
admin.add_view(BrandView())
admin.mount_to(app)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
