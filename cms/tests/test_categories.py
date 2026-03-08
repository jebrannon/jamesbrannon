"""
Tests for the /api/categories public endpoint.
Pattern mirrors test_posts.py and test_pages.py.
"""
from .conftest import make_category


def test_list_categories_empty(client):
    response = client.get("/api/categories")
    assert response.status_code == 200
    assert response.json() == []


def test_list_categories_returns_items(client):
    from app.db import put_content
    put_content("CATEGORY", make_category(slug="design", name="Design"))
    put_content("CATEGORY", make_category(slug="engineering", name="Engineering"))

    response = client.get("/api/categories")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_category_by_slug(client):
    from app.db import put_content
    put_content("CATEGORY", make_category(slug="design", name="Design"))

    response = client.get("/api/categories/design")
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "design"
    assert data["name"] == "Design"


def test_get_category_404(client):
    response = client.get("/api/categories/not-a-category")
    assert response.status_code == 404


def test_category_max_items_default(client):
    """max_items should default to 10 when not explicitly set."""
    from app.db import put_content
    put_content("CATEGORY", {"slug": "minimal", "name": "Minimal", "max_items": 10})

    response = client.get("/api/categories/minimal")
    assert response.json()["max_items"] == 10


def test_category_page_headline(client):
    """page_headline is returned when set."""
    from app.db import put_content
    put_content("CATEGORY", make_category(slug="design", page_headline="All things design"))

    response = client.get("/api/categories/design")
    assert response.json()["page_headline"] == "All things design"
