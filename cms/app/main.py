import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.base import BaseAdmin as Admin

from .admin.auth import SimpleAuthProvider
from .admin.views import BrandView, HomepageView, PageView, PortfolioView, PostView, STATIC_DIR

ADMIN_TEMPLATES_DIR = Path(__file__).parent / "admin" / "templates"
from .db import create_table_if_not_exists
from .routers import pages, portfolio, posts, settings

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table_if_not_exists()
    yield


app = FastAPI(
    title="James Brannon CMS",
    description="Content API and admin for jamesbrannon.co.uk",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
)

# ── Static files (favicons and other uploaded assets) ─────────────────────────
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ── Public content API ────────────────────────────────────────────────────────
app.include_router(posts.router, prefix="/api")
app.include_router(pages.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


# ── Admin UI (/admin) ─────────────────────────────────────────────────────────
admin = Admin(
    title="James Brannon CMS",
    auth_provider=SimpleAuthProvider(),
    templates_dir=str(ADMIN_TEMPLATES_DIR),
)
admin.add_view(PostView())
admin.add_view(PageView())
admin.add_view(PortfolioView())
admin.add_view(BrandView())
admin.add_view(HomepageView())
admin.mount_to(app)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
