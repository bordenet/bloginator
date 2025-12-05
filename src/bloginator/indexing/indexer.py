"""ChromaDB indexer for document corpus."""

from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias, cast

import chromadb
from chromadb.api.types import IncludeEnum
from sentence_transformers import SentenceTransformer

from bloginator.models import Chunk, Document


if TYPE_CHECKING:
    from collections.abc import Mapping


# ChromaDB metadata value types (None not allowed in actual metadata dicts)
MetadataValue: TypeAlias = str | int | float | bool


class CorpusIndexer:
    """Indexer for building and managing document corpus vector store.

    Uses ChromaDB for persistent vector storage and sentence-transformers
    for generating embeddings.

    Attributes:
        output_dir: Directory for ChromaDB persistence
        collection_name: Name of ChromaDB collection
        client: ChromaDB client
        collection: ChromaDB collection
        embedding_model: Sentence transformer model
    """

    def __init__(
        self,
        output_dir: Path,
        collection_name: str = "bloginator_corpus",
        embedding_model_name: str = "all-MiniLM-L6-v2",
    ):
        """Initialize corpus indexer.

        Args:
            output_dir: Directory for ChromaDB persistence
            collection_name: Name of ChromaDB collection (default: bloginator_corpus)
            embedding_model_name: Sentence transformer model name
        """
        self.output_dir = output_dir
        self.collection_name = collection_name

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=str(self.output_dir))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model_name)

    def get_document_checksum(self, document_id: str) -> str | None:
        """Get the content checksum for an indexed document.

        Args:
            document_id: ID of document to check

        Returns:
            Content checksum if document exists in index, None otherwise
        """
        results = self.collection.get(
            where={"document_id": document_id},
            limit=1,
            include=[IncludeEnum.metadatas],
        )

        if results and results["metadatas"]:
            return cast("str | None", results["metadatas"][0].get("content_checksum"))

        return None

    def document_needs_reindexing(self, document: Document) -> bool:
        """Check if document needs to be reindexed based on checksum.

        Args:
            document: Document to check

        Returns:
            True if document needs reindexing (new or content changed)
        """
        if not document.content_checksum:
            # No checksum, reindex to be safe
            return True

        existing_checksum = self.get_document_checksum(document.id)

        # New document or checksum changed
        return existing_checksum is None or existing_checksum != document.content_checksum

    def index_document(self, document: Document, chunks: list[Chunk]) -> None:
        """Add document chunks to vector store with metadata.

        Args:
            document: Document metadata
            chunks: List of text chunks to index
        """
        if not chunks:
            return

        # Generate embeddings
        contents = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.encode(contents, show_progress_bar=False)

        # Prepare metadata for each chunk
        metadatas: list[Mapping[str, MetadataValue]] = []
        for chunk in chunks:
            metadata: dict[str, MetadataValue] = {
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "section_heading": chunk.section_heading or "",
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                # Document-level metadata
                "source": document.filename,  # Critical: used by outline/draft prompts
                "filename": document.filename,
                "format": document.format,
                "quality_rating": str(
                    document.quality_rating.value
                    if hasattr(document.quality_rating, "value")
                    else document.quality_rating
                ),
                "is_external_source": document.is_external_source,
                "tags": ",".join(document.tags) if document.tags else "",
            }

            # Add dates if available
            if document.created_date:
                metadata["created_date"] = document.created_date.isoformat()
            if document.modified_date:
                metadata["modified_date"] = document.modified_date.isoformat()

            # Add content checksum for incremental indexing
            if document.content_checksum:
                metadata["content_checksum"] = document.content_checksum

            metadatas.append(metadata)

        # Add to ChromaDB collection
        self.collection.add(
            ids=[chunk.id for chunk in chunks],
            embeddings=embeddings.tolist(),
            documents=contents,
            metadatas=metadatas,
        )

    def get_total_chunks(self) -> int:
        """Get total number of chunks in index.

        Returns:
            Number of chunks in collection
        """
        return int(self.collection.count())

    def delete_document(self, document_id: str) -> None:
        """Delete all chunks for a document from the index.

        Args:
            document_id: ID of document to delete
        """
        # Query for chunks with this document_id
        results = self.collection.get(where={"document_id": document_id})

        if results and results["ids"]:
            self.collection.delete(ids=results["ids"])

    def clear_index(self) -> None:
        """Clear all documents from the index."""
        # Delete collection and recreate
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def get_collection_info(self) -> dict[str, Any]:
        """Get information about the collection.

        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()

        return {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "output_dir": str(self.output_dir),
        }
