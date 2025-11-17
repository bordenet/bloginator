"""FastAPI application for Bloginator web UI."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from bloginator import __version__


logger = logging.getLogger(__name__)

# Get the directory containing this file
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


def create_app(
    title: str = "Bloginator",
    description: str = "Authentic content generation from your own corpus",
    version: str = __version__,
    debug: bool = False,
) -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        title: Application title
        description: Application description
        version: Application version
        debug: Enable debug mode

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        debug=debug,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Configure templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.state.templates = templates

    # Mount static files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register routers
    from bloginator.web.routes import corpus, documents, main

    app.include_router(main.router, tags=["main"])
    app.include_router(corpus.router, prefix="/api/corpus", tags=["corpus"])
    app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": version,
        }

    logger.info(f"Bloginator web UI initialized (version {version})")

    return app


# Create default app instance
app = create_app()
