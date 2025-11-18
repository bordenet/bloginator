"""Content generation page for Bloginator Streamlit UI.

This module has been refactored into smaller focused components.
This file serves as the main entry point, delegating to specialized modules.
"""

import streamlit as st

from bloginator.ui.pages.generate_draft_ui import show_draft_generation
from bloginator.ui.pages.generate_outline_ui import show_outline_generation
from bloginator.ui.pages.generate_ui_utils import (
    check_index_exists,
    check_ollama_available,
)


def show() -> None:
    """Display the content generation page."""

    st.header("📝 Generate Content")

    st.markdown(
        """
        Generate blog outlines and drafts from your corpus in your authentic voice.
        """
    )

    # Check if index exists
    if not check_index_exists():
        st.warning(
            """
            ⚠️ **No index found!**

            Build an index first in the Corpus Management section.
            """
        )
        return

    # Check Ollama status
    ollama_available, error_msg = check_ollama_available()
    if not ollama_available:
        st.error(error_msg)
        return

    # Tabs for outline and draft generation
    tab1, tab2 = st.tabs(["Generate Outline", "Generate Draft"])

    with tab1:
        show_outline_generation()

    with tab2:
        show_draft_generation()
