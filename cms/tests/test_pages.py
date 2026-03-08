from .conftest import make_page


def test_get_page(client):
    from app.db import put_content
    put_content("PAGE", make_page(slug="about", title="About Me"))

    response = client.get("/api/pages/about")
    assert response.status_code == 200
    assert response.json()["title"] == "About Me"


def test_get_page_not_found(client):
    response = client.get("/api/pages/nonexistent")
    assert response.status_code == 404


def test_page_includes_theme_fields(client):
    from app.db import put_content
    put_content("PAGE", make_page(slug="services", theme_mode="light", theme_style="thoughts"))

    response = client.get("/api/pages/services")
    data = response.json()
    assert data["theme_mode"] == "light"
    assert data["theme_style"] == "thoughts"


def test_page_defaults_dark_professional(client):
    from app.db import put_content
    put_content("PAGE", make_page(slug="contact"))

    response = client.get("/api/pages/contact")
    data = response.json()
    assert data["theme_mode"] == "dark"
    assert data["theme_style"] == "professional"


def test_page_body_content(client):
    from app.db import put_content
    put_content("PAGE", make_page(slug="about", body="# About\n\nHello world."))

    response = client.get("/api/pages/about")
    assert "Hello world." in response.json()["body"]


def test_list_pages(client):
    """GET /api/pages should return only published pages by default."""
    from app.db import put_content
    put_content("PAGE", make_page(slug="about"))
    put_content("PAGE", make_page(slug="contact", title="Contact"))

    response = client.get("/api/pages")
    assert response.status_code == 200
    slugs = [p["slug"] for p in response.json()]
    assert "about" in slugs
    assert "contact" in slugs


def test_list_pages_empty(client):
    response = client.get("/api/pages")
    assert response.status_code == 200
    assert response.json() == []


def test_list_pages_returns_only_published_by_default(client):
    """Draft pages must be excluded from the default list response."""
    from app.db import put_content
    put_content("PAGE", make_page(slug="pub", title="Published", published=True))
    put_content("PAGE", make_page(slug="draft", title="Draft", published=False))

    response = client.get("/api/pages")
    slugs = [p["slug"] for p in response.json()]
    assert "pub" in slugs
    assert "draft" not in slugs


def test_list_pages_published_false_returns_drafts(client):
    """GET /api/pages?published=false should return only drafts."""
    from app.db import put_content
    put_content("PAGE", make_page(slug="pub", title="Published", published=True))
    put_content("PAGE", make_page(slug="draft", title="Draft", published=False))

    response = client.get("/api/pages?published=false")
    assert response.status_code == 200
    slugs = [p["slug"] for p in response.json()]
    assert "draft" in slugs
    assert "pub" not in slugs


def test_draft_page_not_returned_by_slug(client):
    """Draft pages must return 404 when fetched by slug."""
    from app.db import put_content
    put_content("PAGE", make_page(slug="about", published=False))
    response = client.get("/api/pages/about")
    assert response.status_code == 404


def test_published_page_returned_by_slug(client):
    """Published pages must be returned when fetched by slug."""
    from app.db import put_content
    put_content("PAGE", make_page(slug="about", published=True))
    response = client.get("/api/pages/about")
    assert response.status_code == 200
    assert response.json()["slug"] == "about"


def test_page_published_field_stored(client):
    """The published field should be persisted to DynamoDB."""
    from app.db import put_content, get_content
    put_content("PAGE", make_page(slug="about", published=False))
    item = get_content("PAGE", "about")
    assert item["published"] is False
