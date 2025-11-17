"""Semantic search and retrieval module.

This module handles:
- Semantic similarity search
- Recency weighting (prefer recent content)
- Quality weighting (prefer marked "preferred" content)
- Combined scoring and ranking
"""

from bloginator.search.searcher import CorpusSearcher, SearchResult


# Backward compatibility alias
Searcher = CorpusSearcher

__all__ = ["CorpusSearcher", "SearchResult", "Searcher"]
