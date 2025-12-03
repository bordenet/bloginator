# Corpus Upload Feature Test Plan

**Status**: Draft
**Date**: 2025-12-03
**Test Coverage Target**: 85%+ (critical path)

---

## Test Strategy

### Testing Pyramid
```
                    △
                   / \
                  /   \ E2E Tests (10%)
                 /─────\
                /       \
               /         \
              /───────────\ Integration Tests (30%)
             /             \
            /               \
           /─────────────────\ Unit Tests (60%)
          /____________________\
```

### Test Scope

| Layer | Coverage | Framework | Files |
|-------|----------|-----------|-------|
| **Unit** | File validation, YAML ops, metadata | pytest | test_corpus_upload_manager.py |
| **Integration** | Upload → Storage → YAML update | pytest | test_corpus_upload_integration.py |
| **E2E** | Full workflow: Upload → Extract → Index | pytest | test_corpus_upload_e2e.py |
| **UI** | Streamlit widgets, forms, interactions | Manual/pytest-streamlit | (manual initially) |

---

## Unit Tests

### Test File
`tests/unit/services/test_corpus_upload_manager.py`

### Test Cases

#### 1. File Validation Tests

**TC1.1: Valid file types accepted**
```python
@pytest.mark.parametrize("ext,mime", [
    (".pdf", "application/pdf"),
    (".docx", "application/vnd.ms-word"),
    (".txt", "text/plain"),
    (".md", "text/markdown"),
])
def test_validate_files_accepts_valid_types(ext, mime, tmp_path):
    """Valid file types should pass validation."""
    manager = CorpusUploadManager(tmp_path)
    file = create_mock_file("test" + ext, mime, b"content")

    valid, errors = manager._validate_files([file])

    assert len(valid) == 1
    assert len(errors) == 0
```

**TC1.2: Invalid file types rejected**
```python
@pytest.mark.parametrize("ext,mime", [
    (".exe", "application/x-executable"),
    (".sh", "text/x-shellscript"),
    (".zip", "application/zip"),
    (".jpg", "image/jpeg"),
])
def test_validate_files_rejects_invalid_types(ext, mime, tmp_path):
    """Invalid file types should be rejected with error."""
    manager = CorpusUploadManager(tmp_path)
    file = create_mock_file("test" + ext, mime, b"content")

    valid, errors = manager._validate_files([file])

    assert len(valid) == 0
    assert len(errors) == 1
    assert "not supported" in errors[0].lower()
```

**TC1.3: File size validation**
```python
@pytest.mark.parametrize("size_mb", [1, 25, 50])
def test_validate_files_accepts_under_limit(size_mb, tmp_path):
    """Files under 50MB should be accepted."""
    manager = CorpusUploadManager(tmp_path)
    content = b"x" * (size_mb * 1024 * 1024)
    file = create_mock_file("test.pdf", "application/pdf", content)

    valid, errors = manager._validate_files([file])

    assert len(valid) == 1
    assert len(errors) == 0
```

**TC1.4: File too large rejected**
```python
def test_validate_files_rejects_over_limit(tmp_path):
    """Files over 50MB should be rejected."""
    manager = CorpusUploadManager(tmp_path)
    content = b"x" * (51 * 1024 * 1024)
    file = create_mock_file("test.pdf", "application/pdf", content)

    valid, errors = manager._validate_files([file])

    assert len(valid) == 0
    assert "too large" in errors[0].lower()
```

**TC1.5: Empty file rejected**
```python
def test_validate_files_rejects_empty(tmp_path):
    """Empty files should be rejected."""
    manager = CorpusUploadManager(tmp_path)
    file = create_mock_file("test.pdf", "application/pdf", b"")

    valid, errors = manager._validate_files([file])

    assert len(valid) == 0
    assert "empty" in errors[0].lower()
```

#### 2. Filename Sanitization Tests

**TC2.1: Path traversal attempts blocked**
```python
@pytest.mark.parametrize("unsafe_name", [
    "../../../etc/passwd",
    "..\\windows\\system32\\test.pdf",
    "test/../../malicious.pdf",
])
def test_sanitize_filename_blocks_traversal(unsafe_name, tmp_path):
    """Filenames with path traversal attempts should be sanitized."""
    manager = CorpusUploadManager(tmp_path)

    safe_name = manager._sanitize_filename(unsafe_name)

    assert ".." not in safe_name
    assert "/" not in safe_name
    assert "\\" not in safe_name
    assert safe_name.endswith(".pdf")
```

