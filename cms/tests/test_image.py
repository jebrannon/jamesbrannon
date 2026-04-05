"""Tests for cms/app/services/image.py — _inject_dark_mode."""

import pytest
from app.services.image import _inject_dark_mode


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
