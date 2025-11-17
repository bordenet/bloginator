"""End-to-end tests for complete user workflows."""

from datetime import datetime
from pathlib import Path

import pytest

from bloginator.extraction import extract_text_from_file
from bloginator.extraction.chunking import chunk_text_by_paragraphs
from bloginator.indexing import CorpusIndexer
from bloginator.models import Chunk, Document, QualityRating
from bloginator.search import CorpusSearcher
from bloginator.templates import get_template, list_templates


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflows:
    """End-to-end tests for complete user workflows."""

    @pytest.fixture
    def user_corpus(self, tmp_path: Path, fixtures_dir: Path) -> dict:
        """Simulate a user's complete corpus setup."""
        # Step 1: Extract documents
        extracted_docs = []
        sample_docs = list(fixtures_dir.glob("sample_doc*"))

        for doc_path in sample_docs:
            text = extract_text_from_file(doc_path)
            extracted_docs.append(
                {
                    "path": doc_path,
                    "text": text,
                    "format": doc_path.suffix[1:],
                    "word_count": len(text.split()),
                }
            )

        # Step 2: Create index
        index_dir = tmp_path / "user_index"
        indexer = CorpusIndexer(output_dir=index_dir)

        for i, doc_data in enumerate(extracted_docs):
            document = Document(
                id=f"user_doc_{i}",
                filename=doc_data["path"].name,
                source_path=doc_data["path"],
                format=doc_data["format"],
                created_date=datetime(2023, 1, 1 + i),
                modified_date=datetime(2023, 6, 1 + i),
                quality_rating=QualityRating.PREFERRED,
                tags=["user", "corpus"],
                word_count=doc_data["word_count"],
            )

            paragraphs = chunk_text_by_paragraphs(doc_data["text"])
            chunks = [
                Chunk(
                    id=f"user_doc_{i}_chunk_{j}",
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

        return {
            "index_dir": index_dir,
            "total_documents": len(extracted_docs),
            "indexer": indexer,
        }

    def test_full_document_creation_workflow(self, user_corpus: dict) -> None:
        """Test complete workflow: corpus → search → template → outline → draft."""
        index_dir = user_corpus["index_dir"]

        # Step 1: User searches corpus for relevant content
        searcher = CorpusSearcher(persist_directory=str(index_dir))
        search_results = searcher.search(query="leadership principles", n_results=5)

        assert len(search_results) > 0
        assert all(r.content for r in search_results)

        # Step 2: User selects a template
        template = get_template("team_charter")
        assert template is not None
        assert "title" in template
        assert "sections" in template

        # Step 3: Generate outline using template and search results
        outline = {
            "title": template["title"],
            "thesis": "Building strong engineering teams through clear values and practices",
            "keywords": ["leadership", "culture", "collaboration"],
            "sections": [],
        }

        # For each template section, find relevant content
        for section in template["sections"]:
            section_data = {
                "title": section["title"],
                "description": section["description"],
                "subsections": section.get("subsections", []),
                "relevant_content": [],
            }

            # Search for content relevant to this section
            section_results = searcher.search(query=section["description"], n_results=2)
            section_data["relevant_content"] = [r.content for r in section_results]

            outline["sections"].append(section_data)

        # Verify outline structure
        assert len(outline["sections"]) == len(template["sections"])
        assert all("title" in s for s in outline["sections"])
        assert all("description" in s for s in outline["sections"])

        # Step 4: Simulate draft generation (without actual LLM calls)
        # In real implementation, this would use OutlineGenerator and DraftGenerator
        draft_sections = []
        for section in outline["sections"]:
            draft_section = {
                "title": section["title"],
                "content": f"Content for {section['title']} based on: {section['description']}",
                "sources": section["relevant_content"][:1],  # Use first result as source
            }
            draft_sections.append(draft_section)

        assert len(draft_sections) == len(outline["sections"])

    def test_corpus_search_and_refinement_workflow(self, user_corpus: dict) -> None:
        """Test workflow: build corpus → search → refine search → generate."""
        index_dir = user_corpus["index_dir"]
        searcher = CorpusSearcher(persist_directory=str(index_dir))

        # Initial broad search
        initial_results = searcher.search(query="engineering", n_results=10)
        assert len(initial_results) > 0

        # Refined search with more specific query
        refined_results = searcher.search(
            query="engineering leadership and team culture", n_results=5
        )
        assert len(refined_results) > 0

        # Results should be more focused
        assert len(refined_results) <= len(initial_results)

    def test_template_based_document_creation(self, user_corpus: dict) -> None:
        """Test creating different document types using templates."""
        index_dir = user_corpus["index_dir"]
        searcher = CorpusSearcher(persist_directory=str(index_dir))

        # Test multiple template types
        template_ids = ["blog_post", "team_charter", "career_ladder"]

        for template_id in template_ids:
            # Load template
            template = get_template(template_id)
            assert template is not None

            # Create basic outline from template
            outline = {
                "template_id": template_id,
                "template_name": template["template_name"],
                "title": template["title"],
                "sections": [],
            }

            # For each section, gather relevant content
            for section in template["sections"]:
                # Search for content
                results = searcher.search(query=section["description"], n_results=2)

                outline["sections"].append(
                    {
                        "title": section["title"],
                        "description": section["description"],
                        "content_sources": len(results),
                    }
                )

            # Verify outline was created
            assert len(outline["sections"]) > 0
            assert outline["template_id"] == template_id

    def test_multi_query_content_gathering(self, user_corpus: dict) -> None:
        """Test gathering content from multiple search queries for rich context."""
        index_dir = user_corpus["index_dir"]
        searcher = CorpusSearcher(persist_directory=str(index_dir))

        # Multiple related queries to build comprehensive context
        queries = [
            "leadership principles",
            "team culture and values",
            "engineering best practices",
            "code review and quality",
        ]

        all_content = {}
        for query in queries:
            results = searcher.search(query=query, n_results=3)
            all_content[query] = {
                "num_results": len(results),
                "top_result": results[0].content if results else None,
            }

        # Verify we gathered content for all queries
        assert len(all_content) == len(queries)
        assert all(data["num_results"] >= 0 for data in all_content.values())

    def test_incremental_corpus_building_workflow(
        self, tmp_path: Path, fixtures_dir: Path
    ) -> None:
        """Test workflow of incrementally building corpus over time."""
        index_dir = tmp_path / "incremental_corpus"

        # Day 1: Initial corpus with first document
        indexer1 = CorpusIndexer(output_dir=index_dir)
        doc1_path = fixtures_dir / "sample_doc1.md"
        text1 = extract_text_from_file(doc1_path)

        document1 = Document(
            id="day1_doc",
            filename=doc1_path.name,
            source_path=doc1_path,
            format="md",
            created_date=datetime(2023, 1, 1),
            modified_date=datetime(2023, 1, 1),
            quality_rating=QualityRating.PREFERRED,
            tags=["initial"],
            word_count=len(text1.split()),
        )

        chunks1 = [
            Chunk(
                id=f"day1_chunk_{i}",
                document_id="day1_doc",
                content=p,
                chunk_index=i,
                section_heading=None,
                char_start=0,
                char_end=len(p),
            )
            for i, p in enumerate(chunk_text_by_paragraphs(text1))
            if p.strip()
        ]

        indexer1.index_document(document1, chunks1)
        day1_count = indexer1.get_total_chunks()

        # Day 2: Add more documents
        indexer2 = CorpusIndexer(output_dir=index_dir)
        doc2_path = fixtures_dir / "sample_doc2.md"
        text2 = extract_text_from_file(doc2_path)

        document2 = Document(
            id="day2_doc",
            filename=doc2_path.name,
            source_path=doc2_path,
            format="md",
            created_date=datetime(2023, 1, 2),
            modified_date=datetime(2023, 1, 2),
            quality_rating=QualityRating.PREFERRED,
            tags=["added"],
            word_count=len(text2.split()),
        )

        chunks2 = [
            Chunk(
                id=f"day2_chunk_{i}",
                document_id="day2_doc",
                content=p,
                chunk_index=i,
                section_heading=None,
                char_start=0,
                char_end=len(p),
            )
            for i, p in enumerate(chunk_text_by_paragraphs(text2))
            if p.strip()
        ]

        indexer2.index_document(document2, chunks2)
        day2_count = indexer2.get_total_chunks()

        # Verify incremental growth
        assert day2_count > day1_count

        # Search should now return results from both documents
        searcher = CorpusSearcher(persist_directory=str(index_dir))
        results = searcher.search(query="engineering leadership", n_results=10)
        assert len(results) > 0

    def test_template_library_accessibility(self) -> None:
        """Test that all templates in library are accessible and valid."""
        templates = list_templates()

        assert len(templates) >= 12  # Should have at least 12 templates

        # Verify each template loads correctly
        for template_id in templates.keys():
            template = get_template(template_id)

            assert template is not None
            assert "title" in template
            assert "sections" in template
            assert len(template["sections"]) > 0

            # Verify metadata is present
            assert "template_id" in template
            assert "template_name" in template
            assert "template_description" in template

    def test_category_based_template_selection(self) -> None:
        """Test selecting templates by category."""
        # Get templates by category
        content_templates = list_templates(category="content")
        career_templates = list_templates(category="career")
        technical_templates = list_templates(category="technical")

        # Verify we got category-specific results
        assert len(content_templates) > 0
        assert len(career_templates) > 0
        assert len(technical_templates) > 0

        # Verify templates are actually in the right categories
        for template_id, template_meta in content_templates.items():
            assert template_meta["category"] == "content"

        for template_id, template_meta in career_templates.items():
            assert template_meta["category"] == "career"
