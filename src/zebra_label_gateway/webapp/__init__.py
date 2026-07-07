"""FastAPI web application for uploading, manipulating, and printing labels."""

from .server import app, create_app

__all__ = ["app", "create_app"]
