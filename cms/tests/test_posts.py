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
    """Draft posts must return 404 when fetched by slug — they are invisible on the public API."""
    from app.db import put_content
    put_content("POST", make_post(slug="secret-draft", published=False))
    response = client.get("/api/posts/secret-draft")
    assert response.status_code == 404


def test_posts_sorted_by_date_descending(client):
    """Posts should be returned with the most recent first."""
    from app.db import put_content
    put_content("POST", make_post(slug="older", date="2024-01-01"))
    put_content("POST", make_post(slug="newer", date="2025-01-01"))
    put_content("POST", make_post(slug="newest", date="2026-01-01"))

    response = client.get("/api/posts")
    slugs = [p["slug"] for p in response.json()]
    assert slugs.index("newest") < slugs.index("newer") < slugs.index("older")


def test_post_has_category_field(client):
    """Creating a post with a category slug stores and returns it."""
    from app.db import put_content
    put_content("POST", make_post(slug="categorised", category="design"))

    response = client.get("/api/posts/categorised")
    assert response.status_code == 200
    assert response.json()["category"] == "design"


def test_post_category_defaults_to_none(client):
    """Posts created without a category should return null/absent category."""
    from app.db import put_content
    put_content("POST", make_post(slug="no-category"))

    response = client.get("/api/posts/no-category")
    data = response.json()
    assert data.get("category") is None


# ── Tags removed ──────────────────────────────────────────────────────────────

def test_post_model_has_no_tags_field(client):
    """The Post API response must not include a tags key."""
    from app.db import put_content
    put_content("POST", make_post(slug="no-tags"))
    data = client.get("/api/posts/no-tags").json()
    assert "tags" not in data


# ── Excerpt field ─────────────────────────────────────────────────────────────

def test_post_has_excerpt_field(client):
    """Posts can store and return an excerpt."""
    from app.db import put_content
    put_content("POST", make_post(slug="summed", excerpt="Short preview."))
    data = client.get("/api/posts/summed").json()
    assert data["excerpt"] == "Short preview."


def test_post_excerpt_defaults_to_none(client):
    """Posts without an excerpt return null."""
    from app.db import put_content
    put_content("POST", make_post(slug="no-excerpt"))
    data = client.get("/api/posts/no-excerpt").json()
    assert data.get("excerpt") is None


# ── Hero image fields ─────────────────────────────────────────────────────────

def test_post_api_includes_hero_urls(client):
    """GET /api/posts/{slug} must include hero_image_url and hero_thumbnail_url."""
    from app.db import put_content
    put_content("POST", make_post(
        slug="hero-api",
        hero_image_url="/static/post-images/hero-api-hero.jpg",
        hero_thumbnail_url="/static/post-images/hero-api-thumb.jpg",
    ))
    data = client.get("/api/posts/hero-api").json()
    assert data["hero_image_url"] == "/static/post-images/hero-api-hero.jpg"
    assert data["hero_thumbnail_url"] == "/static/post-images/hero-api-thumb.jpg"


def test_post_hero_urls_default_to_none(client):
    """Posts without hero images should return null for both URL fields."""
    from app.db import put_content
    put_content("POST", make_post(slug="plain-post"))
    data = client.get("/api/posts/plain-post").json()
    assert data.get("hero_image_url") is None
    assert data.get("hero_thumbnail_url") is None


# ── Blocks field ───────────────────────────────────────────────────────────────

def test_post_api_returns_blocks_as_array(client):
    """GET /api/posts/{slug} must return blocks as a JSON array, not a string."""
    from app.db import put_content
    put_content("POST", make_post(slug="blocks-post"))
    data = client.get("/api/posts/blocks-post").json()
    assert isinstance(data["blocks"], list)


def test_post_blocks_default_to_empty_array(client):
    """Post with no blocks stored returns blocks: [] in API response."""
    from app.db import put_content
    put_content("POST", make_post(slug="no-blocks"))
    data = client.get("/api/posts/no-blocks").json()
    assert data["blocks"] == []
