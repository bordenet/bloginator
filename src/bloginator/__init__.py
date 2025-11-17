"""Bloginator: Authentic content generation from your own writing corpus.

Bloginator helps engineering leaders create authentic, high-quality documents
by leveraging their own historical writing corpus. The system indexes years of
prior written material to generate new content that reads in the author's
authentic voice—avoiding generic "AI slop" while dramatically reducing
document creation time.
"""

__version__ = "0.1.0"
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
