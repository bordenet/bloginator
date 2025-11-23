"""Generation history page for Bloginator Streamlit UI."""

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from bloginator.export.factory import ExportFormat, create_exporter
from bloginator.models.draft import Draft
from bloginator.models.history import GenerationType
from bloginator.models.outline import Outline
from bloginator.services.history_manager import HistoryManager


def show():
    """Display the generation history page."""
    st.header("📜 Generation History")

    st.markdown(
        """
        View and manage your generation history. Track all outlines and drafts you've created,
        filter by classification or audience, and re-export in different formats.
        """
    )

    # Initialize history manager
    history_manager = HistoryManager()
    history = history_manager.load_history()

    if not history.entries:
        st.info(
            """
            📝 **No generation history yet**

            Generate your first outline or draft to start building history.
            History is automatically tracked when you save generations.
            """
        )
        return

    # Summary metrics
    st.subheader("Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Generations", len(history.entries))

    with col2:
        outlines = len(history.filter_by_type(GenerationType.OUTLINE))
        st.metric("Outlines", outlines)

    with col3:
        drafts = len(history.filter_by_type(GenerationType.DRAFT))
        st.metric("Drafts", drafts)

    with col4:
        # Most recent generation
        recent = history.get_recent(1)
        if recent:
            hours_ago = (datetime.now() - recent[0].timestamp).total_seconds() / 3600
            if hours_ago < 1:
                time_str = f"{int(hours_ago * 60)}m ago"
            elif hours_ago < 24:
                time_str = f"{int(hours_ago)}h ago"
            else:
                time_str = f"{int(hours_ago / 24)}d ago"
            st.metric("Last Generation", time_str)

    st.markdown("---")

    # Filters
    st.subheader("Filters")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        type_filter = st.selectbox(
            "Type",
            options=["All", "Outline", "Draft"],
            index=0,
        )

    with col2:
        # Get unique classifications
        classifications = sorted({e.classification for e in history.entries})
        classification_filter = st.selectbox(
            "Classification",
            options=["All"] + classifications,
            index=0,
        )

    with col3:
        # Get unique audiences
        audiences = sorted({e.audience for e in history.entries})
        audience_filter = st.selectbox(
            "Audience",
            options=["All"] + audiences,
            index=0,
        )

    with col4:
        limit = st.number_input(
            "Limit",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
        )

    # Query with filters
    filtered_entries = history.entries

    if type_filter != "All":
        filtered_entries = [e for e in filtered_entries if e.generation_type == type_filter.lower()]

    if classification_filter != "All":
        filtered_entries = [
            e for e in filtered_entries if e.classification == classification_filter
        ]

    if audience_filter != "All":
        filtered_entries = [e for e in filtered_entries if e.audience == audience_filter]

    # Sort by timestamp (newest first)
    filtered_entries = sorted(filtered_entries, key=lambda e: e.timestamp, reverse=True)
    filtered_entries = filtered_entries[:limit]

    # Display results
    st.markdown("---")
    st.subheader(f"History Entries ({len(filtered_entries)})")

    if not filtered_entries:
        st.warning("No entries match your filters")
        return

    # Display entries as cards
    for entry in filtered_entries:
        with st.expander(
            f"{'📝' if entry.generation_type == 'outline' else '📄'} {entry.title} - {entry.timestamp.strftime('%Y-%m-%d %H:%M')}",
            expanded=False,
        ):
            # Entry details
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown(f"**Type:** {entry.generation_type.upper()}")
                st.markdown(f"**Classification:** {entry.classification.replace('-', ' ').title()}")
                st.markdown(f"**Audience:** {entry.audience.replace('-', ' ').title()}")
                st.markdown(f"**Format:** {entry.output_format}")

            with col2:
                st.markdown(f"**ID:** `{entry.id[:8]}`")
                st.markdown(f"**Created:** {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**Output:** `{Path(entry.output_path).name}`")

            # Input parameters
            if entry.input_params:
                st.markdown("**Input Parameters:**")
                for key, value in entry.input_params.items():
                    if isinstance(value, list):
                        st.markdown(f"- {key}: {', '.join(str(v) for v in value)}")
                    else:
                        st.markdown(f"- {key}: {value}")

            # Metadata
            if entry.metadata:
                st.markdown("**Metadata:**")
                for key, value in entry.metadata.items():
                    st.markdown(f"- {key}: {value}")

            # Action buttons
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                # View file button
                file_path = Path(entry.output_path)
                if file_path.exists() and st.button("📖 View", key=f"view_{entry.id}"):
                    _show_file_content(file_path, entry.generation_type)

            with col2:
                # Re-export button
                if file_path.exists() and st.button("📥 Re-export", key=f"export_{entry.id}"):
                    st.session_state[f"export_entry_{entry.id}"] = True

                # Export dialog
                if st.session_state.get(f"export_entry_{entry.id}", False):
                    _show_export_dialog(entry, file_path)

            with col3:
                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{entry.id}", type="secondary"):
                    if history_manager.delete_entry(entry.id):
                        st.success(f"Deleted entry: {entry.title}")
                        st.rerun()
                    else:
                        st.error("Failed to delete entry")


