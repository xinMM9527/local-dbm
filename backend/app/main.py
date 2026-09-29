from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.routers import connections, schemas, query, ddl, data

app = FastAPI(title="DBM - Local Database Manager", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- API routes ----------
app.include_router(connections.router, prefix="/api/v1")
app.include_router(schemas.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
app.include_router(ddl.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ---------- Serve frontend static files (production mode) ----------
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIST.is_dir():
    # Mount static assets (js/css/images)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve static files or fallback to index.html for SPA routing."""
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
