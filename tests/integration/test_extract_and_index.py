"""Integration tests for extract and index workflow."""

from datetime import datetime
from pathlib import Path

import pytest

from bloginator.extraction import extract_text_from_file
from bloginator.extraction.chunking import chunk_text_by_paragraphs
from bloginator.indexing import CorpusIndexer
from bloginator.models import Chunk, Document, QualityRating


@pytest.mark.integration
@pytest.mark.slow
class TestExtractAndIndexWorkflow:
    """Integration tests for extracting documents and indexing them."""

    @pytest.fixture
    def sample_docs(self, fixtures_dir: Path) -> list[Path]:
        """Return list of sample document paths."""
        return list(fixtures_dir.glob("sample_doc*"))

    def test_extract_and_index_multiple_documents(
        self, tmp_path: Path, sample_docs: list[Path]
    ) -> None:
        """Test extracting and indexing multiple documents."""
        # Initialize indexer
        index_dir = tmp_path / "test_index"
        indexer = CorpusIndexer(output_dir=index_dir)

        total_chunks = 0

        # Extract and index each document
        for doc_path in sample_docs:
            # Extract text
            text = extract_text_from_file(doc_path)
            assert text is not None
            assert len(text) > 0

            # Create document model
            document = Document(
                id=f"doc_{doc_path.stem}",
                filename=doc_path.name,
                source_path=doc_path,
                format=doc_path.suffix[1:],  # Remove leading dot
                created_date=datetime(2023, 1, 1),
                modified_date=datetime(2023, 6, 1),
                quality_rating=QualityRating.PREFERRED,
                tags=["test", "sample"],
                word_count=len(text.split()),
            )

            # Chunk the text
            paragraphs = chunk_text_by_paragraphs(text, "test_doc")
            chunks = []
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip():  # Skip empty paragraphs
                    chunk = Chunk(
                        id=f"{document.id}_chunk_{i}",
                        document_id=document.id,
                        content=paragraph,
                        chunk_index=i,
                        section_heading=None,
                        char_start=0,
                        char_end=len(paragraph),
                    )
                    chunks.append(chunk)

            # Index document
            indexer.index_document(document, chunks)
            total_chunks += len(chunks)

        # Verify all documents were indexed
        assert indexer.get_total_chunks() == total_chunks
        assert indexer.get_total_chunks() > 0

        # Verify collection info
        info = indexer.get_collection_info()
        assert info["collection_name"] == "bloginator_corpus"
        assert info["total_chunks"] == total_chunks

    def test_extract_and_index_markdown(self, tmp_path: Path, fixtures_dir: Path) -> None:
        """Test extracting and indexing a markdown document."""
        md_file = fixtures_dir / "sample_doc1.md"

        # Extract text
        text = extract_text_from_file(md_file)
        assert "Engineering Leadership Principles" in text
        assert "Technical Excellence" in text

        # Create document
        document = Document(
            id="md_test_doc",
            filename=md_file.name,
            source_path=md_file,
            format="md",
            created_date=datetime(2023, 1, 1),
            modified_date=datetime(2023, 6, 1),
            quality_rating=QualityRating.STANDARD,
            tags=[],
            word_count=len(text.split()),
        )

        # Chunk text
        paragraphs = chunk_text_by_paragraphs(text, "test_doc")
        chunks = [
            Chunk(
                id=f"md_chunk_{i}",
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

        # Index
        index_dir = tmp_path / "md_index"
        indexer = CorpusIndexer(output_dir=index_dir)
        indexer.index_document(document, chunks)

        assert indexer.get_total_chunks() == len(chunks)
        assert len(chunks) > 0

    def test_extract_and_index_text_file(self, tmp_path: Path, fixtures_dir: Path) -> None:
        """Test extracting and indexing a plain text file."""
        txt_file = fixtures_dir / "sample_doc3.txt"

        # Extract text
        text = extract_text_from_file(txt_file)
        assert "Code Review Best Practices" in text
        assert "Review Code, Not People" in text

        # Create document
        document = Document(
            id="txt_test_doc",
            filename=txt_file.name,
            source_path=txt_file,
            format="txt",
            created_date=datetime(2023, 1, 1),
            modified_date=datetime(2023, 6, 1),
            quality_rating=QualityRating.DRAFT,
            tags=["code-review"],
            word_count=len(text.split()),
        )

        # Chunk text
        paragraphs = chunk_text_by_paragraphs(text, "test_doc")
        chunks = [
            Chunk(
                id=f"txt_chunk_{i}",
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

        # Index
        index_dir = tmp_path / "txt_index"
        indexer = CorpusIndexer(output_dir=index_dir)
        indexer.index_document(document, chunks)

        assert indexer.get_total_chunks() == len(chunks)
        assert len(chunks) > 0

    def test_incremental_indexing(self, tmp_path: Path, fixtures_dir: Path) -> None:
        """Test incremental indexing - adding documents to existing index."""
        index_dir = tmp_path / "incremental_index"
        indexer = CorpusIndexer(output_dir=index_dir)

        # Index first document
        doc1_path = fixtures_dir / "sample_doc1.md"
        text1 = extract_text_from_file(doc1_path)
        document1 = Document(
            id="doc1",
            filename=doc1_path.name,
            source_path=doc1_path,
            format="md",
            created_date=datetime(2023, 1, 1),
            modified_date=datetime(2023, 6, 1),
            quality_rating=QualityRating.PREFERRED,
            tags=[],
            word_count=len(text1.split()),
        )
        chunks1 = [
            Chunk(
                id=f"doc1_chunk_{i}",
                document_id="doc1",
                content=p,
                chunk_index=i,
                section_heading=None,
                char_start=0,
                char_end=len(p),
            )
            for i, p in enumerate(chunk_text_by_paragraphs(text1, "test_doc"))
            if p.strip()
        ]
        indexer.index_document(document1, chunks1)
        count_after_first = indexer.get_total_chunks()

        # Create new indexer instance (simulating reopening)
        indexer2 = CorpusIndexer(output_dir=index_dir)

        # Index second document
        doc2_path = fixtures_dir / "sample_doc2.md"
        text2 = extract_text_from_file(doc2_path)
        document2 = Document(
            id="doc2",
            filename=doc2_path.name,
            source_path=doc2_path,
            format="md",
            created_date=datetime(2023, 1, 1),
            modified_date=datetime(2023, 6, 1),
            quality_rating=QualityRating.PREFERRED,
            tags=[],
            word_count=len(text2.split()),
        )
        chunks2 = [
            Chunk(
                id=f"doc2_chunk_{i}",
                document_id="doc2",
                content=p,
                chunk_index=i,
                section_heading=None,
                char_start=0,
                char_end=len(p),
            )
            for i, p in enumerate(chunk_text_by_paragraphs(text2, "test_doc"))
            if p.strip()
        ]
        indexer2.index_document(document2, chunks2)

        # Verify total chunks is sum of both documents
        final_count = indexer2.get_total_chunks()
        assert final_count == count_after_first + len(chunks2)
        assert final_count > count_after_first
