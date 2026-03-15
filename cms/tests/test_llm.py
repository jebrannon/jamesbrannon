"""Tests for the LLM excerpt-generation service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx


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
