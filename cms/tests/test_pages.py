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
