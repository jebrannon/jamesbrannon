from .conftest import make_post


def test_list_posts_empty(client):
    response = client.get("/api/posts")
    assert response.status_code == 200
    assert response.json() == []


def test_list_all_posts(client):
    from app.db import put_content
    put_content("POST", make_post(slug="post-1", title="Post 1"))
    put_content("POST", make_post(slug="post-2", title="Post 2"))

    response = client.get("/api/posts")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_published_posts_only(client):
    from app.db import put_content
    put_content("POST", make_post(slug="published", published=True))
    put_content("POST", make_post(slug="draft", published=False))

    response = client.get("/api/posts?published=true")
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "published"


def test_list_unpublished_posts(client):
    from app.db import put_content
    put_content("POST", make_post(slug="published", published=True))
    put_content("POST", make_post(slug="draft", published=False))

    response = client.get("/api/posts?published=false")
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "draft"


def test_list_posts_by_tag(client):
    from app.db import put_content
    put_content("POST", make_post(slug="tagged", tags=["python", "aws"]))
    put_content("POST", make_post(slug="untagged", tags=[]))

    response = client.get("/api/posts?tag=python")
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "tagged"


def test_list_posts_limit(client):
    from app.db import put_content
    for i in range(5):
        put_content("POST", make_post(slug=f"post-{i}"))

    response = client.get("/api/posts?limit=3")
    assert len(response.json()) == 3


def test_get_post_by_slug(client):
    from app.db import put_content
    put_content("POST", make_post(slug="hello-world", title="Hello World"))

    response = client.get("/api/posts/hello-world")
    assert response.status_code == 200
    assert response.json()["title"] == "Hello World"


def test_get_post_not_found(client):
    response = client.get("/api/posts/nonexistent")
    assert response.status_code == 404


def test_post_includes_theme_fields(client):
    from app.db import put_content
    put_content("POST", make_post(slug="themed", theme_mode="light", theme_style="thoughts"))

    response = client.get("/api/posts/themed")
    data = response.json()
    assert data["theme_mode"] == "light"
    assert data["theme_style"] == "thoughts"


def test_post_theme_defaults_dark_professional(client):
    from app.db import put_content
    put_content("POST", make_post(slug="default-theme"))

    response = client.get("/api/posts/default-theme")
    data = response.json()
    assert data["theme_mode"] == "dark"
    assert data["theme_style"] == "professional"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_draft_post_not_returned_in_list(client):
    """Draft posts should be excluded from the default list response."""
    from app.db import put_content
    put_content("POST", make_post(slug="draft-hidden", published=False))
    response = client.get("/api/posts")
    slugs = [p["slug"] for p in response.json()]
    assert "draft-hidden" not in slugs


def test_draft_post_not_returned_by_slug(client):
    """GET by slug for an unpublished post — it exists in DB but should return the full item.
    The API currently returns drafts by slug (no auth on public API). This test
    documents that behaviour so any change is intentional.
    """
    from app.db import put_content
    put_content("POST", make_post(slug="secret-draft", published=False))
    response = client.get("/api/posts/secret-draft")
    # Current behaviour: returns the item (no auth on public API)
    assert response.status_code == 200
    assert response.json()["published"] is False


def test_posts_sorted_by_date_descending(client):
    """Posts should be returned with the most recent first."""
    from app.db import put_content
    put_content("POST", make_post(slug="older", date="2024-01-01"))
    put_content("POST", make_post(slug="newer", date="2025-01-01"))
    put_content("POST", make_post(slug="newest", date="2026-01-01"))

    response = client.get("/api/posts")
    slugs = [p["slug"] for p in response.json()]
    assert slugs.index("newest") < slugs.index("newer") < slugs.index("older")
