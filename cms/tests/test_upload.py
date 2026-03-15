"""Tests for the /api/upload-image endpoint."""
import io
from unittest.mock import patch

import pytest
from PIL import Image


def _make_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(128, 64, 32)).save(buf, format="JPEG")
    return buf.getvalue()


def _auth_session(client):
    """Log in and return the client (session cookie is set on the client)."""
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "testpass"},
        follow_redirects=True,
    )
    return client


# ── Unauthenticated ────────────────────────────────────────────────────────────

def test_upload_image_unauthenticated(client):
    data = {"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")}
    resp = client.post("/api/upload-image", files=data)
    assert resp.status_code == 401
    assert resp.json()["error"] == "Unauthorized"


# ── Authenticated ──────────────────────────────────────────────────────────────

def test_upload_image_authenticated_returns_url(client, tmp_path, monkeypatch):
    from app.services import image as image_mod
    monkeypatch.setattr(image_mod, "POST_IMAGES_DIR", tmp_path)

    _auth_session(client)
    data = {"file": ("photo.jpg", _make_jpeg_bytes(), "image/jpeg")}
    resp = client.post("/api/upload-image", files=data)
    assert resp.status_code == 200
    body = resp.json()
    assert "url" in body
    assert body["url"].startswith("/static/post-images/block-")


def test_upload_image_no_extension_defaults_to_jpg(client, tmp_path, monkeypatch):
    from app.services import image as image_mod
    monkeypatch.setattr(image_mod, "POST_IMAGES_DIR", tmp_path)

    _auth_session(client)
    # Filename with no extension — endpoint should default to .jpg
    data = {"file": ("photo", _make_jpeg_bytes(), "image/jpeg")}
    resp = client.post("/api/upload-image", files=data)
    assert resp.status_code == 200
    assert resp.json()["url"].endswith(".jpg")
