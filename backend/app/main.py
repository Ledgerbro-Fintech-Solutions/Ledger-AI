import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.session_manager import session_manager

from backend.app.routes import (
    health_routes,
    ocr_routes,
    invoice_routes,
    chat_upload_routes,
    chat_analyze_routes
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"=== {settings.app_name} v{settings.app_version} Starting ===")
    logger.info(f"Vision Model: {settings.groq_model_extraction}")
    logger.info(f"Standardization Model: {settings.groq_model_standardization}")
    logger.info(f"Chat Model: {settings.groq_model_chat}")
    logger.info(f"Frontend Static Directory: {settings.frontend_dist_dir} (exists: {os.path.exists(settings.frontend_dist_dir)})")
    yield
    # Shutdown
    session_manager.cleanup_all_sessions()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# --- Register API Routers --- #

# 1. Root-level legacy compatibility endpoints
app.include_router(health_routes.router)
app.include_router(ocr_routes.router)
app.include_router(invoice_routes.router)

# 2. /api/v1 endpoints (Chatbot compatibility)
app.include_router(health_routes.router, prefix="/api/v1")
app.include_router(chat_upload_routes.router, prefix="/api/v1")
app.include_router(chat_analyze_routes.router, prefix="/api/v1")

# 3. Clean unified /api routes for frontend
app.include_router(health_routes.router, prefix="/api")
app.include_router(ocr_routes.router, prefix="/api/ocr")
app.include_router(invoice_routes.router, prefix="/api/ocr")
app.include_router(chat_upload_routes.router, prefix="/api/chat")
app.include_router(chat_analyze_routes.router, prefix="/api/chat")


# --- Static Frontend Serving & Single-Page Application (SPA) Fallback --- #
dist_dir = os.path.abspath(settings.frontend_dist_dir)

if settings.serve_frontend and os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Ignore API routes and docs
        if full_path.startswith(("api", "docs", "redoc", "openapi.json", "extract-ocr-data", "process-invoices", "health")):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        file_path = os.path.join(dist_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html for SPA client-side routing
        index_file = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
else:
    @app.get("/")
    async def root():
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/health"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port, reload=True)
