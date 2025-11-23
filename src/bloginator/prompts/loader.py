"""Prompt loading and rendering from YAML files."""

from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template
from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """Loaded prompt template with metadata."""

    name: str
    version: str
    description: str
    context: str
    system_prompt: str
    user_prompt_template: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    quality_criteria: list[str] = Field(default_factory=list)
    ai_slop_patterns: dict[str, Any] = Field(default_factory=dict)

    def render_system_prompt(self, **kwargs: Any) -> str:
        """Render system prompt with variables."""
        template = Template(self.system_prompt)
        return template.render(**kwargs)

    def render_user_prompt(self, **kwargs: Any) -> str:
        """Render user prompt with variables."""
        template = Template(self.user_prompt_template)
        return template.render(**kwargs)


class PromptLoader:
    """Load and cache prompt templates from YAML files."""

    def __init__(self, prompts_dir: Path | None = None):
        """Initialize prompt loader.

        Args:
            prompts_dir: Directory containing prompt YAML files.
                        Defaults to project root/prompts directory.
        """
        if prompts_dir is None:
            # Find project root by looking for pyproject.toml
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / "pyproject.toml").exists():
                    prompts_dir = current / "prompts"
                    break
                current = current.parent
            else:
                raise RuntimeError("Could not find project root (pyproject.toml)")

        self.prompts_dir = Path(prompts_dir)
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")

        self._cache: dict[str, PromptTemplate] = {}

    def load(self, prompt_path: str) -> PromptTemplate:
        """Load prompt template from YAML file.

        Args:
            prompt_path: Relative path to prompt file (e.g., "outline/base.yaml")

        Returns:
            Loaded prompt template

        Raises:
            FileNotFoundError: If prompt file doesn't exist
            ValueError: If prompt file is invalid
        """
        # Check cache first
        if prompt_path in self._cache:
            return self._cache[prompt_path]

        # Load from file
        full_path = self.prompts_dir / prompt_path
        if not full_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {full_path}")

        with full_path.open() as f:
            data = yaml.safe_load(f)

        # Validate and create template
        try:
            template = PromptTemplate(**data)
        except Exception as e:
            raise ValueError(f"Invalid prompt file {prompt_path}: {e}") from e

        # Cache and return
        self._cache[prompt_path] = template
        return template

    def clear_cache(self) -> None:
        """Clear the prompt template cache."""
        self._cache.clear()

