"""Tests for TemplateManager service."""

from pathlib import Path

import pytest
from jinja2 import TemplateSyntaxError

from bloginator.models.template import TemplateType
from bloginator.services.template_manager import TemplateManager


@pytest.fixture()
def temp_template_manager(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TemplateManager:
    monkeypatch.setattr("bloginator.models.template.get_template_dir", lambda: tmp_path / "tpls")
    monkeypatch.setattr("bloginator.models.template.get_preset_dir", lambda: tmp_path / "presets")
    return TemplateManager()


def test_create_and_get_template_roundtrip(temp_template_manager: TemplateManager) -> None:
    manager = temp_template_manager
    template = manager.create_template(
        name="My Template",
        type=TemplateType.DRAFT,
        template="Title: {{ title }}",
        description="Simple template",
        tags=["test"],
    )

    loaded = manager.get_template(template.id)
    assert loaded is not None
    assert loaded.name == "My Template"
    assert "title" in loaded.required_variables


def test_create_template_invalid_jinja_raises(temp_template_manager: TemplateManager) -> None:
    manager = temp_template_manager
    with pytest.raises(TemplateSyntaxError):
        manager.create_template(
            name="Bad",
            type=TemplateType.DRAFT,
            template="{% for x in %}",
        )


def test_list_and_delete_templates(temp_template_manager: TemplateManager) -> None:
    manager = temp_template_manager
    tpl = manager.create_template(
        name="To Delete",
        type=TemplateType.DRAFT,
        template="{{ body }}",
    )

    templates = manager.list_templates()
    assert any(t.id == tpl.id for t in templates)

    deleted = manager.delete_template(tpl.id)
    assert deleted is True

    templates_after = manager.list_templates()
    assert all(t.id != tpl.id for t in templates_after)


def test_render_template_success_and_failure(temp_template_manager: TemplateManager) -> None:
    manager = temp_template_manager
    tpl = manager.create_template(
        name="Render",
        type=TemplateType.DRAFT,
        template="Hello {{ name }}",
    )

    rendered = manager.render_template(tpl.id, name="World")
    assert rendered == "Hello World"

    with pytest.raises(ValueError):
        manager.render_template("nonexistent", name="X")

    bad_tpl = manager.create_template(
        name="Bad Render",
        type=TemplateType.DRAFT,
        template="{{ 1/0 }}",
    )
    with pytest.raises(TemplateSyntaxError):
        manager.render_template(bad_tpl.id)


def test_create_and_list_presets(temp_template_manager: TemplateManager) -> None:
    manager = temp_template_manager
    tpl = manager.create_template(
        name="Preset Template",
        type=TemplateType.DRAFT,
        template="{{ body }}",
    )

    preset = manager.create_preset(
        name="My Preset",
        description="My preset description",
        template_id=tpl.id,
        classification="guidance",
        audience="all-disciplines",
        temperature=0.7,
        max_tokens=2000,
        keywords=["blog", "test"],
        tags=["unit-test"],
    )

    loaded_preset = manager.get_preset(preset.id)
    assert loaded_preset is not None
    assert loaded_preset.name == "My Preset"

    presets = manager.list_presets()
    assert any(p.id == preset.id for p in presets)

    deleted = manager.delete_preset(preset.id)
    assert deleted is True
