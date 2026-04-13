"""Tests for the /api/upload-image and /api/preview-svg endpoints."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

_MINIMAL_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="5" fill="#000"/></svg>'


def _make_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(128, 64, 32)).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture()
def auth_client(aws_mock):
    """TestClient authenticated against the admin UI."""
    from app.admin.auth import _failed_attempts
    from app.main import app
    _failed_attempts.clear()
    client = TestClient(app, raise_server_exceptions=True, follow_redirects=True)
    client.post("/admin/login", data={"username": "admin", "password": "testpass"})
    return client


# ── Unauthenticated ────────────────────────────────────────────────────────────

def test_upload_image_unauthenticated(client):
    data = {"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")}
    resp = client.post("/api/upload-image", files=data)
    assert resp.status_code == 401
    assert resp.json()["error"] == "Unauthorized"


# ── Authenticated ──────────────────────────────────────────────────────────────

def test_upload_image_authenticated_returns_url(auth_client):
    data = {"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")}
    resp = auth_client.post("/api/upload-image", files=data)
    assert resp.status_code == 200
    body = resp.json()
    assert "url" in body
    assert "post-images/block-" in body["url"]
    assert body["url"].endswith(".jpg")


def test_upload_image_no_extension_defaults_to_jpg(auth_client):
    data = {"file": ("photo", _make_jpeg_bytes(), "image/jpeg")}
    resp = auth_client.post("/api/upload-image", files=data)
    assert resp.status_code == 200
    assert resp.json()["url"].endswith(".jpg")


# ── /api/preview-svg ─────────────────────────────────────────────────────────

def test_preview_svg_unauthenticated(client):
    data = {"file": ("logo.svg", _MINIMAL_SVG, "image/svg+xml")}
    resp = client.post("/api/preview-svg", files=data)
    assert resp.status_code == 403
    assert resp.json()["error"] == "Unauthorized"


def test_preview_svg_returns_both_data_urls(auth_client):
    """Response includes preview (light) and preview_dark, both as data URLs."""
    data = {"file": ("logo.svg", _MINIMAL_SVG, "image/svg+xml")}
    resp = auth_client.post("/api/preview-svg", files=data)
    assert resp.status_code == 200
    body = resp.json()
    assert body["preview"].startswith("data:image/svg+xml;base64,")
    assert body["preview_dark"].startswith("data:image/svg+xml;base64,")


def test_preview_svg_invalid_content_returns_400(auth_client):
    data = {"file": ("logo.svg", b"not an svg file at all", "image/svg+xml")}
    resp = auth_client.post("/api/preview-svg", files=data)
    assert resp.status_code == 400
    assert resp.json()["error"] == "Invalid SVG"


def test_preview_svg_dark_svg_light_preview_is_original(auth_client):
    """Dark SVG: light preview is the original, dark preview has light fills."""
    import base64
    dark_svg = b'<svg xmlns="http://www.w3.org/2000/svg"><circle cx="5" cy="5" r="5" fill="#000"/></svg>'
    data = {"file": ("logo.svg", dark_svg, "image/svg+xml")}
    resp = auth_client.post("/api/preview-svg", files=data)
    assert resp.status_code == 200
    body = resp.json()
    light_raw = base64.b64decode(body["preview"].split(",", 1)[1])
    dark_raw  = base64.b64decode(body["preview_dark"].split(",", 1)[1])
    assert light_raw == dark_svg
    assert b"#FBFBFB" in dark_raw
    assert b"prefers-color-scheme" not in dark_raw


def test_preview_svg_light_svg_dark_preview_is_original(auth_client):
    """Light SVG: dark preview is the original, light preview has dark fills."""
    import base64
    light_svg = b'<svg xmlns="http://www.w3.org/2000/svg"><circle cx="5" cy="5" r="5" fill="#FBFBFB"/></svg>'
    data = {"file": ("logo.svg", light_svg, "image/svg+xml")}
    resp = auth_client.post("/api/preview-svg", files=data)
    assert resp.status_code == 200
    body = resp.json()
    light_raw = base64.b64decode(body["preview"].split(",", 1)[1])
    dark_raw  = base64.b64decode(body["preview_dark"].split(",", 1)[1])
    assert dark_raw == light_svg
    assert b"#2D2D2D" in light_raw
    assert b"prefers-color-scheme" not in light_raw


# ── /api/preview-og-image ────────────────────────────────────────────────────

def test_preview_og_image_unauthenticated(client):
    data = {"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")}
    resp = client.post("/api/preview-og-image", files=data)
    assert resp.status_code == 403
    assert resp.json()["error"] == "Unauthorized"


def test_preview_og_image_returns_jpeg_data_url(auth_client):
    """Response includes a single JPEG data URL cropped to 1200×630."""
    import base64
    data = {"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")}
    resp = auth_client.post("/api/preview-og-image", files=data)
    assert resp.status_code == 200
    body = resp.json()
    assert "preview" in body
    assert body["preview"].startswith("data:image/jpeg;base64,")
    raw = base64.b64decode(body["preview"].split(",", 1)[1])
    img = Image.open(io.BytesIO(raw))
    assert img.width == 1200
    assert img.height == 630


def test_preview_og_image_empty_file_returns_400(auth_client):
    data = {"file": ("empty.jpg", b"", "image/jpeg")}
    resp = auth_client.post("/api/preview-og-image", files=data)
    assert resp.status_code == 400
