"""Tests for quality assurance system."""

import pytest

from bloginator.models.draft import Draft, DraftSection
from bloginator.models.outline import Outline, OutlineSection
from bloginator.quality.quality_assurance import QualityAssurance, QualityLevel


@pytest.fixture
def qa_system():
    """Create quality assurance system."""
    return QualityAssurance(
        min_acceptable_score=3.5,
        max_retries=3,
        critical_violations_threshold=0,
    )


@pytest.fixture
def clean_outline():
    """Create outline with no slop."""
    return Outline(
        title="Test Title",
        sections=[
            OutlineSection(
                title="Introduction",
                description="Overview of the topic",
                subsections=[],
            ),
            OutlineSection(
                title="Main Content",
                description="Core concepts and principles",
                subsections=[],
            ),
        ],
    )


@pytest.fixture
def clean_draft():
    """Create draft with no slop."""
    return Draft(
        title="Test Title",
        sections=[
            DraftSection(
                title="Introduction",
                content="This is a clean introduction with no slop. It uses simple, direct language.",
            ),
            DraftSection(
                title="Main Content",
                content="The main content is clear and specific. It avoids jargon and hedging.",
            ),
        ],
    )


@pytest.fixture
def sloppy_draft():
    """Create draft with slop violations."""
    return Draft(
        title="Test Title",
        sections=[
            DraftSection(
                title="Introduction",
                content="This introduction—with an em-dash—demonstrates critical slop. "
                "It might perhaps leverage synergies to drive innovation.",
            ),
            DraftSection(
                title="Main Content",
                content="The content could potentially unlock value through best-in-class solutions. "
                "This may help you navigate the landscape of possibilities.",
            ),
        ],
    )


def test_assess_clean_content(qa_system, clean_outline, clean_draft):
    """Test assessment of clean content."""
    assessment = qa_system.assess_quality(clean_outline, clean_draft)

    assert assessment.quality_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD]
    assert assessment.score >= 4.0
    assert assessment.critical_violations == 0
    assert not assessment.retry_suggested


def test_assess_sloppy_content(qa_system, clean_outline, sloppy_draft):
    """Test assessment of sloppy content."""
    assessment = qa_system.assess_quality(clean_outline, sloppy_draft)

    assert assessment.quality_level == QualityLevel.POOR
    assert assessment.critical_violations > 0  # Em-dash
    assert assessment.high_violations > 0  # Corporate jargon
    assert assessment.total_violations > 0
    assert assessment.retry_suggested
    assert len(assessment.issues) > 0
    assert len(assessment.recommendations) > 0


def test_critical_violations_threshold(clean_outline, sloppy_draft):
    """Test critical violations threshold."""
    qa = QualityAssurance(critical_violations_threshold=0)
    assessment = qa.assess_quality(clean_outline, sloppy_draft)
    assert assessment.quality_level == QualityLevel.POOR

    qa_lenient = QualityAssurance(critical_violations_threshold=10)
    assessment_lenient = qa_lenient.assess_quality(clean_outline, sloppy_draft)
    # Even with lenient threshold, score will be low due to violations
    assert assessment_lenient.total_violations > 0


def test_score_calculation(qa_system, clean_outline):
    """Test score calculation with different violation levels."""
    # Draft with only low violations
    low_violation_draft = Draft(
        title="Test",
        sections=[
            DraftSection(
                title="Section",
                content="This content has some vague language and general statements.",
            )
        ],
    )
    assessment = qa_system.assess_quality(clean_outline, low_violation_draft)
    assert assessment.score >= 4.0  # Low violations have minimal impact


def test_recommendations_generation(qa_system, clean_outline, sloppy_draft):
    """Test that recommendations are generated for violations."""
    assessment = qa_system.assess_quality(clean_outline, sloppy_draft)

    assert len(assessment.recommendations) > 0
    # Should recommend fixing em-dashes
    assert any("em-dash" in rec.lower() for rec in assessment.recommendations)


def test_quality_levels(qa_system, clean_outline):
    """Test different quality levels."""
    # Excellent quality (score >= 4.5)
    excellent_draft = Draft(
        title="Test",
        sections=[DraftSection(title="Section", content="Perfect clean content.")],
    )
    assessment = qa_system.assess_quality(clean_outline, excellent_draft)
    assert assessment.quality_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD]

    # Poor quality (critical violations)
    poor_draft = Draft(
        title="Test",
        sections=[
            DraftSection(
                title="Section",
                content="Content with em-dash—which is critical violation.",
            )
        ],
    )
    assessment = qa_system.assess_quality(clean_outline, poor_draft)
    assert assessment.quality_level == QualityLevel.POOR

