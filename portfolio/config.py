import os
from portfolio.models import AppConfig

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_OLLAMA_MODEL = "phi4-mini"
DEFAULT_CURRENCY = "EUR"
DEFAULT_REQUEST_TIMEOUT = 180


def load_config() -> AppConfig:
    timeout_raw = os.getenv("REQUEST_TIMEOUT", str(DEFAULT_REQUEST_TIMEOUT))
    try:
        timeout = int(timeout_raw)
        if timeout <= 0 or timeout > 120:
            raise ValueError
    except ValueError:
        timeout = DEFAULT_REQUEST_TIMEOUT

    ollama_url = os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL)
    if not (ollama_url.startswith("http://") or ollama_url.startswith("https://")):
        ollama_url = DEFAULT_OLLAMA_URL

    return AppConfig(
        ollama_url=ollama_url,
        ollama_model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
        default_currency=os.getenv("DEFAULT_CURRENCY", DEFAULT_CURRENCY),
        request_timeout=timeout,
    )