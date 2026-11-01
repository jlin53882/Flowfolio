from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router as api_router
from .core.config import get_settings
from .core.errors import DomainError, domain_error_handler
from .db.migrate import upgrade_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    upgrade_database()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Flowfolio API", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.include_router(api_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "flowfolio", "version": "0.1.0"}

    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    assets = frontend_dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}")
    async def frontend(path: str, _: Request):
        if path.startswith("api/") or path == "health":
            return HTMLResponse("找不到路徑", status_code=404)
        if frontend_dist.is_dir():
            candidate = (frontend_dist / path).resolve()
            try:
                candidate.relative_to(frontend_dist.resolve())
            except ValueError:
                return HTMLResponse("找不到路徑", status_code=404)
            if candidate.is_file():
                return FileResponse(candidate)
            index = frontend_dist / "index.html"
            if index.is_file():
                return FileResponse(index)
        return HTMLResponse(
            (
                "<h1>Flowfolio 前端尚未建置</h1>"
                "<p>請先執行 <code>npm install</code> 與 <code>npm run build</code>。</p>"
            ),
            status_code=503,
        )

    return app


app = create_app()
