"""Corpus management page for Bloginator Streamlit UI."""

import subprocess
from pathlib import Path

import streamlit as st
import yaml


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


def show_extraction_tab():
    """Show the extraction interface."""
    st.subheader("Extract Documents")

    st.markdown(
        """
        Extract text from your document corpus (PDF, DOCX, Markdown, TXT).
        Configure your corpus sources in `corpus/corpus.yaml`.
        """
    )

    # Check if corpus config exists
    corpus_config = Path("corpus/corpus.yaml")
    if not corpus_config.exists():
        st.warning(
            """
            ⚠️ **No corpus configuration found!**

            Create `corpus/corpus.yaml` based on `corpus.yaml.example` to define your document sources.
            """
        )

        if st.button("Create Example Config"):
            example_config = Path("corpus.yaml.example")
            if example_config.exists():
                corpus_config.write_text(example_config.read_text())
                st.success("✓ Created corpus/corpus.yaml from example")
                st.rerun()
            else:
                st.error("Example config not found")

        return

    # Load and display corpus config
    with corpus_config.open() as f:
        config = yaml.safe_load(f)

    st.success(f"✓ Loaded configuration from {corpus_config}")

    # Display configured sources
    if "sources" in config:
        st.subheader(f"Configured Sources ({len(config['sources'])})")

        for idx, source in enumerate(config["sources"]):
            with st.expander(f"📂 {source.get('name', f'Source {idx+1}')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.text(f"Path: {source.get('path', 'N/A')}")
                    st.text(f"Quality: {source.get('quality', 'standard')}")
                with col2:
                    enabled = source.get("enabled", True)
                    st.text(f"Enabled: {'✓' if enabled else '✗'}")
                    tags = source.get("tags", [])
                    if tags:
                        st.text(f"Tags: {', '.join(tags)}")

                voice_notes = source.get("voice_notes", "")
                if voice_notes:
                    st.caption(f"Notes: {voice_notes}")

    st.markdown("---")

    # Extraction options
    st.subheader("Extraction Options")

    col1, col2 = st.columns(2)

    with col1:
        output_dir = st.text_input(
            "Output Directory",
            value="output/extracted",
            key="extract_output_dir",
            help="Where to save extracted files",
        )

    with col2:
        force_extract = st.checkbox(
            "Force Re-extraction",
            value=False,
            key="extract_force_reextraction",
            help="Re-extract all files, even if already extracted",
        )

    # Run extraction
    if st.button("🚀 Run Extraction", type="primary", use_container_width=True):
        with st.spinner("Extracting documents..."):
            try:
                cmd = [
                    "bloginator",
                    "extract",
                    "-o",
                    output_dir,
                    "--config",
                    str(corpus_config),
                ]

                if force_extract:
                    cmd.append("--force")

                # nosec B603 - subprocess without shell=True is safe, cmd is controlled
                result = subprocess.run(  # nosec B603
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

                if result.returncode == 0:
                    st.success("✓ Extraction complete!")
                    st.code(result.stdout, language="text")

                    # Count extracted files
                    extracted_dir = Path(output_dir)
                    if extracted_dir.exists():
                        json_count = len(list(extracted_dir.glob("*.json")))
                        txt_count = len(list(extracted_dir.glob("*.txt")))
                        st.metric("Extracted Files", f"{json_count} documents")
                        st.caption(f"{txt_count} text files, {json_count} metadata files")
                else:
                    st.error(f"✗ Extraction failed (exit code {result.returncode})")
                    st.code(result.stderr, language="text")

            except subprocess.TimeoutExpired:
                st.error("✗ Extraction timed out (>5 minutes)")
            except Exception as e:
                st.error(f"✗ Error: {str(e)}")


def show_indexing_tab():
    """Show the indexing interface."""
    st.subheader("Build Search Index")

    st.markdown(
        """
        Build a semantic search index from your extracted documents.
        This creates vector embeddings and stores them in ChromaDB.
        """
    )

    # Check if extracted files exist
    extracted_dir = Path("output/extracted")
    if not extracted_dir.exists() or not any(extracted_dir.glob("*.json")):
        st.warning(
            """
            ⚠️ **No extracted files found!**

            Extract your corpus first in the "Extract" tab.
            """
        )
        return

    # Show extracted file count
    json_count = len(list(extracted_dir.glob("*.json")))
    st.success(f"✓ Found {json_count} extracted files ready for indexing")

    st.markdown("---")

    # Indexing options
    st.subheader("Index Options")

    col1, col2 = st.columns(2)

    with col1:
        index_dir = st.text_input(
            "Index Directory",
            value=".bloginator/chroma",
            key="index_output_dir",
            help="Where to store the index",
        )

    with col2:
        chunk_size = st.number_input(
            "Chunk Size",
            min_value=100,
            max_value=5000,
            value=1000,
            step=100,
            help="Maximum characters per chunk",
        )

    # Run indexing
    if st.button("🔨 Build Index", type="primary", use_container_width=True):
        with st.spinner("Building index... This may take a few minutes."):
            try:
                cmd = [
                    "bloginator",
                    "index",
                    str(extracted_dir),
                    "-o",
                    index_dir,
                    "--chunk-size",
                    str(chunk_size),
                ]

                # nosec B603 - subprocess without shell=True is safe, cmd is controlled
                result = subprocess.run(  # nosec B603
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800,  # 30 minute timeout
                )

                if result.returncode == 0:
                    st.success("✓ Index built successfully!")
                    st.code(result.stdout, language="text")

                    # Show index stats
                    index_path = Path(index_dir)
                    if index_path.exists():
                        try:
                            import chromadb

                            client = chromadb.PersistentClient(path=index_dir)
                            collections = client.list_collections()
                            if collections:
                                collection = collections[0]
                                chunk_count = collection.count()
                                st.metric("Indexed Chunks", f"{chunk_count:,}")
                        except Exception as e:
                            st.warning(f"Could not read index stats: {e}")
                else:
                    st.error(f"✗ Indexing failed (exit code {result.returncode})")
                    st.code(result.stderr, language="text")

            except subprocess.TimeoutExpired:
                st.error("✗ Indexing timed out (>30 minutes)")
            except Exception as e:
                st.error(f"✗ Error: {str(e)}")


def show_status_tab():
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
                        import json

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
