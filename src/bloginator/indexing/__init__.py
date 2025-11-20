"""Document indexing and vector storage module.

This module handles:
- Text chunking strategies
- Embedding generation with sentence-transformers
- Vector storage with ChromaDB
- Metadata indexing and filtering
"""

from bloginator.indexing.indexer import CorpusIndexer


__all__ = ["CorpusIndexer"]
