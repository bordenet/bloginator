# Corpus Directory Import Feature Design

**Status**: Draft
**Date**: 2025-12-03
**Architecture**: Directory scanning service with UI integration

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI Layer                       │
│         (corpus.py: "Add Directory" tab + button)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Directory Scanner Service                     │
│  (new: corpus_directory_scanner.py)                         │
│  ├─ Directory validation & discovery                        │
│  ├─ File scanning & filtering                               │
│  ├─ Preview generation                                       │
│  └─ Source configuration                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌──────────────────────┐      ┌──────────────────────┐
│  Filesystem Access   │      │  corpus.yaml Manager │
│  (pathlib, os.walk)  │      │  (corpus_config.py)  │
└──────────────────────┘      └──────────────────────┘
```

---

## Component Breakdown

### 1. Streamlit UI Component
**File**: `src/bloginator/ui/_pages/corpus.py` (extend existing)

**Responsibilities**:
- Provide directory picker/path input
- Display scan results and file preview
- Collect optional source metadata
- Show import confirmation and results

**Key Functions**:
```python
def show_add_directory_section():
    """Show directory import interface."""

def render_directory_picker() -> str:
    """Get directory path from user."""

def render_file_preview(files: list[Path]) -> None:
    """Display paginated list of discoverable files."""

def render_import_form(file_count: int) -> dict:
    """Collect source metadata (name, tags, etc)."""
```

**UI Structure**:
- Button: "Add Directory Source"
- Modal/expander: Directory selection
  - Path input or file picker
  - "Scan" button to discover files
- Preview section (if files found)
  - File count by format
  - Paginated file list
  - File browser link
- Form section
  - Source name (auto-filled from dir name)
  - Tags, quality rating, voice notes
  - Recursion checkbox
  - Pattern filter (optional)
- Confirmation and results

### 2. Directory Scanner Service
**File**: `src/bloginator/services/corpus_directory_scanner.py` (NEW)

**Responsibilities**:
- Validate directory paths
- Discover supported document types
- Generate preview information
- Handle symlinks and permissions
- Create source configuration

**Public Interface**:
```python
class DirectoryScanner:
    """Scans directories for documents and generates corpus sources."""

    def __init__(self, max_depth: int = 10):
        """Initialize scanner.

        Args:
            max_depth: Maximum recursion depth (prevent infinite loops)
        """

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        pattern: str | None = None,
        follow_symlinks: bool = False,
    ) -> ScanResult:
        """Scan directory for supported documents.

        Args:
            directory: Directory to scan
            recursive: Whether to recurse into subdirectories
            pattern: Optional regex to filter filenames
            follow_symlinks: Whether to follow symlinks

        Returns:
            ScanResult with file list and statistics
        """

    def validate_directory(self, directory: Path) -> tuple[bool, str]:
        """Validate directory is accessible and readable.

        Returns:
            (is_valid, error_message)
        """

    def create_source_config(
        self,
        directory: Path,
        source_name: str,
        tags: list[str] | None = None,
        quality: str = "standard",
        is_external: bool = False,
        voice_notes: str = "",
        recursive: bool = True,
    ) -> SourceConfig:
        """Create source configuration from directory.

        Returns:
            SourceConfig ready to add to corpus.yaml
        """
```

**Data Classes**:
```python
@dataclass
class FileInfo:
    """Information about discovered file."""
    path: Path
    format: str  # pdf, docx, txt, md
    size: int
    readable: bool

@dataclass
class ScanResult:
    """Result of directory scan."""
    directory: Path
    total_files: int
    files: list[FileInfo]
    by_format: dict[str, int]  # { "pdf": 5, "docx": 2, ... }
    total_size: int
    is_valid: bool
    error: str | None
    scan_time: float

@dataclass
class SourceConfig:
    """Configuration for corpus source."""
    name: str
    path: str  # Stored path (may be relative)
    enabled: bool
    quality: str
    tags: list[str]
    is_external: bool
    voice_notes: str
    recursive: bool
    file_count: int  # From scan
```

**Internal Methods**:
```python
def _validate_path(self, path: Path) -> bool:
    """Check path exists and is readable."""

def _is_supported_format(self, filename: str) -> bool:
    """Check if file format is supported."""

def _walk_directory(
    self,
    directory: Path,
    recursive: bool,
    pattern: str | None,
    follow_symlinks: bool,
    depth: int = 0,
) -> list[FileInfo]:
    """Recursively walk directory and collect files."""

def _detect_symlink_loops(self, path: Path) -> bool:
    """Detect if following symlink would create loop."""

def _normalize_path(self, directory: Path) -> Path:
    """Normalize path (resolve symlinks, absolute, etc)."""

def _format_path_for_config(self, directory: Path) -> str:
    """Format path for storage in corpus.yaml."""
```

### 3. YAML Configuration Extension
**File**: `src/bloginator/corpus_config.py` (extend existing)

**New Methods**:
```python
class CorpusConfig:

    def add_directory_source(
        self,
        name: str,
        path: str,
        enabled: bool = True,
        quality: str = "standard",
        is_external: bool = False,
        tags: list[str] | None = None,
        voice_notes: str = "",
        recursive: bool = True,
    ) -> bool:
        """Add directory source to corpus.yaml."""

    def source_path_exists(self, path: str) -> bool:
        """Check if directory path already exists in corpus."""
```

---

## Data Flow

### Directory Import Flow
```
1. User clicks "Add Directory" button
   ↓
2. Streamlit shows directory picker or path input
   ↓
3. User selects/enters directory path
   ↓
4. User clicks "Scan" button
   ↓
5. DirectoryScanner.scan_directory() runs
   ├─ Validate path
   ├─ Walk directory (with recursion)
   ├─ Filter by format
   ├─ Check permissions
   └─ Collect statistics
   ↓
