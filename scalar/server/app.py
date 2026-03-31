"""Compatibility ASGI entrypoint mirroring top-level server app."""

from openenv_server import app


def main() -> None:
    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)
