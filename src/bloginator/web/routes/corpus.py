"""Corpus management API routes."""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from bloginator.safety.blocklist import BlocklistManager


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
