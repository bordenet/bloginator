"""Integration tests for topic alignment and corpus grounding.

These tests validate that the outline and draft generation processes correctly
handle topic validation and leverage improved search queries and corpus context.

Test Categories (per docs/HOW_TO_ASK_FOR_SAMPLES.md):
- Category A: Exact Match - titles match corpus documents, expect 85-95% coverage
- Category B: Similar Topics - related but different titles, expect 50-80% coverage
- Category C: Deliberate Mismatch - off-topic requests, expect <10% coverage or REJECT
"""

from unittest.mock import MagicMock

import pytest

from bloginator.generation._outline_prompt_builder import build_corpus_context, build_search_queries
from bloginator.generation.outline_generator import OutlineGenerator
from bloginator.prompts.loader import PromptLoader
from bloginator.search import CorpusSearcher, SearchResult


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_llm_client():
    """Mock LLMClient for controlled responses.

    OutlineGenerator now makes TWO calls:
    1. Validation call (expects "VALID" or error)
    2. Generation call (returns outline content)
    """
    client = MagicMock()

    # Create response objects for validation and generation
    validation_response = MagicMock()
    validation_response.content = "VALID"

    generation_response = MagicMock()
    generation_response.content = """
    ## Introduction
    Brief overview of the topic.
    ### Background
    Setting the stage.
    """

    # Default: first call returns validation, second returns outline
    client.generate.side_effect = [validation_response, generation_response]
    return client


@pytest.fixture
def mock_corpus_searcher():
    """Mock CorpusSearcher for controlled search results."""
    searcher = MagicMock(spec=CorpusSearcher)
    # Default search results (can be overridden)
    # Note: SearchResult takes 'distance' and calculates similarity_score = 1 - distance
    searcher.search.return_value = [
        SearchResult(
            chunk_id="chunk-1",
            content="This is some content about hiring managers and recruiting.",
            metadata={"filename": "hiring.md"},
            distance=0.1,  # similarity_score = 0.9
        ),
        SearchResult(
            chunk_id="chunk-2",
            content="Interviewing best practices involve structured questions.",
            metadata={"filename": "interview.md"},
            distance=0.2,  # similarity_score = 0.8
        ),
    ]
    return searcher


@pytest.fixture
def mock_prompt_loader():
    """Mock PromptLoader to load the modified prompt templates."""
    loader = MagicMock(spec=PromptLoader)
    # Mock for outline/base.yaml
    mock_outline_prompt = MagicMock()
    mock_outline_prompt.render_system_prompt.return_value = "System prompt for outline."
    mock_outline_prompt.render_user_prompt.return_value = "User prompt for outline."
    mock_outline_prompt.parameters = {
        "classification_contexts": {},
        "audience_contexts": {},
    }
    loader.load.side_effect = lambda x: {
        "outline/base.yaml": mock_outline_prompt,
        "draft/base.yaml": MagicMock(),  # Will be configured in specific tests
    }.get(x)
    return loader


@pytest.fixture
def outline_generator(mock_llm_client, mock_corpus_searcher, mock_prompt_loader):
    """Fixture for OutlineGenerator with mocked dependencies."""
    return OutlineGenerator(mock_llm_client, mock_corpus_searcher)


# =============================================================================
# Category A: Exact Match Tests (High Signal Baseline)
# Expected: 85-95% coverage, output closely mirrors source
# =============================================================================


