# Corpus Upload Feature Requirements

**Status**: Draft
**Date**: 2025-12-03
**Priority**: HIGH

## Executive Summary

Add ability for users to upload documents directly through the Streamlit UI, without manually editing `corpus/corpus.yaml`. Currently, users must create YAML config files manually, which creates friction and limits usability.

---

## User Needs

### Who
- New users setting up Bloginator
- Users wanting to quickly add individual documents
- Users with non-technical backgrounds unfamiliar with YAML

### What
- Upload files (PDF, DOCX, TXT, Markdown) through web UI
- Optionally provide metadata (name, tags, quality rating, voice notes)
- Organize uploads into logical sources/collections
- View upload history and status

### Why
- Current manual YAML editing is cumbersome
- No visual feedback during setup
- No way to add documents without touching config files
- Reduces adoption barrier

---

## Functional Requirements

### FR1: File Upload Interface
- **File Upload Widget**: Streamlit `st.file_uploader()` accepting multiple files
- **Supported Formats**: PDF, DOCX, TXT, Markdown (.md)
- **File Size Limit**: 50MB per file
- **Multiple Files**: Allow batch upload (5-20 files at once)
- **Progress Tracking**: Show upload progress with file counts

### FR2: Metadata Collection
For each upload, collect optional:
- **Source Name**: Human-readable name (auto-fill from filename)
- **Tags**: Comma-separated list (e.g., "leadership,remote-work")
- **Quality Rating**: Dropdown (external/premium/standard)
- **Is External Source**: Checkbox (true/false)
- **Voice Notes**: Text area for context about the source

### FR3: Upload Destination
- **Default Location**: `corpus/sources/` (user-configurable)
- **Organization**: Store each upload in subdirectory with timestamp or source name
- **File Structure**:
  ```
  corpus/
  ├── sources/
  │   ├── source_1/
  │   │   ├── document_1.pdf
  │   │   ├── document_2.docx
  │   └── source_2/
  │       └── document_3.txt
  └── corpus.yaml
  ```

### FR4: Automatic YAML Configuration
- **Auto-Add Entry**: Automatically add uploaded source to `corpus/corpus.yaml`
- **Preserve Existing**: Don't overwrite manual entries
- **Idempotent**: Handle re-uploads of same source gracefully
- **Backup**: Create backup of corpus.yaml before modifying

### FR5: Status Feedback
- **Success Message**: "✓ Uploaded X files from {source_name}"
- **Extracted File Count**: Show count of successfully stored files
- **Errors**: Display file-specific errors (e.g., "Invalid PDF: file_name.pdf")
- **Next Steps**: Guide users to run extraction/indexing

### FR6: Storage Management
- **View Uploaded Sources**: List all sources with upload date, file count, total size
- **Delete Source**: Remove source and associated files from corpus
- **Edit Metadata**: Modify source tags, quality rating, voice notes
- **Reindex**: Mark source for re-extraction if content changed

---

## Non-Functional Requirements

### NFR1: Performance
- Upload should complete within 30 seconds for reasonable file sizes (< 50MB)
- No UI freezing during upload
- Async processing if possible (Streamlit sessions)

### NFR2: Reliability
- Failed uploads should not corrupt corpus.yaml
- Verify file integrity after upload (check file type magic bytes)
- Graceful handling of disk space issues

### NFR3: Security
- Sanitize uploaded filenames (no path traversal, special chars)
- Verify MIME types match file extensions
- No execution of uploaded files
- Store files in restricted directory with proper permissions

### NFR4: Usability
- Clear visual hierarchy (upload vs. extract vs. index)
- Helpful error messages (not technical)
- Tooltips for all fields
- Mobile-friendly layout

---

## Acceptance Criteria

### AC1: Users Can Upload Files
```gherkin
Given a user is on the Corpus Management page
When they click "Add Sources" tab
Then they should see a file upload widget
And they can select 1-20 files (PDF, DOCX, TXT, MD)
And files < 50MB are accepted
And > 50MB files show error "File too large"
```

### AC2: Metadata Collection Works
```gherkin
Given files are selected for upload
When the user fills in source metadata
Then all fields (name, tags, quality, notes) are optional
And source name defaults to first filename
And tags accept comma-separated values
And quality defaults to "standard"
```

### AC3: Files Are Stored Correctly
```gherkin
Given files are uploaded
When upload completes
Then files are stored in corpus/sources/{source_name}/
And filenames are preserved
And upload timestamp is recorded
And no files are modified or corrupted
```

### AC4: YAML Configuration Updated
```gherkin
Given files are uploaded for a new source
When upload completes
Then corpus/corpus.yaml is updated
And new source entry is added with correct metadata
And existing entries are preserved
And YAML is valid and parseable
```

### AC5: User Gets Feedback
```gherkin
Given files are uploaded
When upload completes
Then user sees success message
And file count is displayed
And next steps (extract, index) are suggested
And any errors are clearly displayed
```

### AC6: Users Can Manage Uploaded Sources
```gherkin
Given sources have been uploaded
When user views "Manage Sources" section
Then they can see all uploaded sources
And each source shows upload date, file count, size
And users can delete sources
And users can edit metadata
```

---

## Out of Scope

- Multi-user permission management (assume single user)
- Cloud storage integration (S3, Google Drive, etc.)
- Real-time collaboration
- Streaming large file uploads
- Automatic duplicate detection
- Advanced file format conversions

---

## Dependencies

### External APIs/Libraries
- Streamlit `st.file_uploader()` - built-in
- YAML library - already in use
- pathlib - standard library
- mimetypes - standard library for MIME type checking

### Internal APIs
- `corpus_config.CorpusConfig` - for YAML management
- Extraction pipeline - for processing uploaded files

### Infrastructure
- Filesystem with write permissions to `corpus/` directory
- Sufficient disk space (no quota enforcement needed initially)

---

## Success Metrics

1. **Usability**: New users can upload corpus files without editing YAML (target: <2 minutes)
2. **Adoption**: Track feature usage in metrics (target: >30% of users use upload feature)
3. **Error Rate**: <1% of uploads fail due to system errors
4. **Satisfaction**: User feedback indicates feature meets needs

---

## Future Enhancements

- Bulk import from directory (drag-and-drop folder)
- Integration with cloud storage services
- Duplicate file detection and merging
- Advanced file validation and preview
- Incremental upload resume
- Source versioning and history
- Import from URLs (fetch remote documents)
