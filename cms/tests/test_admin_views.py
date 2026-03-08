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


# ── Regression: _as_obj wraps dict in SimpleNamespace ────────────────────────

def test_as_obj_returns_namespace_with_attributes():
    """Guards against starlette-admin changing get_pk_value to use dict access."""
    from app.admin.views import _as_obj
    obj = _as_obj({"slug": "test", "title": "Test"})
    assert obj.slug == "test"
    assert obj.title == "Test"


def test_as_obj_deep_wraps_nested_dicts():
    """Nested dicts must also be SimpleNamespace so CollectionField getattr works."""
    from app.admin.views import _as_obj
    obj = _as_obj({"blog": {"headline": "Hi", "limit": 3}})
    # getattr must return the stored value, not a dict method
    assert obj.blog.headline == "Hi"
    assert obj.blog.limit == 3


def test_as_obj_deep_wraps_list_of_dicts():
    """Lists of dicts must have their items wrapped so nested CollectionField works."""
    from app.admin.views import _as_obj
    obj = _as_obj({"strengths": {"headline": "S", "items": [{"name": "X"}]}})
    # The 'items' key must not resolve to dict.items() method
    assert obj.strengths.headline == "S"
    assert obj.strengths.items[0].name == "X"


# ── Integration: admin CRUD persists to DynamoDB ──────────────────────────────

def test_post_create_persists_to_dynamodb(admin_client, aws_mock):
    """Creating a post via admin should make it retrievable from the public API."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "hello-world",
            "title": "Hello World",
            "body": "This is a test post.",
            "published": "on",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "hello-world")
    assert item is not None
    assert item["title"] == "Hello World"
    assert item["slug"] == "hello-world"


def test_post_edit_updates_dynamodb(admin_client, aws_mock):
    """Editing a post via admin should update the stored record."""
    from app.db import get_content, put_content
    put_content("POST", {"slug": "edit-me", "title": "Original", "body": "Old body."})
    admin_client.post(
        "/admin/post/edit/edit-me",
        data={
            "slug": "edit-me",
            "title": "Updated Title",
            "body": "New body.",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "edit-me")
    assert item is not None
    assert item["title"] == "Updated Title"


def test_post_delete_removes_from_dynamodb(admin_client, aws_mock):
    """Deleting a post via admin should remove it from DynamoDB."""
    from app.db import get_content, put_content
    put_content("POST", {"slug": "delete-me", "title": "To Delete", "body": "body."})
    # starlette-admin delete is a batch action at /api/{identity}/action?name=delete&pks=...
    admin_client.get("/admin/api/post/action?name=delete&pks=delete-me")
    assert get_content("POST", "delete-me") is None


def test_profile_edit_persists_to_dynamodb(admin_client, aws_mock):
    """Saving profile settings via admin should persist to DynamoDB."""
    from app.db import get_setting
    admin_client.post(
        "/admin/profile/edit/PROFILE",
        data={
            "headline": "Product designer",
            "tagline": "Making things",
            "summary": "Hi, I'm James.",
            "blog.headline": "Latest writing",
            "blog.category": "thoughts",
            "blog.limit": "3",
            "strengths.headline": "My Strengths",
        },
    )
    item = get_setting("PROFILE")
    assert item is not None
    assert item["headline"] == "Product designer"
    assert item["blog"]["category"] == "thoughts"
    assert item["strengths"]["headline"] == "My Strengths"


def test_profile_strengths_list_persists(admin_client, aws_mock):
    """Saving strength items via admin should persist as a list in DynamoDB."""
    from app.db import get_setting
    admin_client.post(
        "/admin/profile/edit/PROFILE",
        data={
            "headline": "",
            "tagline": "",
            "summary": "",
            "strengths.headline": "Strengths",
            "strengths.items.0.name": "Product Design",
            "strengths.items.0.description": "End-to-end design.",
        },
    )
    item = get_setting("PROFILE")
    assert isinstance(item["strengths"]["items"], list)
    assert item["strengths"]["items"][0]["name"] == "Product Design"


def test_profile_empty_strengths_list(admin_client, aws_mock):
    """Submitting with no strength items should not error."""
    from app.db import get_setting
    admin_client.post(
        "/admin/profile/edit/PROFILE",
        data={"headline": "Hi", "tagline": "", "summary": ""},
    )
    item = get_setting("PROFILE")
    assert item is not None


def test_seo_edit_persists_to_dynamodb(admin_client, aws_mock):
    """Saving SEO settings via admin should persist to DynamoDB."""
    from app.db import get_setting
    admin_client.post(
        "/admin/seo/edit/SEO",
        data={
            "seo_title": "James Brannon",
            "seo_description": "Portfolio site",
            "og_type": "website",
            "no_index": "",
        },
    )
    item = get_setting("SEO")
    assert item is not None
    assert item["seo_title"] == "James Brannon"


# ── Integration: admin authentication ─────────────────────────────────────────

def test_failed_login_returns_error(aws_mock):
    """Wrong credentials should return 400 Bad Request — starlette-admin's login failure response."""
    from app.main import app
    client = TestClient(app, raise_server_exceptions=True, follow_redirects=True)
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrongpassword"},
    )
    assert response.status_code == 400


def test_unauthenticated_admin_access_redirects(aws_mock):
    """Accessing /admin without a session should redirect to login."""
    from app.main import app
    client = TestClient(app, raise_server_exceptions=True, follow_redirects=False)
    response = client.get("/admin/post/list")
    assert response.status_code in (302, 303)


def test_logout_clears_session(aws_mock):
    """After logout, admin pages should redirect to login."""
    from app.main import app
    client = TestClient(app, raise_server_exceptions=True, follow_redirects=True)
    # Login
    client.post("/admin/login", data={"username": "admin", "password": "testpass"})
    # Access a protected page (should work)
    r1 = client.get("/admin/post/list")
    assert r1.status_code == 200
    # Logout
    client.get("/admin/logout")
    # Now access should redirect — use a no-follow client
    client2 = TestClient(app, raise_server_exceptions=True, follow_redirects=False)
    r2 = client2.get("/admin/post/list")
    assert r2.status_code in (302, 303)


# ── Integration: rate limiting ────────────────────────────────────────────────

def test_rate_limiter_blocks_after_max_attempts(aws_mock):
    """After 5 failed login attempts from the same IP, further attempts are rate limited."""
    from app.admin.auth import _failed_attempts
    from app.main import app
    # Clear any state from other tests
    _failed_attempts.clear()
    client = TestClient(app, raise_server_exceptions=True, follow_redirects=True)
    for _ in range(5):
        client.post("/admin/login", data={"username": "admin", "password": "wrong"})
    response = client.post("/admin/login", data={"username": "admin", "password": "wrong"})
    # 6th attempt should be rate-limited
    assert response.status_code == 400
    assert "Too many" in response.text
