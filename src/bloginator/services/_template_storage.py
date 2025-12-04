"""File I/O operations for templates and presets."""

import json
from pathlib import Path

from bloginator.models.template import GenerationPreset, PromptTemplate


def save_template(template: PromptTemplate, template_dir: Path) -> None:
    """Save template to disk.

    Args:
        template: Template to save
        template_dir: Directory to save template in
    """
    template_path = template_dir / f"{template.id}.json"
    template_path.write_text(template.model_dump_json(indent=2))


def load_template_from_disk(template_id: str, template_dir: Path) -> PromptTemplate | None:
    """Load template from disk.

    Args:
        template_id: Template identifier
        template_dir: Directory containing templates

    Returns:
        PromptTemplate or None if not found or invalid
    """
    template_path = template_dir / f"{template_id}.json"

    if not template_path.exists():
        return None

    try:
        data = json.loads(template_path.read_text())
        return PromptTemplate(**data)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return None


def delete_template_from_disk(template_id: str, template_dir: Path) -> bool:
    """Delete template from disk.

    Args:
        template_id: Template identifier
        template_dir: Directory containing templates

    Returns:
        True if deleted, False if not found
    """
    template_path = template_dir / f"{template_id}.json"
    template_path.unlink(missing_ok=True)
    return True


def list_templates_from_disk(template_dir: Path) -> list[PromptTemplate]:
    """Load all templates from disk.

    Args:
        template_dir: Directory containing templates

    Returns:
        List of PromptTemplate objects
    """
    templates = []

    for template_file in template_dir.glob("*.json"):
        try:
            data = json.loads(template_file.read_text())
            template = PromptTemplate(**data)
            templates.append(template)
        except (json.JSONDecodeError, ValueError):
            continue

    return templates


def save_preset(preset: GenerationPreset, preset_dir: Path) -> None:
    """Save preset to disk.

    Args:
        preset: Preset to save
        preset_dir: Directory to save preset in
    """
    preset_path = preset_dir / f"{preset.id}.json"
    preset_path.write_text(preset.model_dump_json(indent=2))


def load_preset_from_disk(preset_id: str, preset_dir: Path) -> GenerationPreset | None:
    """Load preset from disk.

    Args:
        preset_id: Preset identifier
        preset_dir: Directory containing presets

    Returns:
        GenerationPreset or None if not found or invalid
    """
    preset_path = preset_dir / f"{preset_id}.json"

    if not preset_path.exists():
        return None

    try:
        data = json.loads(preset_path.read_text())
        return GenerationPreset(**data)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return None


def delete_preset_from_disk(preset_id: str, preset_dir: Path) -> bool:
    """Delete preset from disk.

    Args:
        preset_id: Preset identifier
        preset_dir: Directory containing presets

    Returns:
        True if deleted, False if not found
    """
    preset_path = preset_dir / f"{preset_id}.json"

    if not preset_path.exists():
        return False

    preset_path.unlink()
    return True


def list_presets_from_disk(preset_dir: Path) -> list[GenerationPreset]:
    """Load all presets from disk.

    Args:
        preset_dir: Directory containing presets

    Returns:
        List of GenerationPreset objects
    """
    presets = []

    for preset_file in preset_dir.glob("*.json"):
        try:
            data = json.loads(preset_file.read_text())
            presets.append(GenerationPreset(**data))
        except (json.JSONDecodeError, ValueError):
            continue

    return presets
