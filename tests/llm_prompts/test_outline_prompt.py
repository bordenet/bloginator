"""Tests for outline generation prompt with Claude Sonnet 4.5.

Tests validate that the outline prompt produces:
1. Correct structure (5-7 sections, minimal subsections)
2. Topic relevance (sections match keywords)
3. No hallucination (grounded in corpus context)
4. Proper formatting (markdown headings, descriptions)
5. No AI slop (em-dashes, flowery language)
"""

from tests.llm_prompts.conftest import ClaudeSonnet45Client

from bloginator.generation._outline_parser import parse_outline_response
from bloginator.generation._outline_prompt_builder import (
    OutlinePromptBuilder,
    build_corpus_context,
    build_search_queries,
)


class TestOutlinePromptStructure:
    """Test outline prompt produces correct structure."""

    def test_section_count_compliance(
        self,
        claude_client: ClaudeSonnet45Client,
        test_corpus_searcher,
        sample_outline_title: str,
        sample_keywords: list[str],
    ):
        """Outline should have 5-7 top-level sections."""
        # Build prompts
        builder = OutlinePromptBuilder()

        # Search corpus
        queries = build_search_queries(sample_outline_title, sample_keywords)
        results = test_corpus_searcher.search(queries[0], n_results=3)
        corpus_context = build_corpus_context(results)

        # Generate outline
        system_prompt = builder.build_system_prompt()
        user_prompt = builder.build_user_prompt(
            title=sample_outline_title,
            keywords=sample_keywords,
            corpus_context=corpus_context,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000,
        )

        # Parse and validate
        sections = parse_outline_response(response.content)

        assert 5 <= len(sections) <= 7, (
            f"Expected 5-7 sections, got {len(sections)}. "
            f"Sections: {[s.title for s in sections]}"
        )

    def test_minimal_subsections(
        self,
        claude_client: ClaudeSonnet45Client,
        test_corpus_searcher,
        sample_outline_title: str,
        sample_keywords: list[str],
    ):
        """Outline should have minimal subsections (prefer flat structure)."""
        builder = OutlinePromptBuilder()

        queries = build_search_queries(sample_outline_title, sample_keywords)
        results = test_corpus_searcher.search(queries[0], n_results=3)
        corpus_context = build_corpus_context(results)

        system_prompt = builder.build_system_prompt()
        user_prompt = builder.build_user_prompt(
            title=sample_outline_title,
            keywords=sample_keywords,
            corpus_context=corpus_context,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000,
        )

        sections = parse_outline_response(response.content)

        # Count subsections
        total_subsections = sum(len(s.subsections) for s in sections)
        subsection_ratio = total_subsections / len(sections) if sections else 0

        assert subsection_ratio < 1.5, (
            f"Too many subsections: {total_subsections} subsections for {len(sections)} sections. "
            f"Ratio: {subsection_ratio:.2f}, expected < 1.5 (prefer flat structure)"
        )


class TestOutlinePromptTopicRelevance:
    """Test outline prompt produces topic-relevant content."""

    def test_keyword_matching(
        self,
        claude_client: ClaudeSonnet45Client,
        test_corpus_searcher,
        sample_outline_title: str,
        sample_keywords: list[str],
    ):
        """At least 70% of sections should contain provided keywords."""
        builder = OutlinePromptBuilder()

        queries = build_search_queries(sample_outline_title, sample_keywords)
        results = test_corpus_searcher.search(queries[0], n_results=3)
        corpus_context = build_corpus_context(results)

        system_prompt = builder.build_system_prompt()
        user_prompt = builder.build_user_prompt(
            title=sample_outline_title,
            keywords=sample_keywords,
            corpus_context=corpus_context,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000,
        )

        sections = parse_outline_response(response.content)

        # Count sections with keyword matches
        matched_sections = 0
        for section in sections:
            section_text = f"{section.title} {section.description}".lower()
            if any(kw.lower() in section_text for kw in sample_keywords):
                matched_sections += 1

        match_ratio = matched_sections / len(sections) if sections else 0

        assert match_ratio >= 0.7, (
            f"Only {matched_sections}/{len(sections)} sections ({match_ratio*100:.0f}%) "
            f"match keywords {sample_keywords}. Expected ≥70%."
        )

    def test_corpus_grounding(
        self,
        claude_client: ClaudeSonnet45Client,
        test_corpus_searcher,
    ):
        """Outline should detect and reject off-topic corpus content."""
        builder = OutlinePromptBuilder()

        # Use mismatched keywords vs corpus (corpus is about engineering, keywords about cooking)
        title = "How to Bake Perfect Bread"
        keywords = ["baking", "yeast", "kneading", "oven"]

        # Search corpus (will return engineering content, not baking)
        queries = build_search_queries(title, keywords)
        results = test_corpus_searcher.search(queries[0], n_results=3)
        corpus_context = build_corpus_context(results)

        system_prompt = builder.build_system_prompt()
        user_prompt = builder.build_user_prompt(
            title=title,
            keywords=keywords,
            corpus_context=corpus_context,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000,
        )

        # Should contain ERROR message about topic mismatch
        assert "ERROR" in response.content or "topic" in response.content.lower(), (
            "Outline should detect topic mismatch between keywords and corpus. "
            f"Response: {response.content[:200]}..."
        )