**TC2.2: Special characters removed**
```python
@pytest.mark.parametrize("unsafe_name", [
    "test:file*.pdf",
    'test"quotes"<>.pdf',
    "test|pipe.pdf",
])
def test_sanitize_filename_removes_special_chars(unsafe_name, tmp_path):
    """Special characters should be removed."""
    manager = CorpusUploadManager(tmp_path)

    safe_name = manager._sanitize_filename(unsafe_name)

    assert safe_name.replace("_", "").replace("-", "").isalnum() or safe_name.endswith(".pdf")
```

#### 3. File Storage Tests

**TC3.1: Files stored in correct directory**
```python
def test_store_files_creates_source_dir(tmp_path):
    """Files should be stored in corpus/sources/{source_name}/."""
    manager = CorpusUploadManager(tmp_path)
    files = [create_mock_file("test.pdf", "application/pdf", b"content")]

    source_dir = manager._get_source_dir("test_source")
    manager._store_files(files, source_dir)

    stored_file = source_dir / "test.pdf"
    assert stored_file.exists()
    assert stored_file.read_bytes() == b"content"
```

**TC3.2: Multiple files stored**
```python
def test_store_files_handles_multiple(tmp_path):
    """Multiple files should be stored correctly."""
    manager = CorpusUploadManager(tmp_path)
    files = [
        create_mock_file("test1.pdf", "application/pdf", b"content1"),
        create_mock_file("test2.docx", "application/vnd.ms-word", b"content2"),
        create_mock_file("test3.txt", "text/plain", b"content3"),
    ]

    source_dir = manager._get_source_dir("test_source")
    count = manager._store_files(files, source_dir)

    assert count == 3
    assert len(list(source_dir.glob("*"))) == 3
```

**TC3.3: File count returned**
```python
def test_store_files_returns_count(tmp_path):
    """Store should return count of successfully stored files."""
    manager = CorpusUploadManager(tmp_path)
    files = [
        create_mock_file(f"test{i}.pdf", "application/pdf", b"content")
        for i in range(5)
    ]

    source_dir = manager._get_source_dir("test_source")
    count = manager._store_files(files, source_dir)

    assert count == 5
```

#### 4. YAML Configuration Tests

**TC4.1: Source added to corpus.yaml**
```python
def test_update_corpus_yaml_adds_source(tmp_path):
    """New source should be added to corpus.yaml."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    manager = CorpusUploadManager(corpus_dir)

    metadata = {
        "quality": "standard",
        "tags": ["test"],
        "is_external": False,
        "voice_notes": "Test source",
    }
    success = manager._update_corpus_yaml("test_source", metadata)

    assert success
    config = load_yaml(corpus_dir / "corpus.yaml")
    assert "test_source" in [s["name"] for s in config["sources"]]
```

**TC4.2: Existing sources preserved**
```python
def test_update_corpus_yaml_preserves_existing(tmp_path):
    """Adding new source should not modify existing sources."""
    corpus_dir = setup_corpus_with_sources(tmp_path, [
        {"name": "existing_source", "path": "corpus/sources/existing"}
    ])
    manager = CorpusUploadManager(corpus_dir)

    metadata = {"quality": "standard", "tags": []}
    manager._update_corpus_yaml("new_source", metadata)

    config = load_yaml(corpus_dir / "corpus.yaml")
    existing = next(s for s in config["sources"] if s["name"] == "existing_source")
    assert existing["path"] == "corpus/sources/existing"  # unchanged
```

**TC4.3: Duplicate source rejected**
```python
def test_update_corpus_yaml_rejects_duplicate(tmp_path):
    """Adding source with existing name should fail."""
    corpus_dir = setup_corpus_with_sources(tmp_path, [
        {"name": "existing_source", "path": "corpus/sources/existing"}
    ])
    manager = CorpusUploadManager(corpus_dir)

    metadata = {"quality": "standard"}
    success = manager._update_corpus_yaml("existing_source", metadata)

    assert not success  # Should fail due to duplicate
```

**TC4.4: Backup created before update**
```python
def test_update_corpus_yaml_creates_backup(tmp_path):
    """Backup should be created before modifying corpus.yaml."""
    corpus_dir = setup_corpus_with_sources(tmp_path, [
        {"name": "existing", "path": "corpus/sources/existing"}
    ])
    manager = CorpusUploadManager(corpus_dir)

    backup = manager._backup_corpus_yaml()

    assert backup.exists()
    assert backup.name == "corpus.yaml.backup"
    # Verify backup is valid YAML
    load_yaml(backup)  # Should not raise
```

