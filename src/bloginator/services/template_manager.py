"""Template management service for custom prompts."""

import json
import uuid
from pathlib import Path

from jinja2 import Environment, Template, TemplateSyntaxError, meta

from bloginator.models.template import (
    GenerationPreset,
    PromptTemplate,
    TemplateType,
    get_preset_dir,
    get_template_dir,
)


class TemplateManager:
    """Manages prompt templates and generation presets.

    Handles CRUD operations, template rendering, and built-in templates.
    """

    def __init__(self):
        """Initialize template manager."""
        self.template_dir = get_template_dir()
        self.preset_dir = get_preset_dir()
        self.jinja_env = Environment(autoescape=False)

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
            jinja_template = self.jinja_env.from_string(template)
        except TemplateSyntaxError as e:
            raise TemplateSyntaxError(f"Invalid template syntax: {e}") from e

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
        self._save_template(template_obj)

        return template_obj

    def get_template(self, template_id: str) -> PromptTemplate | None:
        """Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            PromptTemplate or None if not found
        """
        template_path = self.template_dir / f"{template_id}.json"

        if not template_path.exists():
            # Check built-in templates
            return self._get_builtin_template(template_id)

        try:
            data = json.loads(template_path.read_text())
            return PromptTemplate(**data)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return None

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
        templates = []

        # Load user templates
        for template_file in self.template_dir.glob("*.json"):
            try:
                data = json.loads(template_file.read_text())
                template = PromptTemplate(**data)

                if type is None or template.type == type:
                    templates.append(template)
            except (json.JSONDecodeError, ValueError):
                continue

        # Add built-in templates
        if include_builtin:
            builtin = self._get_builtin_templates()
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

        template_path = self.template_dir / f"{template_id}.json"
        template_path.unlink(missing_ok=True)

        return True

    def render_template(self, template_id: str, **kwargs) -> str:
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
            raise TemplateSyntaxError(f"Template rendering failed: {e}") from e

    def create_preset(
        self,
        name: str,
        description: str = "",
        template_id: str | None = None,
        **kwargs,
    ) -> GenerationPreset:
        """Create a generation preset.

        Args:
            name: Preset name
            description: Preset description
            template_id: Associated template ID
            **kwargs: Preset parameters

        Returns:
            Created GenerationPreset
        """
        preset = GenerationPreset(
            id=str(uuid.uuid4()), name=name, description=description, template_id=template_id, **kwargs
        )

        self._save_preset(preset)

        return preset

    def get_preset(self, preset_id: str) -> GenerationPreset | None:
        """Get preset by ID.

        Args:
            preset_id: Preset identifier

        Returns:
            GenerationPreset or None if not found
        """
        preset_path = self.preset_dir / f"{preset_id}.json"

        if not preset_path.exists():
            return None

        try:
            data = json.loads(preset_path.read_text())
            return GenerationPreset(**data)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return None

    def list_presets(self) -> list[GenerationPreset]:
        """List all presets.

        Returns:
            List of GenerationPreset objects
        """
        presets = []

        for preset_file in self.preset_dir.glob("*.json"):
            try:
                data = json.loads(preset_file.read_text())
                presets.append(GenerationPreset(**data))
            except (json.JSONDecodeError, ValueError):
                continue

        return sorted(presets, key=lambda p: p.name)

    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset.

        Args:
            preset_id: Preset identifier

        Returns:
            True if deleted, False if not found
        """
        preset_path = self.preset_dir / f"{preset_id}.json"

        if not preset_path.exists():
            return False

        preset_path.unlink()

        return True

    def _save_template(self, template: PromptTemplate) -> None:
        """Save template to disk.

        Args:
            template: Template to save
        """
        template_path = self.template_dir / f"{template.id}.json"
        template_path.write_text(template.model_dump_json(indent=2))

    def _save_preset(self, preset: GenerationPreset) -> None:
        """Save preset to disk.

        Args:
            preset: Preset to save
        """
        preset_path = self.preset_dir / f"{preset.id}.json"
        preset_path.write_text(preset.model_dump_json(indent=2))

    def _get_builtin_template(self, template_id: str) -> PromptTemplate | None:
        """Get built-in template by ID.

        Args:
            template_id: Template identifier

        Returns:
            PromptTemplate or None if not found
        """
        builtins = {t.id: t for t in self._get_builtin_templates()}
        return builtins.get(template_id)

    def _get_builtin_templates(self) -> list[PromptTemplate]:
        """Get all built-in templates.

        Returns:
            List of built-in PromptTemplate objects
        """
        return [
            # Technical writing template
            PromptTemplate(
                id="builtin-technical",
                name="Technical Writing",
                type=TemplateType.OUTLINE,
                description="Formal technical documentation style",
                template="""Create a technical outline for: {{ title }}

Focus on precision, accuracy, and thorough documentation.
Use formal tone, avoid ambiguity, include technical details.

Keywords: {{ keywords }}
{% if thesis %}Thesis: {{ thesis }}{% endif %}

Requirements:
- {{ num_sections }} main sections
- Technical accuracy
- Clear structure
- Reference relevant technical concepts
""",
                variables=["title", "keywords", "thesis", "num_sections"],
                is_builtin=True,
                tags=["technical", "documentation", "formal"],
            ),
            # Blog post template
            PromptTemplate(
                id="builtin-blog",
                name="Blog Post",
                type=TemplateType.OUTLINE,
                description="Conversational blog post style",
                template="""Create an engaging blog outline for: {{ title }}

Use conversational tone, relatable examples, personal insights.
Make it accessible and engaging for general readers.

Keywords: {{ keywords }}
{% if thesis %}Key message: {{ thesis }}{% endif %}

Requirements:
- {{ num_sections }} main sections
- Engaging introduction
- Real-world examples
- Actionable takeaways
""",
                variables=["title", "keywords", "thesis", "num_sections"],
                is_builtin=True,
                tags=["blog", "casual", "engaging"],
            ),
            # Executive summary template
            PromptTemplate(
                id="builtin-executive",
                name="Executive Summary",
                type=TemplateType.OUTLINE,
                description="High-level strategic overview",
                template="""Create an executive summary outline for: {{ title }}

Focus on high-level insights, strategic implications, key decisions.
Target executive audience - concise, actionable, business-focused.

Keywords: {{ keywords }}
{% if thesis %}Strategic thesis: {{ thesis }}{% endif %}

Requirements:
- {{ num_sections }} key points
- Business impact focus
- Data-driven insights
- Actionable recommendations
""",
                variables=["title", "keywords", "thesis", "num_sections"],
                is_builtin=True,
                tags=["executive", "business", "strategic"],
            ),
            # Tutorial template
            PromptTemplate(
                id="builtin-tutorial",
                name="Tutorial/How-To",
                type=TemplateType.OUTLINE,
                description="Step-by-step instructional guide",
                template="""Create a tutorial outline for: {{ title }}

Provide clear step-by-step instructions with examples.
Focus on practical learning and hands-on guidance.

Keywords: {{ keywords }}
{% if thesis %}Learning goal: {{ thesis }}{% endif %}

Requirements:
- {{ num_sections }} main sections
- Clear prerequisites
- Step-by-step instructions
- Examples and exercises
- Common pitfalls
""",
                variables=["title", "keywords", "thesis", "num_sections"],
                is_builtin=True,
                tags=["tutorial", "how-to", "instructional"],
            ),
        ]
