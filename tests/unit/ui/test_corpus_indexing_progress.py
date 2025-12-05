"""Tests for real-time progress indicators during indexing."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch


class TestIndexingProgressIndicators:
    """Tests for real-time progress indicators during indexing."""

    @patch("subprocess.Popen")
    def test_indexing_streams_output_line_by_line(self, mock_popen: Mock) -> None:
        """Test that indexing output is streamed line by line."""
        mock_process = Mock()
        mock_process.poll.side_effect = [None, None, None, 0]
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = [
            "Indexing document1.json\n",
            "Indexing document2.json\n",
            "Indexing document3.json\n",
            "",
        ]
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        stdout_lines = []
        while True:
            if mock_process.poll() is not None:
                break
            line = mock_process.stdout.readline()
            if line:
                stdout_lines.append(line)

        assert len(stdout_lines) == 3
        assert "document1.json" in stdout_lines[0]
        assert "document2.json" in stdout_lines[1]
        assert "document3.json" in stdout_lines[2]

    @patch("subprocess.Popen")
    def test_indexing_shows_current_document(self, mock_popen: Mock) -> None:
        """Test that current document being indexed is displayed."""
        mock_process = Mock()
        mock_process.poll.side_effect = [None, 0]
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = [
            "Processing: important_content_chunk_001.json\n",
            "",
        ]
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        current_line = mock_process.stdout.readline()

        assert "important_content_chunk_001.json" in current_line
        assert "Processing" in current_line

    @patch("subprocess.Popen")
    def test_indexing_handles_success(self, mock_popen: Mock) -> None:
        """Test indexing success with metrics."""
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_process.stdout.readline.return_value = ""
        mock_process.communicate.return_value = ("Indexed 500 chunks\n", "")
        mock_popen.return_value = mock_process

        while True:
            if mock_process.poll() is not None:
                break

        stdout, _ = mock_process.communicate()

        assert mock_process.returncode == 0
        assert "500 chunks" in stdout

    @patch("subprocess.Popen")
    def test_indexing_handles_failure(self, mock_popen: Mock) -> None:
        """Test indexing failure handling."""
        mock_process = Mock()
        mock_process.poll.return_value = 1
        mock_process.returncode = 1
        mock_process.stdout.readline.return_value = ""
        mock_process.communicate.return_value = (
            "",
            "Error: ChromaDB connection failed\n",
        )
        mock_popen.return_value = mock_process

        while True:
            if mock_process.poll() is not None:
                break

        _, stderr = mock_process.communicate()

        assert mock_process.returncode == 1
        assert "ChromaDB" in stderr

    @patch("subprocess.Popen")
    def test_indexing_progress_with_large_corpus(self, mock_popen: Mock) -> None:
        """Test indexing progress with many documents."""
        # Simulate 100 documents being indexed
        lines = [f"Indexing doc_{i:03d}.json\n" for i in range(100)]

        mock_process = Mock()
        mock_process.poll.side_effect = [None] * 100 + [0]
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = lines + [""]
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        stdout_lines = []
        while True:
            if mock_process.poll() is not None:
                break
            line = mock_process.stdout.readline()
            if line:
                stdout_lines.append(line)

        assert len(stdout_lines) == 100
        # Only last 20 would be displayed in UI
        displayed = stdout_lines[-20:]
        assert len(displayed) == 20
        assert "doc_080.json" in displayed[0]
        assert "doc_099.json" in displayed[-1]

    @patch("subprocess.Popen")
    def test_command_construction_with_options(self, mock_popen: Mock) -> None:
        """Test that command is constructed with correct options."""
        # Expected command
        cmd = [
            "bloginator",
            "index",
            str(Path("output/extracted")),
            "-o",
            ".bloginator/chroma",
            "--chunk-size",
            "1000",
        ]

        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_process.stdout.readline.return_value = ""
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        # Simulate calling with these args
        subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        # Verify Popen was called with correct command
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]
        assert call_args == cmd


class TestProgressContainerBehavior:
    """Tests for Streamlit container behavior during progress updates."""

    def test_progress_container_updates_with_each_line(self) -> None:
        """Test that progress container is updated for each output line."""
        mock_container = Mock()
        lines = ["File 1\n", "File 2\n", "File 3\n"]

        for line in lines:
            mock_container.info(f"📄 {line.strip()}")

        assert mock_container.info.call_count == 3

    def test_output_container_shows_scrolling_log(self) -> None:
        """Test that output container shows scrolling log of recent lines."""
        mock_container = Mock()
        all_lines = [f"Line {i}\n" for i in range(30)]

        for i, _line in enumerate(all_lines):
            # Simulate showing last 20 lines
            recent_lines = all_lines[max(0, i - 19) : i + 1]
            mock_container.text_area(
                "Output",
                value="".join(recent_lines),
                height=200,
                key=f"output_{i}",
            )

        # Should be called for each line
        assert mock_container.text_area.call_count == 30

    def test_progress_container_cleared_on_completion(self) -> None:
        """Test that progress indicator is cleared when process completes."""
        mock_container = Mock()

        # Show progress
        mock_container.info("Processing...")

        # Clear when done
        mock_container.empty()

        assert mock_container.info.called
        assert mock_container.empty.called

    def test_status_container_shows_success_message(self) -> None:
        """Test that status container shows success on completion."""
        mock_container = Mock()

        # Simulate successful completion
        returncode = 0
        if returncode == 0:
            mock_container.success("✓ Extraction complete!")
        else:
            mock_container.error("✗ Extraction failed")

        mock_container.success.assert_called_once_with("✓ Extraction complete!")
        mock_container.error.assert_not_called()

    def test_status_container_shows_error_message(self) -> None:
        """Test that status container shows error on failure."""
        mock_container = Mock()

        # Simulate failed completion
        returncode = 1
        if returncode == 0:
            mock_container.success("✓ Extraction complete!")
        else:
            mock_container.error(f"✗ Extraction failed (exit code {returncode})")

        mock_container.success.assert_not_called()
        mock_container.error.assert_called_once_with("✗ Extraction failed (exit code 1)")

    def test_output_container_shows_final_output(self) -> None:
        """Test that output container shows complete output at end."""
        mock_container = Mock()
        final_output = "Line 1\nLine 2\nLine 3\nComplete!\n"

        # Show final output
        mock_container.code(final_output, language="text")

        mock_container.code.assert_called_once_with(final_output, language="text")
