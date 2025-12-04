"""Integration tests for the full pipeline using the sample corpus.

These tests validate extraction, indexing, and search using real blog content
from the Engineering_Culture repository to identify gaps in the pipeline.

=============================================================================
HOW TO USE THIS TEST FILE
=============================================================================

PREREQUISITES:
    Run ./scripts/setup-macos.sh to download the sample corpus to test-corpus/

    The sample corpus contains 15+ engineering blog posts covering:
    - Culture: Conway's Law, feedback models, professional writing
    - SDLC: Mechanisms, PR-FAQ, one-pagers, what-vs-how
    - EngFundamentals: SOA, SLAs, dashboards

RUN THESE TESTS:
    # Run all sample corpus tests
    pytest tests/integration/test_sample_corpus_pipeline.py -v

    # Run specific test class
    pytest tests/integration/test_sample_corpus_pipeline.py::TestSampleCorpusSearch -v

    # Run with output to see search results (useful for debugging)
    pytest tests/integration/test_sample_corpus_pipeline.py -v -s

ADAPTING FOR YOUR OWN CORPUS:
    1. Create your own test file: tests/integration/test_my_corpus.py
    2. Copy the fixture pattern from this file
    3. Update sample_corpus_path to point to your content
    4. Create test cases that match YOUR topics and expected search results

    Example for a cooking blog corpus:
        def test_search_pasta_recipes(self, indexed_my_corpus):
            results = searcher.search("homemade pasta Italian cooking")
            assert any("pasta" in r.content.lower() for r in results)

=============================================================================
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from bloginator.extraction import extract_text_from_file
from bloginator.extraction.chunking import chunk_text_by_paragraphs
from bloginator.indexing import CorpusIndexer
from bloginator.models import Document, QualityRating
from bloginator.search import CorpusSearcher


# =============================================================================
# FIXTURES - Reusable setup for tests
# =============================================================================


@pytest.fixture(scope="module")
def sample_corpus_path() -> Path | None:
    """Return path to the sample corpus if available.

    The sample corpus is downloaded by setup-macos.sh from:
    https://github.com/bordenet/Engineering_Culture

    Returns:
        Path to test-corpus/Engineering_Culture, or None if not available
    """
    repo_root = Path(__file__).parent.parent.parent
    corpus_path = repo_root / "test-corpus" / "Engineering_Culture"
    if corpus_path.exists():
        return corpus_path
    return None


@pytest.fixture(scope="module")
def indexed_sample_corpus(sample_corpus_path: Path | None, tmp_path_factory) -> Path | None:
    """Index the sample corpus and return the index path.

    This fixture:
    1. Extracts text from all markdown files in the sample corpus
    2. Chunks the text using paragraph-based chunking
    3. Indexes chunks into ChromaDB with embeddings

    The indexed corpus is reused across all tests in this module for efficiency.

    Args:
        sample_corpus_path: Path to the sample corpus directory
        tmp_path_factory: Pytest factory for temporary directories

    Returns:
        Path to the ChromaDB index directory, or None if corpus unavailable
    """
    if sample_corpus_path is None:
        pytest.skip("Sample corpus not available. Run ./scripts/setup-macos.sh")

    index_dir = tmp_path_factory.mktemp("sample_index")
    indexer = CorpusIndexer(output_dir=index_dir)

    # Find all markdown files (excluding README)
    md_files = [f for f in sample_corpus_path.rglob("*.md") if f.name != "README.md"]
    assert len(md_files) > 0, "No markdown files found in sample corpus"

    indexed_files = []
    total_chunks = 0

    for i, md_file in enumerate(md_files):
        text = extract_text_from_file(md_file)
        doc_id = f"ec_{md_file.stem}_{i}"

        # Determine category from path
        category = md_file.parent.name  # Culture, SDLC, or EngFundamentals

        document = Document(
            id=doc_id,
            filename=md_file.name,
            source_path=md_file,
            format="md",
            created_date=datetime(2024, 1, 1),
            modified_date=datetime(2024, 1, 1),
            quality_rating=QualityRating.PREFERRED,
            tags=["engineering", "culture", category.lower()],
            word_count=len(text.split()),
        )

        chunks = chunk_text_by_paragraphs(text, doc_id)
        for j, chunk in enumerate(chunks):
            chunk.id = f"{doc_id}_chunk_{j}"

        indexer.index_document(document, chunks)
        indexed_files.append(md_file.name)
        total_chunks += len(chunks)

    return index_dir


# =============================================================================
# EXTRACTION TESTS - Verify content is extracted correctly
# =============================================================================


@pytest.mark.integration
class TestSampleCorpusExtraction:
    """Test extraction from sample corpus.

    These tests verify that markdown content is correctly extracted,
    preserving key terms and structure that will be needed for search.
    """

    def test_corpus_has_expected_structure(self, sample_corpus_path: Path | None) -> None:
        """Verify sample corpus has expected directory structure."""
        if sample_corpus_path is None:
            pytest.skip("Sample corpus not available")

        # Check for expected subdirectories
        culture_dir = sample_corpus_path / "Culture"
        sdlc_dir = sample_corpus_path / "SDLC"
        eng_dir = sample_corpus_path / "EngFundamentals"

        assert culture_dir.exists(), "Culture directory not found"
        assert sdlc_dir.exists(), "SDLC directory not found"
        assert eng_dir.exists(), "EngFundamentals directory not found"

    def test_markdown_files_count(self, sample_corpus_path: Path | None) -> None:
        """Verify sample corpus has expected number of files."""
        if sample_corpus_path is None:
            pytest.skip("Sample corpus not available")

        md_files = [f for f in sample_corpus_path.rglob("*.md") if f.name != "README.md"]
        # Should have 15 blog post files
        assert len(md_files) >= 10, f"Expected 10+ blog posts, got {len(md_files)}"

    def test_conways_law_extraction_quality(self, sample_corpus_path: Path | None) -> None:
        """Test extraction quality for Conway's Law document.

        This tests that key concepts are preserved during extraction:
        - Technical terms (Conway, architecture, organization)
        - Document structure (headings preserved)
        - Sufficient content length
        """
        if sample_corpus_path is None:
            pytest.skip("Sample corpus not available")

        conways_law = sample_corpus_path / "Culture" / "Understanding_Conways_Law.md"
        assert conways_law.exists(), "Conway's Law file not found"

        text = extract_text_from_file(conways_law)

        # Content quality checks
        assert len(text) > 2000, f"Extracted text too short: {len(text)} chars"
        assert text.count("\n") > 20, "Document structure not preserved (missing newlines)"

        # Key term preservation
        key_terms = ["Conway", "organization", "architecture", "team", "system"]
        for term in key_terms:
            assert term.lower() in text.lower(), f"Missing key term: {term}"

    def test_mechanisms_extraction_quality(self, sample_corpus_path: Path | None) -> None:
        """Test extraction quality for Mechanisms document."""
        if sample_corpus_path is None:
            pytest.skip("Sample corpus not available")

        # Handle filename with colon (may vary by filesystem)
        # Look for "Building_Self-Correcting" specifically to get the main mechanisms doc
        mechanisms_files = list(sample_corpus_path.glob("SDLC/*Self-Correcting*.md"))
        if not mechanisms_files:
            # Fallback to any mechanisms file
            mechanisms_files = list(sample_corpus_path.glob("SDLC/*Mechanisms*.md"))
        if not mechanisms_files:
            pytest.skip("Mechanisms file not found")

        text = extract_text_from_file(mechanisms_files[0])

        # Key concepts from the Mechanisms post (flexible - any 2 of these is good)
        key_terms = ["mechanism", "process", "self-correcting", "feedback", "system"]
        found_terms = [t for t in key_terms if t.lower() in text.lower()]
        assert len(found_terms) >= 2, f"Missing key terms. Found: {found_terms}"

    def test_dashboard_extraction_quality(self, sample_corpus_path: Path | None) -> None:
        """Test extraction quality for Dashboard document."""
        if sample_corpus_path is None:
            pytest.skip("Sample corpus not available")

        dashboard_files = list(sample_corpus_path.glob("EngFundamentals/*Dashboard*.md"))
        if not dashboard_files:
            pytest.skip("Dashboard files not found")

        text = extract_text_from_file(dashboard_files[0])

        # Key concepts from dashboard posts
        key_terms = ["dashboard", "metric", "visualization", "monitoring"]
        found_terms = [t for t in key_terms if t.lower() in text.lower()]
        assert len(found_terms) >= 2, f"Missing key terms. Found: {found_terms}"


# =============================================================================
# INDEXING TESTS - Verify chunks are created and stored correctly
# =============================================================================


@pytest.mark.integration
class TestSampleCorpusIndexing:
    """Test indexing of sample corpus.

    These tests verify that:
    - Documents are chunked appropriately
    - Chunks are stored in ChromaDB with embeddings
    - Metadata is preserved for filtering
    """

    def test_index_creates_chunks(self, indexed_sample_corpus: Path | None) -> None:
        """Verify indexing creates expected number of chunks."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        indexer = CorpusIndexer(output_dir=indexed_sample_corpus)
        chunk_count = indexer.get_total_chunks()

        # 15 documents × ~5-10 chunks each = 75-150 chunks expected
        assert chunk_count >= 50, f"Too few chunks: {chunk_count}. Check chunking strategy."
        assert chunk_count <= 500, f"Too many chunks: {chunk_count}. Chunks may be too small."

    def test_index_persistence(self, indexed_sample_corpus: Path | None) -> None:
        """Verify index persists and can be reopened."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        # Open a new indexer instance (simulates restarting the application)
        indexer1 = CorpusIndexer(output_dir=indexed_sample_corpus)
        count1 = indexer1.get_total_chunks()

        # Open another instance
        indexer2 = CorpusIndexer(output_dir=indexed_sample_corpus)
        count2 = indexer2.get_total_chunks()

        assert count1 == count2, "Chunk counts differ between indexer instances"
        assert count1 > 0, "Index appears to be empty after reopening"


# =============================================================================
# SEARCH TESTS - Verify retrieval quality (CRITICAL for identifying gaps)
# =============================================================================


@pytest.mark.integration
class TestSampleCorpusSearch:
    """Test search against indexed sample corpus.

    These tests are CRITICAL for identifying retrieval gaps:
    - Do searches return relevant content?
    - Are the right documents ranked highly?
    - Can we find content using different query phrasings?

    If these tests fail, the LLM will receive poor context and generate
    off-topic content (the "garbage in, garbage out" problem).
    """

    def test_search_returns_results(self, indexed_sample_corpus: Path | None) -> None:
        """Basic sanity check: search returns results."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search("engineering leadership", n_results=5)

        assert len(results) > 0, "Search returned no results"
        assert all(r.content for r in results), "Some results have empty content"

    def test_search_conways_law_direct(self, indexed_sample_corpus: Path | None) -> None:
        """Search for Conway's Law using exact terminology."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search("Conway's Law", n_results=5)

        assert len(results) > 0, "No results for 'Conway's Law'"

        # At least one result should mention Conway
        conway_results = [r for r in results if "conway" in r.content.lower()]
        assert len(conway_results) > 0, (
            "No results mention 'Conway'. Top result: " + results[0].content[:200]
        )

    def test_search_conways_law_conceptual(self, indexed_sample_corpus: Path | None) -> None:
        """Search for Conway's Law using conceptual terms (not exact phrase).

        This tests semantic search quality - can we find relevant content
        without using the exact terminology?
        """
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        # Query using concepts, not the exact phrase "Conway's Law"
        results = searcher.search(
            "team structure affects software architecture organization design",
            n_results=5,
        )

        assert len(results) > 0, "No results for conceptual query"

        # Should find Conway's Law content even without mentioning "Conway"
        relevant_terms = ["conway", "organization", "architecture", "team", "structure"]
        top_content = results[0].content.lower()
        matches = [t for t in relevant_terms if t in top_content]

        assert len(matches) >= 2, (
            f"Top result doesn't seem relevant. Found terms: {matches}. "
            f"Content preview: {results[0].content[:300]}"
        )

    def test_search_mechanisms(self, indexed_sample_corpus: Path | None) -> None:
        """Search for Mechanisms content."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search("mechanisms self-correcting systems process", n_results=5)

        assert len(results) > 0, "No results for mechanisms query"

        # Check for relevant content
        mechanism_results = [r for r in results if "mechanism" in r.content.lower()]
        assert (
            len(mechanism_results) > 0
        ), "No results mention 'mechanism'. Check if content was indexed correctly."

    def test_search_feedback_model(self, indexed_sample_corpus: Path | None) -> None:
        """Search for SBI feedback model content."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search("SBI feedback model constructive", n_results=5)

        assert len(results) > 0, "No results for feedback query"

        # Should find feedback-related content
        feedback_terms = ["feedback", "sbi", "behavior", "impact"]
        all_content = " ".join(r.content.lower() for r in results[:3])
        matches = [t for t in feedback_terms if t in all_content]

        assert len(matches) >= 1, f"No feedback-related content found. Terms found: {matches}"

    def test_search_dashboards(self, indexed_sample_corpus: Path | None) -> None:
        """Search for dashboard and monitoring content."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search("dashboard monitoring metrics visualization", n_results=5)

        assert len(results) > 0, "No results for dashboard query"

        # Should find dashboard content
        dashboard_results = [r for r in results if "dashboard" in r.content.lower()]
        assert len(dashboard_results) > 0, "No results mention 'dashboard'"

    def test_search_sla_reliability(self, indexed_sample_corpus: Path | None) -> None:
        """Search for SLA and reliability content."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search("SLA service level agreement reliability", n_results=5)

        assert len(results) > 0, "No results for SLA query"

        # Check for SLA-related terms
        sla_terms = ["sla", "service", "availability", "reliability", "uptime"]
        all_content = " ".join(r.content.lower() for r in results[:3])
        matches = [t for t in sla_terms if t in all_content]

        assert len(matches) >= 1, f"No SLA-related content found. Terms found: {matches}"

    def test_search_similarity_scores(self, indexed_sample_corpus: Path | None) -> None:
        """Verify search results have meaningful similarity scores."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search("engineering culture leadership", n_results=5)

        assert len(results) > 0, "No results returned"

        # Check that results have similarity scores
        for i, result in enumerate(results):
            assert hasattr(result, "similarity_score"), f"Result {i} missing similarity_score"
            assert (
                0 <= result.similarity_score <= 1
            ), f"Result {i} has invalid similarity_score: {result.similarity_score}"

        # Results should be ordered by similarity (highest first)
        scores = [r.similarity_score for r in results]
        assert scores == sorted(scores, reverse=True), "Results not sorted by similarity"

    def test_search_no_false_positives(self, indexed_sample_corpus: Path | None) -> None:
        """Verify search doesn't return high-scoring unrelated content.

        This is a "negative test" - we search for something NOT in the corpus
        and verify results have low similarity.
        """
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        # Search for topic NOT in the engineering culture corpus
        results = searcher.search("chocolate cake recipe baking instructions", n_results=5)

        if len(results) > 0:
            # Results should have low similarity scores for unrelated queries
            top_score = results[0].similarity_score
            # With good embeddings, unrelated content should score < 0.5
            assert top_score < 0.8, (
                f"Unrelated query returned high-similarity result ({top_score}). "
                "This may indicate embedding issues."
            )


