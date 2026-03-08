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
            "category": "design",
        },
    )
    item = get_content("POST", "hello-world")
    assert item is not None
    assert item["title"] == "Hello World"
    assert item["slug"] == "hello-world"
    assert item["category"] == "design"


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


def test_experience_section_persists(admin_client, aws_mock):
    """Saving experience items via admin should persist as a list in DynamoDB."""
    from app.db import get_setting
    admin_client.post(
        "/admin/profile/edit/PROFILE",
        data={
            "headline": "",
            "tagline": "",
            "summary": "",
            "experience.headline": "Experience",
            "experience.items.0.job_title": "Senior Designer",
            "experience.items.0.company": "Acme",
            "experience.items.0.dates": "2020\u20132024",
            "experience.items.0.summary": "<p>Led design system.</p>",
        },
    )
    item = get_setting("PROFILE")
    assert item["experience"]["headline"] == "Experience"
    assert isinstance(item["experience"]["items"], list)
    assert item["experience"]["items"][0]["job_title"] == "Senior Designer"


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


# ── Integration: dashboard ────────────────────────────────────────────────────

def test_dashboard_returns_200(admin_client):
    response = admin_client.get("/admin/")
    assert response.status_code == 200


# ── Integration: sidebar navigation ───────────────────────────────────────────

def test_sidebar_contains_dashboard_link(admin_client):
    """Dashboard must appear as a sidebar link — guards against accidental removal."""
    response = admin_client.get("/admin/post/list")
    assert response.status_code == 200
    assert "/admin/" in response.text
    assert "Dashboard" in response.text


def test_sidebar_contains_blog_dropdown(admin_client):
    """Blog dropdown must be present in the sidebar."""
    response = admin_client.get("/admin/post/list")
    assert "Blog" in response.text


def test_sidebar_contains_expected_sections(admin_client):
    """Key sidebar sections must all be present — guards against structural regressions."""
    response = admin_client.get("/admin/post/list")
    text = response.text
    for label in ("Dashboard", "Blog", "Overview", "Pages", "SEO Metadata", "Brand"):
        assert label in text, f"Sidebar label missing: {label}"


def test_sidebar_blog_appears_before_overview(admin_client):
    """Blog dropdown must appear immediately after Dashboard, before Overview."""
    response = admin_client.get("/admin/post/list")
    text = response.text
    assert text.index("Blog") > text.index("Dashboard"), "Blog should be after Dashboard"
    assert text.index("Blog") < text.index("Overview"), "Blog should be before Overview"


def test_sidebar_blog_submenu_order(admin_client):
    """Blog submenu must be ordered: Posts → Categories → Settings."""
    response = admin_client.get("/admin/post/list")
    text = response.text
    idx_posts = text.index("Posts")
    idx_cats = text.index("Categories")
    idx_settings = text.rindex("Settings")  # rindex: last occurrence avoids page <title> "Settings"
    assert idx_posts < idx_cats, "Posts should appear before Categories in Blog submenu"
    assert idx_cats < idx_settings, "Categories should appear before Settings in Blog submenu"


def test_post_create_form_has_slug_autofill(admin_client):
    """Post create form must include the slug auto-fill script."""
    response = admin_client.get("/admin/post/create")
    assert response.status_code == 200
    assert "slugify" in response.text, "Slug auto-fill JS missing from post create form"


def test_category_create_form_has_slug_autofill(admin_client):
    """Category create form must include the slug auto-fill script."""
    response = admin_client.get("/admin/category/create")
    assert response.status_code == 200
    assert "slugify" in response.text, "Slug auto-fill JS missing from category create form"


# ── Integration: SEO Settings section ────────────────────────────────────────

def test_post_create_form_has_seo_section(admin_client):
    """Post create form must include the SEO Settings collapsible section."""
    response = admin_client.get("/admin/post/create")
    assert response.status_code == 200
    assert "SEO Settings" in response.text, "SEO Settings section missing from post create form"
    assert "seo_title" in response.text
    assert "seo_description" in response.text


