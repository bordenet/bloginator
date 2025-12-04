"""Corpus indexing UI component."""

import shutil
import subprocess
from pathlib import Path

import streamlit as st
import yaml


def show_indexing_tab() -> None:
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
            _prune_index()

    with col2:
        st.markdown("**Delete entire index**")
        st.markdown(
            """
            Remove all indexed documents and rebuild from scratch.
            Your corpus sources remain intact.
            """
        )

        if st.button("🗑️ Delete Index", type="secondary", use_container_width=True):
            _delete_index()

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

    # Force re-index option
    force_reindex = st.checkbox(
        "Force Re-index",
        value=False,
        key="index_force_reindex",
        help="Delete existing index and rebuild from scratch",
    )

    # Run indexing
    if st.button("🔨 Build Index", type="primary", use_container_width=True):
        _run_indexing(extracted_dir, index_dir, chunk_size, force_reindex)


def _prune_index() -> None:
    """Prune orphaned documents from index."""
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


def _delete_index() -> None:
    """Delete entire index."""
    try:
        index_dir = Path(".bloginator/chroma")
        if index_dir.exists():
            shutil.rmtree(index_dir)
            st.success("✓ Index deleted. You can now rebuild it with the Build Index button below.")
        else:
            st.info("No index found to delete")
    except Exception as e:
        st.error(f"Failed to delete index: {e}")


def _run_indexing(
    extracted_dir: Path, index_dir: str, chunk_size: int, force_reindex: bool
) -> None:
    """Run indexing process with real-time output.

    Args:
        extracted_dir: Directory containing extracted documents
        index_dir: Output directory for index
        chunk_size: Maximum characters per chunk
        force_reindex: Whether to force re-index
    """
    # Create placeholders for real-time progress
    current_doc_container = st.empty()
    skipped_docs_container = st.empty()
    status_container = st.empty()

    try:
        # If force re-index, purge existing index first
        if force_reindex:
            index_path = Path(index_dir)
            if index_path.exists():
                shutil.rmtree(index_path)
                st.info(f"🗑️ Purged existing index: {index_dir}")

        cmd = [
            "bloginator",
            "index",
            str(extracted_dir),
            "-o",
            index_dir,
            "--chunk-size",
            str(chunk_size),
        ]

        # Run with real-time output streaming
        # nosec B603 - subprocess without shell=True is safe, cmd is controlled
        process = subprocess.Popen(  # nosec B603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )

        stdout_lines = []
        stderr_lines = []
        skipped_docs = []  # Track skipped documents
        current_doc = "Starting..."

        # Read output line by line as it comes
        while True:
            # Check if process is still running
            if process.poll() is not None:
                break

            # Read available output
            line = process.stdout.readline()
            if line:
                stdout_lines.append(line)

                # Parse line to detect skip events or current document
                stripped = line.strip()
                if stripped.startswith("[SKIP]"):
                    # Parse skip event: [SKIP] /path/to/doc (reason)
                    skip_info = stripped[6:].strip()  # Remove "[SKIP] " prefix
                    skipped_docs.append(f"• {skip_info}")
                    # Update skipped documents display
                    skipped_docs_container.text_area(
                        "Skipped Documents",
                        value="\n".join(skipped_docs),
                        height=300,
                        key="indexing_skipped_docs",
                        disabled=True,
                    )
                elif stripped.startswith("Indexing:"):
                    # Parse current document: "Indexing: /path/to/file"
                    current_doc = stripped[9:].strip()  # Remove "Indexing: " prefix
                    # Update current document display
                    current_doc_container.info(f"🔨 Current: {current_doc}")

        # Get remaining output
        stdout_remaining, stderr_remaining = process.communicate()
        if stdout_remaining:
            stdout_lines.extend(stdout_remaining.splitlines(keepends=True))
        if stderr_remaining:
            stderr_lines.extend(stderr_remaining.splitlines(keepends=True))

        # Clear current document indicator
        current_doc_container.empty()

        if process.returncode == 0:
            status_container.success("✓ Index built successfully!")

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

            # Show final skip count
            if skipped_docs:
                st.info(f"📋 {len(skipped_docs)} document(s) skipped (see list above)")
        else:
            status_container.error(f"✗ Indexing failed (exit code {process.returncode})")
            if stderr_lines:
                st.code("".join(stderr_lines), language="text")

    except Exception as e:
        status_container.error(f"✗ Error: {str(e)}")
