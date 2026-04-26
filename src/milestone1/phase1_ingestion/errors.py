from __future__ import annotations


class IngestionError(Exception):
    """Raised when the Hub dataset cannot be read or fails schema checks."""
