"""Template management service for custom prompts."""

import uuid

from jinja2 import Environment, TemplateSyntaxError, meta

from bloginator.models.template import (
    GenerationPreset,
    PromptTemplate,
    TemplateType,
    get_preset_dir,
    get_template_dir,
)
from bloginator.services._builtin_templates import get_builtin_templates
from bloginator.services._template_storage import (
    delete_preset_from_disk,
    delete_template_from_disk,
    list_presets_from_disk,
    list_templates_from_disk,
    load_preset_from_disk,
    load_template_from_disk,
    save_preset,
    save_template,
)


class TemplateManager:
    """Manages prompt templates and generation presets.

    Handles CRUD operations, template rendering, and built-in templates.
    """

    def __init__(self) -> None:
        """Initialize template manager."""
        self.template_dir = get_template_dir()
        self.preset_dir = get_preset_dir()
        # nosec B701: These are plain text templates for LLM prompts, not HTML.
        # No XSS risk as output is not rendered in a browser.
        self.jinja_env = Environment(autoescape=False)  # nosec B701

    def create_template(
        self,
        name: str,
        type: TemplateType,
        template: str,
        description: str = "",
        tags: list[str] | None = None,
    ) -> PromptTemplate:
        """Create a new template.

        Args:
            name: Template name
            type: Template type
            template: Jinja2 template string
            description: Template description
            tags: Optional tags

        Returns:
            Created PromptTemplate

        Raises:
            TemplateSyntaxError: If template has syntax errors
        """
        # Validate template syntax
        try:
            _ = self.jinja_env.from_string(template)
        except TemplateSyntaxError as e:
            # Wrap the original error with a more descriptive message while preserving the cause.
            raise TemplateSyntaxError(f"Invalid template syntax: {e}", 0) from e

        # Extract variables from template
        ast = self.jinja_env.parse(template)
        variables = list(meta.find_undeclared_variables(ast))

        # Create template object
        template_obj = PromptTemplate(
            id=str(uuid.uuid4()),
            name=name,
            type=type,
            description=description,
            template=template,
            variables=variables,
            tags=tags or [],
        )

        # Save to disk
        save_template(template_obj, self.template_dir)

        return template_obj

    def get_template(self, template_id: str) -> PromptTemplate | None:
        """Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            PromptTemplate or None if not found
        """
        # Try loading from disk
        template = load_template_from_disk(template_id, self.template_dir)
        if template is not None:
            return template

        # Check built-in templates
        return self._get_builtin_template(template_id)

    def list_templates(
        self, type: TemplateType | None = None, include_builtin: bool = True
    ) -> list[PromptTemplate]:
        """List all templates.

        Args:
            type: Filter by template type
            include_builtin: Include built-in templates

        Returns:
            List of PromptTemplate objects
        """
        # Load user templates from disk
        templates = list_templates_from_disk(self.template_dir)

        # Filter by type if specified
        if type is not None:
            templates = [t for t in templates if t.type == type]

        # Add built-in templates
        if include_builtin:
            builtin = get_builtin_templates()
            if type is None:
                templates.extend(builtin)
            else:
                templates.extend([t for t in builtin if t.type == type])

        return sorted(templates, key=lambda t: t.name)

    def delete_template(self, template_id: str) -> bool:
        """Delete a template.

        Args:
            template_id: Template identifier

        Returns:
            True if deleted, False if not found or is built-in
        """
        template = self.get_template(template_id)

        if template is None or template.is_builtin:
            return False

        return delete_template_from_disk(template_id, self.template_dir)

    def render_template(self, template_id: str, **kwargs: object) -> str:
        """Render a template with variables.

        Args:
            template_id: Template identifier
            **kwargs: Template variables

        Returns:
            Rendered template string

        Raises:
            ValueError: If template not found
            TemplateSyntaxError: If rendering fails
        """
        template = self.get_template(template_id)

        if template is None:
            raise ValueError(f"Template not found: {template_id}")

        try:
            jinja_template = self.jinja_env.from_string(template.template)
            return jinja_template.render(**kwargs)
        except Exception as e:
            # Normalize rendering failures as TemplateSyntaxError so callers can
            # handle both parse-time and render-time issues consistently.
            raise TemplateSyntaxError(f"Template rendering failed: {e}", 0) from e

    def create_preset(
        self,
        name: str,
        description: str = "",
        template_id: str | None = None,
        classification: str = "guidance",
        audience: str = "all-disciplines",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        keywords: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> GenerationPreset:
        """Create a generation preset.

        This API mirrors :class:`GenerationPreset` fields explicitly rather than
        accepting arbitrary ``**kwargs``. That keeps the preset schema
        discoverable and MyPy-friendly while still providing sensible defaults.

        Args:
            name: Preset name
            description: Preset description
            template_id: Associated template ID
            classification: Default classification
            audience: Default audience
            temperature: Default LLM temperature
            max_tokens: Default max tokens
            keywords: Default keywords
            tags: Tags for categorization

        Returns:
            Created GenerationPreset
        """
        preset = GenerationPreset(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            template_id=template_id,
            classification=classification,
            audience=audience,
            temperature=temperature,
            max_tokens=max_tokens,
            keywords=keywords or [],
            tags=tags or [],
        )

        save_preset(preset, self.preset_dir)

        return preset

    def get_preset(self, preset_id: str) -> GenerationPreset | None:
        """Get preset by ID.

        Args:
            preset_id: Preset identifier

        Returns:
            GenerationPreset or None if not found
        """
        return load_preset_from_disk(preset_id, self.preset_dir)

    def list_presets(self) -> list[GenerationPreset]:
        """List all presets.

        Returns:
            List of GenerationPreset objects
        """
        presets = list_presets_from_disk(self.preset_dir)
        return sorted(presets, key=lambda p: p.name)

    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset.

        Args:
            preset_id: Preset identifier

        Returns:
            True if deleted, False if not found
        """
        return delete_preset_from_disk(preset_id, self.preset_dir)

    def _get_builtin_template(self, template_id: str) -> PromptTemplate | None:
        """Get built-in template by ID.

        Args:
            template_id: Template identifier

        Returns:
            PromptTemplate or None if not found
        """
        builtins = {t.id: t for t in get_builtin_templates()}
        return builtins.get(template_id)
