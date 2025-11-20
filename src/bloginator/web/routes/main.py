"""Main UI routes."""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> Any:
    """Home page."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "Bloginator",
        },
    )


@router.get("/corpus", response_class=HTMLResponse)
async def corpus_page(request: Request) -> Any:
    """Corpus management page."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        "corpus.html",
        {
            "request": request,
            "title": "Corpus Management",
        },
    )


@router.get("/create", response_class=HTMLResponse)
async def create_page(request: Request) -> Any:
    """Document creation page."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        "create.html",
        {
            "request": request,
            "title": "Create Document",
        },
    )


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request) -> Any:
    """Search page."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "title": "Search Corpus",
        },
    )
