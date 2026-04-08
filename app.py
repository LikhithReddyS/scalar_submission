"""Root-level app.py that re-exports the FastAPI app from server.app for compatibility."""
from server.app import app

__all__ = ["app"]
