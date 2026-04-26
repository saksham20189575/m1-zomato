from __future__ import annotations


class GroqTransportError(RuntimeError):
    """HTTP or network failure talking to Groq."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class RankingsParseError(ValueError):
    """LLM output was not valid JSON or did not match the expected rankings schema."""
