"""
Tests for favicon SVG → PNG variant generation.

The _generate_favicon_pngs helper converts an SVG to four PNG sizes
(16, 32, 192, 512 px) and returns them as in-memory bytes.
save_favicon handles both S3 upload and local filesystem paths.

Two test groups:
* Always-run: behaviour when cairosvg is not available (fast, no deps)
* Skipped when libcairo absent: real conversion + dimension checks
"""

import pytest
from unittest.mock import patch

import app.services.image as image_module
from app.services.image import _generate_favicon_pngs, EXPECTED_FAVICON_SIZES


# ── Minimal valid SVG ──────────────────────────────────────────────────────────

_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    b'<circle cx="32" cy="32" r="32" fill="#0a0a0a"/>'
    b'</svg>'
)

_SKIPIF_NO_CAIRO = pytest.mark.skipif(
    not image_module._CAIROSVG,
    reason="cairosvg / libcairo not installed (brew install cairo)",
)


# ── No-cairosvg path ──────────────────────────────────────────────────────────

def test_generate_favicon_pngs_no_cairosvg_returns_empty():
    """Returns empty list when cairosvg is unavailable."""
    with patch.object(image_module, "_CAIROSVG", False):
        result = _generate_favicon_pngs(_SVG, "test-fav")
    assert result == []


def test_generate_favicon_pngs_no_cairosvg_no_exception():
    """Should never raise even when cairosvg is absent."""
    with patch.object(image_module, "_CAIROSVG", False):
        _generate_favicon_pngs(_SVG, "test-fav")  # must not raise


# ── Full conversion path (requires libcairo) ──────────────────────────────────

@_SKIPIF_NO_CAIRO
def test_generate_favicon_pngs_returns_all_sizes():
    """All four PNG variants are returned."""
    result = _generate_favicon_pngs(_SVG, "favicon-light")
    assert len(result) == len(EXPECTED_FAVICON_SIZES)
    keys = [r[0] for r in result]
    for size in EXPECTED_FAVICON_SIZES:
        assert f"favicons/favicon-light-{size}.png" in keys


@_SKIPIF_NO_CAIRO
def test_generate_favicon_pngs_bytes_are_non_empty():
    """Generated PNG bytes contain data (not zero-byte stubs)."""
    result = _generate_favicon_pngs(_SVG, "favicon-dark")
    for key, data in result:
        assert len(data) > 0, f"{key} is empty"


@_SKIPIF_NO_CAIRO
def test_generate_favicon_pngs_correct_pixel_dimensions():
    """Each PNG has exactly the expected pixel dimensions."""
    from PIL import Image
    import io
    result = _generate_favicon_pngs(_SVG, "favicon-light")
    size_map = {key: data for key, data in result}
    for size in EXPECTED_FAVICON_SIZES:
        key = f"favicons/favicon-light-{size}.png"
        with Image.open(io.BytesIO(size_map[key])) as img:
            assert img.width == size, f"{key}: expected width {size}, got {img.width}"
            assert img.height == size, f"{key}: expected height {size}, got {img.height}"


@_SKIPIF_NO_CAIRO
def test_generate_favicon_pngs_different_names_do_not_collide():
    """Light and dark favicons produce distinct keys."""
    light = {key for key, _ in _generate_favicon_pngs(_SVG, "favicon-light")}
    dark = {key for key, _ in _generate_favicon_pngs(_SVG, "favicon-dark")}
    assert light.isdisjoint(dark)


# ── save_favicon S3 path ──────────────────────────────────────────────────────

def test_save_favicon_uploads_to_s3(aws_mock):
    """save_favicon uploads SVG (and PNGs if cairosvg available) to S3 and returns a URL."""
    from app.services.image import save_favicon
    url = save_favicon(_SVG, "favicon-light")
    assert "favicon-light.svg" in url


def test_save_favicon_local_fallback(tmp_path, monkeypatch):
    """save_favicon writes to local filesystem when S3 is not configured."""
    from app.services.image import save_favicon as _save_favicon
    monkeypatch.setattr(image_module, "_USE_S3", False)
    monkeypatch.setattr(image_module, "FAVICON_DIR", tmp_path)
    url = _save_favicon(_SVG, "favicon-light")
    assert url == "/static/favicons/favicon-light.svg"
    assert (tmp_path / "favicon-light.svg").exists()


def test_save_favicon_local_injects_dark_mode(tmp_path, monkeypatch):
    """save_favicon embeds dark-mode CSS when inject_dark_mode=True."""
    from app.services.image import save_favicon as _save_favicon
    monkeypatch.setattr(image_module, "_USE_S3", False)
    monkeypatch.setattr(image_module, "FAVICON_DIR", tmp_path)
    _save_favicon(_SVG, "favicon-dark-inject", inject_dark_mode=True)
    content = (tmp_path / "favicon-dark-inject.svg").read_text()
    assert "prefers-color-scheme" in content


def test_save_favicon_local_no_dark_mode(tmp_path, monkeypatch):
    """save_favicon saves SVG unchanged when inject_dark_mode=False."""
    from app.services.image import save_favicon as _save_favicon
    monkeypatch.setattr(image_module, "_USE_S3", False)
    monkeypatch.setattr(image_module, "FAVICON_DIR", tmp_path)
    # _SVG already lacks a prefers-color-scheme rule
    _save_favicon(_SVG, "favicon-no-dm", inject_dark_mode=False)
    content = (tmp_path / "favicon-no-dm.svg").read_text()
    assert "prefers-color-scheme" not in content
