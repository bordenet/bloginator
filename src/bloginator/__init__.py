"""Bloginator: Content generation from your own writing corpus.

Bloginator helps create documents by leveraging historical writing. The system
indexes prior written material to generate new content based on the author's
existing corpus, using retrieval-augmented generation (RAG) with local or cloud LLMs.
"""

__version__ = "1.0.0"
__author__ = "Matt Bordenet"
__email__ = "matt@bordenet.com"

from bloginator import cli, extraction, generation, indexing, models, safety, search, voice

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "cli",
    "extraction",
    "indexing",
    "search",
    "generation",
    "voice",
    "safety",
    "models",
]
