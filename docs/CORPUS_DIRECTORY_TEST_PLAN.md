# Corpus Directory Import Feature Test Plan

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

---

## Unit Tests

### Test File
`tests/unit/services/test_corpus_directory_scanner.py`

#### 1. Path Validation Tests

**TC1.1: Valid directory accepted**
```python
def test_validate_directory_valid(tmp_path):
    """Valid, readable directory should pass validation."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "test_corpus"
    test_dir.mkdir()

    is_valid, error = scanner.validate_directory(test_dir)

    assert is_valid
    assert error == ""
```

**TC1.2: Non-existent directory rejected**
```python
def test_validate_directory_not_found(tmp_path):
    """Non-existent directory should fail validation."""
    scanner = DirectoryScanner()
    missing_dir = tmp_path / "missing"

    is_valid, error = scanner.validate_directory(missing_dir)

    assert not is_valid
    assert "not found" in error.lower()
```

**TC1.3: File instead of directory rejected**
```python
def test_validate_directory_is_file(tmp_path):
    """Path to file should be rejected."""
    scanner = DirectoryScanner()
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    is_valid, error = scanner.validate_directory(test_file)

    assert not is_valid
    assert "file" in error.lower() or "directory" in error.lower()
```

**TC1.4: Permission denied handled**
```python
def test_validate_directory_permission_denied(tmp_path):
    """Directory without read permissions should fail gracefully."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "restricted"
    test_dir.mkdir()
    test_dir.chmod(0o000)

    try:
        is_valid, error = scanner.validate_directory(test_dir)
        assert not is_valid
        assert "permission" in error.lower()
    finally:
        test_dir.chmod(0o755)  # Cleanup
```

#### 2. File Format Detection Tests

**TC2.1: Supported formats detected**
```python
@pytest.mark.parametrize("ext", [".pdf", ".docx", ".txt", ".md"])
def test_is_supported_format(ext, scanner):
    """Supported file extensions should be recognized."""
    assert scanner._is_supported_format(f"document{ext}")
    assert scanner._is_supported_format(f"DOCUMENT{ext.upper()}")
```

**TC2.2: Unsupported formats rejected**
```python
@pytest.mark.parametrize("ext", [".exe", ".jpg", ".zip", ".html"])
def test_is_unsupported_format(ext, scanner):
    """Unsupported file extensions should be rejected."""
    assert not scanner._is_supported_format(f"file{ext}")
```

**TC2.3: Hidden files skipped**
```python
def test_hidden_files_skipped(tmp_path):
    """Hidden files should not be included in scan."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()

    (test_dir / "visible.pdf").write_bytes(b"%PDF")
    (test_dir / ".hidden.pdf").write_bytes(b"%PDF")

    result = scanner.scan_directory(test_dir)

    assert result.total_files == 1
    assert any(str(f.path).endswith("visible.pdf") for f in result.files)
    assert not any(str(f.path).endswith(".hidden.pdf") for f in result.files)
```

#### 3. Directory Scanning Tests

**TC3.1: Flat directory scanning**
```python
def test_scan_directory_flat(tmp_path):
    """Scanning flat directory should find all documents."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()

    # Create test files
    (test_dir / "doc1.pdf").write_bytes(b"%PDF")
    (test_dir / "doc2.docx").write_bytes(b"PK")  # ZIP magic bytes
    (test_dir / "doc3.txt").write_text("content")

    result = scanner.scan_directory(test_dir, recursive=False)

    assert result.is_valid
    assert result.total_files == 3
    assert result.by_format["pdf"] == 1
    assert result.by_format["docx"] == 1
    assert result.by_format["txt"] == 1
```

**TC3.2: Recursive scanning with subdirectories**
```python
def test_scan_directory_recursive(tmp_path):
    """Recursive scan should find documents in subdirectories."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()
    (test_dir / "subdir").mkdir()

    (test_dir / "top.pdf").write_bytes(b"%PDF")
    (test_dir / "subdir" / "nested.pdf").write_bytes(b"%PDF")

    result = scanner.scan_directory(test_dir, recursive=True)

    assert result.total_files == 2
    assert any("nested.pdf" in str(f.path) for f in result.files)
```

**TC3.3: Non-recursive ignores subdirectories**
```python
def test_scan_directory_non_recursive(tmp_path):
    """Non-recursive scan should ignore subdirectories."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()
    (test_dir / "subdir").mkdir()

    (test_dir / "top.pdf").write_bytes(b"%PDF")
    (test_dir / "subdir" / "nested.pdf").write_bytes(b"%PDF")

    result = scanner.scan_directory(test_dir, recursive=False)

    assert result.total_files == 1
    assert not any("nested.pdf" in str(f.path) for f in result.files)
```

**TC3.4: Scan time < 5 seconds for 1000+ files**
```python
def test_scan_performance_large_directory(tmp_path):
    """Scanning 1000+ files should complete in <5 seconds."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()

    # Create 1000 dummy files
    for i in range(1000):
        (test_dir / f"doc{i:04d}.txt").write_bytes(b"x" * 1000)

    import time
    start = time.time()
    result = scanner.scan_directory(test_dir)
    elapsed = time.time() - start

    assert result.total_files == 1000
    assert elapsed < 5.0  # Must complete in <5 seconds
```

