"""
Admin application - runs on port 5001
Separate from main app for security (can be firewalled from public access)
Shares the same database with main app
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.proxyheaders import ProxyHeadersMiddleware

from fixjeict_app.config import settings
from fixjeict_app.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting FixJeICT Admin v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database (same as main app)
    init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down FixJeICT Admin")


# Create FastAPI application
admin_app = FastAPI(
    title=f"{settings.APP_NAME} Admin",
    version=settings.APP_VERSION,
    description="FixJeICT Admin Portal",
    docs_url="/admin/docs" if settings.DEBUG else None,
    redoc_url="/admin/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# Middleware
# Proxy headers for Cloudflare tunnel
admin_app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

# Session middleware for admin authentication
admin_app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="fixjeict_admin_session",
    max_age=86400 * 1,  # 1 day for admin sessions
    same_site="strict",
    https_only=settings.is_production,
)

# GZip compression
admin_app.add_middleware(GZipMiddleware, minimum_size=1000)


# Exception handlers
@admin_app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "success": False},
    )


@admin_app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> HTMLResponse:
    """404 error handler"""
    return HTMLResponse(content="<h1>404 - Pagina niet gevonden</h1>", status_code=404)


# Static files (shared with main app)
static_dir = settings.BASE_DIR / "fixjeict_app" / "static"
if static_dir.exists():
    admin_app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Static files mounted from: {static_dir}")


# Include only admin router
from fixjeict_app.routers import admin

admin_app.include_router(admin.router, tags=["Admin"])


# Health check endpoint
@admin_app.get("/admin/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "app": f"{settings.APP_NAME} Admin",
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "admin_app:admin_app",
        host=settings.HOST,
        port=settings.ADMIN_PORT,
        reload=settings.DEBUG,
        workers=1,  # Always single worker for admin
    )
