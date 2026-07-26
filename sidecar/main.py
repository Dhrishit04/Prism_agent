"""Prism sidecar entry point — runs the FastAPI server."""

import uvicorn
from server import app


def main():
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()