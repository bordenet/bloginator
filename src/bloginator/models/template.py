"""Template models for custom prompt generation."""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class TemplateType(str, Enum):
    """Type of template."""

    OUTLINE = "outline"
    DRAFT = "draft"
    SECTION = "section"


class PromptTemplate(BaseModel):
    """Custom prompt template for generation.

    Attributes:
        id: Unique template identifier
        name: Display name
        type: Template type (outline, draft, section)
        description: Template description
        template: Jinja2 template string
        variables: List of variable names used in template
        is_builtin: Whether this is a built-in template
        created_date: When template was created
        modified_date: When template was last modified
        tags: Tags for categorization
    """

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Template name")
    type: TemplateType = Field(..., description="Template type")
    description: str = Field(default="", description="Template description")
    template: str = Field(..., description="Jinja2 template content")
    variables: list[str] = Field(default_factory=list, description="Template variables")
    is_builtin: bool = Field(default=False, description="Built-in template flag")
    created_date: datetime = Field(default_factory=datetime.now)
    modified_date: datetime = Field(default_factory=datetime.now)
    tags: list[str] = Field(default_factory=list, description="Tags")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class GenerationPreset(BaseModel):
    """Saved generation configuration preset.

    Attributes:
        id: Unique preset identifier
        name: Display name
        description: Preset description
        template_id: Associated template ID
        classification: Default classification
        audience: Default audience
        temperature: Default temperature
        max_tokens: Default max tokens
        keywords: Default keywords
        tags: Tags for categorization
        created_date: When preset was created
    """

    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Preset name")
    description: str = Field(default="", description="Preset description")
    template_id: str | None = Field(default=None, description="Template ID")
    classification: str = Field(default="guidance", description="Content classification")
    audience: str = Field(default="all-disciplines", description="Target audience")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="LLM temperature")
    max_tokens: int = Field(default=2000, ge=100, le=8000, description="Max tokens")
    keywords: list[str] = Field(default_factory=list, description="Default keywords")
    tags: list[str] = Field(default_factory=list, description="Tags")
    created_date: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


def get_template_dir() -> Path:
    """Get user template directory.

    Returns:
        Path to ~/.bloginator/templates/
    """
    template_dir = Path.home() / ".bloginator" / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    return template_dir


def get_preset_dir() -> Path:
    """Get user preset directory.

    Returns:
        Path to ~/.bloginator/presets/
    """
    preset_dir = Path.home() / ".bloginator" / "presets"
    preset_dir.mkdir(parents=True, exist_ok=True)
    return preset_dir
