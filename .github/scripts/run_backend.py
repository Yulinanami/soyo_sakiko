"""PyInstaller 入口脚本 - 构建时复制到 backend/run_backend.py"""

import os
import sys
import threading
import webbrowser
import uvicorn
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException


def get_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def setup_frontend(app):
    root = get_root()
    frontend_dir = root / "frontend"
    if frontend_dir.is_dir():
        remove_root_route(app)

        # Mount assets separately for better performance/caching
        assets_dir = frontend_dir / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

        # SPA Catch-all handler
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Not Found")

            # Check if it is an existing file
            file_path = frontend_dir / full_path
            if file_path.is_file():
                return FileResponse(file_path)

            # Fallback to index.html
            index = frontend_dir / "index.html"
            if index.exists():
                return FileResponse(index)
            return HTTPException(status_code=404, detail="Page not found")

        return True
    return False


def remove_root_route(app):
    routes = []
    for route in app.router.routes:
        if getattr(route, "path", None) == "/":
            continue
        routes.append(route)
    app.router.routes = routes


if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH") and getattr(sys, "frozen", False):
    browsers_path = get_root() / "playwright-browsers"
    if browsers_path.exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)

from app.main import app

has_frontend = setup_frontend(app)


def open_browser():
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    if has_frontend:
        threading.Timer(1.0, open_browser).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
