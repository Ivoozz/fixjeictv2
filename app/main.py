import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import public, admin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting up FixJeICT application...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FixJeICT application...")


def create_public_app() -> FastAPI:
    """Create the public FastAPI application"""
    app = FastAPI(
        title="FixJeICT - Publiek",
        description="FixJeICT Ticket Systeem - Publieke Routes",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # Add proxy headers middleware for Cloudflare
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
    
    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Mount static files
    static_dir = os.path.join(base_dir, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Include public routers
    app.include_router(public.router)
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "fixjeict-public"}
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        """Handle internal server errors"""
        logger.error(f"Internal error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )
    
    return app


def create_admin_app() -> FastAPI:
    """Create the admin FastAPI application"""
    app = FastAPI(
        title="FixJeICT - Admin",
        description="FixJeICT Ticket Systeem - Admin Routes",
        version="2.0.0",
        lifespan=lifespan
    )
    
    # Add proxy headers middleware for Cloudflare
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
    
    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Mount static files
    static_dir = os.path.join(base_dir, "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Include admin routers with prefix
    app.include_router(admin.router, prefix="/admin")
    
    @app.get("/")
    async def admin_root():
        """Redirect to admin dashboard"""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/admin/")
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "fixjeict-admin"}
    
    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        """Handle internal server errors"""
        logger.error(f"Internal error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )
    
    return app


# Create application instances
public_app = create_public_app()
admin_app = create_admin_app()
