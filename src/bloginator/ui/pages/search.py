"""Search page for Bloginator Streamlit UI."""

import subprocess
from pathlib import Path

import streamlit as st


def show():
    """Display the search page."""

    st.header("🔍 Search Corpus")

    st.markdown(
        """
        Search your indexed corpus using semantic similarity.
        Find relevant passages from your past writing by meaning, not just keywords.
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

    # Search interface
    st.subheader("Search Query")

    query = st.text_input(
        "Enter your search query",
        placeholder="e.g., kubernetes devops automation culture",
        help="Enter keywords or a natural language question",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        num_results = st.slider(
            "Number of Results",
            min_value=1,
            max_value=20,
            value=5,
            help="How many results to return",
        )

    with col2:
        quality_filter = st.selectbox(
            "Quality Filter",
            options=["All", "Preferred", "Standard", "Deprecated"],
            index=0,
            help="Filter by quality rating",
        )

    with col3:
        recency_weight = st.slider(
            "Recency Weight",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.1,
            help="How much to favor recent documents (0=ignore, 1=heavily favor)",
        )

    # Search button
    if st.button("🔍 Search", type="primary", use_container_width=True) or (
        query and "last_query" in st.session_state and st.session_state.last_query != query
    ):
        if query:
            with st.spinner("Searching..."):
                try:
                    cmd = [
                        "bloginator",
                        "search",
                        str(index_dir),
                        query,
                        "-n",
                        str(num_results),
                    ]

                    if quality_filter != "All":
                        cmd.extend(["--quality-filter", quality_filter.lower()])

                    if recency_weight > 0:
                        cmd.extend(["--recency-weight", str(recency_weight)])

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    st.session_state.last_query = query

                    if result.returncode == 0:
                        st.success(f"✓ Found results for: {query}")
                        st.markdown("---")

                        # Display results in a nice format
                        st.subheader("Search Results")

                        # Parse and display results
                        output = result.stdout

                        # Simple display of raw output
                        st.code(output, language="text")

                        # TODO: Parse output into structured format for better display
                    else:
                        st.error(f"✗ Search failed (exit code {result.returncode})")
                        st.code(result.stderr, language="text")

                except subprocess.TimeoutExpired:
                    st.error("✗ Search timed out (>30 seconds)")
                except Exception as e:
                    st.error(f"✗ Error: {str(e)}")
        else:
            st.warning("Please enter a search query")

    st.markdown("---")

    # Search tips
    with st.expander("💡 Search Tips"):
        st.markdown(
            """
            **Effective Search Strategies:**

            1. **Natural Language**: Search for concepts, not just keywords
               - Good: "how to build team culture in remote environment"
               - Also Good: "kubernetes deployment best practices"

            2. **Quality Filtering**: Filter by content quality
               - "Preferred": Your most refined, authentic writing
               - "Standard": General quality content
               - "Deprecated": Older content you've moved past

            3. **Recency Weighting**: Balance relevance vs. recency
               - 0.0: Only semantic similarity matters
               - 0.5: Balance between relevance and recency
               - 1.0: Heavily favor recent documents

            4. **Multiple Queries**: Try different phrasings
               - Sometimes rephrasing reveals different relevant passages

            **Example Queries:**
            - "building devops culture"
            - "technical leadership without authority"
            - "career development for senior engineers"
            - "agile transformation challenges"
            """
        )

    # Recent searches
    if "search_history" in st.session_state and st.session_state.search_history:
        st.subheader("Recent Searches")

        for recent_query in st.session_state.search_history[-5:]:
            if st.button(f"🔍 {recent_query}", key=f"recent_{recent_query}"):
                st.session_state.last_query = recent_query
                st.rerun()
