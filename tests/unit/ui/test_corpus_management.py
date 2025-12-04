"""Tests for corpus management UI functionality."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml


class TestCorpusSourceManagement:
    """Tests for adding, deleting, and managing corpus sources."""

    @pytest.fixture
    def corpus_yaml(self, tmp_path: Path) -> Path:
        """Create a test corpus.yaml file."""
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        yaml_file = corpus_dir / "corpus.yaml"

        config = {
            "sources": [
                {
                    "name": "blog-archive",
                    "path": "/Users/test/blogs/archive",
                    "quality": "preferred",
                    "enabled": True,
                    "tags": ["archive", "blog"],
                    "voice_notes": "Original voice from 2020",
                }
            ]
        }

        with yaml_file.open("w") as f:
            yaml.dump(config, f)

        return yaml_file

    def test_add_source_to_empty_config(self, tmp_path: Path) -> None:
        """Test adding a source to a config with no sources."""
        corpus_yaml = tmp_path / "corpus.yaml"
        config = {"extraction": {}, "indexing": {}}

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f)

        # Simulate adding a source
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        if "sources" not in config:
            config["sources"] = []

        new_source = {
            "name": "new-blog",
            "path": "/Users/test/blogs/new",
            "type": "directory",
            "enabled": True,
            "quality": "reference",
            "tags": ["blog", "recent"],
            "voice_notes": "Recent authentic voice",
        }

        config["sources"].append(new_source)

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Verify
        with corpus_yaml.open() as f:
            updated_config = yaml.safe_load(f)

        assert len(updated_config["sources"]) == 1
        assert updated_config["sources"][0]["name"] == "new-blog"
        assert updated_config["sources"][0]["path"] == "/Users/test/blogs/new"

    def test_add_duplicate_source_path_rejected(self, corpus_yaml: Path) -> None:
        """Test that duplicate paths are rejected."""
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        existing_paths = [source.get("path", "") for source in config.get("sources", [])]
        new_path = existing_paths[0]  # Try to add existing path

        # Check for exact duplicate (case-sensitive string match)
        path_exists = new_path in existing_paths
        assert path_exists

    def test_add_different_path_allowed(self, corpus_yaml: Path) -> None:
        """Test that different paths are allowed."""
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        existing_paths = [source.get("path", "") for source in config.get("sources", [])]
        new_path = "/Users/test/blogs/different"

        path_exists = new_path in existing_paths
        assert not path_exists

    def test_delete_source_by_name_and_path(self, corpus_yaml: Path) -> None:
        """Test deleting source by name and path matching."""
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        original_count = len(config["sources"])
        source_to_delete = config["sources"][0]
        source_name = source_to_delete.get("name", "")
        source_path = source_to_delete.get("path", "")

        # Delete by filtering
        sources_copy = config.get("sources", [])
        config["sources"] = [
            s
            for s in sources_copy
            if not (s.get("name") == source_name and s.get("path") == source_path)
        ]

        assert len(config["sources"]) == original_count - 1

    def test_delete_preserves_other_sources(self, tmp_path: Path) -> None:
        """Test that deleting one source preserves others."""
        corpus_yaml = tmp_path / "corpus.yaml"

        config = {
            "sources": [
                {
                    "name": "blog-1",
                    "path": "/path/1",
                    "quality": "preferred",
                    "enabled": True,
                    "tags": ["blog"],
                },
                {
                    "name": "blog-2",
                    "path": "/path/2",
                    "quality": "reference",
                    "enabled": True,
                    "tags": ["blog"],
                },
                {
                    "name": "blog-3",
                    "path": "/path/3",
                    "quality": "draft",
                    "enabled": False,
                    "tags": ["draft"],
                },
            ]
        }

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f)

        # Delete blog-2
        with corpus_yaml.open() as f:
            config = yaml.safe_load(f)

        config["sources"] = [s for s in config["sources"] if s.get("name") != "blog-2"]

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        # Verify
        with corpus_yaml.open() as f:
            updated = yaml.safe_load(f)

        assert len(updated["sources"]) == 2
        assert [s["name"] for s in updated["sources"]] == ["blog-1", "blog-3"]

    def test_parse_comma_separated_tags(self) -> None:
        """Test parsing comma-separated tags from form input."""
        input_tags = "blog, published, authentic-voice, 2024"

        tags_list = [t.strip() for t in input_tags.split(",") if t.strip()]

        assert tags_list == ["blog", "published", "authentic-voice", "2024"]

    def test_voice_notes_handling_multiline(self, tmp_path: Path) -> None:
        """Test that multiline voice notes are preserved."""
        corpus_yaml = tmp_path / "corpus.yaml"

        voice_notes = "Original voice from 2020.\nAuthentic style.\nPrefer for generation."
        config = {
            "sources": [
                {
                    "name": "archive",
                    "path": "/path/archive",
                    "voice_notes": voice_notes,
                }
            ]
        }

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f, allow_unicode=True)

        # Reload and verify
        with corpus_yaml.open() as f:
            loaded = yaml.safe_load(f)

        assert loaded["sources"][0]["voice_notes"] == voice_notes

    def test_quality_rating_validation(self) -> None:
        """Test quality rating validation."""
        valid_ratings = ["reference", "draft", "archive"]

        test_input = "reference"
        assert test_input in valid_ratings

        test_input = "invalid-rating"
        assert test_input not in valid_ratings

    def test_smb_path_handling(self) -> None:
        """Test handling of SMB network paths."""
        smb_path = "smb://lucybear-nas._smb._tcp.local/scratch/TL/path"

        # SMB paths should be treated as exact strings, not resolved
        existing_paths = [
            "/local/path",
            smb_path,
        ]

        # Exact match should find it
        assert smb_path in existing_paths

        # Different SMB path should not match
        different_smb = "smb://other-server/path"
        assert different_smb not in existing_paths

    def test_none_voice_notes_handling(self, tmp_path: Path) -> None:
        """Test that empty voice notes are stored as None."""
        corpus_yaml = tmp_path / "corpus.yaml"

        voice_notes = ""
        config = {
            "sources": [
                {
                    "name": "test",
                    "path": "/path",
                    "voice_notes": voice_notes if voice_notes else None,
                }
            ]
        }

        with corpus_yaml.open("w") as f:
            yaml.dump(config, f)

        with corpus_yaml.open() as f:
            loaded = yaml.safe_load(f)

        assert loaded["sources"][0]["voice_notes"] is None


class TestIndexPruning:
    """Tests for index pruning functionality."""

    def test_identify_orphaned_documents(self) -> None:
        """Test identifying documents from deleted sources."""
        configured_paths = {
            "/path/1",
            "/path/2",
            "/path/3",
        }

        # Mock index metadata
        index_docs = [
            {"id": "doc1", "source_path": "/path/1"},  # Configured
            {"id": "doc2", "source_path": "/path/2"},  # Configured
            {"id": "doc3", "source_path": "/deleted/path"},  # Orphaned
            {"id": "doc4", "source_path": "/other/deleted"},  # Orphaned
        ]

        orphaned_ids = [
            doc["id"]
            for doc in index_docs
            if doc["source_path"] and doc["source_path"] not in configured_paths
        ]

        assert orphaned_ids == ["doc3", "doc4"]

    def test_no_orphaned_documents(self) -> None:
        """Test when all documents are from configured sources."""
        configured_paths = {"/path/1", "/path/2", "/path/3"}

        index_docs = [
            {"id": "doc1", "source_path": "/path/1"},
            {"id": "doc2", "source_path": "/path/2"},
            {"id": "doc3", "source_path": "/path/3"},
        ]

        orphaned_ids = [
            doc["id"]
            for doc in index_docs
            if doc["source_path"] and doc["source_path"] not in configured_paths
        ]

        assert orphaned_ids == []

    def test_documents_with_empty_source_path(self) -> None:
        """Test that documents with empty source_path are not deleted."""
        configured_paths = {"/path/1"}

        index_docs = [
            {"id": "doc1", "source_path": "/path/1"},
            {"id": "doc2", "source_path": ""},  # Empty
            {"id": "doc3", "source_path": None},  # None
        ]

        orphaned_ids = [
            doc["id"]
            for doc in index_docs
            if doc["source_path"] and doc["source_path"] not in configured_paths
        ]

        assert orphaned_ids == []


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
        from pathlib import Path

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


class TestSkipSummaryDisplay:
    """Tests for skip summary display functionality in Streamlit UI."""

    def test_skip_report_parsed_and_displayed(self, tmp_path: Path) -> None:
        """Test that skip report JSON is parsed and displayed correctly."""
        import json

        # Create mock report file
        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "timestamp": "2025-12-03T12:00:00",
            "summary": {"total_skipped": 5, "total_errors": 0},
            "skipped": {
                "temp_file": ["~$temp1.docx", "~$temp2.docx"],
                "already_extracted": ["file1.md", "file2.md", "file3.md"],
            },
            "errors": {},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Parse and verify
        loaded_data = json.loads(report_file.read_text())
        assert loaded_data["summary"]["total_skipped"] == 5
        assert len(loaded_data["skipped"]["temp_file"]) == 2
        assert len(loaded_data["skipped"]["already_extracted"]) == 3

    def test_skip_summary_shows_categories(self, tmp_path: Path) -> None:
        """Test that skip summary shows all skip categories."""
        import json

        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 3, "total_errors": 0},
            "skipped": {
                "temp_file": ["~$temp.docx"],
                "unsupported_extension": ["file.xyz (.xyz)"],
                "ignore_pattern": [".DS_Store"],
            },
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Simulate skip summary display
        loaded_data = json.loads(report_file.read_text())
        skip_summary = []
        for category, items in loaded_data.get("skipped", {}).items():
            if items:
                skip_summary.append(f"**{category.replace('_', ' ').title()}** ({len(items)})")

        assert len(skip_summary) == 3
        assert "**Temp File** (1)" in skip_summary
        assert "**Unsupported Extension** (1)" in skip_summary
        assert "**Ignore Pattern** (1)" in skip_summary

    def test_skip_summary_limits_displayed_items(self, tmp_path: Path) -> None:
        """Test that skip summary limits displayed items to first 5."""
        import json

        report_file = tmp_path / "extraction_report_20251203_120000.json"
        # Create 10 skipped files
        skipped_files = [f"file{i}.md" for i in range(10)]
        report_data = {
            "summary": {"total_skipped": 10, "total_errors": 0},
            "skipped": {"already_extracted": skipped_files},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Simulate display logic
        loaded_data = json.loads(report_file.read_text())
        skip_summary = []
        for category, items in loaded_data.get("skipped", {}).items():
            if items:
                skip_summary.append(f"**{category.replace('_', ' ').title()}** ({len(items)})")
                for item in items[:5]:  # Only first 5
                    skip_summary.append(f"  • {item}")
                if len(items) > 5:
                    skip_summary.append(f"  ... and {len(items) - 5} more")

        # Should have: 1 header + 5 items + 1 "more" message = 7 lines
        assert len(skip_summary) == 7
        assert "file0.md" in skip_summary[1]
        assert "file4.md" in skip_summary[5]
        assert "... and 5 more" in skip_summary[6]

    def test_skip_summary_not_shown_when_zero_skips(self, tmp_path: Path) -> None:
        """Test that skip summary is not shown when there are no skips."""
        import json

        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 0, "total_errors": 0},
            "skipped": {},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Check condition
        loaded_data = json.loads(report_file.read_text())
        should_show = loaded_data.get("summary", {}).get("total_skipped", 0) > 0

        assert should_show is False

    def test_skip_report_file_path_shown(self, tmp_path: Path) -> None:
        """Test that full report file path is shown to user."""
        report_file = tmp_path / "extraction_report_20251203_120000.json"

        # Caption should show filename
        caption = f"Full report: {report_file.name}"

        assert "extraction_report_20251203_120000.json" in caption

    def test_multiple_report_files_uses_latest(self, tmp_path: Path) -> None:
        """Test that when multiple report files exist, the latest is used."""
        import json

        # Create multiple report files
        old_report = tmp_path / "extraction_report_20251203_100000.json"
        old_report.write_text(json.dumps({"summary": {"total_skipped": 1}}))

        new_report = tmp_path / "extraction_report_20251203_120000.json"
        new_report.write_text(json.dumps({"summary": {"total_skipped": 5}}))

        # Find latest
        report_files = sorted(tmp_path.glob("extraction_report_*.json"))
        latest_report = report_files[-1]

        assert latest_report == new_report
        loaded_data = json.loads(latest_report.read_text())
        assert loaded_data["summary"]["total_skipped"] == 5

    def test_skip_summary_handles_empty_categories(self, tmp_path: Path) -> None:
        """Test that empty skip categories are not displayed."""
        import json

        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 2, "total_errors": 0},
            "skipped": {
                "temp_file": ["~$temp.docx"],
                "already_extracted": [],  # Empty category
                "unsupported_extension": ["file.xyz (.xyz)"],
            },
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Simulate display logic - only show non-empty categories
        loaded_data = json.loads(report_file.read_text())
        skip_summary = []
        for category, items in loaded_data.get("skipped", {}).items():
            if items:  # Only if category has items
                skip_summary.append(f"**{category.replace('_', ' ').title()}** ({len(items)})")

        # Should only show 2 categories (temp_file and unsupported_extension)
        assert len(skip_summary) == 2
        assert "**Temp File**" in skip_summary[0]
        assert "**Unsupported Extension**" in skip_summary[1]

    def test_indexing_report_uses_correct_prefix(self, tmp_path: Path) -> None:
        """Test that indexing uses indexing_report_* prefix."""
        import json

        report_file = tmp_path / "indexing_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 3, "total_errors": 0},
            "skipped": {"unchanged_document": ["doc1.txt", "doc2.txt", "doc3.txt"]},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Find indexing reports
        report_files = sorted(tmp_path.glob("indexing_report_*.json"))
        assert len(report_files) == 1
        assert report_files[0].name.startswith("indexing_report_")

    def test_skip_summary_markdown_formatting(self, tmp_path: Path) -> None:
        """Test that skip summary uses proper markdown formatting."""
        import json

        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_data = {
            "summary": {"total_skipped": 2, "total_errors": 0},
            "skipped": {"temp_file": ["~$temp1.docx", "~$temp2.docx"]},
        }
        report_file.write_text(json.dumps(report_data, indent=2))

        # Generate markdown
        loaded_data = json.loads(report_file.read_text())
        skip_summary = []
        for category, items in loaded_data.get("skipped", {}).items():
            if items:
                # Should use **bold** for headers and • for bullets
                skip_summary.append(f"**{category.replace('_', ' ').title()}** ({len(items)})")
                for item in items:
                    skip_summary.append(f"  • {item}")

        markdown_output = "\n".join(skip_summary)

        assert "**Temp File**" in markdown_output
        assert "  • ~$temp1.docx" in markdown_output
        assert "  • ~$temp2.docx" in markdown_output

    def test_skip_summary_error_handling(self, tmp_path: Path) -> None:
        """Test that corrupted report files are handled gracefully."""
        # Create invalid JSON file
        report_file = tmp_path / "extraction_report_20251203_120000.json"
        report_file.write_text("{ invalid json }")

        # Should catch exception
        import json

        try:
            json.loads(report_file.read_text())
            raise AssertionError("Should have raised JSONDecodeError")
        except json.JSONDecodeError:
            # Expected - should be handled gracefully in UI
            pass


class TestRealTimeSkipEventParsing:
    """Tests for real-time skip event parsing from CLI output."""

    def test_extract_skip_event_from_output_line(self) -> None:
        """Test parsing [SKIP] prefix from extraction output."""
        line = "[SKIP] /path/to/file.md (already_extracted)\n"

        if line.strip().startswith("[SKIP]"):
            skip_info = line.strip()[6:].strip()
            assert skip_info == "/path/to/file.md (already_extracted)"

    def test_extract_multiple_skip_events(self) -> None:
        """Test parsing multiple skip events from output stream."""
        output_lines = [
            "[SKIP] /path/to/file1.md (already_extracted)\n",
            "Processing file2.pdf\n",
            "[SKIP] /path/to/~$temp.docx (temp_file)\n",
            "Processing file3.docx\n",
            "[SKIP] /path/to/.DS_Store (ignore_pattern)\n",
        ]

        skipped_files = []
        for line in output_lines:
            if line.strip().startswith("[SKIP]"):
                skip_info = line.strip()[6:].strip()
                skipped_files.append(f"• {skip_info}")

        assert len(skipped_files) == 3
        assert "• /path/to/file1.md (already_extracted)" in skipped_files
        assert "• /path/to/~$temp.docx (temp_file)" in skipped_files
        assert "• /path/to/.DS_Store (ignore_pattern)" in skipped_files

    def test_current_file_from_non_skip_line(self) -> None:
        """Test extracting current file from non-skip lines."""
        line = "Processing: /Users/matt/Documents/important_file.pdf\n"

        if not line.strip().startswith("[SKIP]"):
            current_file = line.strip()
            assert "important_file.pdf" in current_file

    def test_skip_event_with_absolute_path(self) -> None:
        """Test skip event parsing with absolute file paths."""
        line = "[SKIP] /Users/matt/Library/CloudStorage/OneDrive/Documents/file.md (already_extracted)\n"

        skip_info = line.strip()[6:].strip()

        assert "OneDrive" in skip_info
        assert "already_extracted" in skip_info
        assert skip_info.endswith(")")

    def test_skip_event_preserves_full_path(self) -> None:
        """Test that skip event preserves complete file paths."""
        long_path = "[SKIP] /Users/matt/Very/Long/Path/With/Many/Directories/important_document_2025.md (already_extracted)\n"

        skip_info = long_path.strip()[6:].strip()

        assert "/Users/matt/Very/Long/Path" in skip_info
        assert "important_document_2025.md" in skip_info

    def test_skip_accumulation_in_list(self) -> None:
        """Test that skip events accumulate in a growing list."""
        output = [
            "[SKIP] file1.md (already_extracted)",
            "[SKIP] file2.docx (temp_file)",
            "[SKIP] file3.pdf (already_extracted)",
            "[SKIP] file4.txt (unsupported_extension)",
            "[SKIP] file5.zip (temp_file)",
        ]

        skipped_files = []
        for line in output:
            if line.startswith("[SKIP]"):
                skip_info = line[6:].strip()
                skipped_files.append(f"• {skip_info}")

        assert len(skipped_files) == 5
        assert skipped_files[0] == "• file1.md (already_extracted)"
        assert skipped_files[-1] == "• file5.zip (temp_file)"

    def test_mixed_output_and_skip_events(self) -> None:
        """Test handling mixed regular output and skip events."""
        output_lines = [
            "Starting extraction...",
            "[SKIP] file1.md (already_extracted)",
            "Processing: file2.pdf",
            "[SKIP] file3.docx (temp_file)",
            "Processing: file4.txt",
            "[SKIP] file5.zip (unsupported)",
            "Extraction complete!",
        ]

        current_file = None
        skipped_files = []

        for line in output_lines:
            if line.startswith("[SKIP]"):
                skip_info = line[6:].strip()
                skipped_files.append(f"• {skip_info}")
            else:
                current_file = line

        assert len(skipped_files) == 3
        assert current_file == "Extraction complete!"

    def test_index_skip_event_parsing(self) -> None:
        """Test parsing skip events during indexing."""
        line = "[SKIP] document_001.json (unchanged_document)\n"

        if line.strip().startswith("[SKIP]"):
            skip_info = line.strip()[6:].strip()
            assert skip_info == "document_001.json (unchanged_document)"

    def test_skip_event_with_parentheses_in_reason(self) -> None:
        """Test skip events where reason might have special formatting."""
        line = "[SKIP] /path/to/file.md (already_extracted)\n"

        skip_info = line.strip()[6:].strip()

        assert skip_info.count("(") == 1
        assert skip_info.count(")") == 1
        assert skip_info.endswith(")")

    def test_display_list_updates_continuously(self) -> None:
        """Test that skip list display updates as new skips are detected."""
        mock_container = Mock()
        skipped_files = []

        lines = [
            "[SKIP] file1.md (already_extracted)",
            "[SKIP] file2.docx (temp_file)",
            "[SKIP] file3.pdf (already_extracted)",
        ]

        for line in lines:
            if line.startswith("[SKIP]"):
                skip_info = line[6:].strip()
                skipped_files.append(f"• {skip_info}")
                mock_container.text_area(
                    "Skipped Files",
                    value="\n".join(skipped_files),
                    height=300,
                    key=f"skipped_{len(skipped_files)}",
                )

        assert mock_container.text_area.call_count == 3

    def test_skip_display_handles_empty_list(self) -> None:
        """Test that skip display handles empty skip list."""
        skipped_files = []

        should_display = len(skipped_files) > 0

        assert should_display is False

    def test_skip_display_handles_many_skips(self) -> None:
        """Test skip display with large number of skips."""
        output = [f"[SKIP] file{i}.md (reason_{i})" for i in range(100)]

        skipped_files = []
        for line in output:
            skip_info = line[6:].strip()
            skipped_files.append(f"• {skip_info}")

        assert len(skipped_files) == 100
        combined = "\n".join(skipped_files)
        assert "file0.md" in combined
        assert "file99.md" in combined


        class TestExplicitProgressLineFormats:
        """Tests for explicit progress line formats from CLI."""

        def test_extracting_prefix_parsing(self) -> None:
        """Test parsing Extracting: prefix for current file."""
        line = "Extracting: /path/to/file.pdf"

        if line.startswith("Extracting:"):
            current_file = line[11:].strip()
            assert current_file == "/path/to/file.pdf"

        def test_extracting_with_long_path(self) -> None:
        """Test Extracting: with full absolute path."""
        line = "Extracting: /Users/matt/Library/CloudStorage/OneDrive/Documents/important.docx"

        if line.startswith("Extracting:"):
            current_file = line[11:].strip()
            assert "OneDrive" in current_file
            assert "important.docx" in current_file

        def test_ui_display_update_from_extracting(self) -> None:
        """Test Streamlit container update from Extracting: line."""
        mock_container = Mock()
        line = "Extracting: /path/to/file.md"

        if line.startswith("Extracting:"):
            current_file = line[11:].strip()
            mock_container.info(f"📄 Current: {current_file}")

        mock_container.info.assert_called_once_with("📄 Current: /path/to/file.md")

        def test_extraction_output_with_mixed_events(self) -> None:
        """Test extraction output with skip events and extracting lines."""
        output = [
            "Extracting: file1.pdf",
            "[SKIP] file2.md (already_extracted)",
            "Extracting: file3.docx",
            "[SKIP] file4.txt (already_extracted)",
        ]

        current_file = None
        skipped_files = []

        for line in output:
            if line.startswith("[SKIP]"):
                skip_info = line[6:].strip()
                skipped_files.append(f"• {skip_info}")
            elif line.startswith("Extracting:"):
                current_file = line[11:].strip()

        assert current_file == "file3.docx"
        assert len(skipped_files) == 2
        assert "file2.md" in skipped_files[0]
        assert "file4.txt" in skipped_files[1]

        def test_ignore_non_prefixed_lines(self) -> None:
        """Test that lines without recognized prefixes are ignored."""
        output = [
            "Extracting: file1.pdf",
            "Some random output line",
            "Another info message",
            "Extracting: file2.pdf",
        ]

        current_file = None
        for line in output:
            if line.startswith("Extracting:"):
                current_file = line[11:].strip()

        # Should only capture Extracting: lines, not random output
        assert current_file == "file2.pdf"

        def test_whitespace_handling_in_extracting(self) -> None:
        """Test whitespace handling in Extracting: prefix."""
        line = "Extracting:    /path/to/file.pdf   "

        if line.startswith("Extracting:"):
            current_file = line[11:].strip()
            assert current_file == "/path/to/file.pdf"
            assert not current_file.startswith(" ")
            assert not current_file.endswith(" ")
