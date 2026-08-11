import os

def get_backend_url() -> str:
    """Return the FastAPI base URL for local or Render execution."""
    explicit = os.getenv("BACKEND_API_URL") or os.getenv("API_URL")
    if explicit:
        return explicit.rstrip("/")
    hostport = os.getenv("BACKEND_API_HOSTPORT")
    if hostport:
        return f"http://{hostport}".rstrip("/")
    return "http://localhost:8000"