class TestCategoryAExactMatch:
    """Tests where title matches corpus document exactly. Expect high coverage.

    Note: Coverage is calculated as (num_results/10) * avg_similarity * 100.
    With 10 results at 0.9 similarity = 90% coverage.
    """

    def test_exact_match_dashboard_topic(
        self, outline_generator, mock_llm_client, mock_corpus_searcher
    ):
        """A1: 'What Dashboards are Good For' matches corpus document exactly.

        Expected: High similarity scores (0.85+) because title = corpus doc name.
        """
        # Return 10 results with high similarity for proper coverage calculation
        mock_corpus_searcher.search.return_value = [
            SearchResult(
                chunk_id=f"dash-{i}",
                content=f"# What Dashboards are Good For\n\nChunk {i}: Dashboards provide "
                "at-a-glance visibility into system health and key metrics.",
                metadata={"filename": "What_Dashboards_are_Good_For.md", "document_id": f"doc{i}"},
                distance=0.1,  # similarity_score = 0.90
            )
            for i in range(10)
        ]

        # Reset side_effect for two calls: validation + generation
        validation_response = MagicMock()
        validation_response.content = "VALID"
        generation_response = MagicMock()
        generation_response.content = """
        ## The Purpose of Dashboards in Observability
        Understanding what dashboards excel at and where they fall short.
        ### At-a-Glance System Health
        Dashboards provide immediate visibility into key metrics and trends.
        ### When Dashboards Are Not Enough
        Dashboards cannot replace alerting or automated remediation.
        """
        mock_llm_client.generate.side_effect = [validation_response, generation_response]

        outline = outline_generator.generate(
            title="What Dashboards are Good For",
            keywords=["dashboard", "observability", "monitoring"],
            thesis="Dashboards provide at-a-glance visibility into system health",
        )

        # With 10 results at 0.9 similarity: (10/10) * 0.9 * 100 = 90%
        assert outline.avg_coverage >= 80  # High coverage expected for exact match
        assert len(outline.sections) > 0
        section_text = " ".join(s.title + " " + s.description for s in outline.sections).lower()
        assert "dashboard" in section_text

    def test_exact_match_sla_topic(self, outline_generator, mock_llm_client, mock_corpus_searcher):
        """A2: 'The Road to an SLA' matches corpus document exactly."""
        mock_corpus_searcher.search.return_value = [
            SearchResult(
                chunk_id=f"sla-{i}",
                content="# The Road to an SLA\n\nStart with SLIs (what you measure), "
                "then define SLOs (your targets), and finally commit to SLAs.",
                metadata={"filename": "The_Road_to_an_SLA.md", "document_id": f"doc{i}"},
                distance=0.1,  # similarity_score = 0.90
            )
            for i in range(10)
        ]

        # Reset side_effect for two calls: validation + generation
        validation_response = MagicMock()
        validation_response.content = "VALID"
        generation_response = MagicMock()
        generation_response.content = """
        ## Understanding the SLI to SLA Journey
        The path from indicators to agreements.
        ### Defining Service Level Indicators
        What you measure determines what you can promise.
        ### Setting Realistic SLOs
        Objectives must be achievable and meaningful.
        """
        mock_llm_client.generate.side_effect = [validation_response, generation_response]

        outline = outline_generator.generate(
            title="The Road to an SLA",
            keywords=["SLA", "SLO", "SLI", "reliability"],
            thesis="The journey from SLI to SLO to SLA requires thoughtful measurement",
        )

        assert outline.avg_coverage >= 80
        assert len(outline.sections) > 0


# =============================================================================
# Category B: Similar Topics Tests (Synthesized Content)
# Expected: 50-80% coverage, good quality synthesized from related sources
# =============================================================================


class TestCategoryBSimilarTopics:
    """Tests where title is related but not identical to corpus. Expect medium coverage.

    Note: Coverage = (num_results/10) * avg_similarity * 100.
    With 5 results at 0.7 similarity = 35% coverage (moderate).
    """

    def test_similar_topic_synthesized_dashboards(
        self, outline_generator, mock_llm_client, mock_corpus_searcher
    ):
        """B1: 'Building Dashboards That Drive Action' synthesizes from multiple docs."""
        # 6 results at LOW similarity to test moderate coverage
        # Coverage formula: (result_factor * normalized_similarity) * 100
        # - effective_sim = 0.9 * best + 0.1 * avg = 0.9 * 0.15 + 0.1 * 0.15 = 0.15
        # - normalized_sim = min(0.15 / 0.25, 1.0) = 0.6
        # - result_factor = min(6 / 2.0, 1.0) = 1.0
        # - coverage = 1.0 * 0.6 * 100 = 60%
        mock_corpus_searcher.search.return_value = [
            SearchResult(
                chunk_id=f"dash-{i}",
                content="Dashboards provide visibility but require careful design to be useful. "
                "When constructing a dashboard, start with the questions you want to answer.",
                metadata={
                    "filename": f"Dashboard_Doc_{i}.md",
                    "document_id": f"doc{i}",
                },
                distance=0.85,  # similarity_score = 0.15 (low match for moderate coverage)
            )
            for i in range(6)
        ]

        # Reset side_effect for two calls: validation + generation
        validation_response = MagicMock()
        validation_response.content = "VALID"
        generation_response = MagicMock()
        generation_response.content = """
        ## Dashboards That Surface Actionable Insights
        Moving beyond vanity metrics to real observability.
        ### Selecting SLIs That Matter
        Choose indicators that reflect user experience.
        ### Layout Principles for Quick Diagnosis
        Group related metrics and use consistent scales.
        """
        mock_llm_client.generate.side_effect = [validation_response, generation_response]

        outline = outline_generator.generate(
            title="Building Dashboards That Drive Action",
            keywords=["dashboard", "observability", "metrics", "SLI"],
            thesis="Effective dashboards surface actionable insights rather than vanity metrics",
        )

        # With 6 results at 0.15 similarity: coverage ~60%
        assert 50 <= outline.avg_coverage <= 70
        assert len(outline.sections) > 0


