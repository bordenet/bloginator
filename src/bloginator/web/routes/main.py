"""Main UI routes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse


if TYPE_CHECKING:  # pragma: no cover
    from fastapi.templating import Jinja2Templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> Any:
    """Home page."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": "Bloginator",
        },
    )


@router.get("/corpus", response_class=HTMLResponse)
async def corpus_page(request: Request) -> Any:
    """Corpus management page."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "corpus.html",
        {
            "title": "Corpus Management",
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_page(request: Request) -> Any:
    """Document creation page."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "create.html",
        {
            "title": "Create Document",
        },
    )


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request) -> Any:
    """Search page."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "search.html",
        {
            "title": "Search Corpus",
        },
    )
