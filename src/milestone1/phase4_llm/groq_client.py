from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx

from milestone1.phase3_integration.model import PromptPayload

from milestone1.phase4_llm.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    DEFAULT_TIMEOUT_SEC,
    GROQ_CHAT_COMPLETIONS_URL,
)
from milestone1.phase4_llm.errors import GroqTransportError


@dataclass(frozen=True, slots=True)
class GroqCompletion:
    """Normalized chat completion result."""

    text: str
    usage: dict[str, int] | None
    model: str


def _retryable_status(code: int) -> bool:
    return code in {408, 429, 500, 502, 503, 504}


def _messages_from_prompt(payload: PromptPayload) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": payload.system_message},
        {"role": "user", "content": payload.user_message},
    ]


def complete_chat(
    payload: PromptPayload,
    *,
    api_key: str,
    model: str,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    max_retries: int = DEFAULT_MAX_RETRIES,
    use_json_object_mode: bool = True,
) -> GroqCompletion:
    """
    Call Groq OpenAI-compatible chat completions with retries on transient errors.

    ``use_json_object_mode`` requests ``response_format: json_object`` when True
    (supported on many Groq models; disable if a model rejects it).
    """
    if not api_key.strip():
        raise GroqTransportError("GROQ_API_KEY is empty.")

    body: dict[str, Any] = {
        "model": model,
        "messages": _messages_from_prompt(payload),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if use_json_object_mode:
        body["response_format"] = {"type": "json_object"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_err: Exception | None = None
    for attempt in range(max(1, max_retries)):
        try:
            with httpx.Client(timeout=timeout_sec) as client:
                r = client.post(GROQ_CHAT_COMPLETIONS_URL, headers=headers, json=body)
            if r.status_code >= 400:
                if _retryable_status(r.status_code) and attempt < max_retries - 1:
                    time.sleep(min(2.0**attempt + random.random(), 8.0))
                    continue
                raise GroqTransportError(
                    f"Groq API error: HTTP {r.status_code}: {r.text[:500]}",
                    status_code=r.status_code,
                )
            data = r.json()
        except httpx.RequestError as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(min(2.0**attempt + random.random(), 8.0))
                continue
            raise GroqTransportError(f"Groq request failed: {e}") from e

        try:
            choice = data["choices"][0]
            msg = choice["message"]
            content = msg.get("content") or ""
        except (KeyError, IndexError, TypeError) as e:
            raise GroqTransportError(f"Unexpected Groq response shape: {data!r}") from e

        usage_raw = data.get("usage")
        usage: dict[str, int] | None
        if isinstance(usage_raw, dict):
            usage = {k: int(v) for k, v in usage_raw.items() if isinstance(v, (int, float))}
        else:
            usage = None

        return GroqCompletion(text=str(content).strip(), usage=usage, model=str(data.get("model", model)))

    assert last_err is not None
    raise GroqTransportError(f"Groq request failed after retries: {last_err}") from last_err


def complete_chat_json_relaxed(
    payload: PromptPayload,
    *,
    api_key: str,
    model: str,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> GroqCompletion:
    """
    Try JSON object mode first; on HTTP 400 mentioning response_format, retry without it.
    """
    try:
        return complete_chat(
            payload,
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_sec=timeout_sec,
            max_retries=max_retries,
            use_json_object_mode=True,
        )
    except GroqTransportError as e:
        if e.status_code == 400 and "response_format" in str(e).lower():
            return complete_chat(
                payload,
                api_key=api_key,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_sec=timeout_sec,
                max_retries=max_retries,
                use_json_object_mode=False,
            )
        raise