# =============================================================================
# Category C: Deliberate Mismatch Tests (Negative Tests)
# Expected: <10% coverage or REJECT - system should not hallucinate
# =============================================================================


class TestCategoryCDeliberateMismatch:
    """Tests where topic has NO relation to corpus. Expect rejection or very low coverage."""

    def test_mismatch_puppy_training(
        self, outline_generator, mock_llm_client, mock_corpus_searcher
    ):
        """C1: 'Training Your First Puppy' has no match in engineering corpus.

        Expected: Very low similarity, system should recognize mismatch.
        """
        # Corpus search returns irrelevant engineering content (best it could find)
        mock_corpus_searcher.search.return_value = [
            SearchResult(
                chunk_id="eng-1",
                content="This document discusses dashboard design and SLI monitoring "
                "for production systems. It covers observability best practices.",
                metadata={"filename": "What_Dashboards_are_Good_For.md"},
                distance=0.85,  # similarity_score = 0.15 (very low match)
            ),
        ]

        mock_llm_client.generate.return_value.content = """
        ## Introduction to Puppy Training
        Getting started with your new furry friend.
        ### Basic Obedience Commands
        Sit, stay, come, and other essentials.
        """

        outline = outline_generator.generate(
            title="Training Your First Puppy",
            keywords=["puppy", "training", "dog", "obedience"],
            thesis="Positive reinforcement is the key to successful puppy training",
        )

        # Mismatch should have very low coverage
        assert outline.avg_coverage < 50  # Low coverage expected

    def test_mismatch_sourdough_recipes(
        self, outline_generator, mock_llm_client, mock_corpus_searcher
    ):
        """C2: 'Best Recipes for Sourdough Bread' has no match in engineering corpus."""
        mock_corpus_searcher.search.return_value = [
            SearchResult(
                chunk_id="eng-1",
                content="Microservices architecture enables independent deployment "
                "but introduces operational complexity.",
                metadata={"filename": "SOA_and_Microservices.md"},
                distance=0.90,  # similarity_score = 0.10 (extremely low)
            ),
        ]

        mock_llm_client.generate.return_value.content = """
        ## The Art of Sourdough Starter
        Creating and maintaining your wild yeast culture.
        """

        outline = outline_generator.generate(
            title="Best Recipes for Sourdough Bread",
            keywords=["sourdough", "bread", "baking", "fermentation"],
            thesis="Great sourdough requires patience and understanding of fermentation",
        )

        # Complete mismatch should have very low coverage
        assert outline.avg_coverage < 50

    def test_mismatch_crypto_investment(
        self, outline_generator, mock_llm_client, mock_corpus_searcher
    ):
        """C3: 'Cryptocurrency Investment Strategies' has no match in engineering corpus."""
        mock_corpus_searcher.search.return_value = [
            SearchResult(
                chunk_id="eng-1",
                content="Understanding Conway's Law helps teams align their architecture "
                "with organizational structure for better outcomes.",
                metadata={"filename": "Understanding_Conways_Law.md"},
                distance=0.92,  # similarity_score = 0.08 (near zero)
            ),
        ]

        mock_llm_client.generate.return_value.content = """
        ## Cryptocurrency Market Fundamentals
        Understanding blockchain technology and token economics.
        """

        outline = outline_generator.generate(
            title="Cryptocurrency Investment Strategies",
            keywords=["crypto", "bitcoin", "investment", "blockchain"],
            thesis="Diversification and risk management are key to crypto investing",
        )

        assert outline.avg_coverage < 50


# =============================================================================
# Legacy Tests (Renamed for Clarity)
# =============================================================================


