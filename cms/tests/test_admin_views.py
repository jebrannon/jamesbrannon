"""
Tests for BrandView and HomepageView admin views.

Covers the can_create / can_delete fix: starlette-admin calls these as
methods — setting them as plain bool attributes caused:
    TypeError: 'bool' object is not callable
They must be proper method overrides that accept a Request argument.
"""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient


# ── Unit: can_create / can_delete are callable methods returning False ─────────

def test_brand_can_create_is_callable():
    from app.admin.views import BrandView
    view = BrandView()
    assert callable(view.can_create), "can_create must be a method, not a bool"


def test_brand_can_create_returns_false():
    from app.admin.views import BrandView
    assert BrandView().can_create(MagicMock()) is False


def test_brand_can_delete_is_callable():
    from app.admin.views import BrandView
    view = BrandView()
    assert callable(view.can_delete), "can_delete must be a method, not a bool"


def test_brand_can_delete_returns_false():
    from app.admin.views import BrandView
    assert BrandView().can_delete(MagicMock()) is False


def test_homepage_can_create_is_callable():
    from app.admin.views import HomepageView
    view = HomepageView()
    assert callable(view.can_create), "can_create must be a method, not a bool"


def test_homepage_can_create_returns_false():
    from app.admin.views import HomepageView
    assert HomepageView().can_create(MagicMock()) is False


def test_homepage_can_delete_is_callable():
    from app.admin.views import HomepageView
    view = HomepageView()
    assert callable(view.can_delete), "can_delete must be a method, not a bool"


def test_homepage_can_delete_returns_false():
    from app.admin.views import HomepageView
    assert HomepageView().can_delete(MagicMock()) is False


# ── Unit: content views still allow create/delete ─────────────────────────────

def test_post_view_can_create_is_true():
    """PostView should still allow creation (default behaviour)."""
    from app.admin.views import PostView
    assert PostView().can_create(MagicMock()) is True


def test_post_view_can_delete_is_true():
    from app.admin.views import PostView
    assert PostView().can_delete(MagicMock()) is True


def test_page_view_can_create_is_true():
    from app.admin.views import PageView
    assert PageView().can_create(MagicMock()) is True


def test_portfolio_view_can_create_is_true():
    from app.admin.views import PortfolioView
    assert PortfolioView().can_create(MagicMock()) is True


# ── Integration: admin list pages return 200 (not 500 TypeError) ──────────────

@pytest.fixture()
def admin_client(aws_mock):
    """
    TestClient authenticated against the admin UI.
    Uses a fresh client (not raise_server_exceptions) so we see real HTTP
    status codes rather than re-raised Python exceptions.
    """
    from app.main import app
    client = TestClient(app, raise_server_exceptions=True, follow_redirects=True)
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "testpass"},
    )
    return client


def test_brand_list_page_returns_200(admin_client):
    """
    Previously crashed with:
        TypeError: 'bool' object is not callable
    because can_delete was set as a class-level bool instead of a method.
    """
    response = admin_client.get("/admin/brand/list")
    assert response.status_code == 200


def test_homepage_list_page_returns_200(admin_client):
    """Same fix as BrandView — HomepageView.can_delete must be a method."""
    response = admin_client.get("/admin/homepage/list")
    assert response.status_code == 200


def test_brand_edit_page_returns_200(admin_client):
    """Edit page for the brand singleton should load without error."""
    response = admin_client.get("/admin/brand/edit/BRAND")
    assert response.status_code == 200


def test_homepage_edit_page_returns_200(admin_client):
    """Edit page for the homepage singleton should load without error."""
    response = admin_client.get("/admin/homepage/edit/HOMEPAGE")
    assert response.status_code == 200


def test_brand_list_has_no_create_button(admin_client):
    """can_create returns False — the Create button must not appear."""
    response = admin_client.get("/admin/brand/list")
    # starlette-admin uses this URL pattern for its create links
    assert "/admin/brand/create" not in response.text


def test_homepage_list_has_no_create_button(admin_client):
    """can_create returns False — the Create button must not appear."""
    response = admin_client.get("/admin/homepage/list")
    assert "/admin/homepage/create" not in response.text


# ── Integration: content admin routes are still accessible ────────────────────

def test_post_admin_list_returns_200(admin_client):
    """PostView list page should still be reachable."""
    response = admin_client.get("/admin/post/list")
    assert response.status_code == 200


def test_page_admin_list_returns_200(admin_client):
    response = admin_client.get("/admin/page/list")
    assert response.status_code == 200


def test_portfolio_admin_list_returns_200(admin_client):
    response = admin_client.get("/admin/portfolio/list")
    assert response.status_code == 200
