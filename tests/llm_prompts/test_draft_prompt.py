"""Tests for draft generation prompt with Claude Sonnet 4.5.

Tests validate that the draft prompt produces:
1. Extreme brevity (60-80 words, max 100)
2. No redundancy (each concept stated once)
3. Source grounding (no hallucination)
4. Table usage for comparisons
5. No PowerPoint bullets
6. No AI slop
"""

import pytest

from bloginator.prompts.loader import PromptLoader
from tests.llm_prompts.conftest import ClaudeSonnet45Client


class TestDraftPromptBrevity:
    """Test draft prompt produces extremely brief content."""

    def test_word_count_compliance(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
        sample_section_content: str,
    ):
        """Draft sections should be 60-80 words, never exceed 100."""
        prompt_template = prompt_loader.load("draft/base.yaml")

        # Render prompts
        system_prompt = prompt_template.render_system_prompt(
            title="Technical Leadership",
            classification_guidance="Provide helpful suggestions and recommendations",
            audience_context="engineering leaders",
            voice_samples="",  # Skip voice samples for this test
            company_name="our company",
            company_possessive="our",
        )

        user_prompt = prompt_template.render_user_prompt(
            title="What Makes Effective Technical Leaders",
            description="How technical leaders balance hands-on work with team enablement",
            source_context=sample_section_content,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500,
        )

        word_count = len(response.content.split())

        assert word_count <= 100, (
            f"Draft section exceeded 100 words ({word_count} words). "
            f"FAILED brevity requirement. Content:\n{response.content}"
        )

        # Warn if not in target range
        if not (60 <= word_count <= 80):
            print(
                f"\n⚠️  Word count {word_count} outside target range 60-80 "
                f"(but within max 100, so PASS)"
            )

    def test_paragraph_count(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
        sample_section_content: str,
    ):
        """Draft sections should have 1-2 paragraphs maximum."""
        prompt_template = prompt_loader.load("draft/base.yaml")

        system_prompt = prompt_template.render_system_prompt(
            title="Technical Leadership",
            classification_guidance="Provide helpful suggestions and recommendations",
            audience_context="engineering leaders",
            voice_samples="",
            company_name="our company",
            company_possessive="our",
        )

        user_prompt = prompt_template.render_user_prompt(
            title="Code Review Practices",
            description="How effective leaders review code for patterns, not syntax",
            source_context=sample_section_content,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500,
        )

        # Count paragraphs (separated by blank lines)
        paragraphs = [p.strip() for p in response.content.split("\n\n") if p.strip()]
        # Exclude tables (starts with |)
        prose_paragraphs = [p for p in paragraphs if not p.startswith("|")]

        assert len(prose_paragraphs) <= 2, (
            f"Draft section has {len(prose_paragraphs)} paragraphs, expected ≤2. "
            f"Content:\n{response.content}"
        )


class TestDraftPromptRedundancy:
    """Test draft prompt eliminates redundancy."""

    def test_no_repeated_concepts(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
    ):
        """Draft should not repeat the same concept multiple times."""
        prompt_template = prompt_loader.load("draft/base.yaml")

        # Use repetitive source material
        repetitive_sources = """[Source 1]
        Code reviews improve quality. Teams that do code reviews catch more bugs.

        [Source 2]
        Regular code reviews help teams find defects early.

        [Source 3]
        Code review is essential for catching bugs before production.
        """

        system_prompt = prompt_template.render_system_prompt(
            title="Code Reviews",
            classification_guidance="Present proven approaches",
            audience_context="engineering teams",
            voice_samples="",
            company_name="our company",
            company_possessive="our",
        )

        user_prompt = prompt_template.render_user_prompt(
            title="Benefits of Code Review",
            description="How code reviews improve quality",
            source_context=repetitive_sources,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500,
        )

        content_lower = response.content.lower()

        # Check for repetition (crude but effective)
        # If "review" and "bug/defect/quality" appear more than twice together, likely repetitive
        review_mentions = content_lower.count("review")
        quality_mentions = sum(
            [
                content_lower.count("quality"),
                content_lower.count("bug"),
                content_lower.count("defect"),
            ]
        )

        # Heuristic: mentioning the same core concept 3+ times in 60-80 words is repetitive
        assert review_mentions + quality_mentions <= 4, (
            f"Content appears repetitive: 'review' mentioned {review_mentions} times, "
            f"quality/bug/defect mentioned {quality_mentions} times. "
            f"Content:\n{response.content}"
        )