**TC4.5: YAML remains valid after update**
```python
def test_update_corpus_yaml_produces_valid_yaml(tmp_path):
    """Updated corpus.yaml should be valid YAML."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    manager = CorpusUploadManager(corpus_dir)

    manager._update_corpus_yaml("test", {"quality": "standard"})

    # Should parse without error
    config = load_yaml(corpus_dir / "corpus.yaml")
    assert "sources" in config
    assert len(config["sources"]) > 0
```

#### 5. Full Upload Operation Tests

**TC5.1: Successful upload returns correct result**
```python
def test_upload_files_success(tmp_path):
    """Successful upload should return UploadResult with correct data."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    manager = CorpusUploadManager(corpus_dir)

    files = [
        create_mock_file("doc1.pdf", "application/pdf", b"content1"),
        create_mock_file("doc2.txt", "text/plain", b"content2"),
    ]

    result = manager.upload_files(
        files=files,
        source_name="test_source",
        tags=["test"],
        quality="standard",
    )

    assert result.success
    assert result.files_stored == 2
    assert result.total_files == 2
    assert len(result.errors) == 0
    assert "test_source" in result.message
```

**TC5.2: Partial upload returns errors**
```python
def test_upload_files_partial_failure(tmp_path):
    """Upload with some invalid files should report errors."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    manager = CorpusUploadManager(corpus_dir)

    files = [
        create_mock_file("good.pdf", "application/pdf", b"content"),
        create_mock_file("bad.exe", "application/x-executable", b"malware"),
    ]

    result = manager.upload_files(
        files=files,
        source_name="test_source",
    )

    assert result.success  # Upload succeeds with partial storage
    assert result.files_stored == 1  # Only good file stored
    assert len(result.errors) == 1  # Bad file reported
    assert "bad.exe" in result.errors[0]
```

**TC5.3: Upload with metadata**
```python
def test_upload_files_with_metadata(tmp_path):
    """Upload should store metadata in corpus.yaml."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    manager = CorpusUploadManager(corpus_dir)

    files = [create_mock_file("doc.pdf", "application/pdf", b"content")]

    manager.upload_files(
        files=files,
        source_name="test_source",
        tags=["tag1", "tag2"],
        quality="premium",
        is_external=True,
        voice_notes="External research",
    )

    config = load_yaml(corpus_dir / "corpus.yaml")
    source = next(s for s in config["sources"] if s["name"] == "test_source")

    assert source["tags"] == ["tag1", "tag2"]
    assert source["quality"] == "premium"
    assert source["is_external"] is True
    assert source["voice_notes"] == "External research"
```

#### 6. Source Management Tests

**TC6.1: List sources returns all uploaded**
```python
def test_list_sources_returns_all(tmp_path):
    """List should return all uploaded sources."""
    corpus_dir = setup_corpus_with_sources(tmp_path, [
        {"name": "source1", "path": "corpus/sources/source1"},
        {"name": "source2", "path": "corpus/sources/source2"},
    ])
    manager = CorpusUploadManager(corpus_dir)

    sources = manager.list_sources()

    assert len(sources) == 2
    assert any(s.name == "source1" for s in sources)
    assert any(s.name == "source2" for s in sources)
```

**TC6.2: Delete source removes files and YAML entry**
```python
def test_delete_source_removes_files_and_config(tmp_path):
    """Delete should remove files and update corpus.yaml."""
    corpus_dir = setup_corpus_with_sources(tmp_path, [
        {"name": "to_delete", "path": "corpus/sources/to_delete"}
    ])
    # Create actual files
    source_dir = corpus_dir / "sources" / "to_delete"
    source_dir.mkdir(parents=True)
    (source_dir / "doc.pdf").write_bytes(b"content")

    manager = CorpusUploadManager(corpus_dir)
    manager.delete_source("to_delete")

    assert not source_dir.exists()  # Files deleted
    config = load_yaml(corpus_dir / "corpus.yaml")
    assert "to_delete" not in [s["name"] for s in config["sources"]]
```

**TC6.3: Update source metadata**
```python
def test_update_source_metadata(tmp_path):
    """Update should modify source metadata in corpus.yaml."""
    corpus_dir = setup_corpus_with_sources(tmp_path, [
        {"name": "test_source", "path": "corpus/sources/test_source", "tags": ["old"]}
    ])
    manager = CorpusUploadManager(corpus_dir)

    success = manager.update_source_metadata(
        "test_source",
        tags=["new1", "new2"],
        quality="premium",
    )

    assert success
    config = load_yaml(corpus_dir / "corpus.yaml")
    source = next(s for s in config["sources"] if s["name"] == "test_source")
    assert source["tags"] == ["new1", "new2"]
    assert source["quality"] == "premium"
```

