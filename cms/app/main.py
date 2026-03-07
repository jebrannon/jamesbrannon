import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette_admin.base import BaseAdmin as Admin

from .admin.auth import SimpleAuthProvider
from .admin.views import PageView, PortfolioView, PostView
from .db import create_table_if_not_exists
from .routers import pages, portfolio, posts

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

# ── Public content API ────────────────────────────────────────────────────────
app.include_router(posts.router, prefix="/api")
app.include_router(pages.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")


# ── Admin UI (/admin) ─────────────────────────────────────────────────────────
admin = Admin(
    title="James Brannon CMS",
    auth_provider=SimpleAuthProvider(),
)
admin.add_view(PostView())
admin.add_view(PageView())
admin.add_view(PortfolioView())
admin.mount_to(app)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
