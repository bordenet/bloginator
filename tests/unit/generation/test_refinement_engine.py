"""Tests for refinement engine."""

from unittest.mock import Mock

import pytest

from bloginator.generation.refinement_engine import RefinementEngine
from bloginator.models.draft import Draft, DraftSection
from bloginator.search import SearchResult


class TestRefinementEngine:
    """Tests for RefinementEngine."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM client."""
        mock = Mock()
        mock.generate.return_value = Mock(content="Generated content")
        return mock

    @pytest.fixture
    def mock_searcher(self):
        """Create mock searcher."""
        mock = Mock()
        mock.search.return_value = [
            SearchResult(
                chunk_id=f"chunk{i}",
                content=f"Relevant content {i}",
                similarity_score=0.8,
                metadata={"filename": f"source{i}.md"},
            )
            for i in range(3)
        ]
        return mock

    @pytest.fixture
    def engine(self, mock_llm, mock_searcher):
        """Create refinement engine with mocks."""
        return RefinementEngine(
            llm_client=mock_llm,
            searcher=mock_searcher,
        )

    def test_initialization(self, mock_llm, mock_searcher):
        """Test engine initialization."""
        engine = RefinementEngine(
            llm_client=mock_llm,
            searcher=mock_searcher,
        )

        assert engine.llm_client == mock_llm
        assert engine.searcher == mock_searcher
        assert engine.voice_scorer is None
        assert engine.safety_validator is None
        assert engine.draft_generator is not None

    def test_initialization_with_optional_components(
        self,
        mock_llm,
        mock_searcher,
    ):
        """Test initialization with voice scorer and validator."""
        mock_scorer = Mock()
        mock_validator = Mock()

        engine = RefinementEngine(
            llm_client=mock_llm,
            searcher=mock_searcher,
            voice_scorer=mock_scorer,
            safety_validator=mock_validator,
        )

        assert engine.voice_scorer == mock_scorer
        assert engine.safety_validator == mock_validator

    def test_parse_feedback_regenerate(self, engine, mock_llm):
        """Test parsing feedback for regeneration action."""
        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[
                DraftSection(title="Introduction", content="Intro"),
                DraftSection(title="Body", content="Body"),
            ],
        )

        # Mock LLM response
        mock_llm.generate.return_value = Mock(
            content="""ACTION: regenerate
SECTIONS: Introduction
INSTRUCTIONS: Regenerate with more detail"""
        )

        result = engine.parse_feedback(draft, "Add more detail to intro")

        assert result["action"] == "regenerate"
        assert "Introduction" in result["target_sections"]
        assert "detail" in result["instructions"].lower()

    def test_parse_feedback_global(self, engine, mock_llm):
        """Test parsing feedback for global changes."""
        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[DraftSection(title="Section", content="Content")],
        )

        # Mock LLM response
        mock_llm.generate.return_value = Mock(
            content="""ACTION: global
SECTIONS: all
INSTRUCTIONS: Make entire document more optimistic"""
        )

        result = engine.parse_feedback(draft, "Be more optimistic")

        assert result["action"] == "global"
        assert result["target_sections"] == []  # Empty means all
        assert "optimistic" in result["instructions"].lower()

    def test_parse_feedback_multiple_sections(self, engine, mock_llm):
        """Test parsing feedback targeting multiple sections."""
        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[
                DraftSection(title="Intro", content="Intro"),
                DraftSection(title="Methods", content="Methods"),
                DraftSection(title="Results", content="Results"),
            ],
        )

        # Mock LLM response
        mock_llm.generate.return_value = Mock(
            content="""ACTION: expand
SECTIONS: Methods, Results
INSTRUCTIONS: Add more technical detail"""
        )

        result = engine.parse_feedback(draft, "More detail in methods and results")

        assert result["action"] == "expand"
        assert "Methods" in result["target_sections"]
        assert "Results" in result["target_sections"]

    def test_parse_feedback_fallback(self, engine, mock_llm):
        """Test fallback when LLM parsing fails."""
        draft = Draft(title="Test", keywords=[], sections=[])

        # Mock LLM error
        mock_llm.generate.side_effect = Exception("LLM failed")

        result = engine.parse_feedback(draft, "Some feedback")

        # Should fallback to global with raw feedback
        assert result["action"] == "global"
        assert result["target_sections"] == []
        assert result["instructions"] == "Some feedback"

    def test_refine_draft_single_section(self, engine, mock_llm, mock_searcher):
        """Test refining a single section."""
        section1 = DraftSection(title="Intro", content="Original intro")
        section2 = DraftSection(title="Body", content="Original body")

        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[section1, section2],
        )

        # Mock feedback parsing
        mock_llm.generate.side_effect = [
            Mock(
                content="""ACTION: tone_change
SECTIONS: Intro
INSTRUCTIONS: Make more engaging"""
            ),
            Mock(content="Refined introduction content"),
        ]

        refined = engine.refine_draft(
            draft=draft,
            feedback="Make intro more engaging",
            validate_safety=False,
            score_voice=False,
        )

        assert len(refined.sections) == 2
        assert refined.sections[0].title == "Intro"
        assert refined.sections[0].content == "Refined introduction content"
        # Body should be unchanged
        assert refined.sections[1].content == "Original body"

    def test_refine_draft_all_sections(self, engine, mock_llm, mock_searcher):
        """Test refining all sections (global change)."""
        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[
                DraftSection(title="S1", content="Content 1"),
                DraftSection(title="S2", content="Content 2"),
            ],
        )

        # Mock parsing for global change
        mock_llm.generate.side_effect = [
            Mock(
                content="""ACTION: global
SECTIONS: all
INSTRUCTIONS: Make more optimistic"""
            ),
            Mock(content="Refined S1 content"),
            Mock(content="Refined S2 content"),
        ]

        refined = engine.refine_draft(
            draft=draft,
            feedback="Make more optimistic",
            validate_safety=False,
            score_voice=False,
        )

        # Both sections should be refined
        assert refined.sections[0].content == "Refined S1 content"
        assert refined.sections[1].content == "Refined S2 content"

    def test_refine_draft_no_matching_sections(self, engine, mock_llm, mock_searcher):
        """Test refinement when no sections match target."""
        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[DraftSection(title="Intro", content="Content")],
        )

        # Mock parsing targeting non-existent section
        mock_llm.generate.return_value = Mock(
            content="""ACTION: regenerate
SECTIONS: NonExistent
INSTRUCTIONS: Do something"""
        )

        refined = engine.refine_draft(
            draft=draft,
            feedback="Fix NonExistent section",
            validate_safety=False,
            score_voice=False,
        )

        # Should return original draft unchanged
        assert refined.sections[0].content == "Content"

    def test_refine_draft_with_voice_scoring(
        self,
        engine,
        mock_llm,
        mock_searcher,
    ):
        """Test refinement with voice scoring enabled."""
        mock_scorer = Mock()
        engine.voice_scorer = mock_scorer

        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[DraftSection(title="Section", content="Content")],
        )

        mock_llm.generate.side_effect = [
            Mock(content="ACTION: global\nSECTIONS: all\nINSTRUCTIONS: Improve"),
            Mock(content="Refined content"),
        ]

        refined = engine.refine_draft(
            draft=draft,
            feedback="Improve it",
            validate_safety=False,
            score_voice=True,
        )

        # Voice scorer should be called
        mock_scorer.score_draft.assert_called_once_with(refined)

    def test_refine_draft_with_safety_validation(
        self,
        engine,
        mock_llm,
        mock_searcher,
    ):
        """Test refinement with safety validation."""
        mock_validator = Mock()
        engine.safety_validator = mock_validator

        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[DraftSection(title="Section", content="Content")],
        )

        mock_llm.generate.side_effect = [
            Mock(content="ACTION: global\nSECTIONS: all\nINSTRUCTIONS: Improve"),
            Mock(content="Refined content"),
        ]

        refined = engine.refine_draft(
            draft=draft,
            feedback="Improve it",
            validate_safety=True,
            score_voice=False,
        )

        # Validator should be called
        mock_validator.validate_draft.assert_called_once_with(refined)

    def test_refine_section_basic(self, engine, mock_llm, mock_searcher):
        """Test refining a single section."""
        section = DraftSection(title="Test Section", content="Original content")

        mock_llm.generate.return_value = Mock(content="Refined section content")

        refined_section = engine._refine_section(
            section=section,
            instructions="Make it better",
            keywords=["test"],
        )

        assert refined_section.title == "Test Section"
        assert refined_section.content == "Refined section content"
        assert len(refined_section.citations) > 0

    def test_refine_section_no_search_results(self, engine, mock_llm, mock_searcher):
        """Test refinement when search returns no results."""
        section = DraftSection(title="Test", content="Content")

        mock_searcher.search.return_value = []

        refined_section = engine._refine_section(
            section=section,
            instructions="Improve",
            keywords=["test"],
        )

        # Should return original section
        assert refined_section == section

    def test_refine_section_llm_error(self, engine, mock_llm, mock_searcher):
        """Test section refinement when LLM fails."""
        section = DraftSection(title="Test", content="Content")

        mock_llm.generate.side_effect = Exception("LLM failed")

        refined_section = engine._refine_section(
            section=section,
            instructions="Improve",
            keywords=["test"],
        )

        # Should return original section on error
        assert refined_section == section

    def test_refine_section_preserves_subsections(
        self,
        engine,
        mock_llm,
        mock_searcher,
    ):
        """Test that subsections are preserved during refinement."""
        subsection = DraftSection(title="Sub", content="Sub content")
        section = DraftSection(
            title="Main",
            content="Main content",
            subsections=[subsection],
        )

        mock_llm.generate.return_value = Mock(content="Refined main content")

        refined_section = engine._refine_section(
            section=section,
            instructions="Improve",
            keywords=["test"],
        )

        # Subsections should be preserved
        assert len(refined_section.subsections) == 1
        assert refined_section.subsections[0].title == "Sub"

    def test_refine_section_only(self, engine, mock_llm, mock_searcher):
        """Test refining a section by title."""
        sections = [
            DraftSection(title="Intro", content="Intro content"),
            DraftSection(title="Body", content="Body content"),
        ]

        draft = Draft(title="Test", keywords=["test"], sections=sections)

        mock_llm.generate.return_value = Mock(content="Refined body content")

        refined_section = engine.refine_section_only(
            draft=draft,
            section_title="Body",
            instructions="Improve body",
        )

        assert refined_section is not None
        assert refined_section.title == "Body"
        assert refined_section.content == "Refined body content"

    def test_refine_section_only_not_found(
        self,
        engine,
        mock_llm,
        mock_searcher,
    ):
        """Test refining non-existent section."""
        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[DraftSection(title="Section", content="Content")],
        )

        result = engine.refine_section_only(
            draft=draft,
            section_title="NonExistent",
            instructions="Improve",
        )

        assert result is None

    def test_refine_draft_citations_added(self, engine, mock_llm, mock_searcher):
        """Test that refinement adds citations from search results."""
        draft = Draft(
            title="Test",
            keywords=["test"],
            sections=[DraftSection(title="Section", content="Content")],
        )

        mock_llm.generate.side_effect = [
            Mock(content="ACTION: global\nSECTIONS: all\nINSTRUCTIONS: Improve"),
            Mock(content="Refined content"),
        ]

        refined = engine.refine_draft(
            draft=draft,
            feedback="Improve it",
            validate_safety=False,
            score_voice=False,
        )

        # Should have citations from search results
        assert len(refined.sections[0].citations) > 0
        assert refined.sections[0].citations[0].filename == "source0.md"