class TestDraftPromptSourceGrounding:
    """Test draft prompt stays grounded in sources."""

    def test_topic_validation(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
    ):
        """Draft should detect off-topic sources and reject them."""
        prompt_template = prompt_loader.load("draft/base.yaml")

        # Mismatched: section about baking, sources about engineering
        off_topic_sources = """[Source 1]
        Technical leaders balance hands-on work with team enablement.

        [Source 2]
        Leaders document decisions in ADRs (Architecture Decision Records).
        """

        system_prompt = prompt_template.render_system_prompt(
            title="Baking Bread",
            classification_guidance="Provide helpful suggestions",
            audience_context="home bakers",
            voice_samples="",
            company_name="our company",
            company_possessive="our",
        )

        user_prompt = prompt_template.render_user_prompt(
            title="How to Knead Dough Properly",
            description="Techniques for kneading bread dough",
            source_context=off_topic_sources,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500,
        )

        # Should contain ERROR about mismatched sources
        assert "ERROR" in response.content or "topic" in response.content.lower(), (
            "Draft should detect off-topic sources. "
            f"Response: {response.content}"
        )


class TestDraftPromptTableUsage:
    """Test draft prompt uses tables for comparisons."""

    def test_table_for_structured_data(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
    ):
        """Draft should use tables for level/tier comparisons."""
        prompt_template = prompt_loader.load("draft/base.yaml")

        # Source with structured comparison data
        table_worthy_sources = """[Source 1]
        | Level | Experience | Scope | Key Differentiator |
        |-------|------------|-------|-------------------|
        | SDE-1 | 0-2 years | Task | Learning the codebase |
        | SDE-2 | 2-5 years | Feature | Independent delivery |
        | Senior | 5-8 years | Team | Technical leadership |

        [Source 2]
        The career ladder has three levels. Junior engineers work on tasks.
        Mid-level engineers own features. Senior engineers lead teams.
        """

        system_prompt = prompt_template.render_system_prompt(
            title="Career Ladders",
            classification_guidance="Describe proven approaches",
            audience_context="engineering leaders",
            voice_samples="",
            company_name="our company",
            company_possessive="our",
        )

        user_prompt = prompt_template.render_user_prompt(
            title="Engineering Levels",
            description="Comparison of engineering levels and expectations",
            source_context=table_worthy_sources,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500,
        )

        # Should contain markdown table
        has_table = "|" in response.content and "---" in response.content

        assert has_table, (
            "Draft should use table for level comparisons (sources contain structured data). "
            f"Content:\n{response.content}"
        )


class TestDraftPromptAntiPowerPoint:
    """Test draft prompt avoids PowerPoint-style bullets."""

    def test_no_bullet_lists(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
        sample_section_content: str,
    ):
        """Draft should not use bullet points - use prose or tables instead."""
        prompt_template = prompt_loader.load("draft/base.yaml")

        system_prompt = prompt_template.render_system_prompt(
            title="Leadership Practices",
            classification_guidance="Provide helpful suggestions",
            audience_context="engineering leaders",
            voice_samples="",
            company_name="our company",
            company_possessive="our",
        )

        user_prompt = prompt_template.render_user_prompt(
            title="Key Leadership Skills",
            description="Essential skills for technical leaders",
            source_context=sample_section_content,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500,
        )

        # Check for bullet points
        has_bullets = any(
            [
                response.content.count("\n- ") > 0,
                response.content.count("\n* ") > 0,
                response.content.count("\n• ") > 0,
            ]
        )

        # Warn if bullets found (soft failure - tables OK, bullets not)
        if has_bullets and "|" not in response.content:
            pytest.fail(
                f"Draft contains bullet points without table. Use prose or tables instead. "
                f"Content:\n{response.content}"
            )


class TestDraftPromptQuality:
    """Test draft prompt produces quality content without AI slop."""

    def test_no_ai_slop(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
        sample_section_content: str,
    ):
        """Draft should not contain AI slop (em-dashes, flowery language)."""
        prompt_template = prompt_loader.load("draft/base.yaml")

        system_prompt = prompt_template.render_system_prompt(
            title="Technical Leadership",
            classification_guidance="Provide helpful suggestions",
            audience_context="engineering leaders",
            voice_samples="",
            company_name="our company",
            company_possessive="our",
        )

        user_prompt = prompt_template.render_user_prompt(
            title="Decision Making",
            description="How leaders document and communicate decisions",
            source_context=sample_section_content,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500,
        )

        content = response.content.lower()

        # Check for banned patterns
        banned_phrases = [
            "—",  # em-dash
            "dive deep",
            "leverage",
            "game changer",
            "synergy",
            "paradigm shift",
            "at the end of the day",
        ]

        found_slop = [phrase for phrase in banned_phrases if phrase in content]

        assert not found_slop, (
            f"Found AI slop in draft: {found_slop}. "
            f"Content should be direct and professional. "
            f"Full content:\n{response.content}"
        )
