"""Settings page for Bloginator Streamlit UI."""

import os
from pathlib import Path

import streamlit as st


def show():
    """Display the settings page."""
    st.header("⚙️ Settings")

    st.markdown(
        """
        Configure Bloginator settings: LLM provider, paths, and preferences.
        """
    )

    # Tabs for different settings
    tab1, tab2, tab3 = st.tabs(["LLM Configuration", "Paths", "About"])

    with tab1:
        show_llm_settings()

    with tab2:
        show_path_settings()

    with tab3:
        show_about()


def show_llm_settings():
    """Show LLM configuration settings."""
    st.subheader("LLM Configuration")

    st.markdown(
        """
        Configure your LLM provider for content generation.
        Currently supports Ollama (local) and OpenAI-compatible endpoints.
        """
    )

    # LLM Provider selection
    provider = st.selectbox(
        "LLM Provider",
        options=["Ollama (Local)", "Custom (OpenAI-compatible)"],
        index=0,
        help="Select your LLM provider",
    )

    if provider == "Ollama (Local)":
        st.markdown("**Ollama Configuration**")

        # Ollama host
        ollama_host = st.text_input(
            "Ollama Server URL",
            value=st.session_state.get("ollama_host", "http://localhost:11434"),
            help="URL of your Ollama server",
        )

        # Test connection
        if st.button("Test Connection"):
            with st.spinner("Testing connection..."):
                try:
                    import requests

                    response = requests.get(f"{ollama_host}/api/tags", timeout=5)
                    if response.status_code == 200:
                        st.success(f"✓ Connected to Ollama at {ollama_host}")

                        # Show available models
                        data = response.json()
                        if "models" in data:
                            st.markdown("**Available Models:**")
                            for model in data["models"]:
                                st.text(f"  - {model.get('name', 'unknown')}")
                    else:
                        st.error(f"✗ Connection failed (status {response.status_code})")
                except Exception as e:
                    st.error(f"✗ Connection failed: {str(e)}")

        # Model selection
        ollama_model = st.text_input(
            "Model Name",
            value=st.session_state.get("ollama_model", "mixtral:8x7b"),
            help="Name of the Ollama model to use",
        )

        # Save settings
        if st.button("Save Ollama Settings", type="primary"):
            st.session_state.ollama_host = ollama_host
            st.session_state.ollama_model = ollama_model

            # Update environment variables
            os.environ["OLLAMA_HOST"] = ollama_host
            os.environ["OLLAMA_MODEL"] = ollama_model

            st.success("✓ Settings saved")

    else:  # Custom provider
        st.markdown("**Custom LLM Configuration**")

        api_base = st.text_input(
            "API Base URL",
            value=st.session_state.get("llm_api_base", "https://api.openai.com/v1"),
            help="Base URL for your LLM API",
        )

        api_key = st.text_input(
            "API Key",
            value="",
            type="password",
            help="Your API key (stored in session only)",
        )

        model_name = st.text_input(
            "Model Name",
            value=st.session_state.get("llm_model_name", "gpt-4-turbo"),
            help="Name of the model to use",
        )

        if st.button("Save Custom Settings", type="primary"):
            st.session_state.llm_api_base = api_base
            st.session_state.llm_api_key = api_key
            st.session_state.llm_model_name = model_name

            os.environ["BLOGINATOR_LLM_BASE_URL"] = api_base
            os.environ["BLOGINATOR_LLM_MODEL"] = model_name
            if api_key:
                os.environ["BLOGINATOR_LLM_API_KEY"] = api_key

            st.success("✓ Settings saved")

    st.markdown("---")

    # Generation parameters
    st.subheader("Generation Defaults")

    default_temperature = st.slider(
        "Default Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state.get("default_temperature", 0.7),
        step=0.1,
        help="Default creativity level (0=deterministic, 1=creative)",
    )

    default_sections = st.slider(
        "Default Sections",
        min_value=3,
        max_value=10,
        value=st.session_state.get("default_sections", 5),
        help="Default number of sections in outlines",
    )

    if st.button("Save Generation Defaults"):
        st.session_state.default_temperature = default_temperature
        st.session_state.default_sections = default_sections
        st.success("✓ Defaults saved")