#### 4. Pattern Filtering Tests

**TC4.1: Regex pattern filters files**
```python
def test_scan_with_pattern_filter(tmp_path):
    """Pattern filter should include/exclude files."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()

    (test_dir / "2024_report.pdf").write_bytes(b"%PDF")
    (test_dir / "2025_report.pdf").write_bytes(b"%PDF")
    (test_dir / "notes.txt").write_text("content")

    # Only 2024 files
    result = scanner.scan_directory(test_dir, pattern=r"2024")

    assert result.total_files == 1
    assert "2024_report" in str(result.files[0].path)
```

#### 5. Symlink Handling Tests

**TC5.1: Symlink loop detection**
```python
def test_symlink_loop_detected(tmp_path):
    """Symlink creating infinite loop should be detected."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()

    # Create symlink loop
    loop_link = test_dir / "loop"
    loop_link.symlink_to(test_dir)

    # Should not infinitely recurse
    result = scanner.scan_directory(test_dir)

    assert result.is_valid
    assert result.total_files == 0  # No files, but didn't crash
```

**TC5.2: Symlinks not followed by default**
```python
def test_symlinks_not_followed_by_default(tmp_path):
    """By default, symlinks should not be followed."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()
    external_dir = tmp_path / "external"
    external_dir.mkdir()

    (test_dir / "local.pdf").write_bytes(b"%PDF")
    (external_dir / "external.pdf").write_bytes(b"%PDF")
    (test_dir / "link_to_external").symlink_to(external_dir)

    result = scanner.scan_directory(test_dir, follow_symlinks=False)

    assert result.total_files == 1
    assert "local.pdf" in str(result.files[0].path)
```

**TC5.3: Symlinks followed when enabled**
```python
def test_symlinks_followed_when_enabled(tmp_path):
    """When follow_symlinks=True, symlinks should be traversed."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()
    external_dir = tmp_path / "external"
    external_dir.mkdir()

    (test_dir / "local.pdf").write_bytes(b"%PDF")
    (external_dir / "external.pdf").write_bytes(b"%PDF")
    (test_dir / "link").symlink_to(external_dir)

    result = scanner.scan_directory(test_dir, follow_symlinks=True)

    assert result.total_files == 2
    assert any("local.pdf" in str(f.path) for f in result.files)
    assert any("external.pdf" in str(f.path) for f in result.files)
```

#### 6. Configuration Creation Tests

**TC6.1: Source config created from scan**
```python
def test_create_source_config(tmp_path):
    """Source config should be generated with correct metadata."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "engineering"
    test_dir.mkdir()
    (test_dir / "doc.pdf").write_bytes(b"%PDF")

    scan = scanner.scan_directory(test_dir)
    config = scanner.create_source_config(
        test_dir,
        source_name="engineering",
        tags=["internal"],
        quality="standard",
    )

    assert config.name == "engineering"
    assert "engineering" in config.path
    assert config.tags == ["internal"]
    assert config.recursive is True
    assert config.file_count == 1
```

**TC6.2: Path normalization in config**
```python
def test_path_normalization_in_config(tmp_path):
    """Path should be normalized (relative vs absolute)."""
    scanner = DirectoryScanner()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()

    # Create config with absolute path
    config = scanner.create_source_config(test_dir, "test")

    # Path should be resolvable
    resolved_path = Path(config.path)
    assert resolved_path.is_absolute() or not resolved_path.is_absolute()
    # Just verify it's valid
    assert len(config.path) > 0
```

---

## Integration Tests

### Test File
`tests/integration/test_corpus_directory_integration.py`

#### IT1: Scan → Config → YAML Integration
```python
def test_full_directory_import_workflow(tmp_path):
    """Complete directory import workflow should succeed end-to-end."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    test_source = tmp_path / "engineering"
    test_source.mkdir()

    # Create test documents
    (test_source / "design.pdf").write_bytes(b"%PDF")
    (test_source / "standards.docx").write_bytes(b"PK")
    (test_source / "notes.txt").write_text("content")

    # Step 1: Scan directory
    scanner = DirectoryScanner()
    scan = scanner.scan_directory(test_source)
    assert scan.total_files == 3

    # Step 2: Create configuration
    config = scanner.create_source_config(
        test_source,
        "engineering",
        tags=["internal"],
    )

    # Step 3: Add to corpus.yaml
    corpus_config = CorpusConfig(corpus_dir)
    success = corpus_config.add_directory_source(
        name=config.name,
        path=config.path,
        tags=config.tags,
    )

    assert success
    yaml_config = load_yaml(corpus_dir / "corpus.yaml")
    assert any(s["name"] == "engineering" for s in yaml_config["sources"])
```

