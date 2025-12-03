"""Home page for Bloginator Streamlit UI."""

from pathlib import Path

import streamlit as st


def show():
    """Display the home page."""
    st.header("Welcome to Bloginator")

    st.markdown(
        """
        Bloginator is an AI-assisted content generation system that helps you create
        authentic, high-quality documents by leveraging your own historical writing corpus.

        ### 🚀 Quick Start Guide

        1. **Extract Your Corpus** - Process your historical documents (PDFs, DOCX, Markdown)
        2. **Index the Content** - Build a searchable semantic index
        3. **Search & Explore** - Find relevant passages from your past writing
        4. **Generate Content** - Create outlines and drafts in your authentic voice

        ### 📊 System Status
        """
    )

    # System status cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        index_dir = Path(".bloginator/chroma")
        if index_dir.exists():
            st.success("✓ Index Ready")
            try:
                import chromadb

                client = chromadb.PersistentClient(path=str(index_dir))
                collections = client.list_collections()
                if collections:
                    chunk_count = collections[0].count()
                    st.metric("Indexed Chunks", f"{chunk_count:,}")
            except Exception:
                st.warning("Index exists but unreadable")
        else:
            st.info("ℹ No Index")
            st.caption("Run extraction and indexing")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        extracted_dir = Path("output/extracted")
        if extracted_dir.exists():
            json_count = len(list(extracted_dir.glob("*.json")))
            if json_count > 0:
                st.success(f"✓ {json_count} Files Extracted")
            else:
                st.info("ℹ No Files")
        else:
            st.info("ℹ No Extractions")
            st.caption("Start with corpus extraction")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        # Check Ollama status
        try:
            import requests

            ollama_host = st.session_state.get("ollama_host", "http://localhost:11434")
            response = requests.get(f"{ollama_host}/api/tags", timeout=2)
            if response.status_code == 200:
                st.success("✓ LLM Ready")
                st.caption(ollama_host)
            else:
                st.warning("⚠ LLM Unreachable")
        except (requests.RequestException, OSError):
            st.warning("⚠ LLM Offline")
            st.caption("Start Ollama server")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Workflow visualization
    st.subheader("📋 Typical Workflow")

    st.markdown(
        """
        ```mermaid
        graph LR
            A[Your Documents] --> B[Extract Text]
            B --> C[Build Index]
            C --> D[Search Corpus]
            C --> E[Generate Outline]
            E --> F[Generate Draft]
            F --> G[Refine & Export]
        ```
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Key Features")
        st.markdown(
            """
            - **Voice Preservation**: Generated content matches your writing style
            - **Corpus Grounding**: All content sourced from your own documents
            - **Multi-Format Support**: PDF, DOCX, Markdown, plain text
            - **Semantic Search**: Find relevant content by meaning, not just keywords
            - **Quality Weighting**: Prefer your more recent, refined thinking
            - **Safety Checks**: Block proprietary terms from former employers
            """
        )

    with col2:
        st.subheader("📚 Getting Started")
        if st.button("🚀 Run End-to-End Demo", type="primary", use_container_width=True):
            st.info(
                """
                **To run the E2E demo:**

                Open a terminal and run:
                ```bash
                ./run-e2e.sh
                ```

                Or with verbose output:
                ```bash
                ./run-e2e.sh --verbose
                ```
                """
            )

        if st.button("📖 View Documentation", use_container_width=True):
            st.info("Documentation available at `docs/USER_GUIDE.md`")

        if st.button("⚙️ Configure Settings", use_container_width=True):
            st.session_state.current_page = "settings"
            st.rerun()

    st.markdown("---")

    # Recent activity (if any)
    st.subheader("📅 Recent Activity")

    generated_dir = Path("output/generated")
    if generated_dir.exists() and any(generated_dir.iterdir()):
        recent_files = sorted(
            generated_dir.glob("*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:5]

        if recent_files:
            st.markdown("**Recently Generated Files:**")
            for file_path in recent_files:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.text(file_path.name)
                with col2:
                    st.caption(f"{file_path.stat().st_size} bytes")
                with col3:
                    if st.button("View", key=f"view_{file_path.name}"):
                        st.code(file_path.read_text(), language="markdown")
        else:
            st.caption("No generated files yet. Create your first outline!")
    else:
        st.caption("No activity yet. Start by extracting and indexing your corpus.")

    st.markdown("---")
    st.caption("💡 Tip: Use the sidebar to navigate between different sections of the application.")
