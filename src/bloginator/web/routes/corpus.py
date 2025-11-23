"""Corpus management API routes."""

import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from bloginator.extraction.extractor import DocumentExtractor
from bloginator.safety.blocklist_manager import BlocklistManager


router = APIRouter()


class BlocklistEntryRequest(BaseModel):
    """Request model for adding blocklist entry."""

    pattern: str
    pattern_type: str = "exact"
    category: str = "other"
    notes: str = ""


class BlocklistEntryResponse(BaseModel):
    """Response model for blocklist entry."""

    id: str
    pattern: str
    pattern_type: str
    category: str
    notes: str
    created_at: str


class IndexStatsResponse(BaseModel):
    """Response model for index statistics."""

    total_documents: int
    total_chunks: int
    index_path: str


@router.post("/upload")
async def upload_documents(
    files: list[UploadFile] = File(...),
    quality: str | None = Form(None),
    tags: str | None = Form(None),
) -> dict[str, Any]:
    """Upload and extract documents.

    Args:
        files: List of files to upload
        quality: Quality rating (preferred, standard, reference)
        tags: Comma-separated tags

    Returns:
        Extraction results
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Create temporary directory for uploaded files
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Save uploaded files
        file_paths = []
        for file in files:
            file_path = temp_path / file.filename
            content = await file.read()
            with file_path.open("wb") as f:
                f.write(content)
            file_paths.append(file_path)

        # Extract documents
        extractor = DocumentExtractor()
        output_dir = temp_path / "extracted"
        output_dir.mkdir()

        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        results = []
        for file_path in file_paths:
            try:
                extracted = extractor.extract_file(
                    file_path=file_path,
                    output_dir=output_dir,
                    quality=quality,
                    tags=tag_list,
                )
                results.extend(extracted)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to extract {file_path.name}: {str(e)}",
                )

        return {
            "success": True,
            "extracted_count": len(results),
            "documents": [
                {
                    "filename": r.source_file.name,
                    "quality": r.quality_rating,
                    "tags": r.tags,
                }
                for r in results
            ],
        }


@router.post("/index/create")
async def create_index(
    corpus_path: str = Form(...),
    index_path: str = Form(...),
) -> dict[str, Any]:
    """Create vector index from extracted corpus.

    Args:
        corpus_path: Path to extracted corpus directory
        index_path: Path where index should be created

    Returns:
        Indexing results
    """
    corpus_dir = Path(corpus_path)
    if not corpus_dir.exists():
        raise HTTPException(status_code=404, detail="Corpus directory not found")

    try:
        # TODO: Implement batch indexing API for web routes
        # Current CorpusIndexer API requires indexing documents one at a time
        # See src/bloginator/indexing/indexer.py for available methods
        raise NotImplementedError(
            "Batch corpus indexing not yet implemented for web API. "
            "Use CLI: bloginator index <corpus_dir> -o <index_dir>"
        )
    except NotImplementedError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")


@router.get("/index/stats")
async def get_index_stats(index_path: str) -> IndexStatsResponse:
    """Get statistics about an index.

    Args:
        index_path: Path to index directory

    Returns:
        Index statistics
    """
    index_dir = Path(index_path)
    if not index_dir.exists():
        raise HTTPException(status_code=404, detail="Index not found")

    try:
        # TODO: Implement index stats API for web routes
        # Current CorpusIndexer doesn't have get_index_stats method
        # Use CorpusSearcher.get_stats() instead or implement new method
        raise NotImplementedError(
            "Index statistics not yet implemented for web API. "
            "Use CLI: bloginator search <index_dir> --stats"
        )
    except NotImplementedError:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/blocklist/add")
async def add_blocklist_entry(
    blocklist_path: str,
    entry: BlocklistEntryRequest,
) -> BlocklistEntryResponse:
    """Add entry to blocklist.

    Args:
        blocklist_path: Path to blocklist file
        entry: Entry to add

    Returns:
        Added entry
    """
    try:
        manager = BlocklistManager(blocklist_file=Path(blocklist_path))

        from bloginator.models.blocklist import BlocklistCategory, BlocklistPatternType

        new_entry = manager.add_entry(
            pattern=entry.pattern,
            pattern_type=BlocklistPatternType(entry.pattern_type),
            category=BlocklistCategory(entry.category),
            notes=entry.notes,
        )

        return BlocklistEntryResponse(
            id=new_entry.id,
            pattern=new_entry.pattern,
            pattern_type=new_entry.pattern_type.value,
            category=new_entry.category.value,
            notes=new_entry.notes,
            created_at=new_entry.created_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add entry: {str(e)}")


@router.get("/blocklist/list")
async def list_blocklist_entries(blocklist_path: str) -> dict[str, list[BlocklistEntryResponse]]:
    """List all blocklist entries.

    Args:
        blocklist_path: Path to blocklist file

    Returns:
        List of entries
    """
    try:
        manager = BlocklistManager(blocklist_file=Path(blocklist_path))

        return {
            "entries": [
                BlocklistEntryResponse(
                    id=e.id,
                    pattern=e.pattern,
                    pattern_type=e.pattern_type.value,
                    category=e.category.value,
                    notes=e.notes,
                    created_at=e.created_at.isoformat(),
                )
                for e in manager.entries
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list entries: {str(e)}")


@router.delete("/blocklist/{entry_id}")
async def delete_blocklist_entry(blocklist_path: str, entry_id: str) -> dict[str, Any]:
    """Delete blocklist entry.

    Args:
        blocklist_path: Path to blocklist file
        entry_id: ID of entry to delete

    Returns:
        Success status
    """
    try:
        manager = BlocklistManager(blocklist_file=Path(blocklist_path))

        if manager.remove_entry(entry_id):
            return {"success": True, "deleted_id": entry_id}
        else:
            raise HTTPException(status_code=404, detail="Entry not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete entry: {str(e)}")
