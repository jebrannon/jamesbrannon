"""
Tests for singleton and content admin views.

Covers the can_create / can_delete fix: starlette-admin calls these as
methods — setting them as plain bool attributes caused:
    TypeError: 'bool' object is not callable
They must be proper method overrides that accept a Request argument.
"""

import io

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
    from app.admin.auth import _failed_attempts
    from app.main import app
    _failed_attempts.clear()  # Ensure rate limiter doesn't block fixture login
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


# ── List view column restrictions ─────────────────────────────────────────────

def _list_field_names(admin_client, path: str):
    """
    Return the list of field names embedded in the 'var model = {...}' JSON that
    starlette-admin injects into every list page to drive DataTables.

    This is the only reliable way to verify which columns are configured:
    the table `<th>` elements are empty placeholders; the actual column
    headers and data are generated client-side by DataTables from this JSON.
    """
    import json
    response = admin_client.get(path)
    assert response.status_code == 200, f"List page {path} returned {response.status_code}"
    text = response.text
    marker = "var model = "
    start = text.find(marker)
    assert start != -1, "Could not find 'var model = ' in list page — starlette-admin template changed?"
    start += len(marker)
    end = text.find(";</script>", start)
    assert end != -1, "Could not find end of model JSON in list page"
    model_data = json.loads(text[start:end])
    return [f["name"] for f in model_data["fields"]]


def test_post_list_shows_only_expected_columns(admin_client):
    """Post list DataTable must include title, published, category, date and slug."""
    names = _list_field_names(admin_client, "/admin/post/list")
    for name in ("title", "published", "category", "date", "slug"):
        assert name in names, f"Expected column '{name}' missing from post list model"


def test_post_list_excludes_noisy_columns(admin_client):
    """Post list DataTable must not include blocks, excerpt, hero, theme or SEO fields."""
    names = _list_field_names(admin_client, "/admin/post/list")
    for name in (
        "blocks", "excerpt", "hero_image", "hero_image_url", "hero_thumbnail_url",
        "theme_mode", "theme_style",
        "seo_title", "seo_description", "og_image", "og_type",
        "canonical_url", "no_index",
    ):
        assert name not in names, f"Field '{name}' should be excluded from post list model"


def test_page_list_shows_only_expected_columns(admin_client):
    """Page list DataTable must include title, published and slug."""
    names = _list_field_names(admin_client, "/admin/page/list")
    for name in ("title", "published", "slug"):
        assert name in names, f"Expected column '{name}' missing from page list model"


def test_page_list_excludes_noisy_columns(admin_client):
    """Page list DataTable must not include blocks, theme or SEO fields."""
    names = _list_field_names(admin_client, "/admin/page/list")
    for name in (
        "blocks",
        "theme_mode", "theme_style",
        "seo_title", "seo_description", "og_image", "og_type",
        "canonical_url", "no_index",
    ):
        assert name not in names, f"Field '{name}' should be excluded from page list model"


def test_category_list_shows_name_and_slug(admin_client):
    """Category list DataTable must include name and slug."""
    names = _list_field_names(admin_client, "/admin/category/list")
    assert "name" in names, "Expected column 'name' missing from category list model"
    assert "slug" in names, "Expected column 'slug' missing from category list model"


