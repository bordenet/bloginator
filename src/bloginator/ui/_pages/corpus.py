"""Corpus management page for Bloginator Streamlit UI."""

import streamlit as st

from bloginator.ui._pages._corpus_extraction import show_extraction_tab
from bloginator.ui._pages._corpus_indexing import show_indexing_tab
from bloginator.ui._pages._corpus_status import show_status_tab


def show():
    """Display the corpus management page."""
    st.header("📁 Corpus Management")

    st.markdown(
        """
        Manage your document corpus: extract text from source files and build the searchable index.
        """
    )

    # Tabs for different corpus operations
    tab1, tab2, tab3 = st.tabs(["Extract", "Index", "Status"])

    with tab1:
        show_extraction_tab()

    with tab2:
        show_indexing_tab()

    with tab3:
        show_status_tab()
