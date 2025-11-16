"""Test version information."""

import bloginator


def test_version_exists() -> None:
    """Test that version is defined."""
    assert hasattr(bloginator, "__version__")
    assert isinstance(bloginator.__version__, str)
    assert bloginator.__version__ == "0.1.0"


def test_author_exists() -> None:
    """Test that author is defined."""
    assert hasattr(bloginator, "__author__")
    assert isinstance(bloginator.__author__, str)


def test_email_exists() -> None:
    """Test that email is defined."""
    assert hasattr(bloginator, "__email__")
    assert isinstance(bloginator.__email__, str)
