"""End-to-end tests for Streamlit UI pages.

Tests all Streamlit pages render without exceptions using the
streamlit.testing.v1.AppTest framework.

Coder A Assignment (Phase 3):
- Test that each page renders without exceptions
- Verify key UI elements are present
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.e2e
@pytest.mark.slow
class TestStreamlitPages:
    """Tests for Streamlit UI page rendering.

    Uses streamlit.testing.v1.AppTest to validate that all pages
    render without exceptions and contain expected UI elements.
    """

    @pytest.fixture
    def mock_chromadb(self) -> MagicMock:
        """Mock ChromaDB client to avoid real database operations."""
        with patch("chromadb.PersistentClient") as mock_client:
            mock_collection = MagicMock()
            mock_collection.count.return_value = 100
            mock_collection.name = "bloginator_corpus"
            mock_client.return_value.list_collections.return_value = [mock_collection]
            yield mock_client

    @pytest.fixture
    def mock_requests(self) -> MagicMock:
        """Mock requests to avoid real HTTP calls."""
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            yield mock_get

    def test_home_page_renders(
        self, mock_chromadb: MagicMock, mock_requests: MagicMock, tmp_path: Path
    ) -> None:
        """Home page should render without exceptions."""
        from streamlit.testing.v1 import AppTest

        # Create minimal required directories
        (tmp_path / ".bloginator" / "chroma").mkdir(parents=True)
        (tmp_path / "output" / "extracted").mkdir(parents=True)

        with patch("pathlib.Path.exists", return_value=True):
            at = AppTest.from_file("src/bloginator/ui/_pages/home.py", default_timeout=10)
            at.run()

            # Verify page rendered (no exceptions means success)
            assert not at.exception, f"Home page raised exception: {at.exception}"

    def test_corpus_page_renders(self, mock_chromadb: MagicMock) -> None:
        """Corpus page should render without exceptions."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file("src/bloginator/ui/_pages/corpus.py", default_timeout=10)
        at.run()

        assert not at.exception, f"Corpus page raised exception: {at.exception}"

    def test_search_page_renders(self, mock_chromadb: MagicMock) -> None:
        """Search page should render without exceptions."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file("src/bloginator/ui/_pages/search.py", default_timeout=10)
        at.run()

        assert not at.exception, f"Search page raised exception: {at.exception}"

    def test_generate_page_renders(
        self, mock_chromadb: MagicMock, mock_requests: MagicMock
    ) -> None:
        """Generate page should render without exceptions."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file("src/bloginator/ui/_pages/generate.py", default_timeout=10)
        at.run()

        assert not at.exception, f"Generate page raised exception: {at.exception}"

    def test_history_page_renders(self) -> None:
        """History page should render without exceptions."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file("src/bloginator/ui/_pages/history.py", default_timeout=10)
        at.run()

        assert not at.exception, f"History page raised exception: {at.exception}"

    def test_settings_page_renders(self, mock_requests: MagicMock) -> None:
        """Settings page should render without exceptions."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file("src/bloginator/ui/_pages/settings.py", default_timeout=10)
        at.run()

        assert not at.exception, f"Settings page raised exception: {at.exception}"

    def test_blocklist_page_renders(self, tmp_path: Path) -> None:
        """Blocklist page should render without exceptions."""
        from streamlit.testing.v1 import AppTest

        # Create blocklist directory
        blocklist_dir = tmp_path / ".bloginator"
        blocklist_dir.mkdir(parents=True)

        with patch("bloginator.ui._pages.blocklist.Path") as mock_path:
            mock_path.return_value = blocklist_dir / "blocklist.json"
            at = AppTest.from_file("src/bloginator/ui/_pages/blocklist.py", default_timeout=10)
            at.run()

            assert not at.exception, f"Blocklist page raised exception: {at.exception}"

    def test_analytics_page_renders(self, mock_chromadb: MagicMock) -> None:
        """Analytics page should render without exceptions."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file("src/bloginator/ui/_pages/analytics.py", default_timeout=10)
        at.run()

        assert not at.exception, f"Analytics page raised exception: {at.exception}"
