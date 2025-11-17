"""Tests for voice similarity scorer."""

from unittest.mock import Mock

import numpy as np
import pytest

from bloginator.generation.voice_scorer import VoiceScorer
from bloginator.models.draft import Draft, DraftSection
from bloginator.search import SearchResult


class TestVoiceScorer:
    """Tests for VoiceScorer."""

    @pytest.fixture
    def mock_searcher(self):
        """Create mock searcher with embedding model."""
        searcher = Mock()

        # Mock embedding model
        embedding_model = Mock()
        embedding_model.encode.return_value = np.array(
            [
                [0.1, 0.2, 0.3],  # Mock embedding
            ]
        )

        searcher.embedding_model = embedding_model
        return searcher

    @pytest.fixture
    def scorer(self, mock_searcher):
        """Create voice scorer with mock."""
        return VoiceScorer(
            searcher=mock_searcher,
            sample_size=20,
        )

    def test_initialization(self, mock_searcher):
        """Test scorer initialization."""
        scorer = VoiceScorer(
            searcher=mock_searcher,
            sample_size=10,
        )

        assert scorer.searcher == mock_searcher
        assert scorer.sample_size == 10
        assert scorer.embedding_model == mock_searcher.embedding_model

    def test_initialization_custom_model(self, mock_searcher):
        """Test initialization with custom embedding model."""
        custom_model = Mock()
        scorer = VoiceScorer(
            searcher=mock_searcher,
            embedding_model=custom_model,
        )

        assert scorer.embedding_model == custom_model

    def test_score_section_empty_content(self, scorer, mock_searcher):
        """Test scoring section with no content."""
        section = DraftSection(title="Test", content="")

        scorer._score_section(section, keywords=["test"])

        assert section.voice_score == 0.0

    def test_score_section_no_corpus_samples(self, scorer, mock_searcher):
        """Test scoring when corpus has no samples."""
        mock_searcher.search.return_value = []

        section = DraftSection(title="Test", content="Some content")
        scorer._score_section(section, keywords=["test"])

        # Should get neutral score
        assert section.voice_score == 0.5

    def test_score_section_with_samples(self, scorer, mock_searcher):
        """Test scoring with corpus samples."""
        # Mock search results
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id=f"chunk{i}",
                content=f"Corpus content {i}",
                similarity_score=0.8,
                metadata={},
            )
            for i in range(5)
        ]

        # Mock embeddings
        # Generated content embedding
        generated_emb = np.array([1.0, 0.0, 0.0])
        # Corpus embeddings (similar to generated)
        corpus_embs = np.array(
            [
                [0.9, 0.1, 0.0],
                [0.8, 0.2, 0.0],
                [0.85, 0.15, 0.0],
                [0.95, 0.05, 0.0],
                [0.87, 0.13, 0.0],
            ]
        )

        def encode_side_effect(texts):
            if len(texts) == 1:
                return np.array([generated_emb])
            else:
                return corpus_embs

        scorer.embedding_model.encode.side_effect = encode_side_effect

        section = DraftSection(title="Test", content="Generated content")
        scorer._score_section(section, keywords=["test"])

        # Should have high similarity
        assert section.voice_score > 0.7
        assert section.voice_score <= 1.0

    def test_score_section_bounds_check(self, scorer, mock_searcher):
        """Test that voice score is bounded to [0, 1]."""
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id="chunk1",
                content="Content",
                similarity_score=0.8,
                metadata={},
            )
        ]

        # Mock extreme embeddings that might produce out-of-bounds scores
        def encode_side_effect(texts):
            if len(texts) == 1:
                return np.array([[100.0, 0.0, 0.0]])
            else:
                return np.array([[0.01, 0.01, 0.01]])

        scorer.embedding_model.encode.side_effect = encode_side_effect

        section = DraftSection(title="Test", content="Content")
        scorer._score_section(section, keywords=["test"])

        # Score should be clamped to [0, 1]
        assert 0.0 <= section.voice_score <= 1.0

    def test_score_section_error_handling(self, scorer, mock_searcher):
        """Test error handling during scoring."""
        mock_searcher.search.side_effect = Exception("Search failed")

        section = DraftSection(title="Test", content="Content")
        scorer._score_section(section, keywords=["test"])

        # Should fallback to neutral score
        assert section.voice_score == 0.5

    def test_score_draft_empty(self, scorer):
        """Test scoring draft with no sections."""
        draft = Draft(title="Test", keywords=[])
        scorer.score_draft(draft)

        assert draft.voice_score == 0.0

    def test_score_draft_with_sections(self, scorer, mock_searcher):
        """Test scoring full draft."""
        mock_searcher.search.return_value = []

        sections = [
            DraftSection(title="S1", content="Content 1"),
            DraftSection(title="S2", content="Content 2"),
        ]

        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=sections,
        )

        scorer.score_draft(draft)

        # All sections should be scored
        for section in draft.sections:
            assert section.voice_score >= 0.0

        # Draft stats should be calculated
        assert draft.voice_score >= 0.0

    def test_score_text_basic(self, scorer, mock_searcher):
        """Test scoring arbitrary text."""
        mock_searcher.search.return_value = [
            SearchResult(
                chunk_id="chunk1",
                content="Corpus content",
                similarity_score=0.8,
                metadata={},
            )
        ]

        # Mock similar embeddings
        scorer.embedding_model.encode.return_value = np.array(
            [
                [1.0, 0.0, 0.0],  # Text embedding
            ]
        )

        score = scorer.score_text(
            text="Test text",
            context_keywords=["test"],
        )

        assert 0.0 <= score <= 1.0

    def test_score_text_empty(self, scorer):
        """Test scoring empty text."""
        score = scorer.score_text(
            text="",
            context_keywords=["test"],
        )

        assert score == 0.0

    def test_score_text_no_samples(self, scorer, mock_searcher):
        """Test scoring text with no corpus samples."""
        mock_searcher.search.return_value = []

        score = scorer.score_text(
            text="Test text",
            context_keywords=["test"],
        )

        assert score == 0.5

    def test_get_voice_insights_basic(self, scorer):
        """Test getting voice insights."""
        sections = [
            DraftSection(title="Good 1", content="C1", voice_score=0.8),
            DraftSection(title="Good 2", content="C2", voice_score=0.75),
            DraftSection(title="Weak 1", content="C3", voice_score=0.6),
            DraftSection(title="Weak 2", content="C4", voice_score=0.5),
        ]

        draft = Draft(
            title="Test",
            keywords=[],
            sections=sections,
        )
        draft.calculate_stats()

        insights = scorer.get_voice_insights(draft, threshold=0.7)

        assert insights["overall_score"] == pytest.approx(0.6625, rel=0.01)
        assert insights["total_sections"] == 4
        assert insights["authentic_sections"] == 2
        assert "Good 1" in insights["authentic_section_titles"]
        assert "Good 2" in insights["authentic_section_titles"]
        assert insights["weak_sections"] == 2
        assert len(insights["weak_section_details"]) == 2

    def test_get_voice_insights_custom_threshold(self, scorer):
        """Test insights with custom threshold."""
        sections = [
            DraftSection(title="S1", content="C", voice_score=0.8),
            DraftSection(title="S2", content="C", voice_score=0.6),
        ]

        draft = Draft(title="Test", keywords=[], sections=sections)
        draft.calculate_stats()

        # Low threshold - all authentic
        insights_low = scorer.get_voice_insights(draft, threshold=0.5)
        assert insights_low["authentic_sections"] == 2
        assert insights_low["weak_sections"] == 0

        # High threshold - all weak
        insights_high = scorer.get_voice_insights(draft, threshold=0.9)
        assert insights_high["authentic_sections"] == 0
        assert insights_high["weak_sections"] == 2

    def test_get_voice_insights_nested_sections(self, scorer):
        """Test insights with nested sections."""
        subsection = DraftSection(
            title="Sub",
            content="Sub content",
            voice_score=0.5,
        )

        section = DraftSection(
            title="Main",
            content="Main content",
            voice_score=0.8,
            subsections=[subsection],
        )

        draft = Draft(title="Test", keywords=[], sections=[section])
        draft.calculate_stats()

        insights = scorer.get_voice_insights(draft, threshold=0.7)

        # Should include subsection
        assert insights["total_sections"] == 2
        assert insights["authentic_sections"] == 1
        assert insights["weak_sections"] == 1
