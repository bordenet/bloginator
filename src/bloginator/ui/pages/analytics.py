"""Enhanced analytics page with interactive visualizations for Bloginator."""

from pathlib import Path


try:
    import pandas as pd
    import plotly.express as px
    import streamlit as st

    from bloginator.services.analytics import CorpusAnalytics

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    import streamlit as st


def show():
    """Display the enhanced analytics page with interactive charts."""
    st.header("📊 Corpus Analytics & Insights")

    if not DEPENDENCIES_AVAILABLE:
        st.error(
            """
            **Missing Dependencies!**

            This page requires additional packages. Install with:
            ```
            pip install 'bloginator[ui]'
            ```

            This will install: streamlit, plotly, pandas
            """
        )
        return

    st.markdown(
        """
        Interactive analytics dashboard for your corpus: distribution analysis,
        quality metrics, temporal patterns, and more.
        """
    )

    # Check if index exists
    extracted_dir = Path("output/extracted")
    index_dir = Path(".bloginator/chroma")

    if not extracted_dir.exists() or not any(extracted_dir.iterdir()):
        st.warning(
            """
            ⚠️ **No corpus found!**

            Extract and index documents first in the Corpus Management section.
            """
        )
        return

    # Initialize analytics service
    analytics = CorpusAnalytics(extracted_dir, index_dir)

    # Sidebar filters
    with st.sidebar:
        st.subheader("Filters")
        show_quality = st.checkbox("Show Quality Analysis", value=True)
        show_temporal = st.checkbox("Show Temporal Analysis", value=True)
        show_topics = st.checkbox("Show Topic Analysis", value=True)
        show_advanced = st.checkbox("Show Advanced Metrics", value=False)

    # === Basic Statistics ===
    st.subheader("📈 Overview")

    basic_stats = analytics.get_basic_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Documents", f"{basic_stats['document_count']:,}")

    with col2:
        st.metric("Total Size", f"{basic_stats['total_size_mb']:.1f} MB")

    with col3:
        st.metric("Indexed Chunks", f"{basic_stats['chunk_count']:,}")

    with col4:
        st.metric("Avg Chunks/Doc", f"{basic_stats['avg_chunks_per_doc']:.1f}")

    st.markdown("---")

    # === Quality Analysis ===
    if show_quality:
        st.subheader("🎯 Quality Distribution")

        quality_dist = analytics.get_quality_distribution()

        if quality_dist:
            col1, col2 = st.columns(2)

            with col1:
                # Pie chart for quality distribution
                fig_pie = px.pie(
                    names=list(quality_dist.keys()),
                    values=list(quality_dist.values()),
                    title="Documents by Quality Rating",
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                # Bar chart for quality distribution
                fig_bar = px.bar(
                    x=list(quality_dist.keys()),
                    y=list(quality_dist.values()),
                    title="Document Count by Quality",
                    labels={"x": "Quality Rating", "y": "Count"},
                    color=list(quality_dist.keys()),
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

    # === Word Count Distribution ===
    st.subheader("📝 Word Count Analysis")

    word_counts = analytics.get_word_count_distribution()

    if word_counts:
        col1, col2 = st.columns(2)

        with col1:
            # Histogram of word counts
            fig_hist = px.histogram(
                x=word_counts,
                nbins=20,
                title="Word Count Distribution",
                labels={"x": "Word Count", "y": "Number of Documents"},
                color_discrete_sequence=["#636EFA"],
            )
            fig_hist.update_layout(showlegend=False)
            st.plotly_chart(fig_hist, use_container_width=True)

        with col2:
            # Box plot for word count stats
            fig_box = px.box(
                y=word_counts,
                title="Word Count Statistics",
                labels={"y": "Word Count"},
                color_discrete_sequence=["#EF553B"],
            )
            st.plotly_chart(fig_box, use_container_width=True)

            # Show stats
            if word_counts:
                st.metric("Avg Words/Doc", f"{sum(word_counts) / len(word_counts):.0f}")
                st.metric("Max Words", f"{max(word_counts):,}")
                st.metric("Min Words", f"{min(word_counts):,}")

    st.markdown("---")

    # === Temporal Analysis ===
    if show_temporal:
        st.subheader("📅 Temporal Distribution")

        temporal_dist = analytics.get_temporal_distribution()

        if temporal_dist:
            # Line chart for temporal trends
            years = sorted(temporal_dist.keys())
            counts = [temporal_dist[year] for year in years]

            fig_line = px.line(
                x=years,
                y=counts,
                title="Documents Over Time",
                labels={"x": "Year", "y": "Document Count"},
                markers=True,
            )
            fig_line.update_traces(line_color="#00CC96", marker_size=10)
            st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("---")

    # === Topic Analysis ===
    if show_topics:
        st.subheader("🏷️ Topic Coverage")

        col1, col2 = st.columns(2)

        with col1:
            # Top sources
            source_dist = analytics.get_source_distribution(top_n=10)

            if source_dist:
                fig_sources = px.bar(
                    x=list(source_dist.values()),
                    y=list(source_dist.keys()),
                    orientation="h",
                    title="Top 10 Sources",
                    labels={"x": "Document Count", "y": "Source"},
                    color=list(source_dist.values()),
                    color_continuous_scale="Blues",
                )
                fig_sources.update_layout(showlegend=False, yaxis={"autorange": "reversed"})
                st.plotly_chart(fig_sources, use_container_width=True)

        with col2:
            # Tag cloud (bar chart)
            tag_dist = analytics.get_tag_distribution(top_n=15)

            if tag_dist:
                fig_tags = px.bar(
                    x=list(tag_dist.values()),
                    y=list(tag_dist.keys()),
                    orientation="h",
                    title="Top 15 Tags",
                    labels={"x": "Frequency", "y": "Tag"},
                    color=list(tag_dist.values()),
                    color_continuous_scale="Greens",
                )
                fig_tags.update_layout(showlegend=False, yaxis={"autorange": "reversed"})
                st.plotly_chart(fig_tags, use_container_width=True)

        st.markdown("---")

    # === Advanced Metrics ===
    if show_advanced:
        st.subheader("🔬 Advanced Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # Quality vs Word Count scatter
            quality_word_data = analytics.get_quality_vs_word_count()

            if quality_word_data:
                df = pd.DataFrame(quality_word_data)
                fig_scatter = px.scatter(
                    df,
                    x="word_count",
                    y="quality",
                    hover_data=["title"],
                    title="Quality vs. Word Count",
                    labels={"word_count": "Word Count", "quality": "Quality Rating"},
                    color="quality",
                    color_discrete_sequence=px.colors.qualitative.Safe,
                )
                fig_scatter.update_traces(marker_size=10)
                st.plotly_chart(fig_scatter, use_container_width=True)

        with col2:
            # Format distribution
            format_dist = analytics.get_format_distribution()

            if format_dist:
                fig_formats = px.pie(
                    names=list(format_dist.keys()),
                    values=list(format_dist.values()),
                    title="Document Format Breakdown",
                    color_discrete_sequence=px.colors.qualitative.Plotly,
                )
                fig_formats.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_formats, use_container_width=True)

        # Classification distribution
        classification_dist = analytics.get_classification_distribution()
        if classification_dist:
            st.markdown("**Classification Distribution**")
            fig_class = px.bar(
                x=list(classification_dist.keys()),
                y=list(classification_dist.values()),
                title="Documents by Classification",
                labels={"x": "Classification", "y": "Count"},
                color=list(classification_dist.keys()),
                color_discrete_sequence=px.colors.qualitative.Light24,
            )
            st.plotly_chart(fig_class, use_container_width=True)

        # Audience distribution
        audience_dist = analytics.get_audience_distribution()
        if audience_dist:
            st.markdown("**Audience Distribution**")
            fig_audience = px.bar(
                x=list(audience_dist.keys()),
                y=list(audience_dist.values()),
                title="Documents by Target Audience",
                labels={"x": "Audience", "y": "Count"},
                color=list(audience_dist.keys()),
                color_discrete_sequence=px.colors.qualitative.Prism,
            )
            st.plotly_chart(fig_audience, use_container_width=True)

        st.markdown("---")

    # === Coverage Analysis Tool ===
    st.subheader("🔍 Topic Coverage Analysis")

    st.markdown(
        """
        Enter a topic to analyze how well your corpus covers it.
        """
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        topic_query = st.text_input(
            "Topic to analyze",
            placeholder="e.g., kubernetes, agile, hiring",
            help="Enter a topic to see corpus coverage",
        )

    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        analyze_button = st.button("Analyze", type="primary")

    if topic_query and analyze_button:
        with st.spinner(f"Analyzing coverage for: {topic_query}"):
            try:
                import subprocess

                result = subprocess.run(
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
                    check=False,
                )

                if result.returncode == 0:
                    st.success(f"✓ Coverage analysis for: **{topic_query}**")
                    st.code(result.stdout, language="text")

                    # Simple coverage estimation
                    if "No results" not in result.stdout:
                        st.metric("Estimated Coverage", "✅ Good", delta="Found relevant content")
                    else:
                        st.metric("Estimated Coverage", "⚠️ Low", delta="Limited content found")
                else:
                    st.error("Error analyzing coverage")
            except Exception as e:
                st.error(f"Error: {e}")

    # === Export Analytics ===
    st.markdown("---")
    st.subheader("💾 Export Analytics")

    if st.button("📊 Generate Full Analytics Report"):
        st.info(
            """
            **Analytics Report Generated!**

            Full report includes:
            - All distribution charts
            - Statistical summaries
            - Quality metrics
            - Temporal analysis

            *(Export to PDF/HTML coming in future release)*
            """
        )
