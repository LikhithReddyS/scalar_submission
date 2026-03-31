"""ASGI server entrypoint required by OpenEnv multi-mode validator."""

from openenv_server import app


def main() -> None:
    """Console entrypoint for local launches via project.scripts."""
    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)