class TestOutlinePromptFormatting:
    """Test outline prompt produces proper formatting."""

    def test_markdown_structure(
        self,
        claude_client: ClaudeSonnet45Client,
        test_corpus_searcher,
        sample_outline_title: str,
        sample_keywords: list[str],
    ):
        """Outline should use markdown ## headings for sections."""
        builder = OutlinePromptBuilder()

        queries = build_search_queries(sample_outline_title, sample_keywords)
        results = test_corpus_searcher.search(queries[0], n_results=3)
        corpus_context = build_corpus_context(results)

        system_prompt = builder.build_system_prompt()
        user_prompt = builder.build_user_prompt(
            title=sample_outline_title,
            keywords=sample_keywords,
            corpus_context=corpus_context,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000,
        )

        # Count ## headings
        section_count = response.content.count("\n## ")

        assert section_count >= 5, (
            f"Expected at least 5 '## ' headings for sections, found {section_count}. "
            f"Response:\n{response.content[:500]}..."
        )

    def test_section_descriptions(
        self,
        claude_client: ClaudeSonnet45Client,
        test_corpus_searcher,
        sample_outline_title: str,
        sample_keywords: list[str],
    ):
        """Each section should have a description after the heading."""
        builder = OutlinePromptBuilder()

        queries = build_search_queries(sample_outline_title, sample_keywords)
        results = test_corpus_searcher.search(queries[0], n_results=3)
        corpus_context = build_corpus_context(results)

        system_prompt = builder.build_system_prompt()
        user_prompt = builder.build_user_prompt(
            title=sample_outline_title,
            keywords=sample_keywords,
            corpus_context=corpus_context,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000,
        )

        sections = parse_outline_response(response.content)

        # Check descriptions exist
        sections_with_descriptions = sum(1 for s in sections if s.description.strip())

        assert sections_with_descriptions == len(sections), (
            f"Only {sections_with_descriptions}/{len(sections)} sections have descriptions. "
            f"All sections must have descriptions."
        )


class TestOutlinePromptQuality:
    """Test outline prompt produces quality content without AI slop."""

    def test_no_ai_slop(
        self,
        claude_client: ClaudeSonnet45Client,
        test_corpus_searcher,
        sample_outline_title: str,
        sample_keywords: list[str],
    ):
        """Outline should not contain AI slop (em-dashes, flowery language)."""
        builder = OutlinePromptBuilder()

        queries = build_search_queries(sample_outline_title, sample_keywords)
        results = test_corpus_searcher.search(queries[0], n_results=3)
        corpus_context = build_corpus_context(results)

        system_prompt = builder.build_system_prompt()
        user_prompt = builder.build_user_prompt(
            title=sample_outline_title,
            keywords=sample_keywords,
            corpus_context=corpus_context,
        )

        response = claude_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=2000,
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
        ]

        found_slop = [phrase for phrase in banned_phrases if phrase in content]

        assert not found_slop, (
            f"Found AI slop in outline: {found_slop}. "
            f"Content should be direct and professional."
        )
