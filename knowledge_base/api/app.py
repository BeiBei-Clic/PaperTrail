"""
FastAPI application entry point for PageIndex Knowledge Base.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from knowledge_base.config.settings import get_settings
from knowledge_base.storage.database import get_database
from knowledge_base.api.routes import documents, search
from knowledge_base.api.schemas import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting PageIndex Knowledge Base API...")
    logger.info(f"Version: {settings.version}")
    logger.info(f"Database: {settings.database_url}")

    # Ensure database tables exist
    db = get_database()
    db.create_tables()

    # Check configuration
    if not settings.is_configured:
        logger.warning(
            "OpenAI API key not configured. "
            "Set OPENAI_API_KEY environment variable to enable indexing and search."
        )

    yield

    # Shutdown
    logger.info("Shutting down PageIndex Knowledge Base API...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Local knowledge base deployment using PageIndex tree-based indexing",
    version=settings.version,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(search.router)


@app.get("/", tags=["root"])
def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "status": "running",
        "docs": "/api/docs",
    }


@app.get("/health", tags=["health"], response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.version,
        configured=settings.is_configured,
    )


@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "knowledge_base.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