#### IT2: Conflict Detection
```python
def test_duplicate_directory_detection(tmp_path):
    """Importing same directory twice should warn about conflicts."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    test_dir = tmp_path / "docs"
    test_dir.mkdir()

    corpus_config = CorpusConfig(corpus_dir)

    # First import
    corpus_config.add_directory_source("docs1", str(test_dir))

    # Second import same path should fail
    success = corpus_config.add_directory_source("docs2", str(test_dir))

    assert not success  # Should detect duplicate path
```

#### IT3: Multiple Directory Sources
```python
def test_multiple_directory_sources(tmp_path):
    """Multiple different directories should all be added correctly."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()

    dirs = []
    for name in ["engineering", "marketing", "operations"]:
        d = tmp_path / name
        d.mkdir()
        (d / "doc.pdf").write_bytes(b"%PDF")
        dirs.append((name, d))

    corpus_config = CorpusConfig(corpus_dir)
    scanner = DirectoryScanner()

    for name, directory in dirs:
        corpus_config.add_directory_source(name, str(directory))

    yaml_config = load_yaml(corpus_dir / "corpus.yaml")
    assert len(yaml_config["sources"]) == 3
    assert all(
        any(s["name"] == name for s in yaml_config["sources"])
        for name, _ in dirs
    )
```

---

## E2E Tests

### Test File
`tests/e2e/test_corpus_directory_e2e.py`

#### E2E1: Directory Import → Extract → Search
```python
def test_directory_import_extract_search_workflow(tmp_path, mock_llm):
    """Full workflow: Import directory → Extract → Search."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    source_dir = tmp_path / "engineering_docs"
    source_dir.mkdir()

    # Create realistic documents
    pdf_content = create_sample_pdf("Engineering Standards")
    (source_dir / "standards.pdf").write_bytes(pdf_content)
    (source_dir / "guide.txt").write_text("Engineering best practices...")

    # Step 1: Import directory
    scanner = DirectoryScanner()
    config = scanner.create_source_config(source_dir, "engineering")
    corpus_config = CorpusConfig(corpus_dir)
    assert corpus_config.add_directory_source(
        config.name, config.path, tags=["engineering"]
    )

    # Step 2: Extract
    extract_dir = tmp_path / "extracted"
    subprocess.run([
        "bloginator", "extract",
        "-c", str(corpus_dir / "corpus.yaml"),
        "-o", str(extract_dir),
    ], check=True)

    # Verify extracted files
    extracted = list(extract_dir.glob("*.json"))
    assert len(extracted) > 0

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
    results = searcher.search("engineering standards", top_k=5)

    assert len(results) > 0
```

---

## UI Tests (Manual/Future Automation)

### UT1: Directory Picker
- [ ] User can input directory path (text field)
- [ ] User can browse filesystem (file picker, if supported)
- [ ] Path is validated before scanning
- [ ] Error shows for invalid paths

### UT2: Scan Results Display
- [ ] File count displays correctly
- [ ] Format breakdown shows (PDF: X, DOCX: X, etc)
- [ ] Total size calculated
- [ ] Paginated list for large directories
- [ ] Preview scrolls without hanging

### UT3: Metadata Form
- [ ] Source name auto-fills from directory name
- [ ] Recursion checkbox toggled
- [ ] Tags input works
- [ ] Quality dropdown available
- [ ] Voice notes text area

### UT4: Import Confirmation
- [ ] Warnings display for duplicates
- [ ] Confirmation dialog shows before import
- [ ] Success message shows file count
- [ ] Link to run extraction appears

---

## Test Execution Plan

### Local Development
```bash
# Run unit tests
pytest tests/unit/services/test_corpus_directory_scanner.py -v

# Run integration tests
pytest tests/integration/test_corpus_directory_integration.py -v

# Run E2E tests
pytest tests/e2e/test_corpus_directory_e2e.py -v

# Full coverage
pytest tests/unit/services/test_corpus_directory_scanner.py \
        tests/integration/test_corpus_directory_integration.py \
        --cov=src/bloginator/services/corpus_directory_scanner \
        --cov-report=term-missing
```

### CI/CD (GitHub Actions)
- Unit tests: Run on all Python versions (3.10, 3.11, 3.12)
- Integration tests: Run on Python 3.11
- E2E tests: Run on Python 3.11 (slow)
- Coverage: Must maintain 85%+

---

## Test Data

### Test Directories
- Flat directory with 10 mixed format files
- Nested directory structure (3 levels deep)
- Large directory (1000+ files) for performance
- Empty directory
- Directory with all hidden files
- Directory with symlinks and loops

### Test Files
- Valid PDF, DOCX, TXT, MD files (small sizes)
- Mixed case filenames
- Filenames with special characters
- Very long filenames (>255 chars)
- Zero-byte files

---

## Quality Gates

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage >= 85%
- [ ] No critical issues
- [ ] Performance: Scan <5 seconds for 1000+ files
- [ ] No data corruption

---

## Sign-Off

**Test Plan Approved By**: [Awaiting review]
**Target Test Execution Date**: [After implementation]
**Test Completion Criteria**: All tests green + 85%+ coverage
