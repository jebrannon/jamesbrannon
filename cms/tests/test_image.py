"""Tests for cms/app/services/image.py — _inject_dark_mode, save_hero_image,
save_block_image, save_logo."""

import io
import pytest
from unittest.mock import patch
from PIL import Image

import app.services.image as image_module
from app.services.image import _inject_dark_mode, _make_previews


def _make_jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (200, 200), color=(100, 150, 200)).save(buf, format="JPEG")
    return buf.getvalue()


_DARK_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 96">
<path d="M0 0 L72 96" fill="#2D2D2D"/>
</svg>"""

_LIGHT_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 96">
<path d="M0 0 L72 96" fill="#FBFBFB"/>
</svg>"""

_ALREADY_HAS_DARK_MODE = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 96">
<style>path { fill: #1E1E1E; } @media (prefers-color-scheme: dark) { path { fill: #FBFBFB; } }</style>
<path d="M0 0 L72 96"/>
</svg>"""

_NO_FILLS = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 96">
<path d="M0 0 L72 96"/>
</svg>"""


def test_injects_dark_mode_for_dark_mark():
    result = _inject_dark_mode(_DARK_SVG).decode("utf-8")
    assert "prefers-color-scheme" in result
    assert "#FBFBFB" in result


def test_injects_dark_mode_for_light_mark():
    result = _inject_dark_mode(_LIGHT_SVG).decode("utf-8")
    assert "prefers-color-scheme" in result
    assert "#2D2D2D" in result


def test_leaves_svg_unchanged_if_already_has_dark_mode():
    result = _inject_dark_mode(_ALREADY_HAS_DARK_MODE)
    assert result == _ALREADY_HAS_DARK_MODE


def test_leaves_svg_unchanged_if_no_fills_found():
    result = _inject_dark_mode(_NO_FILLS)
    assert result == _NO_FILLS


def test_style_block_injected_after_svg_opening_tag():
    result = _inject_dark_mode(_DARK_SVG).decode("utf-8")
    svg_tag_end = result.index(">") + 1
    assert "<style>" in result[svg_tag_end - 50: svg_tag_end + 50]


def test_handles_css_fill_syntax():
    svg = b"""<svg xmlns="http://www.w3.org/2000/svg">
    <style>path { fill: #1E1E1E; }</style>
    <path d="M0 0"/>
    </svg>"""
    result = _inject_dark_mode(svg).decode("utf-8")
    assert "prefers-color-scheme" in result
    assert "#FBFBFB" in result


def test_handles_invalid_utf8_gracefully():
    result = _inject_dark_mode(b"\xff\xfe invalid bytes")
    assert result == b"\xff\xfe invalid bytes"


def test_handles_three_char_hex():
    svg = b"""<svg xmlns="http://www.w3.org/2000/svg">
    <path fill="#111"/>
    </svg>"""
    result = _inject_dark_mode(svg).decode("utf-8")
    assert "prefers-color-scheme" in result
    assert "#FBFBFB" in result


# ── _make_previews ────────────────────────────────────────────────────────────

def test_make_previews_dark_svg_light_is_original():
    """Dark SVG: light preview is the original (dark fills visible on white)."""
    light, _ = _make_previews(_DARK_SVG)
    assert light == _DARK_SVG


def test_make_previews_dark_svg_dark_flips_to_light():
    """Dark SVG: dark preview has fills replaced with light colour."""
    _, dark = _make_previews(_DARK_SVG)
    decoded = dark.decode("utf-8")
    assert "#FBFBFB" in decoded
    assert "prefers-color-scheme" not in decoded


def test_make_previews_light_svg_dark_is_original():
    """Light SVG: dark preview is the original (light fills visible on dark bg)."""
    _, dark = _make_previews(_LIGHT_SVG)
    assert dark == _LIGHT_SVG


def test_make_previews_light_svg_light_flips_to_dark():
    """Light SVG: light preview has fills replaced with dark colour."""
    light, _ = _make_previews(_LIGHT_SVG)
    decoded = light.decode("utf-8")
    assert "#2D2D2D" in decoded
    assert "prefers-color-scheme" not in decoded


def test_make_previews_no_fills_returns_original_for_both():
    """SVG with no detectable fills: both previews are the original unchanged."""
    light, dark = _make_previews(_NO_FILLS)
    assert light == _NO_FILLS
    assert dark == _NO_FILLS


def test_make_previews_invalid_utf8_returns_original_for_both():
    bad = b"\xff\xfe invalid bytes"
    light, dark = _make_previews(bad)
    assert light == bad
    assert dark == bad


def test_make_previews_no_media_query_in_either_preview():
    """Neither preview should contain a media query — fills are hardcoded."""
    light, dark = _make_previews(_DARK_SVG)
    assert b"prefers-color-scheme" not in light
    assert b"prefers-color-scheme" not in dark


# ── save_hero_image ───────────────────────────────────────────────────────────

def test_save_hero_image_local_returns_static_urls(tmp_path, monkeypatch):
    """Local path: save_hero_image writes files and returns /static/... URLs."""
    monkeypatch.setattr(image_module, "_USE_S3", False)
    monkeypatch.setattr(image_module, "POST_IMAGES_DIR", tmp_path)
    hero_url, thumb_url = image_module.save_hero_image(_make_jpeg_bytes(), "my-slug", ".jpg")
    assert hero_url == "/static/post-images/my-slug-hero.jpg"
    assert thumb_url == "/static/post-images/my-slug-thumb.jpg"
    assert (tmp_path / "my-slug-hero.jpg").exists()
    assert (tmp_path / "my-slug-thumb.jpg").exists()


def test_save_hero_image_generates_thumbnail(tmp_path, monkeypatch):
    """Thumbnail is resized to THUMB_SIZE (1200×630)."""
    monkeypatch.setattr(image_module, "_USE_S3", False)
    monkeypatch.setattr(image_module, "POST_IMAGES_DIR", tmp_path)
    image_module.save_hero_image(_make_jpeg_bytes(), "thumb-test", ".jpg")
    thumb = Image.open(tmp_path / "thumb-test-thumb.jpg")
    assert thumb.width == 1200
    assert thumb.height == 630


def test_save_hero_image_s3_path(aws_mock):
    """S3 path: save_hero_image uploads to S3 and returns URLs."""
    hero_url, thumb_url = image_module.save_hero_image(_make_jpeg_bytes(), "s3-slug", ".jpg")
    assert "s3-slug-hero.jpg" in hero_url
    assert "s3-slug-thumb.jpg" in thumb_url


# ── save_block_image ──────────────────────────────────────────────────────────

def test_save_block_image_local(tmp_path, monkeypatch):
    """Local path: save_block_image writes file and returns /static/... URL."""
    monkeypatch.setattr(image_module, "_USE_S3", False)
    monkeypatch.setattr(image_module, "POST_IMAGES_DIR", tmp_path)
    url = image_module.save_block_image(_make_jpeg_bytes(), "abc12345", ".jpg")
    assert url == "/static/post-images/block-abc12345.jpg"
    assert (tmp_path / "block-abc12345.jpg").exists()


def test_save_block_image_s3(aws_mock):
    """S3 path: save_block_image uploads to S3 and returns a URL."""
    url = image_module.save_block_image(_make_jpeg_bytes(), "abc12345", ".jpg")
    assert "block-abc12345.jpg" in url


# ── save_logo ─────────────────────────────────────────────────────────────────

_LOGO_SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><path fill="#1a1a1a" d="M0 0h10v10H0z"/></svg>'


def test_save_logo_local(tmp_path, monkeypatch):
    """Local path: save_logo writes logo.svg and returns /static/logos/logo.svg."""
    monkeypatch.setattr(image_module, "_USE_S3", False)
    monkeypatch.setattr(image_module, "LOGO_DIR", tmp_path)
    url = image_module.save_logo(_LOGO_SVG, inject_dark_mode=False)
    assert url == "/static/logos/logo.svg"
    assert (tmp_path / "logo.svg").exists()


def test_save_logo_injects_dark_mode_when_requested(tmp_path, monkeypatch):
    """inject_dark_mode=True causes dark-mode CSS to be embedded in the saved SVG."""
    monkeypatch.setattr(image_module, "_USE_S3", False)
    monkeypatch.setattr(image_module, "LOGO_DIR", tmp_path)
    image_module.save_logo(_LOGO_SVG, inject_dark_mode=True)
    content = (tmp_path / "logo.svg").read_text()
    assert "prefers-color-scheme" in content


def test_save_logo_s3(aws_mock):
    """S3 path: save_logo uploads to S3 and returns a URL."""
    url = image_module.save_logo(_LOGO_SVG, inject_dark_mode=False)
    assert "logo.svg" in url
