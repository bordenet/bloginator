"""Corpus status UI component."""

import json
from pathlib import Path

import streamlit as st


def show_status_tab() -> None:
    """Show corpus status and statistics."""
    st.subheader("Corpus Status")

    # Check extracted files
    extracted_dir = Path("output/extracted")
    if extracted_dir.exists():
        json_files = list(extracted_dir.glob("*.json"))
        txt_files = list(extracted_dir.glob("*.txt"))

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Extracted Documents", len(json_files))

        with col2:
            st.metric("Text Files", len(txt_files))

        with col3:
            total_size = sum(f.stat().st_size for f in txt_files)
            st.metric("Total Size", f"{total_size / 1024 / 1024:.1f} MB")

        # Show recent extractions
        if json_files:
            st.subheader("Recent Extractions")
            recent_files = sorted(json_files, key=lambda p: p.stat().st_mtime, reverse=True)[:10]

            for json_file in recent_files:
                with st.expander(f"📄 {json_file.stem}"):
                    try:
                        metadata = json.loads(json_file.read_text())
                        st.json(metadata)
                    except (json.JSONDecodeError, FileNotFoundError, OSError):
                        st.error("Could not read metadata")
    else:
        st.info("No extracted files yet")

    st.markdown("---")

    # Check index
    index_dir = Path(".bloginator/chroma")
    if index_dir.exists():
        st.success("✓ Index exists")

        try:
            import chromadb

            client = chromadb.PersistentClient(path=str(index_dir))
            collections = client.list_collections()

            if collections:
                collection = collections[0]
                chunk_count = collection.count()

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Collection Name", collection.name)
                with col2:
                    st.metric("Chunk Count", f"{chunk_count:,}")

                st.subheader("Index Details")
                st.text(f"Path: {index_dir}")
                st.text(
                    f"Size: {sum(f.stat().st_size for f in index_dir.rglob('*') if f.is_file()) / 1024 / 1024:.1f} MB"
                )
            else:
                st.warning("Index directory exists but no collections found")

        except Exception as e:
            st.error(f"Error reading index: {e}")
    else:
        st.info("No index built yet")
