"""Outline generation UI component for Bloginator Streamlit."""

import json
from pathlib import Path

import streamlit as st

from bloginator.ui.pages.generate_ui_utils import (
    AUDIENCE_MAP,
    CLASSIFICATION_MAP,
    create_output_directory,
    display_generation_error,
    run_bloginator_command,
)


def show_outline_generation() -> None:
    """Show the outline generation interface."""

    st.subheader("Generate Blog Outline")

    st.markdown("Create a structured outline for your blog post based on your corpus.")

    # Outline parameters
    title = st.text_input(
        "Blog Post Title",
        placeholder="e.g., Building a DevOps Culture at Scale",
        help="The title of your blog post",
    )

    keywords = st.text_input(
        "Keywords (comma-separated)",
        placeholder="e.g., devops, kubernetes, automation, culture",
        help="Keywords to guide content selection from your corpus",
    )

    thesis = st.text_area(
        "Main Thesis",
        placeholder="e.g., Effective DevOps culture requires both technical "
        "infrastructure AND organizational transformation",
        help="The main argument or point of your blog post",
        height=100,
    )

    # Classification and Audience selectors
    st.markdown("---")
    st.subheader("Content Classification & Audience")

    col_class, col_audience = st.columns(2)

    with col_class:
        classification = st.selectbox(
            "Classification",
            options=[
                "Guidance",
                "Best Practice",
                "Mandate",
                "Principle",
                "Opinion",
            ],
            index=0,
            help="""
            **Content authority level:**
            - **Guidance**: Suggestive, non-prescriptive recommendations
            - **Best Practice**: Established patterns with proven value
            - **Mandate**: Required standards or policies (strong authority)
            - **Principle**: Fundamental truths or values (philosophical)
            - **Opinion**: Personal perspective or viewpoint
            """,
        )

    with col_audience:
        audience = st.selectbox(
            "Target Audience",
            options=[
                "All Disciplines (General)",
                "IC Engineers",
                "Senior Engineers",
                "Engineering Leaders",
                "QA Engineers",
                "DevOps/SRE",
                "Product Managers",
                "Technical Leadership",
                "Executives",
                "General (Non-technical)",
            ],
            index=0,
            help="""
            **Target audience affects:**
            - Language level and technical depth
            - Which corpus sources are prioritized
            - Examples and analogies used
            """,
        )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        num_sections = st.slider(
            "Number of Sections",
            min_value=3,
            max_value=10,
            value=5,
            help="How many main sections in the outline",
        )

    with col2:
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Higher = more creative, Lower = more deterministic",
        )

    with col3:
        min_coverage = st.slider(
            "Min Coverage",
            min_value=1,
            max_value=10,
            value=2,
            help="Minimum number of source documents per section",
        )

    # Output format
    output_format = st.selectbox(
        "Output Format",
        options=["Both (JSON + Markdown)", "JSON only", "Markdown only"],
        index=0,
    )

    # Generate button
    if st.button("📝 Generate Outline", type="primary", use_container_width=True):
        if not title or not keywords:
            st.warning("Please provide at least a title and keywords")
            return

        output_dir = create_output_directory()
        outline_path = output_dir / "outline"

        with st.spinner("Generating outline... This may take a few minutes."):
            # Build command
            cmd = [
                "bloginator",
                "outline",
                "--index",
                str(Path(".bloginator/chroma")),
                "--title",
                title,
                "--keywords",
                keywords,
                "--classification",
                CLASSIFICATION_MAP.get(classification, "guidance"),
                "--audience",
                AUDIENCE_MAP.get(audience, "all-disciplines"),
                "--sections",
                str(num_sections),
                "--temperature",
                str(temperature),
                "--output",
                str(outline_path),
                "--min-coverage",
                str(min_coverage),
            ]

            if thesis:
                cmd.extend(["--thesis", thesis])

            # Determine format flag
            if "JSON" in output_format and "Markdown" in output_format:
                cmd.extend(["--format", "both"])
            elif "JSON" in output_format:
                cmd.extend(["--format", "json"])
            else:
                cmd.extend(["--format", "markdown"])

            # Execute command
            success, stdout, stderr = run_bloginator_command(cmd, timeout=600)

            if success:
                _display_outline_success(outline_path)
            else:
                display_generation_error(success, stderr, timeout_seconds=600)


def _display_outline_success(outline_path: Path) -> None:
    """Display successfully generated outline.

    Args:
        outline_path: Base path to outline files (without extension).
    """
    st.success("✓ Outline generated successfully!")

    st.markdown("---")
    st.subheader("Generated Outline")

    # Try to display markdown version
    md_path = Path(f"{outline_path}.md")
    if md_path.exists():
        with st.expander("📄 View Outline (Markdown)", expanded=True):
            st.markdown(md_path.read_text())

    # Try to display JSON version
    json_path = Path(f"{outline_path}.json")
    if json_path.exists():
        with st.expander("📊 View Outline (JSON)"):
            outline_data = json.loads(json_path.read_text())
            st.json(outline_data)

        # Save to session state for draft generation
        st.session_state.latest_outline = str(json_path)

    st.markdown("---")
    st.info(
        f"""
        **Outline saved to:**
        - {md_path if md_path.exists() else 'N/A'}
        - {json_path if json_path.exists() else 'N/A'}

        You can now generate a draft from this outline in the "Generate Draft" tab.
        """
    )
