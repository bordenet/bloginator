"""Corpus extraction execution engine."""

import subprocess
from pathlib import Path

import streamlit as st


def run_extraction(corpus_config: Path, output_dir: str, force_extract: bool) -> None:
    """Run extraction process with real-time output.

    Args:
        corpus_config: Path to corpus config file
        output_dir: Output directory for extracted files
        force_extract: Whether to force re-extraction
    """
    # Create placeholders for real-time progress
    current_file_container = st.empty()
    skipped_files_container = st.empty()
    status_container = st.empty()

    try:
        cmd = [
            "bloginator",
            "extract",
            "-o",
            output_dir,
            "--config",
            str(corpus_config),
        ]

        if force_extract:
            cmd.append("--force")

        # Run with real-time output streaming
        # nosec B603 - subprocess without shell=True is safe, cmd is controlled
        process = subprocess.Popen(  # nosec B603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )

        stdout_lines = []
        stderr_lines = []
        skipped_files = []  # Track skipped files
        current_file = "Starting..."

        # Read output line by line as it comes
        while True:
            # Check if process is still running
            if process.poll() is not None:
                break

            # Read available output
            line = process.stdout.readline()
            if line:
                stdout_lines.append(line)

                # Parse line to detect skip events or current file
                stripped = line.strip()
                if stripped.startswith("[SKIP]"):
                    # Parse skip event: [SKIP] /path/to/file (reason)
                    skip_info = stripped[6:].strip()  # Remove "[SKIP] " prefix
                    skipped_files.append(f"• {skip_info}")
                    # Update skipped files display
                    skipped_files_container.text_area(
                        "Skipped Files",
                        value="\n".join(skipped_files),
                        height=300,
                        key="extraction_skipped_files",
                        disabled=True,
                    )
                elif stripped.startswith("Extracting:"):
                    # Parse current file: "Extracting: /path/to/file"
                    current_file = stripped[11:].strip()  # Remove "Extracting: " prefix
                    # Update current file display
                    current_file_container.info(f"📄 Current: {current_file}")

        # Get remaining output
        stdout_remaining, stderr_remaining = process.communicate()
        if stdout_remaining:
            stdout_lines.extend(stdout_remaining.splitlines(keepends=True))
        if stderr_remaining:
            stderr_lines.extend(stderr_remaining.splitlines(keepends=True))

        # Clear current file indicator
        current_file_container.empty()

        if process.returncode == 0:
            status_container.success("✓ Extraction complete!")

            # Count extracted files
            extracted_dir = Path(output_dir)
            if extracted_dir.exists():
                json_count = len(list(extracted_dir.glob("*.json")))
                txt_count = len(list(extracted_dir.glob("*.txt")))
                st.metric("Extracted Files", f"{json_count} documents")
                st.caption(f"{txt_count} text files, {json_count} metadata files")

            # Show final skip count
            if skipped_files:
                st.info(f"📋 {len(skipped_files)} file(s) skipped (see list above)")
        else:
            status_container.error(f"✗ Extraction failed (exit code {process.returncode})")
            if stderr_lines:
                st.code("".join(stderr_lines), language="text")

    except Exception as e:
        status_container.error(f"✗ Error: {str(e)}")
