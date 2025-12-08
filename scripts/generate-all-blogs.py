#!/usr/bin/env python3
"""Autonomous blog generation tool.

This script generates all blogs from corpus/blog-topics.yaml using the
shadow corpus index. It acts as its own LLM backend, synthesizing content
directly from corpus search results.

Usage:
    python scripts/generate-all-blogs.py --index /tmp/bloginator/corpus_shadow/chroma
    python scripts/generate-all-blogs.py --index /tmp/bloginator/corpus_shadow/chroma --topic "hiring"
    python scripts/generate-all-blogs.py --index /tmp/bloginator/corpus_shadow/chroma --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path

import chromadb
import yaml
from sentence_transformers import SentenceTransformer


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("tmp/blog_generation.log"),
    ],
)
logger = logging.getLogger(__name__)


class CorpusSearcher:
    """Search the corpus index for relevant content."""

    def __init__(self, index_path: str):
        """Initialize with path to ChromaDB index."""
        self.client = chromadb.PersistentClient(path=index_path)
        self.collection = self.client.get_collection("bloginator_corpus")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info(f"Loaded index with {self.collection.count()} chunks")

    def search(self, query: str, n_results: int = 10) -> list[dict]:
        """Search for relevant corpus content."""
        query_embedding = self.model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        sources = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
            strict=False,
        ):
            sources.append(
                {
                    "content": doc,
                    "source": meta.get("source", "unknown"),
                    "distance": dist,
                    "similarity": 1 - dist,  # Convert distance to similarity
                }
            )
        return sources


def load_topics(topics_file: Path) -> list[dict]:
    """Load blog topics from YAML file."""
    with topics_file.open() as f:
        data = yaml.safe_load(f)

    # Handle flat list under 'topics' key
    topics = data.get("topics", [])

    logger.info(f"Loaded {len(topics)} topics from {topics_file}")
    return topics


def clean_source_content(content: str) -> str:
    """Clean extracted content of artifacts."""
    import re

    # Remove image dimension artifacts like "1024x640"
    content = re.sub(r"\b\d{3,4}x\d{3,4}\b", "", content)
    # Remove "Print XX" artifacts
    content = re.sub(r"\bPrint\s+\d+\b", "", content)
    # Remove multiple blank lines
    content = re.sub(r"\n{3,}", "\n\n", content)
    # Remove bullet point artifacts
    content = re.sub(r"^\s*•\s*$", "", content, flags=re.MULTILINE)
    return content.strip()


def dedupe_sources(sources: list[dict]) -> list[dict]:
    """Remove duplicate or near-duplicate sources."""
    seen_content = set()
    deduped = []
    for s in sources:
        # Use first 200 chars as signature
        sig = s["content"][:200].strip()
        if sig not in seen_content:
            seen_content.add(sig)
            deduped.append(s)
    return deduped


def synthesize_section(searcher: CorpusSearcher, section_title: str, topic: dict) -> str:
    """Synthesize content for a section from corpus sources.

    This is where Claude (the script runner) acts as the LLM, reading
    corpus sources and writing synthesized prose.
    """
    # Build search query from section and topic context
    query = f"{topic['title']} {section_title} {' '.join(topic.get('keywords', []))}"

    sources = searcher.search(query, n_results=10)
    sources = dedupe_sources(sources)

    if not sources:
        logger.warning(f"No sources found for: {section_title}")
        return f"[NO CORPUS CONTENT FOUND FOR: {section_title}]"

    # Clean and format sources for synthesis prompt
    cleaned_sources = []
    for i, s in enumerate(sources[:6]):  # Limit to top 6 after dedup
        cleaned = clean_source_content(s["content"])
        if len(cleaned) > 50:  # Skip very short fragments
            cleaned_sources.append(
                {
                    "num": i + 1,
                    "source": s["source"],
                    "similarity": s["similarity"],
                    "content": cleaned,
                }
            )

    # Format sources for the synthesis prompt
    source_text = "\n\n".join(
        [f"[Source {s['num']}] ({s['source']}):\n{s['content']}" for s in cleaned_sources]
    )

    # Return sources with metadata for synthesis
    # The synthesis will be done by Claude reading these files
    return f"""<!-- SOURCES ({len(cleaned_sources)} found):
{source_text}
-->

**[SYNTHESIZE FROM ABOVE SOURCES]**

Key points to cover:
- {section_title}
- Use terminology from sources exactly
- 150-250 words of cohesive prose
"""


def generate_blog(searcher: CorpusSearcher, topic: dict, output_dir: Path) -> Path:
    """Generate a complete blog draft for a topic."""
    title = topic["title"]
    slug = title.lower().replace(" ", "-").replace(":", "")[:50]
    output_file = output_dir / f"{slug}.md"

    logger.info(f"Generating: {title}")

    # Build sections
    sections = topic.get("sections", [])
    if not sections:
        # Create default sections from summary
        sections = [{"title": "Introduction"}, {"title": "Key Points"}, {"title": "Conclusion"}]

    content_parts = [f"# {title}\n"]

    for section in sections:
        # Sections can be strings or dicts with 'title' key
        section_title = section if isinstance(section, str) else section.get("title", str(section))
        section_content = synthesize_section(searcher, section_title, topic)
        content_parts.append(f"\n## {section_title}\n\n{section_content}\n")

    # Write output
    output_file.write_text("\n".join(content_parts))
    logger.info(f"Wrote: {output_file}")

    return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate blogs from corpus")
    parser.add_argument("--index", required=True, help="Path to ChromaDB index")
    parser.add_argument("--topics", default="corpus/blog-topics.yaml", help="Topics YAML")
    parser.add_argument("--output", default="blogs/drafts", help="Output directory")
    parser.add_argument("--topic", help="Filter to topics containing this string")
    parser.add_argument("--dry-run", action="store_true", help="List topics without generating")
    args = parser.parse_args()

    # Ensure output dir exists
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load topics
    topics = load_topics(Path(args.topics))

    if args.topic:
        topics = [t for t in topics if args.topic.lower() in t["title"].lower()]
        logger.info(f"Filtered to {len(topics)} topics matching '{args.topic}'")

    if args.dry_run:
        for t in topics:
            print(f"  - {t['title']} ({t.get('series', 'unknown')})")
        return

    # Initialize searcher
    searcher = CorpusSearcher(args.index)

    # Generate each blog
    for topic in topics:
        try:
            generate_blog(searcher, topic, output_dir)
        except Exception as e:
            logger.error(f"Failed to generate '{topic['title']}': {e}")


if __name__ == "__main__":
    main()
