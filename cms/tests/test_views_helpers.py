"""
Tests for internal admin view helpers:
  - _sanitize_blocks
  - _blocks_as_plain_text
  - _normalize
  - _unpack_file
"""
import json
import pytest
from unittest.mock import MagicMock
from enum import Enum


# ── _sanitize_blocks ──────────────────────────────────────────────────────────

class TestSanitizeBlocks:
    def test_strips_script_tag_from_text(self):
        from app.admin.views import _sanitize_blocks
        raw = json.dumps([{"text": "<p>Hello</p><script>alert(1)</script>", "media": []}])
        result = json.loads(_sanitize_blocks(raw))
        assert "<script>" not in result[0]["text"]

    def test_allows_permitted_tags(self):
        from app.admin.views import _sanitize_blocks
        raw = json.dumps([{"text": "<p>Hello <strong>world</strong></p>", "media": []}])
        result = json.loads(_sanitize_blocks(raw))
        assert "<strong>" in result[0]["text"]

    def test_normalises_null_media_to_empty_list(self):
        from app.admin.views import _sanitize_blocks
        raw = json.dumps([{"text": "<p>Hello</p>", "media": None}])
        result = json.loads(_sanitize_blocks(raw))
        assert result[0]["media"] == []

    def test_normalises_dict_media_to_list(self):
        from app.admin.views import _sanitize_blocks
        raw = json.dumps([{"text": "", "media": {"url": "/img.jpg", "alt": "img"}}])
        result = json.loads(_sanitize_blocks(raw))
        assert isinstance(result[0]["media"], list)
        assert result[0]["media"][0]["url"] == "/img.jpg"

    def test_invalid_json_returns_empty_array(self):
        from app.admin.views import _sanitize_blocks
        result = _sanitize_blocks("not valid json")
        assert result == "[]"

    def test_non_list_json_returns_empty_array(self):
        from app.admin.views import _sanitize_blocks
        result = _sanitize_blocks('{"key": "value"}')
        assert result == "[]"

    def test_empty_text_set_to_none(self):
        from app.admin.views import _sanitize_blocks
        raw = json.dumps([{"text": "   ", "media": []}])
        result = json.loads(_sanitize_blocks(raw))
        assert result[0]["text"] is None

    def test_sanitises_media_alt_text(self):
        from app.admin.views import _sanitize_blocks
        raw = json.dumps([{
            "text": "",
            "media": [{"url": "/img.jpg", "alt": "<script>evil</script>", "caption": ""}]
        }])
        result = json.loads(_sanitize_blocks(raw))
        assert "<script>" not in result[0]["media"][0]["alt"]

    def test_empty_blocks_array(self):
        from app.admin.views import _sanitize_blocks
        assert _sanitize_blocks("[]") == "[]"


# ── _blocks_as_plain_text ─────────────────────────────────────────────────────

class TestBlocksAsPlainText:
    def test_extracts_text_from_blocks(self):
        from app.admin.views import _blocks_as_plain_text
        blocks = [{"text": "<p>Hello world</p>", "media": []}]
        result = _blocks_as_plain_text(json.dumps(blocks))
        assert "Hello world" in result
        assert "<p>" not in result

    def test_joins_multiple_blocks(self):
        from app.admin.views import _blocks_as_plain_text
        blocks = [
            {"text": "<p>First</p>", "media": []},
            {"text": "<p>Second</p>", "media": []},
        ]
        result = _blocks_as_plain_text(json.dumps(blocks))
        assert "First" in result
        assert "Second" in result

    def test_handles_empty_blocks(self):
        from app.admin.views import _blocks_as_plain_text
        result = _blocks_as_plain_text("[]")
        assert result == ""

    def test_handles_none_input(self):
        from app.admin.views import _blocks_as_plain_text
        result = _blocks_as_plain_text(None)
        assert result == ""

    def test_handles_invalid_json(self):
        from app.admin.views import _blocks_as_plain_text
        result = _blocks_as_plain_text("not json")
        assert result == ""

    def test_accepts_list_directly(self):
        from app.admin.views import _blocks_as_plain_text
        blocks = [{"text": "<p>Direct list</p>"}]
        result = _blocks_as_plain_text(blocks)
        assert "Direct list" in result


# ── _normalize ────────────────────────────────────────────────────────────────

class TestNormalize:
    def test_converts_enum_to_value(self):
        from app.admin.views import _normalize
        from app.models import ThemeMode
        result = _normalize({"theme_mode": ThemeMode.dark, "title": "Hello"})
        assert result["theme_mode"] == "dark"
        assert result["title"] == "Hello"

    def test_passes_through_non_enum_values(self):
        from app.admin.views import _normalize
        result = _normalize({"count": 42, "name": "test", "flag": True})
        assert result == {"count": 42, "name": "test", "flag": True}

    def test_empty_dict(self):
        from app.admin.views import _normalize
        assert _normalize({}) == {}


# ── _unpack_file ──────────────────────────────────────────────────────────────

class TestUnpackFile:
    def test_unpacks_tuple(self):
        from app.admin.views import _unpack_file
        mock_file = MagicMock()
        result = _unpack_file((mock_file, False))
        assert result == (mock_file, False)

    def test_unpacks_delete_tuple(self):
        from app.admin.views import _unpack_file
        result = _unpack_file((None, True))
        assert result == (None, True)

    def test_bare_file_returns_false_delete(self):
        from app.admin.views import _unpack_file
        mock_file = MagicMock()
        file, should_delete = _unpack_file(mock_file)
        assert file == mock_file
        assert should_delete is False

    def test_none_returns_none_false(self):
        from app.admin.views import _unpack_file
        file, should_delete = _unpack_file(None)
        assert file is None
        assert should_delete is False


# ── ToggleField ───────────────────────────────────────────────────────────────

class TestToggleField:
    def test_toggle_field_uses_toggle_template(self):
        from app.admin.views import ToggleField
        field = ToggleField("published", label="Published")
        assert field.form_template == "forms/toggle.html"

    def test_toggle_field_is_boolean_field(self):
        from app.admin.views import ToggleField
        from starlette_admin.fields import BooleanField
        field = ToggleField("no_index", label="No Index")
        assert isinstance(field, BooleanField)
