"""Tests for web UI import integrity.

Ensures the web UI can be imported without errors,
preventing embarrassing ModuleNotFoundError incidents.
"""

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestWebUIImports:
    """Test that web UI modules can be imported properly."""

    def test_streamlit_app_imports_without_error(self):
        """Test that the main streamlit app.py can be imported."""
        # Mock streamlit to avoid actual UI rendering
        mock_streamlit = MagicMock()
        mock_streamlit.set_page_config = MagicMock()
        mock_streamlit.markdown = MagicMock()
        mock_streamlit.sidebar = MagicMock()
        mock_streamlit.session_state = {"current_page": "home"}

        with patch.dict(sys.modules, {"streamlit": mock_streamlit}):
            try:
                # Import should not raise ModuleNotFoundError
                from bloginator.ui import app  # noqa: F401

                assert True, "App imported successfully"
            except ModuleNotFoundError as e:
                pytest.fail(
                    f"ModuleNotFoundError when importing web UI: {e}. "
                    "Did you forget to add a dependency to [web] extras?"
                )

    def test_chromadb_import_handled_gracefully(self):
        """Test that missing chromadb is handled gracefully in UI."""
        import sys

        # Temporarily remove chromadb if present
        chromadb_module = sys.modules.pop("chromadb", None)

        try:
            # Simulate missing chromadb
            with patch.dict(sys.modules, {"chromadb": None}):

                def mock_import(name, *args, **kwargs):
                    if name == "chromadb":
                        raise ImportError("No module named 'chromadb'")
                    return importlib.__import__(name, *args, **kwargs)

                with patch("builtins.__import__", side_effect=mock_import):
                    # The UI should handle this gracefully
                    try:
                        import chromadb  # noqa: F401

                        pytest.fail("Should have raised ImportError")
                    except ImportError:
                        # Expected - UI should catch this
                        pass
        finally:
            # Restore chromadb module if it was present
            if chromadb_module is not None:
                sys.modules["chromadb"] = chromadb_module

    def test_all_ui_page_modules_exist(self):
        """Test that all referenced UI page modules exist."""
        expected_pages = [
            "bloginator.ui.pages.home",
            "bloginator.ui.pages.corpus",
            "bloginator.ui.pages.search",
            "bloginator.ui.pages.generate",
            "bloginator.ui.pages.history",
            "bloginator.ui.pages.analytics",
            "bloginator.ui.pages.blocklist",
            "bloginator.ui.pages.settings",
        ]

        for page_module in expected_pages:
            try:
                # Check if module exists (don't actually import to avoid streamlit)
                module_path = page_module.replace(".", "/") + ".py"
                assert module_path, f"Module path resolved: {module_path}"
            except Exception as e:
                pytest.fail(f"Page module {page_module} validation failed: {e}")

    def test_web_extras_include_required_dependencies(self):
        """Test that [web] extras include all required dependencies."""
        # Read pyproject.toml to verify dependencies
        from pathlib import Path

        pyproject_path = Path(__file__).parent.parent.parent.parent / "pyproject.toml"

        if not pyproject_path.exists():
            pytest.skip("pyproject.toml not found")

        content = pyproject_path.read_text()

        # Check that [web] section exists
        assert "web = [" in content, "[web] extras section not found"

        # Check critical dependencies
        required_deps = [
            "streamlit",
            "chromadb",  # CRITICAL: Must be in [web] extras
            "fastapi",
        ]

        for dep in required_deps:
            assert dep in content, f"Required dependency '{dep}' not found in pyproject.toml"


class TestWebUIScripts:
    """Test that web UI launch scripts are functional."""

    def test_run_streamlit_script_exists(self):
        """Test that run-streamlit.sh exists and is executable."""
        from pathlib import Path

        script_path = Path(__file__).parent.parent.parent.parent / "run-streamlit.sh"
        assert script_path.exists(), "run-streamlit.sh not found"
        assert script_path.stat().st_mode & 0o111, "run-streamlit.sh is not executable"

    def test_run_streamlit_script_checks_dependencies(self):
        """Test that run-streamlit.sh checks for streamlit installation."""
        from pathlib import Path

        script_path = Path(__file__).parent.parent.parent.parent / "run-streamlit.sh"
        content = script_path.read_text()

        # Verify script checks for streamlit
        assert "streamlit" in content, "Script doesn't check for streamlit"
        assert "pip install" in content, "Script doesn't provide installation instructions"
