"""
Tests for singleton and content admin views.

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


def test_seo_can_create_is_callable():
    from app.admin.views import SeoView
    view = SeoView()
    assert callable(view.can_create), "can_create must be a method, not a bool"


def test_seo_can_create_returns_false():
    from app.admin.views import SeoView
    assert SeoView().can_create(MagicMock()) is False


def test_seo_can_delete_is_callable():
    from app.admin.views import SeoView
    view = SeoView()
    assert callable(view.can_delete), "can_delete must be a method, not a bool"


def test_seo_can_delete_returns_false():
    from app.admin.views import SeoView
    assert SeoView().can_delete(MagicMock()) is False


def test_profile_can_create_is_callable():
    from app.admin.views import ProfileView
    view = ProfileView()
    assert callable(view.can_create), "can_create must be a method, not a bool"


def test_profile_can_create_returns_false():
    from app.admin.views import ProfileView
    assert ProfileView().can_create(MagicMock()) is False


def test_profile_can_delete_is_callable():
    from app.admin.views import ProfileView
    view = ProfileView()
    assert callable(view.can_delete), "can_delete must be a method, not a bool"


def test_profile_can_delete_returns_false():
    from app.admin.views import ProfileView
    assert ProfileView().can_delete(MagicMock()) is False


# ── Unit: content views still allow create/delete ─────────────────────────────

def test_post_view_can_create_is_true():
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


# ── Integration: admin list and edit pages return 200 ─────────────────────────

@pytest.fixture()
def admin_client(aws_mock):
    """TestClient authenticated against the admin UI."""
    from app.main import app
    client = TestClient(app, raise_server_exceptions=True, follow_redirects=True)
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "testpass"},
    )
    return client


def test_brand_list_page_returns_200(admin_client):
    response = admin_client.get("/admin/brand/list")
    assert response.status_code == 200


def test_brand_edit_page_returns_200(admin_client):
    response = admin_client.get("/admin/brand/edit/BRAND")
    assert response.status_code == 200


def test_brand_list_has_no_create_button(admin_client):
    response = admin_client.get("/admin/brand/list")
    assert "/admin/brand/create" not in response.text


def test_seo_list_page_returns_200(admin_client):
    response = admin_client.get("/admin/seo/list")
    assert response.status_code == 200


def test_seo_edit_page_returns_200(admin_client):
    response = admin_client.get("/admin/seo/edit/SEO")
    assert response.status_code == 200


def test_seo_list_has_no_create_button(admin_client):
    response = admin_client.get("/admin/seo/list")
    assert "/admin/seo/create" not in response.text


def test_profile_list_page_returns_200(admin_client):
    response = admin_client.get("/admin/profile/list")
    assert response.status_code == 200


def test_profile_edit_page_returns_200(admin_client):
    response = admin_client.get("/admin/profile/edit/PROFILE")
    assert response.status_code == 200


def test_profile_list_has_no_create_button(admin_client):
    response = admin_client.get("/admin/profile/list")
    assert "/admin/profile/create" not in response.text


# ── Integration: content admin routes are still accessible ────────────────────

def test_post_admin_list_returns_200(admin_client):
    response = admin_client.get("/admin/post/list")
    assert response.status_code == 200


def test_page_admin_list_returns_200(admin_client):
    response = admin_client.get("/admin/page/list")
    assert response.status_code == 200


def test_portfolio_admin_list_returns_200(admin_client):
    response = admin_client.get("/admin/portfolio/list")
    assert response.status_code == 200
