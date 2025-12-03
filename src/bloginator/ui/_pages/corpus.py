"""Corpus management page for Bloginator Streamlit UI."""

import subprocess
from pathlib import Path

import streamlit as st
import yaml

from bloginator.corpus_config import CorpusConfigManager


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
    sample_config = Path("corpus/corpus.sample.yaml")
    if not corpus_config.exists():
        st.warning(
            """
            ⚠️ **No corpus configuration found!**

            Create `corpus/corpus.yaml` based on `corpus/corpus.sample.yaml` to define your document sources.

            **Note:** `corpus/corpus.yaml` is gitignored to protect your local paths.
            """
        )

        if st.button("Create Config from Sample"):
            if sample_config.exists():
                corpus_config.write_text(sample_config.read_text())
                st.success("✓ Created corpus/corpus.yaml from sample")
                st.rerun()
            else:
                st.error("Sample config not found at corpus/corpus.sample.yaml")

        return

    # Load and display corpus config
    with corpus_config.open() as f:
        config = yaml.safe_load(f)

    st.success(f"✓ Loaded configuration from {corpus_config}")

    # Ensure sources is a list (handle case where YAML has "sources:" with no items)
    if config.get("sources") is None:
        config["sources"] = []

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
                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "✏️ Edit",
                        key=f"edit_source_{idx}",
                        use_container_width=True,
                        disabled=True,
                        help="Edit functionality coming soon",
                    ):
                        pass

                with col2:
                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_source_{idx}",
                        use_container_width=True,
                    ):
                        # Safe deletion using CorpusConfigManager
                        source_id = source.get("id", "")
                        source_name = source.get("name", "")

                        try:
                            manager = CorpusConfigManager(corpus_config)
                            success = manager.delete_source_by_id(source_id)

                            if success:
                                st.success(f"✓ Deleted source: {source_name}")
                                st.info(f"Backup saved to: {manager.backup_dir}")
                                st.rerun()
                            else:
                                st.error(f"Source not found: {source_id}")
                        except Exception as e:
                            st.error(f"Failed to delete source: {e}")

    # Add new source section
    st.markdown("---")
    st.subheader("Add New Source")

    col1, col2 = st.columns(2)

    with col1:
        new_source_name = st.text_input(
            "Source Name",
            key="add_source_name",
            placeholder="e.g., My Blog Posts",
            help="Unique identifier for this source",
        )

    with col2:
        new_source_path = st.text_input(
            "Source Path",
            key="add_source_path",
            placeholder="e.g., /path/to/documents",
            help="Local path or URL to documents",
        )

    # Path helper
    st.markdown("**Quick path helper:**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏠 Home", key="path_home", use_container_width=True):
            st.session_state["add_source_path"] = str(Path.home())
            st.rerun()

    with col2:
        if st.button("📂 Current Dir", key="path_cwd", use_container_width=True):
            st.session_state["add_source_path"] = str(Path.cwd())
            st.rerun()

    with col3:
        if st.button("📁 Desktop", key="path_desktop", use_container_width=True):
            desktop = Path.home() / "Desktop"
            if desktop.exists():
                st.session_state["add_source_path"] = str(desktop)
                st.rerun()
            else:
                st.warning("Desktop folder not found")

    col1, col2, col3 = st.columns(3)

    with col1:
        new_source_quality = st.selectbox(
            "Quality Rating",
            options=["reference", "draft", "archive"],
            key="add_source_quality",
            help="Document quality level",
        )

    with col2:
        new_source_enabled = st.checkbox(
            "Enabled",
            value=True,
            key="add_source_enabled",
            help="Process this source during extraction",
        )

    with col3:
        new_source_tags = st.text_input(
            "Tags (comma-separated)",
            key="add_source_tags",
            placeholder="e.g., blog, published",
            help="Optional tags for filtering",
        )

    new_source_notes = st.text_area(
        "Voice Notes",
        key="add_source_notes",
        placeholder="Style, tone, or other notes about this source...",
        help="Notes about the writing voice or style",
        height=80,
    )

    # Add source button
    if st.button("➕ Add Source", type="primary", use_container_width=True):
        if not new_source_name or not new_source_path:
            st.warning("Please provide both source name and path")
        else:
            # Check for exact duplicate path (case-sensitive string match only)
            existing_paths = [source.get("path", "") for source in config.get("sources", [])]
            if new_source_path in existing_paths:
                st.error(f"Source path already exists: {new_source_path}")
            else:
                # Add to config (ensure sources is a list)
                if "sources" not in config or config["sources"] is None:
                    config["sources"] = []

                # Parse tags
                tags_list = [t.strip() for t in new_source_tags.split(",") if t.strip()]

                # Create new source with unique ID
                from uuid import uuid4

                new_source = {
                    "id": str(uuid4()),
                    "name": new_source_name,
                    "path": new_source_path,
                    "type": "directory",
                    "enabled": new_source_enabled,
                    "quality": new_source_quality,
                    "tags": tags_list,
                    "voice_notes": new_source_notes if new_source_notes else None,
                }

                config["sources"].append(new_source)

                # Save config using safe manager
                try:
                    manager = CorpusConfigManager(corpus_config)
                    manager.save_config(config)
                    st.success(f"✓ Added source: {new_source_name}")
                    # Clear form fields to prevent duplicate submissions
                    for key in [
                        "add_source_name",
                        "add_source_path",
                        "add_source_tags",
                        "add_source_notes",
                    ]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save configuration: {e}")

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

    # Index management section
    st.markdown("---")
    st.subheader("Index Management")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Prune orphaned documents**")
        st.markdown(
            """
            Remove indexed documents from sources that no longer exist in corpus.yaml.
            """
        )

        if st.button("🧹 Prune Index", type="primary", use_container_width=True):
            try:
                import chromadb

                index_dir = Path(".bloginator/chroma")
                client = chromadb.PersistentClient(path=str(index_dir))
                collections = client.list_collections()

                if not collections:
                    st.warning("No index collections found")
                else:
                    collection = collections[0]

                    # Load corpus config to get configured sources
                    corpus_config = Path("corpus/corpus.yaml")
                    if corpus_config.exists():
                        with corpus_config.open() as f:
                            config = yaml.safe_load(f)
                        configured_paths = {
                            str(source.get("path", "")) for source in config.get("sources", [])
                        }
                    else:
                        configured_paths = set()

                    # Get all documents in index
                    all_docs = collection.get()
                    docs_to_delete = []

                    if all_docs["metadatas"]:
                        for i, metadata in enumerate(all_docs["metadatas"]):
                            source_path = metadata.get("source_path", "")
                            # If document's source path is not in configured sources, mark for deletion
                            if source_path and source_path not in configured_paths:
                                docs_to_delete.append(all_docs["ids"][i])

                    if docs_to_delete:
                        # Delete documents from index
                        collection.delete(ids=docs_to_delete)
                        st.success(f"✓ Pruned {len(docs_to_delete)} documents from index")
                    else:
                        st.info("✓ Index is clean - all documents are from configured sources")

            except ImportError:
                st.error("ChromaDB not installed")
            except Exception as e:
                st.error(f"Error pruning index: {e}")

    with col2:
        st.markdown("**Delete entire index**")
        st.markdown(
            """
            Remove all indexed documents and rebuild from scratch.
            Your corpus sources remain intact.
            """
        )

        if st.button("🗑️ Delete Index", type="secondary", use_container_width=True):
            try:
                import shutil

                index_dir = Path(".bloginator/chroma")
                if index_dir.exists():
                    shutil.rmtree(index_dir)
                    st.success(
                        "✓ Index deleted. You can now rebuild it with the Build Index button above."
                    )
                else:
                    st.info("No index found to delete")
            except Exception as e:
                st.error(f"Failed to delete index: {e}")

    st.markdown("---")

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
