"""Draft generation UI component for Bloginator Streamlit."""

from datetime import datetime
from pathlib import Path

import streamlit as st

from bloginator.export.ui_utils import show_export_buttons
from bloginator.ui.pages.generate_ui_utils import (
    display_generation_error,
    run_bloginator_command,
)


def show_draft_generation() -> None:
    """Show the draft generation interface."""

    st.subheader("Generate Draft from Outline")

    st.markdown("Generate a full blog post draft from an existing outline.")

    # Check for outlines
    outlines = list(Path("output/generated").rglob("outline.json"))
    if not outlines and "latest_outline" not in st.session_state:
        st.info(
            """
            ℹ️ **No outlines found**

            Generate an outline first in the "Generate Outline" tab.
            """
        )
        return

    # Outline selection
    if "latest_outline" in st.session_state:
        default_outline = st.session_state.latest_outline
    elif outlines:
        default_outline = str(outlines[0])
    else:
        default_outline = ""

    outline_path = st.text_input(
        "Outline Path (JSON)",
        value=default_outline,
        help="Path to the outline JSON file",
    )

    # Draft parameters
    col1, col2 = st.columns(2)

    with col1:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Higher = more creative, Lower = more deterministic",
        )

    with col2:
        sources_per_section = st.slider(
            "Sources per Section",
            min_value=1,
            max_value=10,
            value=5,
            help="How many source documents to use per section",
        )

    max_section_words = st.slider(
        "Max Words per Section",
        min_value=100,
        max_value=1000,
        value=300,
        step=50,
        help="Target word count for each section",
    )

    # Generate button
    if st.button("✍️ Generate Draft", type="primary", use_container_width=True):
        if not outline_path or not Path(outline_path).exists():
            st.warning("Please provide a valid outline path")
            return

        # Create output path
        outline_file = Path(outline_path)
        draft_path = outline_file.parent / "draft.md"

        with st.spinner("Generating draft... This may take several minutes."):
            # Build command
            cmd = [
                "bloginator",
                "draft",
                "--index",
                str(Path(".bloginator/chroma")),
                "--outline",
                outline_path,
                "--output",
                str(draft_path),
                "--temperature",
                str(temperature),
                "--sources-per-section",
                str(sources_per_section),
                "--max-section-words",
                str(max_section_words),
            ]

            # Execute command (30 minute timeout for drafts)
            success, stdout, stderr = run_bloginator_command(cmd, timeout=1800)

            if success:
                _display_draft_success(draft_path)
            else:
                display_generation_error(success, stderr, timeout_seconds=1800)


def _display_draft_success(draft_path: Path) -> None:
    """Display successfully generated draft.

    Args:
        draft_path: Path to generated draft markdown file.
    """
    st.success("✓ Draft generated successfully!")

    st.markdown("---")
    st.subheader("Generated Draft")

    if draft_path.exists():
        draft_content = draft_path.read_text()

        with st.expander("📄 View Draft", expanded=True):
            st.markdown(draft_content)

        # Word count
        word_count = len(draft_content.split())
        st.metric("Word Count", f"{word_count:,}")

        st.markdown("---")
        st.info(
            f"""
            **Draft saved to:** {draft_path}

            You can now:
            - Edit the draft manually
            - Export it to different formats
            - Refine it with additional prompts
            """
        )

        # Download button
        st.download_button(
            label="⬇️ Download Draft",
            data=draft_content,
            file_name=f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )

        # Check for JSON file for export functionality
        json_path = draft_path.with_suffix(".json")
        if json_path.exists():
            show_export_buttons(json_path, "draft")
