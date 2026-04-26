from __future__ import annotations


class PreferencesValidationError(Exception):
    """One or more preference fields failed validation (for UI / API messages)."""

    def __init__(self, errors: list[tuple[str, str]]) -> None:
        if not errors:
            raise ValueError("errors must be non-empty")
        self.errors: list[tuple[str, str]] = errors
        joined = "; ".join(f"{field}: {msg}" for field, msg in errors)
        super().__init__(joined)
