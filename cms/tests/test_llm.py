"""Tests for the LLM excerpt-generation service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx


# ── _strip_html ───────────────────────────────────────────────────────────────

class TestStripHtml:
    def test_removes_html_tags(self):
        from app.services.llm import _strip_html
        assert _strip_html("<p>Hello world</p>") == "Hello world"

    def test_decodes_html_entities(self):
        from app.services.llm import _strip_html
        assert _strip_html("&amp; &lt;p&gt;") == "& <p>"

    def test_collapses_whitespace(self):
        from app.services.llm import _strip_html
        result = _strip_html("<p>Hello</p>   <p>World</p>")
        assert "  " not in result
        assert "Hello" in result
        assert "World" in result

    def test_empty_string(self):
        from app.services.llm import _strip_html
        assert _strip_html("") == ""

    def test_plain_text_unchanged(self):
        from app.services.llm import _strip_html
        assert _strip_html("Just plain text.") == "Just plain text."

    def test_nested_tags(self):
        from app.services.llm import _strip_html
        result = _strip_html("<div><strong>Bold</strong> and <em>italic</em></div>")
        assert "Bold" in result
        assert "italic" in result
        assert "<" not in result


@pytest.mark.asyncio
async def test_generate_excerpt_returns_text():
    from app.services.llm import generate_excerpt

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "A great excerpt."}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await generate_excerpt("My Title", "<p>Some content here.</p>")

    assert result == "A great excerpt."


@pytest.mark.asyncio
async def test_generate_excerpt_empty_body_returns_none():
    from app.services.llm import generate_excerpt

    result = await generate_excerpt("My Title", "   ")
    assert result is None


@pytest.mark.asyncio
async def test_generate_excerpt_ollama_unavailable_returns_none():
    from app.services.llm import generate_excerpt

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(
        side_effect=httpx.ConnectError("connection refused")
    )

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await generate_excerpt("My Title", "<p>Some content here.</p>")

    assert result is None


@pytest.mark.asyncio
async def test_generate_excerpt_empty_response_returns_none():
    from app.services.llm import generate_excerpt

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"response": "   "}

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await generate_excerpt("My Title", "<p>Content.</p>")

    assert result is None