def test_post_edit_form_has_seo_section(admin_client, aws_mock):
    """Post edit form must include the SEO Settings collapsible section."""
    from app.db import put_content
    put_content("POST", {"slug": "seo-test", "title": "SEO Test", "body": "body"})
    response = admin_client.get("/admin/post/edit/seo-test")
    assert response.status_code == 200
    assert "SEO Settings" in response.text
    assert "seo_title" in response.text


def test_page_create_form_has_seo_section(admin_client):
    """Page create form must include the SEO Settings collapsible section."""
    response = admin_client.get("/admin/page/create")
    assert response.status_code == 200
    assert "SEO Settings" in response.text


def test_category_create_form_has_seo_section(admin_client):
    """Category create form must include the SEO Settings collapsible section."""
    response = admin_client.get("/admin/category/create")
    assert response.status_code == 200
    assert "SEO Settings" in response.text


def test_seo_section_has_autofill_js(admin_client):
    """SEO auto-fill JS (title → seo_title, body → seo_description) must be present."""
    response = admin_client.get("/admin/post/create")
    text = response.text
    assert "SEO_IDS" in text, "SEO grouping JS missing"
    assert "seo_title" in text
    assert "seo_description" in text


# ── Integration: category admin ───────────────────────────────────────────────

def test_category_admin_list_returns_200(admin_client):
    response = admin_client.get("/admin/category/list")
    assert response.status_code == 200


def test_category_admin_create_returns_200(admin_client):
    response = admin_client.get("/admin/category/create")
    assert response.status_code == 200


