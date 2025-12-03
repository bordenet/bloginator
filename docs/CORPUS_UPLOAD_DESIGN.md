# Corpus Upload Feature Design

**Status**: Draft
**Date**: 2025-12-03
**Architecture**: Component-based with separation of concerns

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI Layer                       │
│  (corpus.py: "Add Sources" tab + "Manage Sources" section)  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Upload Manager Service                     │
│  (new: corpus_upload_manager.py)                            │
│  ├─ File validation & storage                              │
│  ├─ YAML configuration management                           │
│  └─ Source metadata handling                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌──────────────────────┐      ┌──────────────────────┐
│  Filesystem Storage  │      │  corpus.yaml Manager │
│  (corpus/sources/)   │      │  (corpus_config.py)  │
└──────────────────────┘      └──────────────────────┘
```

---

## Component Breakdown

### 1. Streamlit UI Component
**File**: `src/bloginator/ui/_pages/corpus.py` (extend existing)

**Responsibilities**:
- Display upload widget
- Collect metadata via forms
- Show upload progress and results
- Display source management UI
- Call UploadManager service

**Key Functions**:
```python
def show_add_sources_tab():
    """Show file upload and metadata collection interface."""

def show_manage_sources_section():
    """Show uploaded sources with delete/edit options."""

def render_upload_form(uploaded_files: list) -> dict:
    """Render metadata form for uploaded files."""
```

**UI Structure**:
- Tab 1: Extract (existing)
- Tab 2: Index (existing)
- Tab 3: Add Sources (NEW)
  - File uploader widget
  - Metadata form (source name, tags, quality, notes)
  - Upload button
  - Progress/results display
- Tab 4: Manage Sources (NEW)
  - Table of uploaded sources
  - Delete buttons
  - Edit metadata modal

### 2. Upload Manager Service
**File**: `src/bloginator/services/corpus_upload_manager.py` (NEW)

**Responsibilities**:
- Validate uploaded files
- Store files in corpus/sources/
- Update corpus.yaml with new source
- Handle errors gracefully
- Provide progress tracking

**Public Interface**:
```python
class CorpusUploadManager:
    """Manages document uploads and corpus configuration."""

    def __init__(self, corpus_dir: Path = Path("corpus")):
        """Initialize with corpus base directory."""
        self.corpus_dir = corpus_dir
        self.sources_dir = corpus_dir / "sources"
        self.config_path = corpus_dir / "corpus.yaml"

    def upload_files(
        self,
        files: list[UploadedFile],
        source_name: str,
        tags: list[str] | None = None,
        quality: str = "standard",
        is_external: bool = False,
        voice_notes: str = "",
    ) -> UploadResult:
        """Upload files and add source to corpus.yaml.

        Args:
            files: List of uploaded Streamlit file objects
            source_name: Human-readable name for source
            tags: Optional tags for categorization
            quality: Quality rating (external, premium, standard)
            is_external: Whether source is external (vs internal)
            voice_notes: Optional notes about source

        Returns:
            UploadResult with status, file count, errors
        """

    def list_sources(self) -> list[SourceInfo]:
        """List all uploaded sources."""

    def delete_source(self, source_name: str) -> bool:
        """Delete source from disk and corpus.yaml."""

    def update_source_metadata(
        self,
        source_name: str,
        tags: list[str] | None = None,
        quality: str | None = None,
        voice_notes: str | None = None,
    ) -> bool:
        """Update source metadata in corpus.yaml."""
```

**Internal Methods**:
```python
def _validate_files(self, files: list) -> tuple[list, list]:
    """Validate file types and sizes.

    Returns:
        (valid_files, error_messages)
    """

def _sanitize_filename(self, filename: str) -> str:
    """Remove unsafe characters from filename."""

def _get_source_dir(self, source_name: str) -> Path:
    """Get or create source directory."""

def _store_files(self, files: list, source_dir: Path) -> int:
    """Store files in source directory.

    Returns:
        Count of successfully stored files
    """

def _update_corpus_yaml(
    self,
    source_name: str,
    metadata: dict,
) -> bool:
    """Add/update source entry in corpus.yaml."""

def _backup_corpus_yaml(self) -> Path:
    """Create backup of corpus.yaml before modification."""
