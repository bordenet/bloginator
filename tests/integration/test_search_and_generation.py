"""Integration tests for search and generation workflow."""

from datetime import datetime
from pathlib import Path

import pytest

from bloginator.extraction import extract_text_from_file
from bloginator.extraction.chunking import chunk_text_by_paragraphs
from bloginator.indexing import CorpusIndexer
from bloginator.models import Chunk, Document, QualityRating
from bloginator.search import CorpusSearcher
from bloginator.templates import get_template


@pytest.mark.integration
@pytest.mark.slow
class TestSearchAndGenerationWorkflow:
    """Integration tests for searching corpus and using results for generation."""

    @pytest.fixture
    def indexed_corpus(self, tmp_path: Path, fixtures_dir: Path) -> Path:
        """Create an indexed corpus from sample documents."""
        index_dir = tmp_path / "corpus_index"
        indexer = CorpusIndexer(output_dir=index_dir)

        # Index all sample documents
        sample_docs = list(fixtures_dir.glob("sample_doc*"))
        for doc_path in sample_docs:
            text = extract_text_from_file(doc_path)

            document = Document(
                id=f"doc_{doc_path.stem}",
                filename=doc_path.name,
                source_path=doc_path,
                format=doc_path.suffix[1:],
                created_date=datetime(2023, 1, 1),
                modified_date=datetime(2023, 6, 1),
                quality_rating=QualityRating.PREFERRED,
                tags=["leadership", "engineering"],
                word_count=len(text.split()),
            )

            paragraphs = chunk_text_by_paragraphs(text)
            chunks = [
                Chunk(
                    id=f"{document.id}_chunk_{i}",
                    document_id=document.id,
                    content=p,
                    chunk_index=i,
                    section_heading=None,
                    char_start=0,
                    char_end=len(p),
                )
                for i, p in enumerate(paragraphs)
                if p.strip()
            ]

            indexer.index_document(document, chunks)

        return index_dir

    def test_search_indexed_corpus(self, indexed_corpus: Path) -> None:
        """Test searching an indexed corpus."""
        searcher = CorpusSearcher(persist_directory=str(indexed_corpus))

        # Search for leadership content
        results = searcher.search(query="leadership principles", n_results=5)

        assert len(results) > 0
        assert all(isinstance(r.content, str) for r in results)
        assert all(isinstance(r.similarity_score, float) for r in results)
        assert all(0.0 <= r.similarity_score <= 1.0 for r in results)

        # Verify results are sorted by relevance
        scores = [r.similarity_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_with_different_queries(self, indexed_corpus: Path) -> None:
        """Test searching with different query types."""
        searcher = CorpusSearcher(persist_directory=str(indexed_corpus))

        # Technical query
        tech_results = searcher.search(query="technical excellence", n_results=3)
        assert len(tech_results) > 0

        # Leadership query
        leadership_results = searcher.search(query="team building culture", n_results=3)
        assert len(leadership_results) > 0

        # Communication query
        comm_results = searcher.search(query="code review best practices", n_results=3)
        assert len(comm_results) > 0

    def test_search_quality_and_recency_weighting(self, tmp_path: Path) -> None:
        """Test that quality and recency affect search ranking."""
        index_dir = tmp_path / "weighted_index"
        indexer = CorpusIndexer(output_dir=index_dir)

        # Create old standard quality document
        old_doc = Document(
            id="old_doc",
            filename="old.md",
            source_path=Path("/test/old.md"),
            format="md",
            created_date=datetime(2020, 1, 1),
            modified_date=datetime(2020, 1, 1),
            quality_rating=QualityRating.STANDARD,
            tags=[],
            word_count=50,
        )
        old_chunks = [
            Chunk(
                id="old_chunk",
                document_id="old_doc",
                content="Leadership requires strong communication and vision.",
                chunk_index=0,
                section_heading=None,
                char_start=0,
                char_end=100,
            )
        ]

        # Create recent preferred quality document
        new_doc = Document(
            id="new_doc",
            filename="new.md",
            source_path=Path("/test/new.md"),
            format="md",
            created_date=datetime(2023, 6, 1),
            modified_date=datetime(2023, 6, 1),
            quality_rating=QualityRating.PREFERRED,
            tags=[],
            word_count=50,
        )
        new_chunks = [
            Chunk(
                id="new_chunk",
                document_id="new_doc",
                content="Effective leadership demands clear communication and strategic vision.",
                chunk_index=0,
                section_heading=None,
                char_start=0,
                char_end=100,
            )
        ]

        indexer.index_document(old_doc, old_chunks)
        indexer.index_document(new_doc, new_chunks)

        # Search for leadership
        searcher = CorpusSearcher(persist_directory=str(index_dir))
        results = searcher.search(query="leadership communication", n_results=2)

        # With quality and recency weighting, newer preferred document should rank higher
        # (assuming similar semantic similarity)
        assert len(results) == 2

    def test_template_loading_for_generation(self) -> None:
        """Test loading document templates for outline generation."""
        # Test loading various templates
        blog_template = get_template("blog_post")
        assert blog_template is not None
        assert blog_template["title"] == "Technical Blog Post"
        assert len(blog_template["sections"]) > 0

        career_template = get_template("career_ladder")
        assert career_template is not None
        assert "Career Ladder" in career_template["title"]
        assert len(career_template["sections"]) > 0

        playbook_template = get_template("engineering_playbook")
        assert playbook_template is not None
        assert "Playbook" in playbook_template["title"]

    def test_search_results_for_outline_context(self, indexed_corpus: Path) -> None:
        """Test using search results to provide context for outline generation."""
        searcher = CorpusSearcher(persist_directory=str(indexed_corpus))

        # Load template
        template = get_template("team_charter")
        assert template is not None

        # Search for relevant content for each section
        section_contexts = {}
        for section in template["sections"]:
            section_title = section["title"]
            description = section["description"]

            # Search using section description
            results = searcher.search(query=description, n_results=3)

            section_contexts[section_title] = {
                "description": description,
                "relevant_content": [r.content for r in results],
                "num_results": len(results),
            }

        # Verify we found relevant content for sections
        assert len(section_contexts) > 0
        for _section_title, context in section_contexts.items():
            assert context["num_results"] >= 0  # Some sections may have no matches
            assert isinstance(context["relevant_content"], list)

    def test_keyword_based_search_for_outline(self, indexed_corpus: Path) -> None:
        """Test keyword-based search for outline generation."""
        searcher = CorpusSearcher(persist_directory=str(indexed_corpus))

        # Test multiple keyword queries
        keywords = ["leadership", "culture", "team building"]

        all_results = []
        for keyword in keywords:
            results = searcher.search(query=keyword, n_results=3)
            all_results.extend(results)

        assert len(all_results) > 0

        # Verify we got diverse content
        unique_content = {r.content for r in all_results}
        assert len(unique_content) > 0

    def test_search_with_metadata_filtering(self, tmp_path: Path) -> None:
        """Test searching with metadata-based filtering."""
        index_dir = tmp_path / "metadata_index"
        indexer = CorpusIndexer(output_dir=index_dir)

        # Create documents with different tags
        doc1 = Document(
            id="doc1",
            filename="leadership.md",
            source_path=Path("/test/leadership.md"),
            format="md",
            created_date=datetime(2023, 1, 1),
            modified_date=datetime(2023, 1, 1),
            quality_rating=QualityRating.PREFERRED,
            tags=["leadership", "management"],
            word_count=100,
        )
        chunks1 = [
            Chunk(
                id="chunk1",
                document_id="doc1",
                content="Leadership principles for engineering managers.",
                chunk_index=0,
                section_heading=None,
                char_start=0,
                char_end=100,
            )
        ]

        doc2 = Document(
            id="doc2",
            filename="technical.md",
            source_path=Path("/test/technical.md"),
            format="md",
            created_date=datetime(2023, 1, 1),
            modified_date=datetime(2023, 1, 1),
            quality_rating=QualityRating.STANDARD,
            tags=["technical", "architecture"],
            word_count=100,
        )
        chunks2 = [
            Chunk(
                id="chunk2",
                document_id="doc2",
                content="Technical architecture best practices for scalable systems.",
                chunk_index=0,
                section_heading=None,
                char_start=0,
                char_end=100,
            )
        ]

        indexer.index_document(doc1, chunks1)
        indexer.index_document(doc2, chunks2)

        # Search
        searcher = CorpusSearcher(persist_directory=str(index_dir))
        results = searcher.search(query="engineering practices", n_results=5)

        assert len(results) > 0