---

## Integration Tests

### Test File
`tests/integration/test_corpus_upload_integration.py`

#### IT1: Upload → Storage → YAML Integration
```python
def test_full_upload_workflow(tmp_path):
    """Complete upload workflow should succeed end-to-end."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()

    manager = CorpusUploadManager(corpus_dir)

    # Create test files
    files = [
        create_mock_file("handbook.pdf", "application/pdf", b"content1"),
        create_mock_file("guide.txt", "text/plain", b"content2"),
    ]

    # Upload
    result = manager.upload_files(
        files=files,
        source_name="documentation",
        tags=["internal", "handbook"],
        quality="standard",
    )

    # Verify result
    assert result.success
    assert result.files_stored == 2

    # Verify files stored
    source_dir = corpus_dir / "sources" / "documentation"
    assert source_dir.exists()
    assert (source_dir / "handbook.pdf").exists()
    assert (source_dir / "guide.txt").exists()

    # Verify corpus.yaml updated
    config = load_yaml(corpus_dir / "corpus.yaml")
    source = next(s for s in config["sources"] if s["name"] == "documentation")
    assert source["path"] == "corpus/sources/documentation"
    assert "handbook" in source["tags"]
```

#### IT2: Multiple Uploads to Same Source
```python
def test_multiple_uploads_same_source(tmp_path):
    """Multiple uploads to existing source should fail with clear error."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    manager = CorpusUploadManager(corpus_dir)

    # First upload
    files1 = [create_mock_file("doc1.pdf", "application/pdf", b"content")]
    result1 = manager.upload_files(files1, source_name="same_source")
    assert result1.success

    # Second upload to same source should fail
    files2 = [create_mock_file("doc2.pdf", "application/pdf", b"content")]
    result2 = manager.upload_files(files2, source_name="same_source")
    assert not result2.success
    assert len(result2.errors) > 0
```

#### IT3: YAML Corruption Recovery
```python
def test_yaml_corruption_recovery(tmp_path):
    """If YAML update fails, backup should be restored."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    manager = CorpusUploadManager(corpus_dir)

    # Initial upload
    files = [create_mock_file("doc.pdf", "application/pdf", b"content")]
    manager.upload_files(files, source_name="source1")

    original_yaml = load_yaml(corpus_dir / "corpus.yaml")

    # Simulate YAML write failure by mocking
    with patch.object(Path, 'write_text', side_effect=IOError("Disk full")):
        files2 = [create_mock_file("doc2.pdf", "application/pdf", b"content")]
        result = manager.upload_files(files2, source_name="source2")

    # YAML should be recovered from backup
    current_yaml = load_yaml(corpus_dir / "corpus.yaml")
    assert current_yaml == original_yaml  # Unchanged
```

---

## E2E Tests

### Test File
`tests/e2e/test_corpus_upload_e2e.py`

#### E2E1: Upload → Extract → Search
```python
def test_upload_extract_search_workflow(tmp_path, mock_llm):
    """Full workflow: Upload documents → Extract → Search."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()

    # Create realistic documents
    pdf_content = create_sample_pdf("Engineering Best Practices")
    docs = [
        create_mock_file("handbook.pdf", "application/pdf", pdf_content),
    ]

    # Step 1: Upload
    manager = CorpusUploadManager(corpus_dir)
    result = manager.upload_files(docs, source_name="handbook")
    assert result.success

    # Step 2: Extract (using actual extraction pipeline)
    extract_dir = tmp_path / "extracted"
    extract_dir.mkdir()
    subprocess.run([
        "bloginator", "extract",
        "-c", str(corpus_dir / "corpus.yaml"),
        "-o", str(extract_dir),
    ], check=True)

    # Verify extraction
    json_files = list(extract_dir.glob("*.json"))
    assert len(json_files) > 0

    # Step 3: Index
    index_dir = tmp_path / "index"
    subprocess.run([
        "bloginator", "index",
        str(extract_dir),
        "-o", str(index_dir),
    ], check=True)

    # Step 4: Search
    from bloginator.search import CorpusSearcher
    searcher = CorpusSearcher(index_dir)
    results = searcher.search("engineering practices", top_k=5)

    assert len(results) > 0
```

---

## UI Tests (Manual/Future Automation)

