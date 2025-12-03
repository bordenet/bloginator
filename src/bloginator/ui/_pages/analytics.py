"""Analytics page for Bloginator Streamlit UI."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import streamlit as st


def show():
    """Display the analytics page."""
    st.header("📊 Analytics & Insights")

    st.markdown(
        """
        Analyze your corpus: coverage by topic, source distribution, quality metrics.
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

    # Corpus statistics
    st.subheader("Corpus Statistics")

    col1, col2, col3, col4 = st.columns(4)

    # Extracted files
    extracted_dir = Path("output/extracted")
    if extracted_dir.exists():
        json_files = list(extracted_dir.glob("*.json"))
        txt_files = list(extracted_dir.glob("*.txt"))

        with col1:
            st.metric("Documents", len(json_files))

        with col2:
            total_size = sum(f.stat().st_size for f in txt_files)
            st.metric("Total Size", f"{total_size / 1024 / 1024:.1f} MB")

        # Indexed chunks
        try:
            import chromadb

            client = chromadb.PersistentClient(path=str(index_dir))
            collections = client.list_collections()
            if collections:
                collection = collections[0]
                chunk_count = collection.count()

                with col3:
                    st.metric("Indexed Chunks", f"{chunk_count:,}")

                with col4:
                    avg_chunks = chunk_count / len(json_files) if json_files else 0
                    st.metric("Avg Chunks/Doc", f"{avg_chunks:.1f}")
        except Exception as e:
            st.error(f"Error reading index: {e}")

    st.markdown("---")

    # Source distribution
    st.subheader("Source Distribution")

    if extracted_dir.exists():
        json_files = list(extracted_dir.glob("*.json"))

        # Analyze metadata
        sources = []
        quality_ratings = []
        tags = []
        dates = []

        for json_file in json_files:
            try:
                metadata = json.loads(json_file.read_text())
                source_name = metadata.get("source_name", "Unknown")
                sources.append(source_name)

                quality = metadata.get("quality_rating", "standard")
                quality_ratings.append(quality)

                doc_tags = metadata.get("tags", [])
                tags.extend(doc_tags)

                created_date = metadata.get("created_date")
                if created_date:
                    from contextlib import suppress

                    with suppress(ValueError, TypeError):
                        dates.append(datetime.fromisoformat(created_date))
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                pass

        # Source distribution chart
        if sources:
            source_counts = Counter(sources)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Documents by Source**")
                for source, count in source_counts.most_common(10):
                    st.metric(source, count)

            with col2:
                st.markdown("**Quality Distribution**")
                quality_counts = Counter(quality_ratings)
                for quality, count in sorted(quality_counts.items()):
                    st.metric(quality.title(), count)

    st.markdown("---")

    # Tag cloud
    st.subheader("Topic Coverage")

    if tags:
        tag_counts = Counter(tags)

        st.markdown("**Most Common Tags**")
        col1, col2, col3 = st.columns(3)

        top_tags = tag_counts.most_common(15)
        for idx, (tag, count) in enumerate(top_tags):
            target_col = col1 if idx % 3 == 0 else col2 if idx % 3 == 1 else col3
            with target_col:
                st.metric(tag, count)

    st.markdown("---")

    # Temporal distribution
    st.subheader("Temporal Distribution")

    if dates:
        st.markdown("**Documents by Year**")

        year_counts = Counter(date.year for date in dates)

        # Simple bar chart using metrics
        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]

        for idx, (year, count) in enumerate(sorted(year_counts.items(), reverse=True)[:12]):
            target_col = cols[idx % 4]
            with target_col:
                st.metric(str(year), count)

    st.markdown("---")

    # Generated content stats
    st.subheader("Generated Content")

    generated_dir = Path("output/generated")
    if generated_dir.exists() and any(generated_dir.iterdir()):
        # Count generated files
        outlines = list(generated_dir.rglob("outline*.json"))
        drafts = list(generated_dir.rglob("draft*.md"))

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Outlines Generated", len(outlines))

        with col2:
            st.metric("Drafts Generated", len(drafts))

        # Recent generations
        if drafts:
            st.markdown("**Recent Drafts**")
            recent_drafts = sorted(drafts, key=lambda p: p.stat().st_mtime, reverse=True)[:5]

            for draft_path in recent_drafts:
                with st.expander(f"📄 {draft_path.parent.name}/{draft_path.name}"):
                    draft_content = draft_path.read_text()
                    word_count = len(draft_content.split())

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Word Count", f"{word_count:,}")
                    with col2:
                        modified = datetime.fromtimestamp(draft_path.stat().st_mtime)
                        st.caption(f"Modified: {modified.strftime('%Y-%m-%d %H:%M')}")

                    st.markdown("**Preview:**")
                    st.markdown(draft_content[:500] + "...")
    else:
        st.info("No generated content yet. Create your first outline!")

    st.markdown("---")

    # Coverage analysis
    st.subheader("Coverage Analysis")

    st.markdown(
        """
        **Topic Coverage Suggestions:**

        Enter a topic to see how well your corpus covers it.
        """
    )

    topic_query = st.text_input(
        "Topic to analyze",
        placeholder="e.g., kubernetes, agile, hiring",
        help="Enter a topic to see corpus coverage",
    )

    if topic_query and st.button("Analyze Coverage"):
        with st.spinner(f"Analyzing coverage for: {topic_query}"):
            try:
                import subprocess

                # nosec B603 - subprocess without shell=True is safe, cmd is controlled
                result = subprocess.run(  # nosec B603
                    [
                        "bloginator",
                        "search",
                        str(index_dir),
                        topic_query,
                        "-n",
                        "10",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    st.success(f"✓ Coverage analysis for: {topic_query}")
                    st.code(result.stdout, language="text")

                    # Simple coverage score based on result count
                    # (This is a simplification - real implementation would analyze scores)
                    st.metric(
                        "Estimated Coverage",
                        "Good" if "No results" not in result.stdout else "Low",
                    )
                else:
                    st.error("Error analyzing coverage")
            except Exception as e:
                st.error(f"Error: {e}")