6. Display preview
   ├─ File count by format
   ├─ Total size
   ├─ Paginated file list
   └─ Warnings (if any)
   ↓
7. User reviews and enters metadata
   ├─ Source name (auto-filled)
   ├─ Tags
   ├─ Quality rating
   └─ Voice notes
   ↓
8. User clicks "Import" button
   ↓
9. Check for conflicts in corpus.yaml
   ├─ If conflict: show warning and options
   └─ If clear: proceed
   ↓
10. Create source configuration
    ├─ Normalize path
    ├─ Store recursive flag
    └─ Record file count
    ↓
11. Update corpus.yaml
    ├─ Backup existing
    ├─ Add new source entry
    ├─ Validate YAML
    └─ Write file
    ↓
12. Display results
    ├─ Success message with file count
    ├─ Link to run extraction
    └─ Option to import another directory
```

---

## Configuration Structure

### Directory Source in corpus.yaml
```yaml
sources:
  - name: "Engineering Documentation"
    path: "/home/user/documents/engineering"  # Or relative: "documents/engineering"
    enabled: true
    quality: standard
    is_external: false
    tags:
      - engineering
      - internal
    voice_notes: "Local documentation collected from team"

    # NEW: Directory-specific metadata
    type: directory                     # Distinguish from uploaded sources
    recursive: true                     # Whether to recurse subdirs
    discovered_at: "2025-12-03T14:30:00Z"  # When directory was added
    file_count: 127                     # Snapshot of file count at discovery
```

### Extraction Pipeline Compatibility
- Extraction pipeline reads `path` field exactly as-is
- Supports both:
  - Directories (directory source): Find all supported files
  - Specific files (uploaded): Single file or file list
- Already supports filesystem paths via `corpus/sources/`

---

## Error Handling

### Validation Errors
| Error | Handling | User Message |
|-------|----------|--------------|
| Directory not found | Reject | "Directory not found: {path}" |
| Permission denied | Reject | "Cannot read directory: Permission denied" |
| Empty directory | Warn but allow | "Directory contains no supported documents" |
| Path is file not dir | Reject | "Path is a file, not a directory" |
| Symlink loop detected | Skip | "Skipping symlink (would create loop)" |
| Too many files | Warn | "Directory has {count} files, preview may be slow" |
| Path already in corpus | Warn | "Path already exists as source: {name}" |

### Recovery
- All YAML modifications create backup first
- Failed operations don't modify corpus.yaml
- Clear error messages guide user action

---

## Security Considerations

### Path Validation
- Check path is absolute or resolve relative to project root
- Verify path is readable and is a directory
- Detect and prevent symlink loops
- Optional: restrict to certain base directories

### Symlink Handling
- Don't follow symlinks by default (follow_symlinks=False)
- Detect loops to prevent infinite recursion
- Log when symlinks are encountered
- Option to follow selectively (Phase 2)

### File Access
- Check each file is readable before reporting
- Handle permission errors gracefully
- Never execute any files
- Treat all as data

---

## Testing Strategy

### Unit Tests
- Path validation (exists, readable, directory)
- Format detection (by extension + magic bytes)
- Recursion logic (depth limiting, symlink detection)
- File filtering (patterns, hidden files)
- Configuration creation

### Integration Tests
- Full scan→config→yaml workflow
- Large directory handling (1000+ files)
- Mixed file formats
- Symlink handling
- Permission denied scenarios

### E2E Tests
- Directory import → Extract → Search workflow
- Multiple directory sources
- Recursive vs non-recursive scanning
- Verify extraction finds files from imported directories

---

## Implementation Phases

### Phase 1 (Core)
- DirectoryScanner service with validation and scanning
- UI with path input and basic preview
- Configuration generation and YAML updates
- Error handling and recovery

### Phase 2 (Enhancements)
- Advanced file filtering (regex patterns)
- Symlink following options
- Directory watching for changes (auto-reindex)
- Selective file inclusion

### Phase 3 (Advanced)
- Network path support (SMB, NFS)
- Cloud storage integration
- Directory versioning

---

## Rollback Plan

If directory import causes issues:
1. Remove "Add Directory" button/section from UI
2. Users continue using manual YAML editing or file uploads
3. Keep DirectoryScanner service for future use
4. No data loss (only corpus.yaml entries, which are backed up)

---

## Dependencies Added

### New External Dependencies
- None (uses Python standard library)

### New Internal Dependencies
- `corpus_config.CorpusConfig` (extend existing)
- Standard library: `pathlib`, `os`, `re` (pattern matching)

### Modified Files
- `src/bloginator/ui/_pages/corpus.py` (extend)
- `src/bloginator/corpus_config.py` (add methods)

### New Files
- `src/bloginator/services/corpus_directory_scanner.py` (NEW)
- `tests/unit/services/test_corpus_directory_scanner.py` (NEW)
- `tests/integration/test_corpus_directory_integration.py` (NEW)

---

## Configuration

### Environment Variables (optional)
- `BLOGINATOR_DIRECTORY_MAX_DEPTH`: Max recursion depth (default: 10)
- `BLOGINATOR_DIRECTORY_MAX_FILES`: Warn if exceeded (default: 5000)
- `BLOGINATOR_FOLLOW_SYMLINKS`: Follow symlinks by default (default: false)

---

## Success Criteria

- [ ] Users can add directory sources without manual YAML editing
- [ ] Directory scanning completes in <5 seconds for 1000+ files
- [ ] All discoverable documents are identified accurately
- [ ] Corpus.yaml properly updated with directory references
- [ ] Extraction pipeline finds and processes directory documents
- [ ] No data loss or corruption on failed imports
- [ ] Clear error messages for all failure scenarios
