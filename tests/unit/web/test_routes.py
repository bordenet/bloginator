"""Tests for web UI routes - skipped by design (optional FastAPI dependency).

These tests are designed to run only when FastAPI is installed via:
    pip install bloginator[web]

The conditional skip mechanism properly handles missing optional dependencies,
so no action is needed to "enable" these tests.
"""

import pytest


try:
    from fastapi.testclient import TestClient

    from bloginator.web.app import create_app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not FASTAPI_AVAILABLE, reason="fastapi not installed (requires: pip install bloginator[web])"
)


class TestMainRoutes:
    """Tests for main UI routes."""

    @pytest.fixture
    def client(self):
        """Create test client."""
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