```

**Data Classes**:
```python
@dataclass
class UploadResult:
    """Result of upload operation."""
    success: bool
    source_name: str
    files_stored: int
    total_files: int
    errors: list[str]
    message: str

@dataclass
class SourceInfo:
    """Information about uploaded source."""
    name: str
    path: str
    file_count: int
    total_size: int
    upload_date: str
    tags: list[str]
    quality: str
    is_external: bool
    voice_notes: str
```

### 3. YAML Configuration Management
**File**: `src/bloginator/corpus_config.py` (extend existing)

**New Methods**:
```python
class CorpusConfig:

    def add_source(
        self,
        name: str,
        path: str,
        enabled: bool = True,
        quality: str = "standard",
        is_external: bool = False,
        tags: list[str] | None = None,
        voice_notes: str = "",
    ) -> bool:
        """Add source to corpus.yaml.

        Raises:
            ValueError: If source already exists
        """

    def update_source(
        self,
        name: str,
        quality: str | None = None,
        tags: list[str] | None = None,
        voice_notes: str | None = None,
    ) -> bool:
        """Update existing source metadata."""

    def remove_source(self, name: str) -> bool:
        """Remove source from corpus.yaml."""

    def get_source(self, name: str) -> dict | None:
        """Retrieve source configuration."""

    def source_exists(self, name: str) -> bool:
        """Check if source already exists."""
```

---

## Data Flow

### Upload Flow
```
1. User selects files via st.file_uploader()
   ↓
2. User fills metadata form
   ├─ Source name (auto-filled from filename)
   ├─ Tags (optional)
   ├─ Quality rating (default: standard)
   ├─ Is external (default: false)
   └─ Voice notes (optional)
   ↓
3. User clicks "Upload" button
   ↓
4. Streamlit UI calls CorpusUploadManager.upload_files()
   ↓
5. Manager validates files
   ├─ Check file size (< 50MB)
   ├─ Check file type (magic bytes)
   └─ Sanitize filenames
   ↓
6. Manager stores files
   ├─ Create corpus/sources/{source_name}/ directory
   ├─ Write each file to directory
   └─ Track success/errors
   ↓
7. Manager updates corpus.yaml
   ├─ Backup existing corpus.yaml
   ├─ Add new source entry
   ├─ Validate YAML syntax
   └─ Write updated file
   ↓
8. Return UploadResult to UI
   ↓
9. UI displays results
   ├─ Success message with file count
   ├─ Link to run extraction
   └─ Any error messages
```

### Delete Source Flow
```
1. User clicks delete button for source
   ↓
2. Confirm dialog ("Delete 'source_name' and X files?")
   ↓
3. User confirms
   ↓
4. Manager deletes files and directories
   ├─ Backup corpus.yaml
   ├─ Remove source directory from corpus/sources/
   ├─ Remove source entry from corpus.yaml
   └─ Validate YAML
   ↓
5. UI refreshes source list
```

---

## File Storage Structure

### Directory Layout
```
corpus/
├── corpus.yaml          # Main config (updated by upload manager)
├── corpus.yaml.backup   # Auto-backup before modifications
├── sources/             # User-uploaded sources (NEW)
│   ├── source_1/
│   │   ├── document_1.pdf
│   │   ├── document_2.docx
│   │   └── document_3.txt
│   └── source_2/
│       └── whitepaper.md
└── README.md
```

### corpus.yaml Format
```yaml
sources:
  - name: "Engineering Handbook"
    path: "corpus/sources/engineering_handbook"
    enabled: true
    quality: standard
    is_external: false
    tags:
      - engineering
      - best-practices
    voice_notes: "Company internal documentation"
    upload_date: "2025-12-03T14:30:00Z"  # NEW
    file_count: 3                         # NEW (auto-calculated)

  - name: "Remote Work Guide"
    path: "corpus/sources/remote_work_guide"
    enabled: true
    quality: premium
    is_external: true
    tags:
      - remote
      - management
    voice_notes: "External research on remote work best practices"
    upload_date: "2025-12-03T15:45:00Z"
    file_count: 1