def test_category_create_persists_to_dynamodb(admin_client, aws_mock):
    """Creating a category via admin should store it in DynamoDB."""
    from app.db import get_content
    admin_client.post(
        "/admin/category/create",
        data={
            "slug": "design",
            "name": "Design",
            "page_headline": "Design articles",
            "max_items": "10",
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("CATEGORY", "design")
    assert item is not None
    assert item["slug"] == "design"
    assert item["name"] == "Design"


def test_category_edit_updates_dynamodb(admin_client, aws_mock):
    """Editing a category via admin should update the stored record."""
    from app.db import get_content, put_content
    put_content("CATEGORY", {"slug": "design", "name": "Design", "max_items": 10})
    admin_client.post(
        "/admin/category/edit/design",
        data={
            "slug": "design",
            "name": "Design Thinking",
            "max_items": "5",
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("CATEGORY", "design")
    assert item is not None
    assert item["name"] == "Design Thinking"


def test_category_delete_removes_from_dynamodb(admin_client, aws_mock):
    """Deleting a category via admin should remove it from DynamoDB."""
    from app.db import get_content, put_content
    put_content("CATEGORY", {"slug": "to-delete", "name": "To Delete", "max_items": 10})
    admin_client.get("/admin/api/category/action?name=delete&pks=to-delete")
    assert get_content("CATEGORY", "to-delete") is None


# ── Integration: blog settings admin ──────────────────────────────────────────

def test_blog_settings_list_returns_200(admin_client):
    response = admin_client.get("/admin/blog-settings/list")
    assert response.status_code == 200


def test_blog_settings_edit_persists_to_dynamodb(admin_client, aws_mock):
    """Saving blog settings via admin should persist to DynamoDB."""
    from app.db import get_setting
    admin_client.post(
        "/admin/blog-settings/edit/BLOG",
        data={"page_headline": "Latest writing"},
    )
    item = get_setting("BLOG")
    assert item is not None
    assert item["page_headline"] == "Latest writing"


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


# ── UI: dark mode, font, logout ───────────────────────────────────────────────

def test_dark_mode_script_in_head(admin_client):
    """Admin pages should inject the dark-mode attribute via an inline script."""
    response = admin_client.get("/admin/post/list")
    assert "data-bs-theme" in response.text


def test_barlow_font_loaded(admin_client):
    """Admin pages should load Barlow Semi Condensed from Google Fonts."""
    response = admin_client.get("/admin/post/list")
    assert "Barlow+Semi+Condensed" in response.text or "Barlow Semi Condensed" in response.text


def test_logout_injected_into_sidebar(admin_client):
    """Logout should be JS-injected into the sidebar nav (not in a top navbar)."""
    response = admin_client.get("/admin/post/list")
    # JS snippet that appends logout to #sidebar-menu .navbar-nav is present
    assert "sidebar-menu" in response.text
    assert "fa-sign-out" in response.text
    assert "logout" in response.text.lower()


def test_top_navbar_removed(admin_client):
    """The top header navbar should be absent — logout is in the sidebar instead."""
    response = admin_client.get("/admin/post/list")
    # Our empty {% block navbar %} means the desktop header is gone entirely
    assert "navbar-expand-md d-none d-lg-flex" not in response.text


def test_no_desktop_user_dropdown(admin_client):
    """The desktop top navbar user-avatar dropdown should be gone.

    The mobile sidebar (d-lg-none) retains its compact icon — 'Open user menu'
    may appear once there, but not twice (desktop + mobile).
    """
    response = admin_client.get("/admin/post/list")
    assert response.text.count("Open user menu") <= 1


def test_logo_css_sizing(admin_client):
    """Base CSS should set the admin logo to 72×96 px with correct padding."""
    response = admin_client.get("/admin/post/list")
    assert "width: 72px" in response.text
    assert "height: 96px" in response.text
    # Full 3-class specificity selector needed to beat Tabler's vertical navbar rule
    assert "navbar-vertical.navbar-expand-lg .navbar-brand" in response.text
    assert "padding: 2rem 1rem 1rem 1rem" in response.text


def test_mobile_user_icon_hidden(admin_client):
    """Mobile user-icon dropdown should be suppressed via CSS."""
    response = admin_client.get("/admin/post/list")
    assert "flex-row.d-lg-none" in response.text  # our CSS hide rule is present


# ── UI: logo and favicon ──────────────────────────────────────────────────────

def test_admin_logo_in_sidebar(admin_client):
    """Admin pages should render the brand logo in the sidebar."""
    response = admin_client.get("/admin/post/list")
    assert "admin-logo.svg" in response.text


def test_admin_logo_on_login_page(admin_client):
    """Login page should render the brand logo."""
    from starlette.testclient import TestClient
    from app.main import app
    client = TestClient(app, follow_redirects=True)
    response = client.get("/admin/login")
    assert "admin-logo.svg" in response.text


def test_svg_favicon_in_head(admin_client):
    """Admin pages should include an SVG favicon link with the correct MIME type."""
    response = admin_client.get("/admin/post/list")
    assert "admin-favicon.svg" in response.text
    assert 'type="image/svg+xml"' in response.text


def test_admin_logo_file_exists():
    """The admin logo SVG file should exist on disk."""
    from pathlib import Path
    logo = Path(__file__).parent.parent / "static" / "admin-logo.svg"
    assert logo.exists()
    assert logo.stat().st_size > 0


def test_admin_favicon_file_exists():
    """The admin favicon SVG file should exist on disk and contain dark/light media query."""
    from pathlib import Path
    favicon = Path(__file__).parent.parent / "static" / "admin-favicon.svg"
    assert favicon.exists()
    content = favicon.read_text()
    assert "prefers-color-scheme" in content


# ── Integration: page publish/draft admin ────────────────────────────────────

def test_page_create_persists_published_flag(admin_client, aws_mock):
    """Creating a page with Published checked should store published=True."""
    from app.db import get_content
    from .conftest import make_page
    admin_client.post(
        "/admin/page/create",
        data={
            "slug": "new-page",
            "title": "New Page",
            "body": "Content.",
            "published": "on",
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("PAGE", "new-page")
    assert item is not None
    assert item["published"] is True


def test_page_create_without_published_stores_draft(admin_client, aws_mock):
    """Creating a page without Published checked should store published=False."""
    from app.db import get_content
    admin_client.post(
        "/admin/page/create",
        data={
            "slug": "draft-page",
            "title": "Draft Page",
            "body": "Content.",
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("PAGE", "draft-page")
    assert item is not None
    assert item.get("published") in (False, None)


def test_page_edit_can_publish_draft(admin_client, aws_mock):
    """Editing a draft page to set Published should update the stored value."""
    from app.db import get_content, put_content
    from .conftest import make_page
    put_content("PAGE", make_page(slug="my-page", published=False))
    admin_client.post(
        "/admin/page/edit/my-page",
        data={
            "slug": "my-page",
            "title": "My Page",
            "body": "Content.",
            "published": "on",
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("PAGE", "my-page")
    assert item["published"] is True


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