def test_category_list_excludes_noisy_columns(admin_client):
    """Category list DataTable must not include headline, max_items, theme or SEO fields."""
    names = _list_field_names(admin_client, "/admin/category/list")
    for name in (
        "page_headline", "max_items",
        "theme_mode", "theme_style",
        "seo_title", "seo_description", "og_image", "og_type",
        "canonical_url", "no_index",
    ):
        assert name not in names, f"Field '{name}' should be excluded from category list model"


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
            "blocks": "[]",
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
    put_content("POST", {"slug": "edit-me", "title": "Original", "blocks": "[]"})
    admin_client.post(
        "/admin/post/edit/edit-me",
        data={
            "slug": "edit-me",
            "title": "Updated Title",
            "blocks": "[]",
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
    put_content("POST", {"slug": "delete-me", "title": "To Delete", "blocks": "[]"})
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


def test_page_titles_prefixed_with_site_name(admin_client):
    """Every admin page title must start with 'JJ Admin /'."""
    pages = [
        "/admin/",
        "/admin/post/list",
        "/admin/page/list",
        "/admin/category/list",
    ]
    for path in pages:
        response = admin_client.get(path)
        assert response.status_code == 200, f"{path} returned {response.status_code}"
        assert "<title>JJ Admin /" in response.text, \
            f"Browser tab title on {path} does not start with 'JJ Admin /'"


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
    """Blog submenu must be ordered: New Post → Posts → Categories → Settings.

    Uses href positions to avoid false matches against the page <title> and
    breadcrumb which also contain the word 'Posts'.
    """
    response = admin_client.get("/admin/post/list")
    text = response.text
    # href values are unique to nav items — not present in page title/breadcrumbs
    idx_new_post = text.index("/admin/post/create")   # New Post link
    idx_posts    = text.index("/admin/post/list")     # Posts list link
    idx_cats     = text.index("/admin/category/list") # Categories list link
    idx_settings = text.rindex("Settings")            # rindex: last "Settings" is in sidebar
    assert idx_new_post < idx_posts, "New Post link should appear before Posts in Blog submenu"
    assert idx_posts < idx_cats, "Posts should appear before Categories in Blog submenu"
    assert idx_cats < idx_settings, "Categories should appear before Settings in Blog submenu"


def test_sidebar_blog_new_post_link_present(admin_client):
    """New Post quick link must appear in the Blog sidebar submenu."""
    response = admin_client.get("/admin/post/list")
    assert response.status_code == 200
    assert "New Post" in response.text


def test_sidebar_blog_new_post_link_points_to_create(admin_client):
    """New Post quick link must href to the post create form."""
    response = admin_client.get("/admin/post/list")
    assert "/admin/post/create" in response.text


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
    put_content("POST", {"slug": "seo-test", "title": "SEO Test", "blocks": "[]"})
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
            "blocks": "[]",
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
            "blocks": "[]",
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
            "blocks": "[]",
            "published": "on",
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("PAGE", "my-page")
    assert item["published"] is True


# ── Integration: post publish/draft admin ─────────────────────────────────────

def test_post_create_persists_published_flag(admin_client, aws_mock):
    """Creating a post with Published checked should store published=True."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "pub-post",
            "title": "Published Post",
            "blocks": "[]",
            "published": "on",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "pub-post")
    assert item is not None
    assert item["published"] is True


def test_post_create_without_published_stores_draft(admin_client, aws_mock):
    """Creating a post without Published checked should store published=False."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "draft-post",
            "title": "Draft Post",
            "blocks": "[]",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "draft-post")
    assert item is not None
    assert item.get("published") in (False, None)


def test_post_edit_can_publish_draft(admin_client, aws_mock):
    """Editing a draft post with Published checked should update the stored value."""
    from app.db import get_content, put_content
    from .conftest import make_post
    put_content("POST", make_post(slug="upgrade-me", published=False))
    admin_client.post(
        "/admin/post/edit/upgrade-me",
        data={
            "slug": "upgrade-me",
            "title": "Upgraded Post",
            "blocks": "[]",
            "published": "on",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "upgrade-me")
    assert item["published"] is True


def test_post_edit_can_unpublish(admin_client, aws_mock):
    """Editing a published post without Published checked should set published=False."""
    from app.db import get_content, put_content
    from .conftest import make_post
    put_content("POST", make_post(slug="demote-me", published=True))
    admin_client.post(
        "/admin/post/edit/demote-me",
        data={
            "slug": "demote-me",
            "title": "Demoted Post",
            "blocks": "[]",
            # no "published": "on" — unchecked checkbox sends nothing
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "demote-me")
    assert item.get("published") in (False, None)


def test_page_edit_can_unpublish(admin_client, aws_mock):
    """Editing a published page without Published checked should set published=False."""
    from app.db import get_content, put_content
    from .conftest import make_page
    put_content("PAGE", make_page(slug="live-page", published=True))
    admin_client.post(
        "/admin/page/edit/live-page",
        data={
            "slug": "live-page",
            "title": "Live Page",
            "blocks": "[]",
            # no "published": "on" — unpublish
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("PAGE", "live-page")
    assert item.get("published") in (False, None)


# ── UI: publish controls HTML markers ─────────────────────────────────────────

def test_post_create_form_has_published_checkbox(admin_client):
    """Post create form must include the published checkbox (used by publish controls JS)."""
    response = admin_client.get("/admin/post/create")
    assert response.status_code == 200
    assert 'name="published"' in response.text


def test_page_create_form_has_published_checkbox(admin_client):
    """Page create form must include the published checkbox."""
    response = admin_client.get("/admin/page/create")
    assert response.status_code == 200
    assert 'name="published"' in response.text


def test_post_create_form_has_publish_controls_script(admin_client):
    """Post create form must embed the publish controls JS (Save Draft / Publish text)."""
    response = admin_client.get("/admin/post/create")
    assert response.status_code == 200
    assert "Save Draft" in response.text
    assert "Publish" in response.text


def test_post_edit_form_has_publish_controls_script(admin_client, aws_mock):
    """Post edit form must embed the publish controls JS."""
    from app.db import put_content
    from .conftest import make_post
    put_content("POST", make_post(slug="ctrl-test"))
    response = admin_client.get("/admin/post/edit/ctrl-test")
    assert response.status_code == 200
    # Published post shows Unpublish/Update; draft shows Save Draft/Publish
    assert ("Unpublish" in response.text or "Save Draft" in response.text)


def test_post_list_has_status_column_script(admin_client):
    """Post list page must embed the badge JS that renames the Published column to Status."""
    response = admin_client.get("/admin/post/list")
    assert response.status_code == 200
    # The JS that renames "Published" → "Status" must be present in the page source
    assert "Status" in response.text


def test_category_form_has_no_published_checkbox(admin_client):
    """Category create form must NOT have a published checkbox — only posts/pages are publishable.

    Note: the publish_controls.html JS contains the string 'name="published"' as part of a
    querySelector call, so we check for the rendered HTML input id instead.
    """
    response = admin_client.get("/admin/category/create")
    assert response.status_code == 200
    # The actual rendered boolean checkbox has id="published" — categories don't have this field
    assert 'id="published"' not in response.text


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


# ── Tags removed ───────────────────────────────────────────────────────────────

def test_post_create_form_has_no_tags_field(admin_client):
    """Post create form must not contain a tags input."""
    response = admin_client.get("/admin/post/create")
    assert response.status_code == 200
    assert 'name="tags"' not in response.text


# ── Hero image ─────────────────────────────────────────────────────────────────

def _make_jpeg_bytes(width: int = 800, height: int = 600) -> bytes:
    """Create a minimal valid JPEG in memory for testing."""
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(100, 149, 237)).save(buf, "JPEG")
    buf.seek(0)
    return buf.read()


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_hero_image_stored_on_create(admin_client, aws_mock):
    """Uploading a hero image on create should store hero_image_url and hero_thumbnail_url."""
    from app.db import get_content
    jpeg = _make_jpeg_bytes()
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "img-post",
            "title": "Image Post",
            "blocks": "[]",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
        files={"hero_image": ("hero.jpg", io.BytesIO(jpeg), "image/jpeg")},
    )
    item = get_content("POST", "img-post")
    assert item is not None
    assert item.get("hero_image_url", "").endswith("-hero.jpg")
    assert item.get("hero_thumbnail_url", "").endswith("-thumb.jpg")


def test_post_hero_thumbnail_is_1200x630(tmp_path):
    """save_hero_image must produce a thumbnail at exactly 1200×630."""
    from PIL import Image
    import app.services.image as img_mod
    original_dir = img_mod.POST_IMAGES_DIR
    img_mod.POST_IMAGES_DIR = tmp_path
    try:
        img_mod.save_hero_image(_make_jpeg_bytes(2000, 1500), "test-slug", ".jpg")
        thumb = Image.open(tmp_path / "test-slug-thumb.jpg")
        assert thumb.size == (1200, 630)
    finally:
        img_mod.POST_IMAGES_DIR = original_dir


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_hero_prefills_og_image(admin_client, aws_mock):
    """When a hero image is uploaded and og_image is blank, og_image is set to the thumbnail URL."""
    from app.db import get_content
    jpeg = _make_jpeg_bytes()
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "og-auto",
            "title": "OG Test",
            "blocks": "[]",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
        files={"hero_image": ("hero.jpg", io.BytesIO(jpeg), "image/jpeg")},
    )
    item = get_content("POST", "og-auto")
    assert item.get("og_image") == item.get("hero_thumbnail_url")


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_hero_does_not_overwrite_manual_og_image(admin_client, aws_mock):
    """If og_image is manually set, uploading a hero image must not overwrite it."""
    from app.db import get_content
    jpeg = _make_jpeg_bytes()
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "og-manual",
            "title": "OG Manual",
            "blocks": "[]",
            "og_image": "https://example.com/my-og.jpg",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
        files={"hero_image": ("hero.jpg", io.BytesIO(jpeg), "image/jpeg")},
    )
    item = get_content("POST", "og-manual")
    assert item.get("og_image") == "https://example.com/my-og.jpg"


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_without_hero_has_no_image_urls(admin_client, aws_mock):
    """Posts saved without a hero image should have empty/null image URL fields."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "no-hero",
            "title": "No Hero",
            "blocks": "[]",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "no-hero")
    assert item.get("hero_image_url") in (None, "")
    assert item.get("hero_thumbnail_url") in (None, "")


# ── Auto-excerpt ────────────────────────────────────────────────────────────────

@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value="Auto summary."))
def test_post_create_auto_generates_excerpt_when_empty(admin_client, aws_mock):
    """Saving a post without an excerpt calls the LLM and stores the result."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "auto-excerpt",
            "title": "Test",
            "blocks": "[]",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "auto-excerpt")
    assert item["excerpt"] == "Auto summary."


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value="LLM text."))
def test_post_create_keeps_manual_excerpt(admin_client, aws_mock):
    """When excerpt is provided manually, the LLM result is ignored."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "manual-excerpt",
            "title": "Test",
            "blocks": "[]",
            "excerpt": "My own summary.",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "manual-excerpt")
    assert item["excerpt"] == "My own summary."


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_create_llm_failure_does_not_block_save(admin_client, aws_mock):
    """If Ollama is unavailable (returns None), the post still saves cleanly."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "llm-fail",
            "title": "Test",
            "blocks": "[]",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    assert get_content("POST", "llm-fail") is not None


