"""Tests for prompt loader."""


import pytest

from bloginator.prompts.loader import PromptLoader, PromptTemplate


def test_prompt_loader_initialization():
    """Test PromptLoader finds prompts directory."""
    loader = PromptLoader()
    assert loader.prompts_dir.exists()
    assert loader.prompts_dir.name == "prompts"


def test_load_outline_prompt():
    """Test loading outline/base.yaml prompt."""
    loader = PromptLoader()
    template = loader.load("outline/base.yaml")

    assert template.name == "outline-base"
    assert template.version == "1.0.0"
    assert "outline" in template.description.lower()
    assert len(template.system_prompt) > 0
    assert len(template.user_prompt_template) > 0
    assert "{{title}}" in template.user_prompt_template
    assert len(template.quality_criteria) > 0


def test_load_draft_prompt():
    """Test loading draft/base.yaml prompt."""
    loader = PromptLoader()
    template = loader.load("draft/base.yaml")

    assert template.name == "draft-base"
    assert template.version == "1.0.0"
    assert len(template.system_prompt) > 0
    assert len(template.user_prompt_template) > 0
    assert "em_dashes" in template.ai_slop_patterns
    assert template.ai_slop_patterns["em_dashes"]["severity"] == "critical"


def test_load_refinement_prompt():
    """Test loading refinement/base.yaml prompt."""
    loader = PromptLoader()
    template = loader.load("refinement/base.yaml")

    assert template.name == "refinement-base"
    assert template.version == "1.0.0"
    assert "{{title}}" in template.user_prompt_template
    assert "{{content}}" in template.user_prompt_template
    assert "{{instructions}}" in template.user_prompt_template


def test_render_system_prompt():
    """Test rendering system prompt with variables."""
    loader = PromptLoader()
    template = loader.load("outline/base.yaml")

    rendered = template.render_system_prompt(
        classification_context="Test classification",
        audience_context="Test audience"
    )

    assert "Test classification" in rendered
    assert "Test audience" in rendered


def test_render_user_prompt():
    """Test rendering user prompt with variables."""
    loader = PromptLoader()
    template = loader.load("outline/base.yaml")

    rendered = template.render_user_prompt(
        title="Test Title",
        classification="guidance",
        audience="ic-engineers",
        keywords=["testing", "quality"],
        thesis="Test thesis statement",
        num_sections=5
    )

    assert "Test Title" in rendered
    assert "guidance" in rendered
    assert "ic-engineers" in rendered
    assert "testing" in rendered
    assert "quality" in rendered


def test_prompt_caching():
    """Test that prompts are cached after first load."""
    loader = PromptLoader()

    # Load twice
    template1 = loader.load("outline/base.yaml")
    template2 = loader.load("outline/base.yaml")

    # Should be same object (cached)
    assert template1 is template2


def test_clear_cache():
    """Test clearing prompt cache."""
    loader = PromptLoader()

    # Load and cache
    template1 = loader.load("outline/base.yaml")

    # Clear cache
    loader.clear_cache()

    # Load again - should be different object
    template2 = loader.load("outline/base.yaml")

    assert template1 is not template2
    assert template1.name == template2.name  # But same content


def test_load_nonexistent_prompt():
    """Test loading non-existent prompt raises error."""
    loader = PromptLoader()

    with pytest.raises(FileNotFoundError):
        loader.load("nonexistent/prompt.yaml")


def test_prompt_template_defaults():
    """Test PromptTemplate default values."""
    template = PromptTemplate(
        name="test",
        version="1.0.0",
        description="Test prompt",
        context="Test context",
        system_prompt="System",
        user_prompt_template="User {{var}}"
    )

    assert template.parameters == {}
    assert template.quality_criteria == []
    assert template.ai_slop_patterns == {}

