"""
Main FastAPI application for AEON
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    setup_logging()
    print("🚀 AEON starting up...")
    
    # Initialize database
    from app.database.session import create_tables
    create_tables()
    print("📊 Database initialized...")
    
    yield
    # Shutdown
    print("🛑 AEON shutting down...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AEON - Digital AI Twin with persistent memory",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_application()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AEON - Digital AI Twin",
        "version": settings.app_version,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "aeon",
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    ) 