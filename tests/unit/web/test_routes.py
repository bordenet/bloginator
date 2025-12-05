"""Tests for web UI routes - skipped by design (optional FastAPI dependency).

These tests are designed to run only when FastAPI and python-multipart are installed via:
    pip install bloginator[web-api]

The conditional skip mechanism properly handles missing optional dependencies,
so no action is needed to "enable" these tests.
"""

import pytest


def _check_web_api_dependencies() -> bool:
    """Check if all web-api dependencies are available."""
    try:
        from fastapi.testclient import TestClient  # noqa: F401

        # python-multipart is required for Form/File uploads
        from python_multipart import __version__  # noqa: F401

        from bloginator.web.app import create_app  # noqa: F401

        return True
    except ImportError:
        return False


WEB_API_AVAILABLE = _check_web_api_dependencies()

pytestmark = pytest.mark.skipif(
    not WEB_API_AVAILABLE,
    reason="web-api dependencies not installed (requires: pip install bloginator[web-api])",
)


class TestMainRoutes:
    """Tests for main UI routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from bloginator.web.app import create_app

        app = create_app()
        return TestClient(app)

    def test_index_page(self, client):
        """Test home page loads."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Bloginator" in response.text

    def test_corpus_page(self, client):
        """Test corpus management page loads."""
        response = client.get("/corpus")
        assert response.status_code == 200
        assert "Corpus Management" in response.text

    def test_create_page(self, client):
        """Test document creation page loads."""
        response = client.get("/create")
        assert response.status_code == 200
        assert "Create Document" in response.text

    def test_search_page(self, client):
        """Test search page loads."""
        response = client.get("/search")
        assert response.status_code == 200
        assert "Search Corpus" in response.text

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_api_docs(self, client):
        """Test API documentation is accessible."""
        response = client.get("/api/docs")
        assert response.status_code == 200
