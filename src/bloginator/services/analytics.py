"""Analytics service for corpus analysis and visualization."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


class CorpusAnalytics:
    """Analytics service for corpus statistics and insights.

    Provides data aggregation for visualizations and reporting.

    Attributes:
        extracted_dir: Directory containing extracted documents
        index_dir: Directory containing ChromaDB index
    """

    def __init__(self, extracted_dir: Path | str, index_dir: Path | str):
        """Initialize analytics service.

        Args:
            extracted_dir: Path to extracted documents
            index_dir: Path to ChromaDB index
        """
        self.extracted_dir = Path(extracted_dir)
        self.index_dir = Path(index_dir)

    def get_basic_stats(self) -> dict[str, Any]:
        """Get basic corpus statistics.

        Returns:
            Dictionary with document count, total size, chunks, etc.
        """
        stats = {
            "document_count": 0,
            "total_size_mb": 0.0,
            "chunk_count": 0,
            "avg_chunks_per_doc": 0.0,
        }

        if not self.extracted_dir.exists():
            return stats

        # Count documents
        json_files = list(self.extracted_dir.glob("*.json"))
        txt_files = list(self.extracted_dir.glob("*.txt"))
        stats["document_count"] = len(json_files)

        # Total size
        if txt_files:
            total_bytes = sum(f.stat().st_size for f in txt_files)
            stats["total_size_mb"] = total_bytes / 1024 / 1024

        # Chunk count from ChromaDB
        try:
            import chromadb

            client = chromadb.PersistentClient(path=str(self.index_dir))
            collections = client.list_collections()
            if collections:
                collection = collections[0]
                stats["chunk_count"] = collection.count()
                if json_files:
                    stats["avg_chunks_per_doc"] = stats["chunk_count"] / len(json_files)
        except Exception:
            pass

        return stats

    def get_quality_distribution(self) -> dict[str, int]:
        """Get distribution of documents by quality rating.

        Returns:
            Dictionary mapping quality rating to count
        """
        quality_counts: dict[str, int] = {}

        if not self.extracted_dir.exists():
            return quality_counts

        for json_file in self.extracted_dir.glob("*.json"):
            try:
                metadata = json.loads(json_file.read_text())
                quality = metadata.get("quality_rating", "standard")
                quality_counts[quality] = quality_counts.get(quality, 0) + 1
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                continue

        return quality_counts

    def get_source_distribution(self, top_n: int = 10) -> dict[str, int]:
        """Get distribution of documents by source.

        Args:
            top_n: Return top N sources (default: 10)

        Returns:
            Dictionary mapping source name to count
        """
        source_counts: Counter[str] = Counter()

        if not self.extracted_dir.exists():
            return dict(source_counts.most_common(top_n))

        for json_file in self.extracted_dir.glob("*.json"):
            try:
                metadata = json.loads(json_file.read_text())
                source = metadata.get("source_name", "Unknown")
                source_counts[source] += 1
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                continue

        return dict(source_counts.most_common(top_n))

    def get_tag_distribution(self, top_n: int = 20) -> dict[str, int]:
        """Get distribution of tags across corpus.

        Args:
            top_n: Return top N tags (default: 20)

        Returns:
            Dictionary mapping tag to count
        """
        tag_counts: Counter[str] = Counter()

        if not self.extracted_dir.exists():
            return dict(tag_counts.most_common(top_n))

        for json_file in self.extracted_dir.glob("*.json"):
            try:
                metadata = json.loads(json_file.read_text())
                tags = metadata.get("tags", [])
                tag_counts.update(tags)
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                continue

        return dict(tag_counts.most_common(top_n))

    def get_temporal_distribution(self) -> dict[int, int]:
        """Get distribution of documents by year.

        Returns:
            Dictionary mapping year to document count
        """
        year_counts: Counter[int] = Counter()

        if not self.extracted_dir.exists():
            return dict(year_counts)

        for json_file in self.extracted_dir.glob("*.json"):
            try:
                metadata = json.loads(json_file.read_text())
                created_date = metadata.get("created_date")
                if created_date:
                    try:
                        date = datetime.fromisoformat(created_date)
                        year_counts[date.year] += 1
                    except (ValueError, TypeError):
                        continue
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                continue

        return dict(year_counts)

    def get_word_count_distribution(self) -> list[int]:
        """Get word counts for all documents.

        Returns:
            List of word counts for histogram
        """
        word_counts = []

        if not self.extracted_dir.exists():
            return word_counts

        for txt_file in self.extracted_dir.glob("*.txt"):
            try:
                content = txt_file.read_text()
                word_count = len(content.split())
                word_counts.append(word_count)
            except FileNotFoundError:
                continue

        return word_counts

    def get_format_distribution(self) -> dict[str, int]:
        """Get distribution of documents by format type.

        Returns:
            Dictionary mapping format to count
        """
        format_counts: Counter[str] = Counter()

        if not self.extracted_dir.exists():
            return dict(format_counts)

        for json_file in self.extracted_dir.glob("*.json"):
            try:
                metadata = json.loads(json_file.read_text())
                format_type = metadata.get("format", "unknown")
                format_counts[format_type] += 1
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                continue

        return dict(format_counts)

    def get_quality_vs_word_count(self) -> list[dict[str, Any]]:
        """Get quality rating vs word count for scatter plot.

        Returns:
            List of dicts with 'quality', 'word_count', 'title'
        """
        data_points = []

        if not self.extracted_dir.exists():
            return data_points

        for json_file in self.extracted_dir.glob("*.json"):
            try:
                metadata = json.loads(json_file.read_text())
                quality = metadata.get("quality_rating", "standard")
                title = metadata.get("title", json_file.stem)

                # Get word count from txt file
                txt_file = json_file.with_suffix(".txt")
                if txt_file.exists():
                    content = txt_file.read_text()
                    word_count = len(content.split())

                    data_points.append(
                        {
                            "quality": quality,
                            "word_count": word_count,
                            "title": title,
                        }
                    )
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                continue

        return data_points

    def get_classification_distribution(self) -> dict[str, int]:
        """Get distribution of documents by classification.

        Returns:
            Dictionary mapping classification to count
        """
        classification_counts: Counter[str] = Counter()

        if not self.extracted_dir.exists():
            return dict(classification_counts)

        for json_file in self.extracted_dir.glob("*.json"):
            try:
                metadata = json.loads(json_file.read_text())
                classification = metadata.get("classification", "unknown")
                if classification != "unknown":
                    classification_counts[classification] += 1
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                continue

        return dict(classification_counts)

    def get_audience_distribution(self) -> dict[str, int]:
        """Get distribution of documents by target audience.

        Returns:
            Dictionary mapping audience to count
        """
        audience_counts: Counter[str] = Counter()

        if not self.extracted_dir.exists():
            return dict(audience_counts)

        for json_file in self.extracted_dir.glob("*.json"):
            try:
                metadata = json.loads(json_file.read_text())
                audience = metadata.get("audience", "unknown")
                if audience != "unknown":
                    audience_counts[audience] += 1
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                continue

        return dict(audience_counts)