# ── SEO pre-fills ───────────────────────────────────────────────────────────────

@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value="Auto excerpt."))
def test_post_create_prefills_seo_description_from_excerpt(admin_client, aws_mock):
    """seo_description is pre-filled from the (auto-generated) excerpt when blank."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "seo-desc",
            "title": "Test",
            "blocks": "[]",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "seo-desc")
    assert item.get("seo_description") == "Auto excerpt."


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value="Auto excerpt."))
def test_post_create_keeps_manual_seo_description(admin_client, aws_mock):
    """A manually supplied seo_description is never overwritten."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "keep-seo",
            "title": "Test",
            "blocks": "[]",
            "seo_description": "My custom meta.",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "keep-seo")
    assert item.get("seo_description") == "My custom meta."


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_create_prefills_seo_title_from_title(admin_client, aws_mock):
    """seo_title is pre-filled from the post title when left blank."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "seo-title",
            "title": "My Great Post",
            "blocks": "[]",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "seo-title")
    assert item.get("seo_title") == "My Great Post"


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_create_preserves_manual_seo_title(admin_client, aws_mock):
    """A manually supplied seo_title is never overwritten."""
    from app.db import get_content
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "custom-seo-title",
            "title": "My Post",
            "blocks": "[]",
            "seo_title": "Custom SEO Title",
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "custom-seo-title")
    assert item.get("seo_title") == "Custom SEO Title"


# ── Blocks editor ──────────────────────────────────────────────────────────────

def test_post_create_form_has_blocks_field(admin_client):
    """Post create form must include the Alpine.js blocks editor component."""
    response = admin_client.get("/admin/post/create")
    assert response.status_code == 200
    assert "blocksEditor" in response.text, "Block editor JS missing from post create form"


def test_page_create_form_has_blocks_field(admin_client):
    """Page create form must include the Alpine.js blocks editor component."""
    response = admin_client.get("/admin/page/create")
    assert response.status_code == 200
    assert "blocksEditor" in response.text, "Block editor JS missing from page create form"


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_create_with_blocks_persists(admin_client, aws_mock):
    """Blocks JSON is stored on post create."""
    import json
    from app.db import get_content
    blocks = [{"id": "abc123", "text": "<p>Test content.</p>", "media": []}]
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "blocks-test",
            "title": "Blocks Test",
            "blocks": json.dumps(blocks),
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "blocks-test")
    assert item is not None
    assert item["blocks"] == json.dumps(blocks) or json.loads(item["blocks"]) == blocks


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_blocks_xss_stripped_on_save(admin_client, aws_mock):
    """<script> tags and on* attrs in block text are stripped on save."""
    import json
    from app.db import get_content
    xss_blocks = [{"id": "xss1", "text": '<p>Safe</p><script>alert(1)</script>', "media": []}]
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "xss-test",
            "title": "XSS Test",
            "blocks": json.dumps(xss_blocks),
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "xss-test")
    assert item is not None
    stored = json.loads(item["blocks"])
    assert "<script>" not in stored[0]["text"]
    assert "Safe" in stored[0]["text"]


def test_page_create_with_blocks_persists(admin_client, aws_mock):
    """Blocks JSON is stored on page create."""
    import json
    from app.db import get_content
    blocks = [{"id": "p1b2c3", "text": "<p>Page content.</p>", "media": []}]
    admin_client.post(
        "/admin/page/create",
        data={
            "slug": "page-blocks",
            "title": "Page Blocks",
            "blocks": json.dumps(blocks),
            "published": "on",
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("PAGE", "page-blocks")
    assert item is not None
    stored = json.loads(item["blocks"])
    assert stored[0]["text"] == "<p>Page content.</p>"


def test_page_blocks_xss_stripped_on_save(admin_client, aws_mock):
    """XSS is stripped from page block text on save."""
    import json
    from app.db import get_content
    xss_blocks = [{"id": "xss2", "text": '<h2>Title</h2><script>evil()</script>', "media": []}]
    admin_client.post(
        "/admin/page/create",
        data={
            "slug": "page-xss",
            "title": "Page XSS",
            "blocks": json.dumps(xss_blocks),
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("PAGE", "page-xss")
    assert item is not None
    stored = json.loads(item["blocks"])
    assert "<script>" not in stored[0]["text"]
    assert "Title" in stored[0]["text"]


def test_upload_image_endpoint_rejects_unauthenticated(aws_mock):
    """POST /admin/api/upload-image without auth session returns 401."""
    import io
    from app.main import app
    client = TestClient(app, raise_server_exceptions=True, follow_redirects=False)
    jpeg = _make_jpeg_bytes()
    response = client.post(
        "/api/upload-image",
        files={"file": ("test.jpg", io.BytesIO(jpeg), "image/jpeg")},
    )
    assert response.status_code == 401


def test_upload_image_endpoint_stores_file(admin_client, aws_mock, tmp_path):
    """Authenticated upload stores file and returns a /static/... URL."""
    import io
    import app.services.image as img_mod
    original_dir = img_mod.POST_IMAGES_DIR
    img_mod.POST_IMAGES_DIR = tmp_path
    try:
        jpeg = _make_jpeg_bytes()
        response = admin_client.post(
            "/api/upload-image",
            files={"file": ("block.jpg", io.BytesIO(jpeg), "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert data["url"].startswith("/static/post-images/")
    finally:
        img_mod.POST_IMAGES_DIR = original_dir


# ── Multi-media per block ───────────────────────────────────────────────────────

@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_post_block_can_have_multiple_media_items(admin_client, aws_mock):
    """A single block can store and return multiple media items."""
    import json
    from app.db import get_content
    blocks = [
        {
            "id": "multi1",
            "text": "<p>Multi-media block.</p>",
            "media": [
                {"id": "m1", "type": "image", "url": "/static/post-images/a.jpg", "alt": "A", "caption": "First"},
                {"id": "m2", "type": "video", "url": "https://youtube.com/watch?v=xyz", "alt": "", "caption": "Second"},
            ],
        }
    ]
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "multi-media-post",
            "title": "Multi Media",
            "blocks": json.dumps(blocks),
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "multi-media-post")
    assert item is not None
    stored = json.loads(item["blocks"])
    assert len(stored[0]["media"]) == 2
    assert stored[0]["media"][0]["type"] == "image"
    assert stored[0]["media"][1]["type"] == "video"


@patch("app.services.llm.generate_excerpt", new=AsyncMock(return_value=None))
def test_block_media_caption_xss_stripped(admin_client, aws_mock):
    """HTML in media caption and alt fields is stripped on save."""
    import json
    from app.db import get_content
    blocks = [
        {
            "id": "cap1",
            "text": "<p>Hello.</p>",
            "media": [
                {
                    "id": "m1",
                    "type": "image",
                    "url": "/static/post-images/a.jpg",
                    "alt": '<script>evil()</script>plain alt',
                    "caption": '<b>bold</b> caption',
                }
            ],
        }
    ]
    admin_client.post(
        "/admin/post/create",
        data={
            "slug": "media-caption-xss",
            "title": "Media Caption XSS",
            "blocks": json.dumps(blocks),
            "theme_mode": "dark",
            "theme_style": "professional",
            "og_type": "article",
        },
    )
    item = get_content("POST", "media-caption-xss")
    assert item is not None
    stored = json.loads(item["blocks"])
    mi = stored[0]["media"][0]
    assert "<script>" not in mi["alt"]
    assert "<b>" not in mi["caption"]
    assert "plain alt" in mi["alt"]
    assert "bold" in mi["caption"]   # text content preserved, tags stripped


def test_sanitize_blocks_normalizes_legacy_single_media():
    """_sanitize_blocks upgrades old media:{...} to media:[{...}] on save."""
    import json
    from app.admin.views import _sanitize_blocks
    legacy = json.dumps([
        {
            "id": "old1",
            "text": "<p>Legacy.</p>",
            "media": {"type": "image", "url": "/static/old.jpg", "alt": "Old", "caption": ""},
        }
    ])
    result = json.loads(_sanitize_blocks(legacy))
    assert isinstance(result[0]["media"], list)
    assert result[0]["media"][0]["type"] == "image"
    assert result[0]["media"][0]["url"] == "/static/old.jpg"


def test_sanitize_blocks_normalizes_null_media():
    """_sanitize_blocks converts media: null to media: []."""
    import json
    from app.admin.views import _sanitize_blocks
    raw = json.dumps([{"id": "n1", "text": "<p>Hi.</p>", "media": None}])
    result = json.loads(_sanitize_blocks(raw))
    assert result[0]["media"] == []


def test_page_block_can_have_multiple_media_items(admin_client, aws_mock):
    """Pages also support multiple media items per block."""
    import json
    from app.db import get_content
    blocks = [
        {
            "id": "pg1",
            "text": "<p>Page with two images.</p>",
            "media": [
                {"id": "m1", "type": "image", "url": "/static/post-images/p1.jpg", "alt": "One", "caption": ""},
                {"id": "m2", "type": "image", "url": "/static/post-images/p2.jpg", "alt": "Two", "caption": ""},
            ],
        }
    ]
    admin_client.post(
        "/admin/page/create",
        data={
            "slug": "page-multi-media",
            "title": "Page Multi Media",
            "blocks": json.dumps(blocks),
            "published": "on",
            "theme_mode": "dark",
            "theme_style": "professional",
        },
    )
    item = get_content("PAGE", "page-multi-media")
    assert item is not None
    stored = json.loads(item["blocks"])
    assert len(stored[0]["media"]) == 2
    assert stored[0]["media"][0]["url"] == "/static/post-images/p1.jpg"
    assert stored[0]["media"][1]["url"] == "/static/post-images/p2.jpg"
