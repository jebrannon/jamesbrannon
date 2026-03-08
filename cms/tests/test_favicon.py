"""
Tests for favicon SVG → PNG variant generation.

The _convert_favicon helper converts an uploaded SVG to four PNG sizes
(16, 32, 192, 512 px).  Two test groups:

* Always-run: behaviour when cairosvg is not available (fast, no deps)
* Skipped when libcairo absent: real conversion + dimension checks
"""

import pytest
from unittest.mock import patch

import app.admin.views as views_module
from app.admin.views import _convert_favicon, EXPECTED_FAVICON_SIZES


# ── Minimal valid SVG ──────────────────────────────────────────────────────────

_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    b'<circle cx="32" cy="32" r="32" fill="#0a0a0a"/>'
    b'</svg>'
)

_SKIPIF_NO_CAIRO = pytest.mark.skipif(
    not views_module._CAIROSVG,
    reason="cairosvg / libcairo not installed (brew install cairo)",
)


# ── No-cairosvg path ──────────────────────────────────────────────────────────

def test_convert_favicon_no_cairosvg_creates_no_files(tmp_path):
    """Returns cleanly and writes nothing when cairosvg is unavailable."""
    with patch.object(views_module, "_CAIROSVG", False), \
         patch.object(views_module, "FAVICON_DIR", tmp_path):
        _convert_favicon(_SVG, "test-fav")
    assert list(tmp_path.iterdir()) == []


def test_convert_favicon_no_cairosvg_no_exception():
    """Should never raise even when cairosvg is absent."""
    with patch.object(views_module, "_CAIROSVG", False):
        _convert_favicon(_SVG, "test-fav")   # must not raise


# ── Full conversion path (requires libcairo) ──────────────────────────────────

@_SKIPIF_NO_CAIRO
def test_convert_favicon_generates_all_sizes(tmp_path, monkeypatch):
    """All four PNG files are created after conversion."""
    monkeypatch.setattr(views_module, "FAVICON_DIR", tmp_path)
    _convert_favicon(_SVG, "favicon-light")
    for size in EXPECTED_FAVICON_SIZES:
        out = tmp_path / f"favicon-light-{size}.png"
        assert out.exists(), f"Expected {out.name} to be generated"


@_SKIPIF_NO_CAIRO
def test_convert_favicon_files_are_non_empty(tmp_path, monkeypatch):
    """Generated PNG files contain data (not zero-byte stubs)."""
    monkeypatch.setattr(views_module, "FAVICON_DIR", tmp_path)
    _convert_favicon(_SVG, "favicon-dark")
    for size in EXPECTED_FAVICON_SIZES:
        out = tmp_path / f"favicon-dark-{size}.png"
        assert out.stat().st_size > 0, f"{out.name} is empty"


@_SKIPIF_NO_CAIRO
def test_convert_favicon_correct_pixel_dimensions(tmp_path, monkeypatch):
    """Each PNG has exactly the expected pixel dimensions."""
    from PIL import Image

    monkeypatch.setattr(views_module, "FAVICON_DIR", tmp_path)
    _convert_favicon(_SVG, "favicon-light")
    for size in EXPECTED_FAVICON_SIZES:
        out = tmp_path / f"favicon-light-{size}.png"
        with Image.open(out) as img:
            assert img.width == size, f"{out.name}: expected width {size}, got {img.width}"
            assert img.height == size, f"{out.name}: expected height {size}, got {img.height}"


@_SKIPIF_NO_CAIRO
def test_convert_favicon_different_names_do_not_collide(tmp_path, monkeypatch):
    """Light and dark favicons are stored under distinct filenames."""
    monkeypatch.setattr(views_module, "FAVICON_DIR", tmp_path)
    _convert_favicon(_SVG, "favicon-light")
    _convert_favicon(_SVG, "favicon-dark")
    for size in EXPECTED_FAVICON_SIZES:
        assert (tmp_path / f"favicon-light-{size}.png").exists()
        assert (tmp_path / f"favicon-dark-{size}.png").exists()


@_SKIPIF_NO_CAIRO
def test_convert_favicon_overwrites_on_second_upload(tmp_path, monkeypatch):
    """Re-uploading replaces existing PNGs rather than appending."""
    monkeypatch.setattr(views_module, "FAVICON_DIR", tmp_path)
    _convert_favicon(_SVG, "favicon-light")
    sizes_before = {
        size: (tmp_path / f"favicon-light-{size}.png").stat().st_size
        for size in EXPECTED_FAVICON_SIZES
    }
    _convert_favicon(_SVG, "favicon-light")
    for size in EXPECTED_FAVICON_SIZES:
        out = tmp_path / f"favicon-light-{size}.png"
        assert out.stat().st_size == sizes_before[size]
