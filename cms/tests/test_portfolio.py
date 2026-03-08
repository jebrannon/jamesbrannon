from .conftest import make_portfolio_item


def test_list_portfolio_empty(client):
    response = client.get("/api/portfolio")
    assert response.status_code == 200
    assert response.json() == []


def test_list_all_portfolio_items(client):
    from app.db import put_content
    put_content("PORTFOLIO", make_portfolio_item(slug="project-a"))
    put_content("PORTFOLIO", make_portfolio_item(slug="project-b"))

    response = client.get("/api/portfolio")
    assert len(response.json()) == 2


def test_list_featured_only(client):
    from app.db import put_content
    put_content("PORTFOLIO", make_portfolio_item(slug="featured", featured=True))
    put_content("PORTFOLIO", make_portfolio_item(slug="not-featured", featured=False))

    response = client.get("/api/portfolio?featured=true")
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "featured"


def test_get_portfolio_item(client):
    from app.db import put_content
    put_content("PORTFOLIO", make_portfolio_item(slug="storystream", title="StoryStream"))

    response = client.get("/api/portfolio/storystream")
    assert response.status_code == 200
    assert response.json()["title"] == "StoryStream"


def test_get_portfolio_item_not_found(client):
    response = client.get("/api/portfolio/nonexistent")
    assert response.status_code == 404


def test_portfolio_item_theme_fields(client):
    from app.db import put_content
    put_content("PORTFOLIO", make_portfolio_item(
        slug="themed-work", theme_mode="light", theme_style="thoughts"
    ))

    response = client.get("/api/portfolio/themed-work")
    data = response.json()
    assert data["theme_mode"] == "light"
    assert data["theme_style"] == "thoughts"


def test_portfolio_item_defaults_dark_professional(client):
    from app.db import put_content
    put_content("PORTFOLIO", make_portfolio_item(slug="default-theme"))

    response = client.get("/api/portfolio/default-theme")
    data = response.json()
    assert data["theme_mode"] == "dark"
    assert data["theme_style"] == "professional"


def test_portfolio_sorted_by_date_descending(client):
    """Portfolio items should be returned with the most recent first."""
    from app.db import put_content
    put_content("PORTFOLIO", make_portfolio_item(slug="older", date="2024-01-01"))
    put_content("PORTFOLIO", make_portfolio_item(slug="newer", date="2025-06-01"))

    response = client.get("/api/portfolio")
    slugs = [p["slug"] for p in response.json()]
    assert slugs.index("newer") < slugs.index("older")
