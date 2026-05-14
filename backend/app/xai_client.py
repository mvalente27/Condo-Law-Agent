"""Thin xAI Chat Completions client with Zero Data Retention header."""
from __future__ import annotations

from typing import Any

import httpx

from .config import get_settings


class XAIError(RuntimeError):
    pass


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    max_tokens: int | None = 4000,
    response_format: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    if not settings.xai_api_key:
        raise XAIError("XAI_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.xai_api_key}",
        "Content-Type": "application/json",
    }
    if settings.xai_zero_data_retention:
        # Honored by xAI for ZDR-eligible accounts; harmless if ignored.
        headers["x-zero-data-retention"] = "true"

    payload: dict[str, Any] = {
        "model": settings.xai_model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if response_format is not None:
        payload["response_format"] = response_format

    url = f"{settings.xai_base_url.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(url, json=payload, headers=headers)
        if r.status_code >= 400:
            raise XAIError(f"xAI {r.status_code}: {r.text}")
        data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:  # pragma: no cover
        raise XAIError(f"Unexpected xAI response: {data}") from e
