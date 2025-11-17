"""Content generation page for Bloginator Streamlit UI."""

import streamlit as st
from pathlib import Path
import subprocess
import json
from datetime import datetime


def show():
    """Display the content generation page."""

    st.header("📝 Generate Content")

    st.markdown(
        """
        Generate blog outlines and drafts from your corpus in your authentic voice.
        """
    )

    # Check if index exists
    index_dir = Path(".bloginator/chroma")
    if not index_dir.exists():
        st.warning(
            """
            ⚠️ **No index found!**

            Build an index first in the Corpus Management section.
            """
        )
        return

    # Check Ollama status
    try:
        import requests

        ollama_host = st.session_state.get("ollama_host", "http://localhost:11434")
        response = requests.get(f"{ollama_host}/api/tags", timeout=2)
        if response.status_code != 200:
            st.error(
                f"""
                ✗ **Ollama server not reachable at {ollama_host}**

                Start Ollama or configure the server address in Settings.
                """
            )
            return
    except:
        st.error(
            """
            ✗ **Ollama server not reachable**

            Start Ollama with: `ollama serve`
            """
        )
        return

    # Tabs for outline and draft generation
    tab1, tab2 = st.tabs(["Generate Outline", "Generate Draft"])

    with tab1:
        show_outline_generation()

    with tab2:
        show_draft_generation()


def show_outline_generation():
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
        placeholder="e.g., Effective DevOps culture requires both technical infrastructure AND organizational transformation",
        help="The main argument or point of your blog post",
        height=100,
    )

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

        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(f"output/generated/{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)

        outline_path = output_dir / "outline"

        with st.spinner("Generating outline... This may take a few minutes."):
            try:
                cmd = [
                    "bloginator",
                    "outline",
                    "--index",
                    str(Path(".bloginator/chroma")),
                    "--title",
                    title,
                    "--keywords",
                    keywords,
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

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minute timeout
                )

                if result.returncode == 0:
                    st.success("✓ Outline generated successfully!")

                    # Display the outline
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

                else:
                    st.error(f"✗ Generation failed (exit code {result.returncode})")
                    with st.expander("Error Details"):
                        st.code(result.stderr, language="text")

            except subprocess.TimeoutExpired:
                st.error("✗ Generation timed out (>10 minutes)")
            except Exception as e:
                st.error(f"✗ Error: {str(e)}")


def show_draft_generation():
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
            try:
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

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=1800,  # 30 minute timeout
                )

                if result.returncode == 0:
                    st.success("✓ Draft generated successfully!")

                    # Display the draft
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

                else:
                    st.error(f"✗ Generation failed (exit code {result.returncode})")
                    with st.expander("Error Details"):
                        st.code(result.stderr, language="text")

            except subprocess.TimeoutExpired:
                st.error("✗ Generation timed out (>30 minutes)")
            except Exception as e:
                st.error(f"✗ Error: {str(e)}")
