"""Tests for retry orchestrator."""

from unittest.mock import MagicMock

import pytest

from bloginator.generation.llm_mock import MockLLMClient
from bloginator.quality.quality_assurance import QualityAssurance
from bloginator.quality.retry_orchestrator import RetryOrchestrator


@pytest.fixture
def mock_llm():
    """Create mock LLM client."""
    return MockLLMClient()


@pytest.fixture
def mock_searcher():
    """Create mock searcher with no actual ChromaDB."""
    searcher = MagicMock()
    # Return empty search results by default
    searcher.search.return_value = []
    return searcher


@pytest.fixture
def qa_system():
    """Create quality assurance system."""
    return QualityAssurance(
        min_acceptable_score=3.5,
        max_retries=3,
        critical_violations_threshold=0,
    )


@pytest.fixture
def orchestrator(mock_llm, mock_searcher, qa_system):
    """Create retry orchestrator."""
    return RetryOrchestrator(
        llm_client=mock_llm,
        searcher=mock_searcher,
        quality_assurance=qa_system,
        max_retries=3,
    )


def test_generate_with_retry_success_first_attempt(orchestrator):
    """Test successful generation on first attempt."""
    result = orchestrator.generate_with_retry(
        title="Test Title",
        keywords=["test", "example"],
        thesis="This is a test thesis",
        classification="best-practice",
        audience="ic-engineers",
    )

    assert result.success
    assert result.total_attempts == 1
    assert result.final_attempt.attempt_number == 1
    assert len(result.all_attempts) == 1


def test_prompt_variants(orchestrator):
    """Test that prompt variants are defined."""
    variants = orchestrator._get_prompt_variants()

    assert len(variants) > 0
    assert "default" in variants
    assert "strict_no_slop" in variants
    assert "minimal" in variants


def test_generation_result_structure(orchestrator):
    """Test that generation result has correct structure."""
    result = orchestrator.generate_with_retry(
        title="Test Title",
        keywords=["test"],
        thesis="Test thesis",
        classification="guidance",
        audience="senior-engineers",
    )

    assert hasattr(result, "success")
    assert hasattr(result, "final_attempt")
    assert hasattr(result, "all_attempts")
    assert hasattr(result, "total_attempts")
    assert hasattr(result, "final_quality")

    # Check attempt structure
    attempt = result.final_attempt
    assert hasattr(attempt, "attempt_number")
    assert hasattr(attempt, "outline")
    assert hasattr(attempt, "draft")
    assert hasattr(attempt, "assessment")
    assert hasattr(attempt, "prompt_variant")


def test_quality_assessment_in_result(orchestrator):
    """Test that quality assessment is included in result."""
    result = orchestrator.generate_with_retry(
        title="Test Title",
        keywords=["test"],
        thesis="Test thesis",
        classification="best-practice",
        audience="ic-engineers",
    )

    assessment = result.final_attempt.assessment
    assert hasattr(assessment, "quality_level")
    assert hasattr(assessment, "score")
    assert hasattr(assessment, "total_violations")
    assert hasattr(assessment, "issues")
    assert hasattr(assessment, "recommendations")


def test_max_retries_limit(mock_llm, mock_searcher):
    """Test that max retries limit is respected."""

    # Create QA system that always suggests retry
    class AlwaysRetryQA(QualityAssurance):
        def assess_quality(self, outline, draft):
            assessment = super().assess_quality(outline, draft)
            # Force retry suggestion
            assessment.retry_suggested = True
            return assessment

    orchestrator = RetryOrchestrator(
        llm_client=mock_llm,
        searcher=mock_searcher,
        quality_assurance=AlwaysRetryQA(max_retries=2),
        max_retries=2,
    )

    result = orchestrator.generate_with_retry(
        title="Test",
        keywords=["test"],
        thesis="Test",
        classification="best-practice",
        audience="ic-engineers",
    )

    # Should attempt: initial + 2 retries = 3 total
    assert result.total_attempts == 3
    assert not result.success  # Never achieved acceptable quality