def show_path_settings():
    """Show path configuration settings."""
    st.subheader("Path Configuration")

    st.markdown("Configure directory paths for corpus, index, and outputs.")

    # Corpus configuration path
    corpus_config = st.text_input(
        "Corpus Configuration",
        value="corpus/corpus.yaml",
        help="Path to your corpus configuration file",
    )

    # Index directory
    index_dir = st.text_input(
        "Index Directory",
        value=".bloginator/chroma",
        help="Where to store the search index",
    )

    # Output directory
    output_dir = st.text_input(
        "Output Directory",
        value="output",
        help="Where to save extracted files and generated content",
    )

    if st.button("Save Path Settings", type="primary"):
        st.session_state.corpus_config = corpus_config
        st.session_state.index_dir = index_dir
        st.session_state.output_dir = output_dir
        st.success("✓ Path settings saved")

    st.markdown("---")

    # Verify paths
    st.subheader("Path Verification")

    paths_to_check = {
        "Corpus Config": corpus_config,
        "Index Directory": index_dir,
        "Output Directory": output_dir,
    }

    for name, path_str in paths_to_check.items():
        path = Path(path_str)
        if path.exists():
            st.success(f"✓ {name}: {path_str}")
        else:
            st.warning(f"⚠ {name}: {path_str} (does not exist)")


def show_about():
    """Show about information."""
    st.subheader("About Bloginator")

    st.markdown(
        """
        **Bloginator** is an AI-assisted content generation system that helps
        engineering leaders create authentic, high-quality documents by leveraging
        their own historical writing corpus.

        ### Key Features

        - **Voice Preservation**: Generates content in your authentic writing style
        - **Corpus Grounding**: All content sourced from your own documents
        - **Multi-Format Support**: PDF, DOCX, Markdown, plain text
        - **Semantic Search**: Find content by meaning, not just keywords
        - **Quality Weighting**: Prefer recent, refined thinking
        - **Safety Checks**: Block proprietary terms and confidential info

        ### Version Information

        - **Version**: 0.1.0
        - **Python**: 3.10+
        - **Key Dependencies**:
          - ChromaDB (vector storage)
          - sentence-transformers (embeddings)
          - Ollama (local LLM)
          - Streamlit (web UI)

        ### Documentation

        - **User Guide**: `docs/USER_GUIDE.md`
        - **Developer Guide**: `docs/DEVELOPER_GUIDE.md`
        - **Claude Guidelines**: `docs/CLAUDE.md`

        ### Support

        - **Repository**: https://github.com/bordenet/bloginator
        - **Issues**: https://github.com/bordenet/bloginator/issues

        ### License

        MIT License - See LICENSE file for details

        ---

        **Created by**: Matt Bordenet
        **Last Updated**: 2025-11-17
        """
    )

    # System diagnostics
    with st.expander("🔧 System Diagnostics"):
        st.markdown("**Environment Variables:**")

        env_vars = {
            "OLLAMA_HOST": os.environ.get("OLLAMA_HOST", "Not set"),
            "OLLAMA_MODEL": os.environ.get("OLLAMA_MODEL", "Not set"),
            "BLOGINATOR_CORPUS_DIR": os.environ.get("BLOGINATOR_CORPUS_DIR", "Not set"),
            "BLOGINATOR_CHROMA_DIR": os.environ.get("BLOGINATOR_CHROMA_DIR", "Not set"),
        }

        for key, value in env_vars.items():
            st.text(f"{key}: {value}")

        st.markdown("---")
        st.markdown("**Python Packages:**")

        try:
            import pkg_resources

            packages = ["chromadb", "streamlit", "sentence-transformers", "ollama"]
            for package in packages:
                try:
                    version = pkg_resources.get_distribution(package).version
                    st.text(f"{package}: {version}")
                except pkg_resources.DistributionNotFound:
                    st.text(f"{package}: Not installed")
        except ImportError:
            st.text("Cannot determine package versions")
