import os


def get_backend_url() -> str:
    """Return the FastAPI backend base URL."""

    explicit = os.getenv("BACKEND_API_URL") or os.getenv("API_URL")

    if explicit:
        return explicit.rstrip("/")

    return "http://localhost:8000"