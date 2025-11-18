"""
Bloginator Streamlit Web UI

Main entry point for the Streamlit web interface.
Provides interactive access to all Bloginator functionality.
"""

import sys
from pathlib import Path

import streamlit as st


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Page configuration
st.set_page_config(
    page_title="Bloginator",
    page_icon="✍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E88E5;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #856404;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        padding: 1rem;
        color: #721c24;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Main header
st.markdown('<div class="main-header">✍️ Bloginator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">AI-Assisted Content Generation from Your Own Corpus</div>',
    unsafe_allow_html=True,
)

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.markdown("---")

pages = {
    "🏠 Home": "home",
    "📁 Corpus Management": "corpus",
    "🔍 Search Corpus": "search",
    "📝 Generate Content": "generate",
    "📊 Analytics": "analytics",
    "⚙️ Settings": "settings",
}

# Page selection
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

for page_name, page_id in pages.items():
    if st.sidebar.button(page_name, key=f"nav_{page_id}", use_container_width=True):
        st.session_state.current_page = page_id

st.sidebar.markdown("---")

# Display corpus status in sidebar
st.sidebar.subheader("Corpus Status")

# Check if index exists
index_dir = Path(".bloginator/chroma")
if index_dir.exists():
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(index_dir))
        collections = client.list_collections()
        if collections:
            collection = collections[0]
            chunk_count = collection.count()
            st.sidebar.success("✓ Index Ready")
            st.sidebar.metric("Indexed Chunks", f"{chunk_count:,}")
        else:
            st.sidebar.warning("⚠ Index Empty")
    except Exception as e:
        st.sidebar.error(f"✗ Index Error: {str(e)[:50]}")
else:
    st.sidebar.info("ℹ No Index Found")
    st.sidebar.caption("Extract and index your corpus first")

# Check extracted files
extracted_dir = Path("output/extracted")
if extracted_dir.exists():
    json_files = list(extracted_dir.glob("*.json"))
    st.sidebar.metric("Extracted Files", len(json_files))
else:
    st.sidebar.caption("No extracted files yet")

st.sidebar.markdown("---")
st.sidebar.caption("Bloginator v0.1.0")

# Main content area - route to appropriate page
current_page = st.session_state.current_page

if current_page == "home":
    from bloginator.ui.pages import home

    home.show()
elif current_page == "corpus":
    from bloginator.ui.pages import corpus

    corpus.show()
elif current_page == "search":
    from bloginator.ui.pages import search

    search.show()
elif current_page == "generate":
    from bloginator.ui.pages import generate

    generate.show()
elif current_page == "analytics":
    from bloginator.ui.pages import analytics

    analytics.show()
elif current_page == "settings":
    from bloginator.ui.pages import settings

    settings.show()
