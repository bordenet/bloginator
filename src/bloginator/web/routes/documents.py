"""Document generation API routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from bloginator.generation.draft_generator import DraftGenerator
from bloginator.generation.llm_client import create_llm_client
from bloginator.generation.outline_generator import OutlineGenerator
from bloginator.generation.refinement_engine import RefinementEngine
from bloginator.models.draft import Draft
from bloginator.models.outline import Outline
from bloginator.search import Searcher

router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for corpus search."""

    query: str
    n_results: int = 10
    index_path: str


class SearchResult(BaseModel):
    """Response model for search result."""

    chunk_id: str
    content: str
    filename: str
    similarity_score: float


class OutlineRequest(BaseModel):
    """Request model for outline generation."""

    title: str
    keywords: list[str]
    thesis: str | None = None
    index_path: str
    llm_model: str = "llama3"


class DraftRequest(BaseModel):
    """Request model for draft generation."""

    outline_json: str
    index_path: str
    llm_model: str = "llama3"
    validate_safety: bool = False
    score_voice: bool = False


class RefineRequest(BaseModel):
    """Request model for draft refinement."""

    draft_json: str
    feedback: str
    index_path: str
    llm_model: str = "llama3"


@router.post("/search")
async def search_corpus(request: SearchRequest):
    """Search the corpus.

    Args:
        request: Search request parameters

    Returns:
        Search results
    """
    index_path = Path(request.index_path)
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index not found")

    try:
        searcher = Searcher(persist_directory=str(index_path))
        results = searcher.search(
            query=request.query,
            n_results=request.n_results,
        )

        return {
            "results": [
                SearchResult(
                    chunk_id=r.chunk_id,
                    content=r.content,
                    filename=r.metadata.get("filename", "unknown"),
                    similarity_score=r.similarity_score,
                )
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/outline/generate")
async def generate_outline(request: OutlineRequest):
    """Generate document outline.

    Args:
        request: Outline generation parameters

    Returns:
        Generated outline
    """
    index_path = Path(request.index_path)
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index not found")

    try:
        searcher = Searcher(persist_directory=str(index_path))
        llm_client = create_llm_client(model=request.llm_model)

        generator = OutlineGenerator(
            llm_client=llm_client,
            searcher=searcher,
        )

        outline = generator.generate_outline(
            title=request.title,
            keywords=request.keywords,
            thesis=request.thesis or "",
        )

        return {
            "outline": outline.model_dump(mode="json"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Outline generation failed: {str(e)}",
        )


@router.post("/draft/generate")
async def generate_draft(request: DraftRequest):
    """Generate document draft from outline.

    Args:
        request: Draft generation parameters

    Returns:
        Generated draft
    """
    index_path = Path(request.index_path)
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index not found")

    try:
        import json

        outline_data = json.loads(request.outline_json)
        outline = Outline(**outline_data)

        searcher = Searcher(persist_directory=str(index_path))
        llm_client = create_llm_client(model=request.llm_model)

        generator = DraftGenerator(
            llm_client=llm_client,
            searcher=searcher,
        )

        draft = generator.generate_draft(
            outline=outline,
            validate_safety=request.validate_safety,
            score_voice=request.score_voice,
        )

        return {
            "draft": draft.model_dump(mode="json"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Draft generation failed: {str(e)}",
        )


@router.post("/draft/refine")
async def refine_draft(request: RefineRequest):
    """Refine a draft with feedback.

    Args:
        request: Refinement parameters

    Returns:
        Refined draft
    """
    index_path = Path(request.index_path)
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Index not found")

    try:
        import json

        draft_data = json.loads(request.draft_json)
        draft = Draft(**draft_data)

        searcher = Searcher(persist_directory=str(index_path))
        llm_client = create_llm_client(model=request.llm_model)

        engine = RefinementEngine(
            llm_client=llm_client,
            searcher=searcher,
        )

        refined = engine.refine_draft(
            draft=draft,
            feedback=request.feedback,
            validate_safety=False,
            score_voice=False,
        )

        return {
            "draft": refined.model_dump(mode="json"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Refinement failed: {str(e)}",
        )


@router.get("/draft/export/{draft_id}")
async def export_draft(
    draft_id: str,
    format: str = "markdown",
    include_citations: bool = True,
):
    """Export draft to various formats.

    Args:
        draft_id: Draft identifier
        format: Export format (markdown, html, text)
        include_citations: Include citations

    Returns:
        Exported content
    """
    # This would load the draft from storage
    # For now, return a placeholder
    return {
        "success": True,
        "format": format,
        "content": "Exported content placeholder",
    }