def _show_file_content(file_path: Path, generation_type: str):
    """Show file content in a modal-like view.

    Args:
        file_path: Path to file to display
        generation_type: Type of generation (outline/draft)
    """
    st.markdown("### File Content")

    # Determine file type and load appropriately
    if file_path.suffix == ".json":
        try:
            content = json.loads(file_path.read_text())
            st.json(content)
        except Exception as e:
            st.error(f"Failed to load JSON: {e}")
    elif file_path.suffix == ".md":
        try:
            content = file_path.read_text()
            st.markdown(content)
        except Exception as e:
            st.error(f"Failed to load markdown: {e}")
    else:
        try:
            content = file_path.read_text()
            st.text(content)
        except Exception as e:
            st.error(f"Failed to load file: {e}")


def _show_export_dialog(entry, file_path: Path):
    """Show export dialog for re-exporting a generation.

    Args:
        entry: History entry
        file_path: Path to generation file
    """
    st.markdown("#### Export Options")

    format_choice = st.selectbox(
        "Format",
        options=["PDF", "Word (DOCX)", "HTML", "Markdown", "Plain Text"],
        key=f"format_{entry.id}",
    )

    format_map = {
        "PDF": ExportFormat.PDF,
        "Word (DOCX)": ExportFormat.DOCX,
        "HTML": ExportFormat.HTML,
        "Markdown": ExportFormat.MARKDOWN,
        "Plain Text": ExportFormat.TEXT,
    }

    if st.button("Export", key=f"do_export_{entry.id}", type="primary"):
        try:
            # Load document
            json_path = file_path.with_suffix(".json")
            if not json_path.exists():
                st.error("JSON file not found. Cannot re-export.")
                return

            data = json.loads(json_path.read_text())

            document = Outline(**data) if entry.generation_type == "outline" else Draft(**data)

            # Create exporter
            exporter = create_exporter(format_map[format_choice])

            # Generate output path
            output_path = (
                json_path.parent / f"{json_path.stem}_export.{exporter.get_file_extension()}"
            )

            # Export
            exporter.export(document, output_path)

            # Provide download
            with output_path.open("rb") as f:
                file_data = f.read()
                st.download_button(
                    label=f"⬇️ Download {format_choice}",
                    data=file_data,
                    file_name=output_path.name,
                    mime=_get_mime_type(format_map[format_choice]),
                    key=f"download_{entry.id}",
                )

            st.success(f"Exported to {output_path.name}")

        except Exception as e:
            st.error(f"Export failed: {str(e)}")


def _get_mime_type(format: ExportFormat) -> str:
    """Get MIME type for export format.

    Args:
        format: Export format

    Returns:
        MIME type string
    """
    mime_types = {
        ExportFormat.PDF: "application/pdf",
        ExportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ExportFormat.HTML: "text/html",
        ExportFormat.MARKDOWN: "text/markdown",
        ExportFormat.TEXT: "text/plain",
    }
    return mime_types.get(format, "application/octet-stream")
