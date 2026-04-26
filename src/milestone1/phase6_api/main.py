from __future__ import annotations

import os


def main() -> None:
    """Run the Phase 6 API with uvicorn (``milestone1-api`` console script)."""
    import uvicorn

    from milestone1.phase6_api.app import app

    host = os.environ.get("API_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
