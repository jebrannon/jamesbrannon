"""Auto-summary generation via local Ollama (http://localhost:11434 by default)."""
import html as _html
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434")
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

_SYSTEM_PROMPT = (
    "You are a concise copywriter. Given a blog post, write a 2–3 sentence "
    "summary suitable as a preview excerpt. Plain text only, no markdown, "
    "no preamble, and no quotation marks around the output."
)


def _strip_html(text: str) -> str:
    """Strip HTML tags and decode entities to plain text."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


async def generate_excerpt(title: str, body: str) -> Optional[str]:
    """
    Call local Ollama to generate a 2–3 sentence excerpt for a blog post.

    Returns the generated text or None on any failure — the calling save
    operation must never be blocked by an LLM timeout or connection error.

    Environment variables:
        OLLAMA_URL   — base URL (default: http://localhost:11434)
        OLLAMA_MODEL — model name (default: llama3.2)
    """
    clean = _strip_html(body)
    if not clean:
        return None

    payload = {
        "model":   _OLLAMA_MODEL,
        "prompt":  f"Title: {title}\n\nContent:\n{clean[:3000]}",
        "system":  _SYSTEM_PROMPT,
        "stream":  False,
        "options": {"temperature": 0.4, "num_predict": 120},
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{_OLLAMA_URL}/api/generate",
                json=payload,
                timeout=30.0,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()
            return text or None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Ollama excerpt generation skipped: %s", exc)
        return None
