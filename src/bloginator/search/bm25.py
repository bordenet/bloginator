"""BM25 lexical search index for keyword matching."""

import math
import re
from collections import Counter
from typing import Any


class BM25Index:
    """BM25 (Best Matching 25) lexical search index.

    BM25 is a ranking function used for keyword-based document retrieval.
    It considers term frequency, inverse document frequency, and document length.

    Attributes:
        k1: Term frequency saturation parameter (default 1.5)
        b: Length normalization parameter (default 0.75)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """Initialize BM25 index.

        Args:
            k1: Term frequency saturation (higher = more weight to repeated terms)
            b: Length normalization (0 = no normalization, 1 = full normalization)
        """
        self.k1 = k1
        self.b = b

        self._documents: list[dict[str, Any]] = []
        self._doc_lengths: list[int] = []
        self._avg_doc_length: float = 0.0
        self._doc_freqs: dict[str, int] = {}  # How many docs contain each term
        self._term_freqs: list[Counter[str]] = []  # Term frequencies per document

    @property
    def document_count(self) -> int:
        """Return the number of documents in the index."""
        return len(self._documents)

    def build(self, documents: list[dict[str, Any]]) -> None:
        """Build BM25 index from documents.

        Args:
            documents: List of dicts with 'id' and 'content' keys
        """
        self._documents = documents
        self._term_freqs = []
        self._doc_lengths = []
        self._doc_freqs = Counter()

        for doc in documents:
            tokens = self._tokenize(doc.get("content", ""))
            term_freq = Counter(tokens)
            self._term_freqs.append(term_freq)
            self._doc_lengths.append(len(tokens))

            # Track which terms appear in this document
            for term in set(tokens):
                self._doc_freqs[term] += 1

        # Calculate average document length
        if self._doc_lengths:
            self._avg_doc_length = sum(self._doc_lengths) / len(self._doc_lengths)
        else:
            self._avg_doc_length = 0.0

    def search(self, query: str, n_results: int = 10) -> list[dict[str, Any]]:
        """Search for documents matching query keywords.

        Args:
            query: Search query string
            n_results: Maximum number of results to return

        Returns:
            List of dicts with 'id', 'score', and original document data
        """
        if not self._documents:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores = []
        n_docs = len(self._documents)

        for doc_idx, _doc in enumerate(self._documents):
            score = 0.0
            doc_length = self._doc_lengths[doc_idx]
            term_freqs = self._term_freqs[doc_idx]

            for term in query_tokens:
                if term not in term_freqs:
                    continue

                tf = term_freqs[term]
                df = self._doc_freqs.get(term, 0)

                # IDF calculation with smoothing
                idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1)

                # BM25 term score
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * (doc_length / self._avg_doc_length)
                )
                score += idf * (numerator / denominator)

            if score > 0:
                scores.append((doc_idx, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        # Return top n results
        results = []
        for doc_idx, score in scores[:n_results]:
            doc = self._documents[doc_idx]
            results.append(
                {
                    "id": doc.get("id", str(doc_idx)),
                    "score": score,
                    **doc,
                }
            )

        return results

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase words.

        Args:
            text: Input text string

        Returns:
            List of lowercase word tokens
        """
        # Simple tokenization: lowercase and split on non-word chars
        text = text.lower()
        tokens = re.findall(r"\b[a-z0-9]+\b", text)
        return tokens