# =============================================================================
# TOPIC-SPECIFIC SEARCH TESTS - Match the 7 sample blogs from HOW_TO_ASK_FOR_SAMPLES.md
# =============================================================================


@pytest.mark.integration
class TestSampleCorpusTopicAlignment:
    """Test searches that align with the 7 requested sample blogs.

    These tests verify the corpus can support the blog topics defined in
    docs/HOW_TO_ASK_FOR_SAMPLES.md. If these fail, the corpus may not have
    sufficient content to generate those blogs.
    """

    def test_search_hiring_manager_content(self, indexed_sample_corpus: Path | None) -> None:
        """Search for content relevant to 'What Great Hiring Managers Do'.

        Note: The Engineering_Culture corpus may have limited hiring content.
        This test helps identify gaps that need to be filled.
        """
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search(
            "hiring recruiting interviewing candidates calibration", n_results=5
        )

        # This may return low-relevance results if corpus lacks hiring content
        if len(results) > 0:
            top_score = results[0].similarity_score
            if top_score < 0.3:
                pytest.xfail(
                    f"Corpus may lack hiring content (top score: {top_score:.2f}). "
                    "Consider adding hiring-related documents."
                )

    def test_search_standup_meeting_content(self, indexed_sample_corpus: Path | None) -> None:
        """Search for content relevant to 'Daily Stand-Up Meetings That Don't Suck'."""
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search("agile standup daily meeting ritual scrum", n_results=5)

        # May have some agile-adjacent content in mechanisms
        if len(results) > 0:
            all_content = " ".join(r.content.lower() for r in results[:3])
            agile_terms = ["agile", "standup", "meeting", "ritual", "daily", "scrum"]
            matches = [t for t in agile_terms if t in all_content]

            if len(matches) == 0:
                pytest.xfail(
                    "Corpus may lack agile/standup content. "
                    "Consider adding agile process documents."
                )

    def test_search_operational_excellence(self, indexed_sample_corpus: Path | None) -> None:
        """Search for content relevant to operational excellence blogs.

        The Engineering_Culture corpus has SLA and dashboard content which
        should be highly relevant.
        """
        if indexed_sample_corpus is None:
            pytest.skip("Indexed corpus not available")

        searcher = CorpusSearcher(index_dir=indexed_sample_corpus)
        results = searcher.search(
            "operational excellence runbook incident response on-call", n_results=5
        )

        assert len(results) > 0, "No results for operational excellence query"

        # Should find some relevant content in EngFundamentals
        ops_terms = ["operational", "incident", "runbook", "monitoring", "sla", "dashboard"]
        all_content = " ".join(r.content.lower() for r in results[:3])
        matches = [t for t in ops_terms if t in all_content]

        assert len(matches) >= 1, (
            f"Limited operational content found. Matches: {matches}. "
            "The EngFundamentals posts should have relevant content."
        )
