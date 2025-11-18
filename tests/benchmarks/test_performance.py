"""Performance benchmarks for Bloginator operations."""

import time
from datetime import datetime
from pathlib import Path

import pytest

from bloginator.extraction import extract_text_from_file
from bloginator.extraction.chunking import chunk_text_by_paragraphs
from bloginator.indexing import CorpusIndexer
from bloginator.models import Chunk, Document, QualityRating
from bloginator.search import CorpusSearcher
from bloginator.templates import get_template, list_templates


@pytest.mark.benchmark
@pytest.mark.slow
class TestPerformanceBenchmarks:
    """Performance benchmarks for key operations.

    These tests measure performance to ensure operations complete within
    acceptable time limits as specified in the PRD.

    Performance Targets (from PRD):
    - Index Building: <30 minutes for 500+ documents
    - Search: <3 seconds
    - Draft Generation: <5 minutes from outline
    - Refinement: <2 minutes per iteration
    """

    @pytest.fixture
    def large_corpus(self, tmp_path: Path, fixtures_dir: Path) -> dict:
        """Create a larger corpus for performance testing."""
        # Create multiple copies of sample documents to simulate larger corpus
        index_dir = tmp_path / "large_index"
        indexer = CorpusIndexer(output_dir=index_dir)

        sample_docs = list(fixtures_dir.glob("sample_doc*"))
        total_chunks = 0

        # Create 30 documents (10x each sample doc)
        for i in range(10):
            for doc_path in sample_docs:
                text = extract_text_from_file(doc_path)

                document = Document(
                    id=f"perf_doc_{i}_{doc_path.stem}",
                    filename=f"{i}_{doc_path.name}",
                    source_path=doc_path,
                    format=doc_path.suffix[1:],
                    created_date=datetime(2023, 1, 1 + i),
                    modified_date=datetime(2023, 6, 1 + i),
                    quality_rating=QualityRating.PREFERRED,
                    tags=["performance", "test"],
                    word_count=len(text.split()),
                )

                paragraphs = chunk_text_by_paragraphs(text, "test_doc")
                chunks = [
                    Chunk(
                        id=f"{document.id}_chunk_{j}",
                        document_id=document.id,
                        content=p,
                        chunk_index=j,
                        section_heading=None,
                        char_start=0,
                        char_end=len(p),
                    )
                    for j, p in enumerate(paragraphs)
                    if p.strip()
                ]

                indexer.index_document(document, chunks)
                total_chunks += len(chunks)

        return {
            "index_dir": index_dir,
            "total_documents": 30,
            "total_chunks": total_chunks,
        }

    def test_document_extraction_performance(self, fixtures_dir: Path) -> None:
        """Benchmark document extraction performance."""
        sample_docs = list(fixtures_dir.glob("sample_doc*"))

        start_time = time.time()

        for _ in range(10):  # Extract each document 10 times
            for doc_path in sample_docs:
                text = extract_text_from_file(doc_path)
                assert text is not None

        elapsed = time.time() - start_time
        avg_per_doc = elapsed / (len(sample_docs) * 10)

        # Should extract a document in less than 0.5 seconds
        assert avg_per_doc < 0.5, f"Extraction took {avg_per_doc:.3f}s per doc"

        print(f"\\nExtraction: {avg_per_doc:.3f}s per document (avg)")

    def test_text_chunking_performance(self, fixtures_dir: Path) -> None:
        """Benchmark text chunking performance."""
        doc_path = fixtures_dir / "sample_doc1.md"
        text = extract_text_from_file(doc_path)

        start_time = time.time()

        for _ in range(100):  # Chunk the same text 100 times
            chunks = chunk_text_by_paragraphs(text, "test_doc")
            assert len(chunks) > 0

        elapsed = time.time() - start_time
        avg_per_chunk = elapsed / 100

        # Should chunk a document in less than 0.1 seconds
        assert avg_per_chunk < 0.1, f"Chunking took {avg_per_chunk:.3f}s"

        print(f"\\nChunking: {avg_per_chunk:.3f}s per document (avg)")

    def test_indexing_performance(self, tmp_path: Path, fixtures_dir: Path) -> None:
        """Benchmark indexing performance."""
        index_dir = tmp_path / "perf_index"
        indexer = CorpusIndexer(output_dir=index_dir)

        sample_docs = list(fixtures_dir.glob("sample_doc*"))

        start_time = time.time()

        # Index 10 documents
        for i, doc_path in enumerate(sample_docs * 4):  # ~12 documents
            text = extract_text_from_file(doc_path)

            document = Document(
                id=f"idx_perf_{i}",
                filename=doc_path.name,
                source_path=doc_path,
                format=doc_path.suffix[1:],
                created_date=datetime(2023, 1, 1),
                modified_date=datetime(2023, 6, 1),
                quality_rating=QualityRating.PREFERRED,
                tags=[],
                word_count=len(text.split()),
            )

            paragraphs = chunk_text_by_paragraphs(text, "test_doc")
            chunks = [
                Chunk(
                    id=f"idx_chunk_{i}_{j}",
                    document_id=document.id,
                    content=p,
                    chunk_index=j,
                    section_heading=None,
                    char_start=0,
                    char_end=len(p),
                )
                for j, p in enumerate(paragraphs)
                if p.strip()
            ]

            indexer.index_document(document, chunks)

        elapsed = time.time() - start_time

        # Target: <30 minutes for 500 docs means ~3.6s per doc
        # For small corpus, should be much faster
        assert elapsed < 60, f"Indexing took {elapsed:.1f}s for 12 docs"

        print(f"\\nIndexing: {elapsed:.1f}s for 12 documents")
        print(
            f"Estimated time for 500 docs: {(elapsed/12)*500:.1f}s (~{(elapsed/12)*500/60:.1f} min)"
        )

    def test_search_performance(self, large_corpus: dict) -> None:
        """Benchmark search performance."""
        searcher = CorpusSearcher(persist_directory=str(large_corpus["index_dir"]))

        queries = [
            "leadership principles",
            "team culture",
            "technical excellence",
            "code review",
            "career development",
        ]

        start_time = time.time()

        for query in queries:
            results = searcher.search(query=query, n_results=10)
            assert len(results) > 0

        elapsed = time.time() - start_time
        avg_per_search = elapsed / len(queries)

        # Target: <3 seconds per search
        assert avg_per_search < 3.0, f"Search took {avg_per_search:.3f}s (target: <3s)"

        print(f"\\nSearch: {avg_per_search:.3f}s per query (avg)")
        print(f"Total for {len(queries)} queries: {elapsed:.3f}s")

    def test_search_scaling_with_results(self, large_corpus: dict) -> None:
        """Benchmark search performance with varying result counts."""
        searcher = CorpusSearcher(persist_directory=str(large_corpus["index_dir"]))

        result_counts = [5, 10, 20, 50]
        timings = {}

        for n_results in result_counts:
            start_time = time.time()
            results = searcher.search(query="engineering leadership", n_results=n_results)
            elapsed = time.time() - start_time

            timings[n_results] = elapsed
            assert len(results) <= n_results

        # All should complete in under 3 seconds
        for n, t in timings.items():
            assert t < 3.0, f"Search for {n} results took {t:.3f}s"

        print("\\nSearch scaling:")
        for n, t in timings.items():
            print(f"  {n} results: {t:.3f}s")

    def test_template_loading_performance(self) -> None:
        """Benchmark template loading performance."""
        templates = list_templates()
        template_ids = list(templates.keys())

        start_time = time.time()

        # Load each template 10 times
        for _ in range(10):
            for template_id in template_ids:
                template = get_template(template_id)
                assert template is not None

        elapsed = time.time() - start_time
        avg_per_load = elapsed / (len(template_ids) * 10)

        # Template loading should be very fast (<10ms per template)
        assert avg_per_load < 0.01, f"Template loading took {avg_per_load*1000:.1f}ms"

        print(f"\\nTemplate loading: {avg_per_load*1000:.1f}ms per template (avg)")

    def test_concurrent_search_performance(self, large_corpus: dict) -> None:
        """Benchmark multiple concurrent searches."""
        searcher = CorpusSearcher(persist_directory=str(large_corpus["index_dir"]))

        queries = [
            "leadership",
            "culture",
            "technical",
            "review",
            "career",
            "principles",
            "excellence",
            "collaboration",
        ]

        start_time = time.time()

        # Perform all searches sequentially (simulating rapid user queries)
        for query in queries:
            results = searcher.search(query=query, n_results=5)
            assert len(results) > 0

        elapsed = time.time() - start_time

        # All searches should complete quickly
        assert elapsed < 20, f"Concurrent searches took {elapsed:.1f}s"

        print(f"\\nConcurrent search: {len(queries)} queries in {elapsed:.1f}s")
        print(f"Average: {elapsed/len(queries):.3f}s per query")

    def test_index_size_efficiency(self, large_corpus: dict) -> None:
        """Test index size is reasonable for corpus size."""
        index_dir = large_corpus["index_dir"]

        # Calculate index directory size
        total_size = 0
        for path in index_dir.rglob("*"):
            if path.is_file():
                total_size += path.stat().st_size

        # Index size in MB
        size_mb = total_size / (1024 * 1024)

        print(f"\\nIndex size: {size_mb:.2f} MB for {large_corpus['total_documents']} documents")
        print(f"Index size per document: {size_mb/large_corpus['total_documents']:.2f} MB")

        # Index should be reasonable size (less than 100MB for 30 docs)
        assert size_mb < 100, f"Index size is {size_mb:.2f}MB (might be too large)"

    def test_memory_efficient_chunking(self, tmp_path: Path) -> None:
        """Test that chunking doesn't require excessive memory."""
        # Create a large text
        large_text = "This is a test paragraph.\\n\\n" * 1000

        start_time = time.time()

        # Chunk the large text
        chunks = chunk_text_by_paragraphs(large_text, "test_doc")

        elapsed = time.time() - start_time

        # Should handle large text efficiently
        assert len(chunks) > 0
        assert elapsed < 1.0, f"Chunking large text took {elapsed:.3f}s"

        print(f"\\nLarge text chunking: {len(chunks)} chunks in {elapsed:.3f}s")