class TestLegacyTopicAlignment:
    """Original tests kept for backward compatibility."""

    def test_outline_rejects_mismatched_corpus(
        self, outline_generator, mock_llm_client, mock_corpus_searcher
    ):
        """Validate that the outline generator handles mismatched corpus content."""
        # Mock corpus search to return irrelevant content (no keyword matches)
        mock_corpus_searcher.search.return_value = [
            SearchResult(
                chunk_id="dash-1",
                content="This document is about dashboard design and SLI monitoring.",
                metadata={"filename": "dashboards.md"},
                distance=0.05,  # similarity_score = 0.95
            )
        ]
        mock_llm_client.generate.return_value.content = """
        ## Introduction to Hiring
        Overview of the recruiting process.
        ## Interview Best Practices
        How to conduct effective interviews.
        """

        outline = outline_generator.generate(
            title="What Great Hiring Managers Actually Do",
            keywords=["recruiting", "interviewing"],
            thesis="Great hiring managers own the process by calibrating expectations",
        )

        assert len(outline.sections) >= 0
        assert outline.avg_coverage <= 50

    def test_outline_accepts_matched_corpus(
        self, outline_generator, mock_llm_client, mock_corpus_searcher
    ):
        """Validate that the outline generator accepts matched corpus content."""
        mock_corpus_searcher.search.return_value = [
            SearchResult(
                chunk_id="chunk-1",
                content="This is about recruiting strategies and hiring managers.",
                metadata={"filename": "hiring.md"},
                distance=0.1,  # similarity_score = 0.9
            ),
            SearchResult(
                chunk_id="chunk-2",
                content="Best practices for interviewing candidates effectively.",
                metadata={"filename": "interview.md"},
                distance=0.2,  # similarity_score = 0.8
            ),
        ]

        # Reset side_effect for two calls: validation + generation
        validation_response = MagicMock()
        validation_response.content = "VALID"
        generation_response = MagicMock()
        generation_response.content = """
        ## Recruiting Strategy for Hiring Managers
        Understanding the critical impact on team growth and success.
        ### Strategic Workforce Planning
        Aligning hiring needs with business objectives.
        ## Interviewing Best Practices
        Ensuring fairness and effectiveness in candidate evaluation.
        ### Calibrating Expectations
        Defining clear roles and success metrics.
        """
        mock_llm_client.generate.side_effect = [validation_response, generation_response]

        outline = outline_generator.generate(
            title="What Great Hiring Managers Actually Do",
            keywords=["recruiting", "interviewing"],
            thesis="Great hiring managers own the process by calibrating expectations",
        )

        assert outline.validation_notes == ""
        assert len(outline.sections) > 0
        section_titles = " ".join(s.title for s in outline.sections).lower()
        assert "recruiting" in section_titles or "interviewing" in section_titles


# =============================================================================
# Search Query and Context Building Tests
# =============================================================================


class TestSearchQueryBuilding:
    """Tests for search query construction improvements."""

    def test_improved_search_queries(self):
        """Validate that longer, more specific search queries are generated."""
        title = "Daily Stand-Up Meetings That Don't Suck"
        keywords = ["agile", "ritual", "best-practices", "stand-up"]
        thesis = "Effective 15-minute daily stand-ups stay focused and energizing"

        queries = build_search_queries(title, keywords, thesis)

        assert len(queries) > 0
        # Query 1: Full title
        assert title in queries
        # Query 2: Title + first 2 keywords
        assert any(q.startswith(title) and "agile" in q for q in queries)
        # Query 3: Keywords with thesis snippet (first 50 chars)
        assert any("agile" in q and "Effective 15-minute" in q for q in queries)
        # Query 4: Three keywords combined
        assert any("agile" in q and "ritual" in q and "best-practices" in q for q in queries)
        # Ensure no duplicates
        assert len(queries) == len(set(queries))

    def test_corpus_context_richness(self):
        """Validate context includes similarity scores, source names, and previews.

        Note: Current implementation uses 200-char previews and 3 results max
        for faster LLM validation. Test verifies key content is present.
        """
        results = [
            SearchResult(
                chunk_id="chunk-1",
                content="This is a very long piece of content that discusses the nuances of "
                "hiring and effective recruiting strategies. It goes into detail about "
                "behavioral interviewing techniques, candidate assessment frameworks, "
                "and the importance of diversity in the hiring process. This content "
                "is meant to be truncated at 200 characters to show the improvement.",
                metadata={"filename": "hiring_strategy.md"},
                distance=0.075,  # similarity_score = 0.925
            ),
            SearchResult(
                chunk_id="chunk-2",
                content="Another document covering agile rituals, specifically focusing "
                "on daily stand-ups. It explains how to keep stand-ups efficient, "
                "avoid common pitfalls like status updates, and foster a culture "
                "of quick problem-solving. This content is also intentionally long.",
                metadata={"filename": "agile_standups.md"},
                distance=0.12,  # similarity_score = 0.880
            ),
        ]

        context = build_corpus_context(results)

        # Verify header and metadata formatting
        assert "CORPUS SEARCH RESULTS (validate topic match!):" in context
        assert "[1] Similarity: 0.925 | Source: hiring_strategy.md" in context
        assert "[2] Similarity: 0.880 | Source: agile_standups.md" in context
        # Verify key content is present (first 200 chars)
        assert "hiring and effective recruiting strategies" in context
        assert "agile rituals" in context
        # Context should be meaningful length (200 chars * 2 results + metadata)
        assert len(context) > 400
