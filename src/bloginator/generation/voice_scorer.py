"""Voice similarity scoring for authentic content validation."""


from sentence_transformers import SentenceTransformer

from bloginator.models.draft import Draft, DraftSection
from bloginator.search import CorpusSearcher


class VoiceScorer:
    """Score voice similarity between generated content and corpus.

    Uses embedding-based similarity to measure how well generated content
    matches the author's historical writing style.

    Attributes:
        embedding_model: Sentence transformer for embeddings
        searcher: Corpus searcher for finding style examples
        sample_size: Number of corpus samples to compare against
    """

    def __init__(
        self,
        searcher: CorpusSearcher,
        embedding_model: SentenceTransformer | None = None,
        sample_size: int = 20,
    ):
        """Initialize voice scorer.

        Args:
            searcher: Corpus searcher for sampling author's writing
            embedding_model: Optional sentence transformer (uses searcher's if None)
            sample_size: Number of corpus samples for comparison
        """
        self.searcher = searcher
        self.embedding_model = embedding_model or searcher.embedding_model
        self.sample_size = sample_size

    def score_draft(self, draft: Draft) -> None:
        """Score voice similarity for entire draft.

        Updates draft.voice_score and each section's voice_score.

        Args:
            draft: Draft to score (modified in place)

        Example:
            >>> scorer = VoiceScorer(searcher)
            >>> scorer.score_draft(draft)
            >>> print(f"Voice similarity: {draft.voice_score:.2f}")
        """
        # Score each section
        for section in draft.get_all_sections():
            self._score_section(section, draft.keywords)

        # Recalculate overall stats
        draft.calculate_stats()

    def _score_section(self, section: DraftSection, keywords: list[str]) -> None:
        """Score voice similarity for a section.

        Updates section.voice_score in place.

        Args:
            section: Section to score
            keywords: Document keywords for context
        """
        if not section.content:
            section.voice_score = 0.0
            return

        try:
            # Get embedding for generated content
            generated_embedding = self.embedding_model.encode([section.content])[0]

            # Sample corpus content with similar topics
            query = f"{section.title} {' '.join(keywords[:2])}"
            corpus_samples = self.searcher.search(
                query=query,
                n_results=self.sample_size,
            )

            if not corpus_samples:
                # No corpus samples to compare against
                section.voice_score = 0.5  # Neutral score
                return

            # Get embeddings for corpus samples
            corpus_texts = [sample.content for sample in corpus_samples]
            corpus_embeddings = self.embedding_model.encode(corpus_texts)

            # Calculate similarities
            from numpy import dot
            from numpy.linalg import norm

            def cosine_similarity(a, b):
                """Calculate cosine similarity between two vectors."""
                return dot(a, b) / (norm(a) * norm(b))

            similarities = [
                cosine_similarity(generated_embedding, corpus_emb)
                for corpus_emb in corpus_embeddings
            ]

            # Voice score is average similarity to corpus samples
            # Higher score = more similar to author's voice
            section.voice_score = float(sum(similarities) / len(similarities))

            # Ensure score is in [0, 1] range
            section.voice_score = max(0.0, min(1.0, section.voice_score))

        except Exception:
            # Fallback on error
            section.voice_score = 0.5

    def score_text(self, text: str, context_keywords: list[str]) -> float:
        """Score voice similarity for arbitrary text.

        Args:
            text: Text to score
            context_keywords: Keywords for corpus sampling context

        Returns:
            Voice similarity score (0-1, higher = more similar)

        Example:
            >>> score = scorer.score_text(
            ...     "Agile transformation requires cultural change.",
            ...     ["agile", "transformation"]
            ... )
            >>> print(f"Voice score: {score:.2f}")
        """
        if not text:
            return 0.0

        try:
            # Get embedding for text
            text_embedding = self.embedding_model.encode([text])[0]

            # Sample corpus content
            query = " ".join(context_keywords[:3])
            corpus_samples = self.searcher.search(
                query=query,
                n_results=self.sample_size,
            )

            if not corpus_samples:
                return 0.5  # Neutral

            # Calculate similarities
            corpus_texts = [s.content for s in corpus_samples]
            corpus_embeddings = self.embedding_model.encode(corpus_texts)

            from numpy import dot
            from numpy.linalg import norm

            def cosine_similarity(a, b):
                return dot(a, b) / (norm(a) * norm(b))

            similarities = [
                cosine_similarity(text_embedding, corpus_emb) for corpus_emb in corpus_embeddings
            ]

            score = float(sum(similarities) / len(similarities))
            return max(0.0, min(1.0, score))

        except Exception:
            return 0.5

    def get_voice_insights(self, draft: Draft, threshold: float = 0.7) -> dict[str, any]:
        """Get insights about voice similarity across draft.

        Args:
            draft: Draft to analyze
            threshold: Score threshold for "good" voice match

        Returns:
            Dictionary with voice analysis insights

        Example:
            >>> insights = scorer.get_voice_insights(draft)
            >>> print(f"Authentic sections: {insights['authentic_sections']}")
            >>> print(f"Weak sections: {insights['weak_sections']}")
        """
        all_sections = draft.get_all_sections()

        authentic_sections = [s.title for s in all_sections if s.voice_score >= threshold]

        weak_sections = [
            (s.title, s.voice_score) for s in all_sections if s.voice_score < threshold
        ]

        return {
            "overall_score": draft.voice_score,
            "total_sections": len(all_sections),
            "authentic_sections": len(authentic_sections),
            "authentic_section_titles": authentic_sections,
            "weak_sections": len(weak_sections),
            "weak_section_details": weak_sections,
            "threshold": threshold,
        }
