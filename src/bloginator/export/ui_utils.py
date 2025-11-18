"""Streamlit UI utilities for export functionality."""

import json
from pathlib import Path

import streamlit as st

from bloginator.export.factory import ExportFormat, create_exporter
from bloginator.models.draft import Draft
from bloginator.models.outline import Outline


def show_export_buttons(document_path: Path, document_type: str = "draft") -> None:
    """Display export buttons for a document.

    Args:
        document_path: Path to the document JSON file
        document_type: Type of document ("draft" or "outline")
    """
    if not document_path.exists():
        return

    st.markdown("---")
    st.subheader("📥 Export")

    # Format selection
    col1, col2 = st.columns([2, 1])

    with col1:
        export_format = st.selectbox(
            "Export Format",
            options=["PDF", "Word (DOCX)", "HTML", "Markdown", "Plain Text"],
            help="Select the format for export",
        )

    # Map display name to ExportFormat
    format_map = {
        "PDF": ExportFormat.PDF,
        "Word (DOCX)": ExportFormat.DOCX,
        "HTML": ExportFormat.HTML,
        "Markdown": ExportFormat.MARKDOWN,
        "Plain Text": ExportFormat.TEXT,
    }

    selected_format = format_map[export_format]

    with col2:
        if st.button("📥 Export", type="primary", use_container_width=True):
            try:
                # Load document
                document = _load_document(document_path, document_type)

                # Create exporter
                exporter = create_exporter(selected_format)

                # Generate output path
                output_path = (
                    document_path.parent
                    / f"{document_path.stem}_export.{exporter.get_file_extension()}"
                )

                # Export
                exporter.export(document, output_path)

                # Success message with download button
                st.success(f"✓ Exported to {output_path.name}")

                # Provide download button
                with output_path.open("rb") as f:
                    file_data = f.read()
                    st.download_button(
                        label=f"⬇️ Download {export_format}",
                        data=file_data,
                        file_name=output_path.name,
                        mime=_get_mime_type(selected_format),
                        use_container_width=True,
                    )

            except Exception as e:
                st.error(f"Export failed: {str(e)}")


def _load_document(document_path: Path, document_type: str) -> Draft | Outline:
    """Load document from JSON file.

    Args:
        document_path: Path to JSON file
        document_type: Type of document ("draft" or "outline")

    Returns:
        Draft or Outline instance
    """
    data = json.loads(document_path.read_text())

    if document_type == "draft":
        return Draft(**data)
    else:
        return Outline(**data)


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
