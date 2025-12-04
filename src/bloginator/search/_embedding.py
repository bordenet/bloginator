"""Embedding model management with caching."""

import logging

from sentence_transformers import SentenceTransformer


# Module-level cache for embedding models to avoid reloading
_EMBEDDING_MODEL_CACHE: dict[str, SentenceTransformer] = {}

logger = logging.getLogger(__name__)


def _get_embedding_model(model_name: str) -> SentenceTransformer:
    """Get or load embedding model with caching.

    This function caches embedding models to avoid reloading them on every
    CorpusSearcher initialization, which can take 10-60 seconds.

    Args:
        model_name: Name of the sentence-transformers model

    Returns:
        Loaded SentenceTransformer model

    Note:
        First load may take time to download model from HuggingFace.
        Subsequent loads use cached instance.
    """
    if model_name not in _EMBEDDING_MODEL_CACHE:
        logger.info(f"Loading embedding model '{model_name}' " f"(this may take 10-60 seconds)...")
        try:
            model = SentenceTransformer(model_name)
            _EMBEDDING_MODEL_CACHE[model_name] = model
            logger.info(f"Embedding model '{model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model '{model_name}': {e}")
            raise RuntimeError(
                f"Failed to load embedding model '{model_name}'. "
                f"This may be due to network issues or missing model files. "
                f"Error: {e}"
            ) from e
    else:
        logger.debug(f"Using cached embedding model '{model_name}'")

    return _EMBEDDING_MODEL_CACHE[model_name]