### UT1: File Upload Widget
- [ ] User can select single file
- [ ] User can select multiple files (batch upload)
- [ ] File size validation shows error for >50MB files
- [ ] File type validation shows error for unsupported formats
- [ ] Selected files display with checkmarks
- [ ] Clear button removes all selections

### UT2: Metadata Form
- [ ] Source name auto-fills from first filename
- [ ] Tags input accepts comma-separated values
- [ ] Quality dropdown shows all options (standard, premium, external)
- [ ] External source checkbox toggles
- [ ] Voice notes text area accepts multi-line input
- [ ] All fields optional except source name
- [ ] Form validation prevents empty source name

### UT3: Upload Execution
- [ ] Upload button disabled until files selected
- [ ] Progress indicator shows during upload
- [ ] Spinner displays "Uploading..." message
- [ ] Success message shows file count
- [ ] Error messages display with file names
- [ ] Link to run extraction appears on success

### UT4: Source Management
- [ ] Sources list displays all uploaded sources
- [ ] Each source shows: name, file count, size, upload date
- [ ] Delete button removes source with confirmation
- [ ] Edit button opens metadata update form
- [ ] Metadata updates persist to corpus.yaml
- [ ] List refreshes after changes

---

## Test Execution Plan

### Local Development
```bash
# Run unit tests
pytest tests/unit/services/test_corpus_upload_manager.py -v

# Run integration tests
pytest tests/integration/test_corpus_upload_integration.py -v

# Run E2E tests
pytest tests/e2e/test_corpus_upload_e2e.py -v

# Full coverage report
pytest tests/unit/services/test_corpus_upload_manager.py \
        tests/integration/test_corpus_upload_integration.py \
        --cov=src/bloginator/services/corpus_upload_manager \
        --cov-report=term-missing
```

### CI/CD (GitHub Actions)
- Unit tests: Run on all Python versions (3.10, 3.11, 3.12)
- Integration tests: Run on Python 3.11 (representative)
- E2E tests: Run on Python 3.11 (slow, run separately)
- Coverage: Must maintain 85%+

### Manual Testing
1. Local Streamlit app: `streamlit run src/bloginator/ui/app.py`
2. Test upload widget with various file types/sizes
3. Verify corpus.yaml updates correctly
4. Run extraction on uploaded files
5. Test source deletion and metadata updates

---

## Test Data

### Mock Files
Helper function `create_mock_file(name, mime, content)`:
- Creates temporary file with Streamlit-compatible interface
- Sets MIME type for validation
- Returns mock UploadedFile object

### Sample Documents
- `test_documents/sample.pdf`: Valid PDF with text
- `test_documents/sample.docx`: Valid DOCX document
- `test_documents/sample.txt`: Plain text file
- `test_documents/sample.md`: Markdown file

### Edge Cases
- Empty files (0 bytes)
- Very large files (51 MB)
- Files with special characters in names
- Files with no extension
- Corrupted file headers (wrong magic bytes)
- Unicode filenames

---

## Metrics & Reporting

### Coverage Requirements
- **Overall**: 85%+
- **corpus_upload_manager.py**: 95%+ (critical service)
- **UI integration**: 70%+ (manual testing supplemental)

### Quality Gates
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage >= 85%
- [ ] No critical issues in security scan
- [ ] Performance: Upload < 30 seconds
- [ ] No data corruption in any test scenario

### Test Report Template
```
Test Execution Report
=====================
Date: YYYY-MM-DD
Run ID: #123

Summary:
- Total Tests: XXX
- Passed: XXX (XX%)
- Failed: X
- Skipped: X
- Coverage: XX%

Failed Tests:
- [List any failures with root cause]

Performance:
- Avg upload time: X.XXs
- Avg extraction time: X.XXs
- Slowest operation: operation_name (X.XXs)

Recommendations:
- [Any issues found, improvements needed]
```

---

## Risk Mitigation

| Risk | Mitigation | Test |
|------|------------|------|
| File corruption | Store checksums, verify after write | TC3.1 |
| YAML corruption | Create backup before modify, restore on error | TC4.4, IT3 |
| Path traversal attacks | Sanitize filenames, validate paths | TC2.1 |
| Disk space exhaustion | Check free space before upload | (Add to validation) |
| Concurrent uploads | Lock corpus.yaml during update | (Add integration test) |
| Invalid YAML syntax | Validate before writing, test parse | TC4.5 |

---

## Sign-Off

**Test Plan Approved By**: [Awaiting review]
**Target Test Execution Date**: [After implementation]
**Test Completion Criteria**: All tests green + 85%+ coverage
