"""Tests for /api/settings/brand, /api/settings/seo and /api/settings/profile."""


# ── Brand settings ─────────────────────────────────────────────────────────────

def test_brand_returns_empty_when_not_set(client):
    response = client.get("/api/settings/brand")
    assert response.status_code == 200
    assert response.json() == {}


def test_brand_returns_settings_when_set(client):
    from app.db import put_setting
    put_setting("BRAND", {
        "logo_url": "/static/logos/logo.svg",
        "favicon_url": "/static/favicons/favicon.svg",
        "linkedin": "https://linkedin.com/in/jamesbrannon",
        "instagram": "https://instagram.com/jamesbrannon",
        "email": "me@jamesbrannon.co.uk",
    })
    response = client.get("/api/settings/brand")
    assert response.status_code == 200
    data = response.json()
    assert data["logo_url"] == "/static/logos/logo.svg"
    assert data["favicon_url"] == "/static/favicons/favicon.svg"
    assert data["linkedin"] == "https://linkedin.com/in/jamesbrannon"
    assert data["instagram"] == "https://instagram.com/jamesbrannon"
    assert data["email"] == "me@jamesbrannon.co.uk"


def test_brand_logo_url_returned(client):
    """logo_url is included in the brand response when set."""
    from app.db import put_setting
    put_setting("BRAND", {"logo_url": "/static/logos/logo.svg"})
    response = client.get("/api/settings/brand")
    assert response.status_code == 200
    assert response.json()["logo_url"] == "/static/logos/logo.svg"


def test_brand_favicon_url_returned(client):
    """favicon_url is included in the brand response when set."""
    from app.db import put_setting
    put_setting("BRAND", {"favicon_url": "/static/favicons/favicon.svg"})
    response = client.get("/api/settings/brand")
    assert response.status_code == 200
    assert response.json()["favicon_url"] == "/static/favicons/favicon.svg"


def test_brand_partial_settings(client):
    """Partial brand data is returned as-is (no required fields)."""
    from app.db import put_setting
    put_setting("BRAND", {"email": "me@jamesbrannon.co.uk"})
    response = client.get("/api/settings/brand")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@jamesbrannon.co.uk"
    assert "favicon_light_url" not in data


def test_brand_overwrites_on_re_save(client):
    """Saving brand settings twice replaces the previous values."""
    from app.db import put_setting
    put_setting("BRAND", {"email": "old@example.com"})
    put_setting("BRAND", {"email": "new@example.com", "linkedin": "https://linkedin.com/in/jb"})
    response = client.get("/api/settings/brand")
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["linkedin"] == "https://linkedin.com/in/jb"


# ── SEO Metadata settings ──────────────────────────────────────────────────────

def test_seo_returns_empty_when_not_set(client):
    response = client.get("/api/settings/seo")
    assert response.status_code == 200
    assert response.json() == {}


def test_seo_returns_settings_when_set(client):
    from app.db import put_setting
    put_setting("SEO", {
        "seo_title": "James Brannon — Designer & Developer",
        "seo_description": "Portfolio of James Brannon.",
        "og_type": "website",
        "no_index": False,
    })
    response = client.get("/api/settings/seo")
    assert response.status_code == 200
    data = response.json()
    assert data["seo_title"] == "James Brannon — Designer & Developer"
    assert data["seo_description"] == "Portfolio of James Brannon."
    assert data["og_type"] == "website"


def test_seo_all_fields_stored(client):
    """All four SEO fields are correctly stored and retrieved."""
    from app.db import put_setting
    put_setting("SEO", {
        "seo_title": "James Brannon",
        "seo_description": "Portfolio site",
        "site_name": "James Brannon",
        "og_image": "https://jamesbrannon.co.uk/og.jpg",
    })
    response = client.get("/api/settings/seo")
    data = response.json()
    assert data["seo_title"] == "James Brannon"
    assert data["seo_description"] == "Portfolio site"
    assert data["site_name"] == "James Brannon"
    assert data["og_image"] == "https://jamesbrannon.co.uk/og.jpg"


def test_homepage_endpoint_removed(client):
    """The old /api/settings/homepage endpoint no longer exists."""
    response = client.get("/api/settings/homepage")
    assert response.status_code == 404


# ── My Profile settings ────────────────────────────────────────────────────────

def test_profile_returns_empty_when_not_set(client):
    response = client.get("/api/settings/profile")
    assert response.status_code == 200
    assert response.json() == {}


def test_profile_returns_settings_when_set(client):
    from app.db import put_setting
    put_setting("PROFILE", {
        "headline": "Product designer & frontend developer",
        "tagline": "Making things people enjoy using",
        "summary": "Hi, I'm James.",
    })
    response = client.get("/api/settings/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["headline"] == "Product designer & frontend developer"
    assert data["tagline"] == "Making things people enjoy using"
    assert data["summary"] == "Hi, I'm James."


def test_profile_partial_settings(client):
    """Partial profile data is returned as-is."""
    from app.db import put_setting
    put_setting("PROFILE", {"headline": "Designer"})
    response = client.get("/api/settings/profile")
    data = response.json()
    assert data["headline"] == "Designer"
    assert "tagline" not in data


# ── Settings are isolated from each other ─────────────────────────────────────

def test_all_settings_are_independent(client):
    from app.db import put_setting
    put_setting("BRAND", {"email": "me@jamesbrannon.co.uk"})
    put_setting("SEO", {"seo_title": "James Brannon"})
    put_setting("PROFILE", {"headline": "Designer"})

    brand = client.get("/api/settings/brand").json()
    seo = client.get("/api/settings/seo").json()
    profile = client.get("/api/settings/profile").json()

    assert brand.get("email") == "me@jamesbrannon.co.uk"
    assert seo.get("seo_title") == "James Brannon"
    assert profile.get("headline") == "Designer"
    assert "seo_title" not in brand
    assert "email" not in seo
    assert "headline" not in brand
