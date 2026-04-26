from __future__ import annotations

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

# Default Groq chat model (override with GROQ_MODEL).
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

DEFAULT_TEMPERATURE = 0.35
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT_SEC = 60.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_TOP_K = 5
