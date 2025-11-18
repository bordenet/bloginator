"""Pydantic models for documents and chunks."""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class QualityRating(str, Enum):
    """Document quality rating.

    Attributes:
        PREFERRED: High-quality, authentic voice (prioritize for generation)
        REFERENCE: Usable content with acceptable quality
        SUPPLEMENTAL: Lower priority content (use sparingly)
        DEPRECATED: Outdated content (avoid using in generation)
    """

    PREFERRED = "preferred"
    REFERENCE = "reference"
    SUPPLEMENTAL = "supplemental"
    DEPRECATED = "deprecated"


class ContentClassification(str, Enum):
    """Content classification for tone and authority level.

    Determines the authoritative stance and prescriptiveness of generated content.

    Attributes:
        GUIDANCE: Suggestive, non-prescriptive recommendations
        BEST_PRACTICE: Established patterns with proven value
        MANDATE: Required standards or policies (strong authority)
        PRINCIPLE: Fundamental truths or values (philosophical)
        OPINION: Personal perspective or viewpoint
    """

    GUIDANCE = "guidance"
    BEST_PRACTICE = "best-practice"
    MANDATE = "mandate"
    PRINCIPLE = "principle"
    OPINION = "opinion"


class TargetAudience(str, Enum):
    """Target audience for content generation.

    Determines which corpus sources and language level to use.

    Attributes:
        IC_ENGINEERS: Individual contributor software engineers
        SENIOR_ENGINEERS: Senior/Staff/Principal engineers
        ENGINEERING_LEADERS: Engineering managers, directors, VPs
        QA_ENGINEERS: Quality assurance and test engineers
        DEVOPS_SRE: DevOps and Site Reliability Engineers
        PRODUCT_MANAGERS: Product management
        TECHNICAL_LEADERSHIP: Technical leads and architects
        ALL_DISCIPLINES: General technical audience (all roles)
        EXECUTIVES: C-level and senior leadership
        GENERAL: Non-technical or broadly technical audience
    """

    IC_ENGINEERS = "ic-engineers"
    SENIOR_ENGINEERS = "senior-engineers"
    ENGINEERING_LEADERS = "engineering-leaders"
    QA_ENGINEERS = "qa-engineers"
    DEVOPS_SRE = "devops-sre"
    PRODUCT_MANAGERS = "product-managers"
    TECHNICAL_LEADERSHIP = "technical-leadership"
    ALL_DISCIPLINES = "all-disciplines"
    EXECUTIVES = "executives"
    GENERAL = "general"


class Document(BaseModel):
    """Document metadata and reference.

    Represents a document in the corpus with metadata for search,
    filtering, and quality weighting.

    Attributes:
        id: Unique document identifier (UUID)
        filename: Original filename
        source_path: Path to source file
        format: Document format (pdf, docx, markdown, txt)
        created_date: Document creation date (if available)
        modified_date: Document modification date (if available)
        indexed_date: When document was indexed
        quality_rating: Content quality rating
        tags: User-defined tags for categorization
        is_external_source: Whether this is external reference material
        attribution_required: Whether attribution is required when quoting
        word_count: Number of words in document
        chunk_ids: List of chunk IDs belonging to this document
        source_name: Name of corpus source (from corpus.yaml)
        voice_notes: Notes about writing voice/style characteristics
        content_checksum: SHA256 checksum for incremental indexing
    """

    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    source_path: Path = Field(..., description="Path to source file")
    format: str = Field(..., description="Document format (pdf, docx, markdown, txt)")
    created_date: datetime | None = Field(None, description="Document creation date")
    modified_date: datetime | None = Field(None, description="Document modification date")
    indexed_date: datetime = Field(
        default_factory=datetime.now, description="When document was indexed"
    )
    quality_rating: QualityRating = Field(
        default=QualityRating.REFERENCE, description="Content quality rating"
    )
    tags: list[str] = Field(default_factory=list, description="User-defined tags")
    is_external_source: bool = Field(
        default=False, description="Whether this is external reference material"
    )
    attribution_required: bool = Field(
        default=False, description="Whether attribution is required when quoting"
    )
    word_count: int = Field(default=0, description="Number of words in document")
    chunk_ids: list[str] = Field(default_factory=list, description="Chunk IDs in this document")
    source_name: str | None = Field(None, description="Name of corpus source (from corpus.yaml)")
    voice_notes: str | None = Field(None, description="Notes about writing voice/style")
    content_checksum: str | None = Field(
        None, description="SHA256 checksum of document content for incremental indexing"
    )

    class Config:
        """Pydantic model configuration."""

        use_enum_values = True


class Chunk(BaseModel):
    """Text chunk with position metadata.

    Represents a chunk of text extracted from a document, with
    position information for context and citation.

    Attributes:
        id: Unique chunk identifier (UUID)
        document_id: ID of parent document
        content: Text content of chunk
        chunk_index: Position in document (0-indexed)
        section_heading: Section heading if available
        char_start: Character offset start in original document
        char_end: Character offset end in original document
    """

    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="ID of parent document")
    content: str = Field(..., description="Text content of chunk")
    chunk_index: int = Field(..., description="Position in document (0-indexed)")
    section_heading: str | None = Field(None, description="Section heading if available")
    char_start: int = Field(..., description="Character offset start in original document")
    char_end: int = Field(..., description="Character offset end in original document")


class GenerationRequest(BaseModel):
    """Request parameters for content generation.

    Encapsulates all parameters needed to generate an outline or draft,
    including topic, classification, and audience targeting.

    Attributes:
        title: Blog post or document title
        keywords: Comma-separated keywords for content selection
        thesis: Main argument or thesis statement
        classification: Content classification (tone and authority level)
        audience: Target audience for content
        num_sections: Number of main sections in outline
        temperature: LLM temperature (0.0-1.0, creativity level)
        min_coverage: Minimum number of source documents per section
    """

    title: str = Field(..., description="Blog post or document title")
    keywords: str = Field(..., description="Comma-separated keywords")
    thesis: str | None = Field(None, description="Main argument or thesis statement")
    classification: ContentClassification = Field(
        default=ContentClassification.GUIDANCE,
        description="Content classification (tone and authority)",
    )
    audience: TargetAudience = Field(
        default=TargetAudience.ALL_DISCIPLINES, description="Target audience"
    )
    num_sections: int = Field(default=5, ge=3, le=10, description="Number of main sections")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="LLM temperature")
    min_coverage: int = Field(default=2, ge=1, description="Min source documents per section")

    class Config:
        """Pydantic model configuration."""

        use_enum_values = True
