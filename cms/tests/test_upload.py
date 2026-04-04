"""Tests for the /api/upload-image endpoint."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image


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
