"""Pytest fixtures for LLM prompt testing with Claude Sonnet 4.5.

This module provides fixtures for testing prompts with a real LLM (Claude Sonnet 4.5)
to validate prompt quality, constraint compliance, and output characteristics.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest


# Skip all tests in this module if anthropic package is not installed
anthropic = pytest.importorskip("anthropic", reason="anthropic package not installed")
Anthropic = anthropic.Anthropic

from bloginator.generation.llm_base import LLMClient, LLMResponse  # noqa: E402
from bloginator.prompts.loader import PromptLoader  # noqa: E402
from bloginator.search import CorpusSearcher  # noqa: E402


if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


class ClaudeSonnet45Client(LLMClient):
    """Claude Sonnet 4.5 LLM client for prompt testing.

    Uses the Anthropic API with claude-sonnet-4-5-20250929 model.
    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self, model: str = "claude-sonnet-4-5-20250929", verbose: bool = False):
        """Initialize Claude client.

        Args:
            model: Claude model ID
            verbose: Whether to print request/response details
        """
        self.model = model
        self.verbose = verbose
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """Generate response using Claude API.

        Args:
            prompt: User prompt/instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"MODEL: {self.model}")
            print(f"TEMPERATURE: {temperature}")
            print(f"MAX_TOKENS: {max_tokens}")
            if system_prompt:
                print(f"\nSYSTEM PROMPT:\n{system_prompt[:500]}...")
            print(f"\nUSER PROMPT:\n{prompt[:500]}...")
            print(f"{'='*80}\n")

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Call API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else "",
            messages=messages,
        )

        # Extract content
        content = response.content[0].text if response.content else ""

        if self.verbose:
            print(f"\nRESPONSE:\n{content[:500]}...")
            print(
                f"\nTOKENS: input={response.usage.input_tokens}, output={response.usage.output_tokens}"
            )

        return LLMResponse(
            content=content,
            model=self.model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            finish_reason=response.stop_reason,
        )

    def is_available(self) -> bool:
        """Check if API key is configured.

        Returns:
            True if ANTHROPIC_API_KEY is set
        """
        return bool(os.environ.get("ANTHROPIC_API_KEY"))


@pytest.fixture
def claude_client() -> LLMClient:
    """Provide LLM client for testing.

    Uses Claude Sonnet 4.5 if ANTHROPIC_API_KEY is set, otherwise uses MockLLMClient.

    Returns:
        LLMClient instance (either ClaudeSonnet45Client or MockLLMClient)
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ClaudeSonnet45Client(verbose=True)
    else:
        # Use mock client when API key not available
        from bloginator.generation._llm_mock_client import MockLLMClient

        return MockLLMClient(model="mock-sonnet-4.5", verbose=True)


@pytest.fixture
def prompt_loader() -> PromptLoader:
    """Provide prompt loader for loading templates.

    Returns:
        PromptLoader instance
    """
    return PromptLoader()


@pytest.fixture
def test_corpus_searcher(tmp_path: Path) -> Generator[CorpusSearcher, None, None]:
    """Provide a test corpus searcher with sample data.

    Creates a small in-memory corpus with technical content for testing.

    Args:
        tmp_path: Pytest temporary directory

    Yields:
        CorpusSearcher with test data
    """
    # Create test corpus directory
    corpus_dir = tmp_path / "test_corpus"
    corpus_dir.mkdir()

    # Sample documents content
    content1 = """# Engineering Leadership Principles

Technical leaders balance hands-on work with team enablement. They write code
30-40% of the time while dedicating the rest to architecture decisions, code
reviews, and mentoring.

## Decision Making

Leaders document decisions in ADRs (Architecture Decision Records) that capture
context, options considered, and rationale. This prevents rehashing settled questions.

## Code Review

Effective leaders review code for patterns, not syntax. They flag architectural
concerns, suggest abstractions, and teach through questions rather than directives.
"""

    content2 = """# Software Engineering Career Ladders

| Level | Experience | Scope | Key Differentiator |
|-------|------------|-------|-------------------|
| SDE-1 | 0-2 years | Task | Learning the codebase |
| SDE-2 | 2-5 years | Feature | Independent delivery |
| Senior | 5-8 years | Team | Technical leadership |
| Staff | 8+ years | Org | Architectural direction |

The first year as an SDE-1 centers on mastering the codebase while establishing
trust through consistent delivery. New engineers tackle well-defined tasks
independently while pairing with senior colleagues on complex work.
"""

    # Write to files (for compatibility)
    (corpus_dir / "engineering_leadership.md").write_text(content1)
    (corpus_dir / "career_ladders.md").write_text(content2)

    # Create and index corpus
    from datetime import datetime

    from bloginator.indexing.indexer import CorpusIndexer
    from bloginator.models import Chunk, Document, QualityRating

    index_dir = tmp_path / "test_index"
    indexer = CorpusIndexer(output_dir=index_dir)

    # Create test documents and chunks manually
    doc1 = Document(
        id="doc_1",
        filename="engineering_leadership.md",
        source_path=corpus_dir / "engineering_leadership.md",
        format="markdown",
        created_date=datetime.now(),
        modified_date=datetime.now(),
        quality_rating=QualityRating.PREFERRED,
        tags=["engineering", "leadership"],
        word_count=100,
    )

    doc2 = Document(
        id="doc_2",
        filename="career_ladders.md",
        source_path=corpus_dir / "career_ladders.md",
        format="markdown",
        created_date=datetime.now(),
        modified_date=datetime.now(),
        quality_rating=QualityRating.PREFERRED,
        tags=["career", "ladder"],
        word_count=100,
    )

    # Index documents with their content as chunks
    indexer.index_document(
        doc1,
        [
            Chunk(
                id="chunk_1",
                document_id=doc1.id,
                content=content1,
                chunk_index=0,
                section_heading="Engineering Leadership",
                char_start=0,
                char_end=len(content1),
            )
        ],
    )

    indexer.index_document(
        doc2,
        [
            Chunk(
                id="chunk_2",
                document_id=doc2.id,
                content=content2,
                chunk_index=0,
                section_heading="Career Ladders",
                char_start=0,
                char_end=len(content2),
            )
        ],
    )

    # Create searcher
    searcher = CorpusSearcher(index_dir=index_dir)

    yield searcher


@pytest.fixture
def sample_keywords() -> list[str]:
    """Provide sample keywords for testing.

    Returns:
        List of common technical keywords
    """
    return ["leadership", "engineering", "technical", "team"]


@pytest.fixture
def sample_outline_title() -> str:
    """Provide sample outline title for testing.

    Returns:
        Sample blog title
    """
    return "What Great Engineering Leaders Do"


@pytest.fixture
def sample_section_content() -> str:
    """Provide sample section content for testing.

    Returns:
        Sample corpus content for section generation
    """
    return """[Source 1]
    Technical leaders balance hands-on work with team enablement. They write code
    30-40% of the time while dedicating the rest to architecture decisions, code
    reviews, and mentoring.

    [Source 2]
    Leaders document decisions in ADRs (Architecture Decision Records) that capture
    context, options considered, and rationale. This prevents rehashing settled questions.

    [Source 3]
    Effective leaders review code for patterns, not syntax. They flag architectural
    concerns, suggest abstractions, and teach through questions rather than directives.
    """
