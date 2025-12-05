"""Corpus configuration settings models.

Contains extraction and indexing settings dataclasses.
"""

from pydantic import BaseModel, Field


class ExtractionSettings(BaseModel):
    """Global extraction settings.

    Attributes:
        chunk_size: Maximum characters per chunk
        follow_symlinks: Whether to follow symbolic links
        recursive: Whether to scan subdirectories
        include_extensions: File extensions to include
        ignore_patterns: Glob patterns to ignore
    """

    chunk_size: int = Field(default=1000, description="Maximum characters per chunk")
    follow_symlinks: bool = Field(default=True, description="Follow symbolic links")
    recursive: bool = Field(default=True, description="Scan subdirectories")
    include_extensions: list[str] = Field(
        default_factory=lambda: [
            # Documents
            ".md", ".markdown", ".txt", ".text", ".pdf", ".docx", ".doc",
            # Rich text
            ".rtf", ".odt", ".html", ".htm",
            # Presentations
            ".pptx", ".ppt",
            # Data/structured
            ".xlsx", ".xml",
            # Email
            ".eml", ".msg",
            # Images (OCR)
            ".png", ".jpg", ".jpeg", ".webp",
        ],
        description="File extensions to include",
    )
    ignore_patterns: list[str] = Field(
        default_factory=lambda: [".*", "_*", "draft_*", "TODO.md", "README.md"],
        description="Glob patterns to ignore",
    )


class IndexingSettings(BaseModel):
    """Indexing and search weighting settings.

    Attributes:
        quality_weights: Multipliers for each quality level
        recency_decay: Weight reduction per year old (0.0-1.0)
        tag_boosts: Multipliers for specific tags
    """

    quality_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "preferred": 1.5,
            "reference": 1.0,
            "supplemental": 0.7,
            "deprecated": 0.3,
        },
        description="Quality level multipliers",
    )
    recency_decay: float = Field(
        default=0.1,
        description="Weight reduction per year old",
    )
    tag_boosts: dict[str, float] = Field(
        default_factory=dict,
        description="Tag-based boost multipliers",
    )