```

---

## Error Handling

### Validation Errors
| Error | Handling | User Message |
|-------|----------|--------------|
| File too large (>50MB) | Reject file | "File '{name}' is too large (>{size}MB). Max: 50MB." |
| Invalid file type | Reject file | "File '{name}' is not supported. Accepted: PDF, DOCX, TXT, MD." |
| Empty file | Reject file | "File '{name}' is empty." |
| Invalid filename | Sanitize | Filename auto-corrected (logged) |
| Source already exists | Check YAML | "Source '{name}' already exists. Use different name or delete first." |
| YAML update fails | Restore backup | "Could not update configuration. Restored backup. Please try again." |
| Disk space full | Catch exception | "Not enough disk space to store files." |

### Recovery
- All YAML modifications create backup first
- Failed uploads don't leave partial files
- Failed YAML updates restore previous version
- Clear error messages guide user action

---

## Security Considerations

### File Upload Security
- **File Type Validation**: Check magic bytes, not just extension
  ```python
  # Check PDF magic bytes (FF D8 FF)
  # Check DOCX magic bytes (PK - ZIP format)
  # Check TXT/MD as plaintext
  ```
- **Filename Sanitization**: Remove path traversal attempts
  ```python
  # Remove: / \ : * ? " < > |
  # Convert to: filename-safe version
  ```
- **Permissions**: Store files with restricted access (0o644)
- **No Execution**: Treat all files as data, never execute

### YAML Security
- **Validation**: Parse YAML before writing to file
- **Atomic Writes**: Write to temp file, then move (no corruption)
- **Backups**: Keep previous version for recovery

---

## Testing Strategy

### Unit Tests
- File validation (size, type, name sanitization)
- YAML add/update/remove operations
- Error handling and recovery
- Directory creation and cleanup

### Integration Tests
- Full upload flow (file + YAML)
- Concurrent uploads
- Source deletion
- Metadata updates

### UI Tests (Manual)
- File upload widget interaction
- Metadata form validation
- Error message display
- Source management UI

### E2E Tests
- Upload files → Extract → Index full workflow
- Verify uploaded files appear in extraction
- Verify corpus.yaml is valid after operations

---

## Implementation Phases

### Phase 1 (Core Functionality)
- UploadManager service with file storage
- Basic YAML integration
- Streamlit UI with upload widget
- Error handling and messages

### Phase 2 (Management)
- List/delete/edit sources UI
- Metadata updates
- Source statistics (file count, size)
- Upload history/logs

### Phase 3 (Enhancements)
- Batch operations (multi-source upload)
- Source versioning
- Integration with extraction pipeline
- Advanced validation (duplicate detection)

---

## Rollback Plan

If upload feature causes issues:
1. Remove "Add Sources" and "Manage Sources" tabs
2. Users use manual YAML editing fallback
3. Keep UploadManager service for future use
4. No data loss (files remain in corpus/sources/)

---

## Dependencies Added

### New External Dependencies
- None (uses Streamlit built-ins)

### New Internal Dependencies
- `corpus_config.CorpusConfig` (extend existing)
- Standard library: `pathlib`, `mimetypes`, `yaml`

### Modified Files
- `src/bloginator/ui/_pages/corpus.py` (extend)
- `src/bloginator/corpus_config.py` (add methods)

### New Files
- `src/bloginator/services/corpus_upload_manager.py` (NEW)
- `tests/unit/services/test_corpus_upload_manager.py` (NEW)
- `tests/integration/test_corpus_upload_e2e.py` (NEW)

---

## Configuration

### Environment Variables (optional)
- `BLOGINATOR_UPLOAD_MAX_SIZE`: Max file size in MB (default: 50)
- `BLOGINATOR_UPLOAD_BATCH_LIMIT`: Max files per upload (default: 20)

### User Preferences
- Upload location: `corpus/sources/` (fixed, no configuration needed initially)
- Auto-extract: Option to auto-run extraction after upload (Phase 2)

---

## Success Criteria (Acceptance)

- [ ] Users can upload files without editing YAML
- [ ] Metadata is collected and stored in corpus.yaml
- [ ] All uploaded files are accessible to extraction pipeline
- [ ] No data corruption or loss
- [ ] Clear error messages for all failure scenarios
- [ ] Upload completes in <30 seconds for typical scenarios
