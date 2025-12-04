"""Corpus extraction UI component."""

from pathlib import Path
from uuid import uuid4

import streamlit as st
import yaml

from bloginator.corpus_config import CorpusConfigManager
from bloginator.ui._pages._corpus_extraction_engine import run_extraction


def show_extraction_tab() -> None:
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
        _add_new_source(
            corpus_config,
            config,
            new_source_name,
            new_source_path,
            new_source_quality,
            new_source_enabled,
            new_source_tags,
            new_source_notes,
        )

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
        run_extraction(corpus_config, output_dir, force_extract)


def _add_new_source(
    corpus_config: Path,
    config: dict,
    name: str,
    path: str,
    quality: str,
    enabled: bool,
    tags_str: str,
    notes: str,
) -> None:
    """Add new source to corpus configuration.

    Args:
        corpus_config: Path to corpus config file
        config: Loaded config dict
        name: Source name
        path: Source path
        quality: Quality rating
        enabled: Whether source is enabled
        tags_str: Comma-separated tags
        notes: Voice notes
    """
    if not name or not path:
        st.warning("Please provide both source name and path")
        return

    # Check for exact duplicate path (case-sensitive string match only)
    existing_paths = [source.get("path", "") for source in config.get("sources", [])]
    if path in existing_paths:
        st.error(f"Source path already exists: {path}")
        return

    # Add to config (ensure sources is a list)
    if "sources" not in config or config["sources"] is None:
        config["sources"] = []

    # Parse tags
    tags_list = [t.strip() for t in tags_str.split(",") if t.strip()]

    # Create new source with unique ID
    new_source = {
        "id": str(uuid4()),
        "name": name,
        "path": path,
        "type": "directory",
        "enabled": enabled,
        "quality": quality,
        "tags": tags_list,
        "voice_notes": notes if notes else None,
    }

    config["sources"].append(new_source)

    # Save config using safe manager
    try:
        manager = CorpusConfigManager(corpus_config)
        manager.save_config(config)
        st.success(f"✓ Added source: {name}")
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
