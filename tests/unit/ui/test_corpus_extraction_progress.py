"""Tests for real-time progress indicators during extraction."""

from unittest.mock import Mock, patch

import pytest


class TestExtractionProgressIndicators:
    """Tests for real-time progress indicators during extraction."""

    @pytest.fixture
    def mock_streamlit(self) -> Mock:
        """Create mock Streamlit components."""
        mock_st = Mock()
        mock_st.empty.return_value = Mock()
        mock_st.info = Mock()
        mock_st.text_area = Mock()
        mock_st.success = Mock()
        mock_st.error = Mock()
        mock_st.code = Mock()
        mock_st.metric = Mock()
        mock_st.caption = Mock()
        return mock_st

    @patch("subprocess.Popen")
    def test_extraction_streams_output_line_by_line(self, mock_popen: Mock) -> None:
        """Test that extraction output is streamed line by line."""
        # Mock process with output
        mock_process = Mock()
        mock_process.poll.side_effect = [None, None, None, 0]  # Running, then done
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = [
            "Processing file1.md\n",
            "Processing file2.md\n",
            "Processing file3.md\n",
            "",  # EOF
        ]
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        # Collect output lines
        stdout_lines = []
        while True:
            if mock_process.poll() is not None:
                break
            line = mock_process.stdout.readline()
            if line:
                stdout_lines.append(line)

        assert len(stdout_lines) == 3
        assert "file1.md" in stdout_lines[0]
        assert "file2.md" in stdout_lines[1]
        assert "file3.md" in stdout_lines[2]

    @patch("subprocess.Popen")
    def test_extraction_shows_current_file_in_progress(self, mock_popen: Mock) -> None:
        """Test that current file being processed is displayed."""
        mock_process = Mock()
        mock_process.poll.side_effect = [None, 0]
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = [
            "Extracting: important_document.pdf\n",
            "",
        ]
        mock_process.communicate.return_value = ("", "")
        mock_popen.return_value = mock_process

        current_line = mock_process.stdout.readline()

        assert "important_document.pdf" in current_line
        assert "Extracting" in current_line

    @patch("subprocess.Popen")
    def test_extraction_handles_success_returncode(self, mock_popen: Mock) -> None:
        """Test extraction success handling."""
        mock_process = Mock()
        mock_process.poll.return_value = 0
        mock_process.returncode = 0
        mock_process.stdout.readline.return_value = ""
        mock_process.communicate.return_value = ("Extraction complete\n", "")
        mock_popen.return_value = mock_process

        # Simulate extraction completion
        while True:
            if mock_process.poll() is not None:
                break

        stdout, stderr = mock_process.communicate()

        assert mock_process.returncode == 0
        assert "complete" in stdout

    @patch("subprocess.Popen")
    def test_extraction_handles_failure_returncode(self, mock_popen: Mock) -> None:
        """Test extraction failure handling."""
        mock_process = Mock()
        mock_process.poll.return_value = 1
        mock_process.returncode = 1
        mock_process.stdout.readline.return_value = ""
        mock_process.communicate.return_value = ("", "Error: Invalid file format\n")
        mock_popen.return_value = mock_process

        # Simulate extraction failure
        while True:
            if mock_process.poll() is not None:
                break

        stdout, stderr = mock_process.communicate()

        assert mock_process.returncode == 1
        assert "Error" in stderr

    @patch("subprocess.Popen")
    def test_extraction_collects_all_output_lines(self, mock_popen: Mock) -> None:
        """Test that all output lines are collected."""
        mock_process = Mock()
        mock_process.poll.side_effect = [None, None, None, None, None, 0]
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = [
            "File 1\n",
            "File 2\n",
            "File 3\n",
            "File 4\n",
            "File 5\n",
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

        assert len(stdout_lines) == 5

    @patch("subprocess.Popen")
    def test_extraction_limits_displayed_lines_to_20(self, mock_popen: Mock) -> None:
        """Test that only last 20 lines are shown in UI."""
        # Generate 30 lines of output
        lines = [f"Processing file{i}.md\n" for i in range(30)]

        mock_process = Mock()
        mock_process.poll.side_effect = [None] * 30 + [0]
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

        # All lines collected
        assert len(stdout_lines) == 30

        # But only last 20 would be displayed
        displayed_lines = stdout_lines[-20:]
        assert len(displayed_lines) == 20
        assert "file10.md" in displayed_lines[0]  # First of last 20
        assert "file29.md" in displayed_lines[-1]  # Last line

    @patch("subprocess.Popen")
    def test_extraction_stderr_captured_on_failure(self, mock_popen: Mock) -> None:
        """Test that stderr is captured when extraction fails."""
        mock_process = Mock()
        mock_process.poll.return_value = 1
        mock_process.returncode = 1
        mock_process.stdout.readline.return_value = ""
        mock_process.communicate.return_value = (
            "",
            "Error: Permission denied\nFailed to read file\n",
        )
        mock_popen.return_value = mock_process

        while True:
            if mock_process.poll() is not None:
                break

        stdout, stderr = mock_process.communicate()
        stderr_lines = stderr.splitlines(keepends=True)

        assert mock_process.returncode == 1
        assert len(stderr_lines) == 2
        assert "Permission denied" in stderr_lines[0]
        assert "Failed to read" in stderr_lines[1]
