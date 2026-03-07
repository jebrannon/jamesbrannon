"""Tests for /api/settings/brand and /api/settings/homepage endpoints."""


# ── Brand settings ─────────────────────────────────────────────────────────────

def test_brand_returns_empty_when_not_set(client):
    response = client.get("/api/settings/brand")
    assert response.status_code == 200
    assert response.json() == {}


def test_brand_returns_settings_when_set(client):
    from app.db import put_setting
    put_setting("BRAND", {
        "favicon_light_url": "/static/favicons/favicon-light.svg",
        "favicon_dark_url": "/static/favicons/favicon-dark.svg",
        "linkedin": "https://linkedin.com/in/jamesbrannon",
        "instagram": "https://instagram.com/jamesbrannon",
        "email": "me@jamesbrannon.co.uk",
    })
    response = client.get("/api/settings/brand")
    assert response.status_code == 200
    data = response.json()
    assert data["favicon_light_url"] == "/static/favicons/favicon-light.svg"
    assert data["favicon_dark_url"] == "/static/favicons/favicon-dark.svg"
    assert data["linkedin"] == "https://linkedin.com/in/jamesbrannon"
    assert data["instagram"] == "https://instagram.com/jamesbrannon"
    assert data["email"] == "me@jamesbrannon.co.uk"


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


# ── Homepage settings ──────────────────────────────────────────────────────────

def test_homepage_returns_empty_when_not_set(client):
    response = client.get("/api/settings/homepage")
    assert response.status_code == 200
    assert response.json() == {}


def test_homepage_returns_settings_when_set(client):
    from app.db import put_setting
    put_setting("HOMEPAGE", {
        "tagline": "Design-led engineering",
        "bio": "Hi, I'm James.",
        "cta_text": "View my work",
        "cta_url": "/work",
        "seo_title": "James Brannon — Designer & Developer",
        "seo_description": "Portfolio of James Brannon.",
        "og_type": "website",
        "no_index": False,
    })
    response = client.get("/api/settings/homepage")
    assert response.status_code == 200
    data = response.json()
    assert data["tagline"] == "Design-led engineering"
    assert data["cta_url"] == "/work"
    assert data["seo_title"] == "James Brannon — Designer & Developer"
    assert data["og_type"] == "website"


def test_homepage_seo_fields_stored(client):
    """All SEO fields are correctly stored and retrieved."""
    from app.db import put_setting
    put_setting("HOMEPAGE", {
        "seo_title": "James Brannon",
        "seo_description": "Portfolio site",
        "og_image": "https://jamesbrannon.co.uk/og.jpg",
        "og_type": "website",
        "canonical_url": "https://jamesbrannon.co.uk/",
        "no_index": False,
    })
    response = client.get("/api/settings/homepage")
    data = response.json()
    assert data["og_image"] == "https://jamesbrannon.co.uk/og.jpg"
    assert data["canonical_url"] == "https://jamesbrannon.co.uk/"
    assert data["no_index"] is False


def test_homepage_no_index_true(client):
    from app.db import put_setting
    put_setting("HOMEPAGE", {"no_index": True})
    response = client.get("/api/settings/homepage")
    assert response.json()["no_index"] is True


# ── Settings are isolated between each other ───────────────────────────────────

def test_brand_and_homepage_are_independent(client):
    from app.db import put_setting
    put_setting("BRAND", {"email": "me@jamesbrannon.co.uk"})
    put_setting("HOMEPAGE", {"tagline": "Hello world"})

    brand = client.get("/api/settings/brand").json()
    homepage = client.get("/api/settings/homepage").json()

    assert brand.get("email") == "me@jamesbrannon.co.uk"
    assert homepage.get("tagline") == "Hello world"
    assert "tagline" not in brand
    assert "email" not in homepage
