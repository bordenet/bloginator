# Corpus Directory Import Feature Requirements

**Status**: Draft
**Date**: 2025-12-03
**Priority**: HIGH

## Executive Summary

Add ability to import directories directly from the filesystem into the corpus configuration, without manually creating YAML entries or uploading files individually. Currently, users must either edit `corpus/corpus.yaml` manually or upload files one-by-one through the UI.

---

## User Needs

### Who
- Users with existing directories of documents on disk
- Users wanting to quickly add local filesystem sources
- Users managing multiple related document collections

### What
- Select a directory from filesystem (local or mounted network)
- Automatically scan and add all documents in directory to corpus
- Optionally recurse into subdirectories
- Organize by directory structure or flat structure
- Validate that documents are in supported formats

### Why
- Many users have documents already organized on disk
- Manual YAML editing or individual file uploads are slow
- Directory imports preserve existing organization
- Enables bulk addition of document collections

---

## Functional Requirements

### FR1: Directory Selection
- **UI Component**: Streamlit directory picker or path input
- **Local Filesystem**: Access to user's local or mounted directories
- **Path Validation**: Verify directory exists and is readable
- **Display**: Show selected path and summary of contents

### FR2: Document Discovery
- **Scan Directory**: Recursively find all supported document types
- **Supported Formats**: PDF, DOCX, TXT, Markdown (.md)
- **Filtering**: Optional regex patterns to include/exclude files
- **Recursion Control**: Option to recurse into subdirectories (depth limit: 10)
- **Hidden Files**: Skip hidden files/directories (starting with `.`)
- **Statistics**: Show count of discoverable documents before importing

### FR3: Source Configuration
- **Source Name**: Auto-generate from directory name or allow custom
- **Path Storage**: Store absolute or relative path to directory in corpus.yaml
- **Enable/Disable**: Extracted configuration with enabled flag
- **Watch Capability**: Optional: mark directory for changes (Phase 2)
- **Metadata**: Inherit tags, quality rating, voice notes from config or UI

### FR4: Preview & Confirmation
- **File List**: Show preview of files that will be imported (paginated if >50 files)
- **Statistics**: Display total count, formats, sizes
- **Conflicts**: Warn if directory already exists in corpus.yaml
- **Permissions**: Check that all files are readable
- **Confirmation Dialog**: Ask user before committing to corpus.yaml

### FR5: Import Execution
- **Atomic Operation**: Update corpus.yaml only on success
- **Error Handling**: Report any permission/access issues
- **Path Normalization**: Normalize paths (resolve symlinks, relative→absolute)
- **Backup**: Create backup of corpus.yaml before modifying
- **Status Feedback**: Show success/failure message with file count

### FR6: Configuration Management
- **Direct Path**: Store actual filesystem path (not copy files)
- **No File Copies**: Directory import doesn't copy files into `corpus/sources/`
- **Extraction Step**: Extraction pipeline reads from configured paths
- **Path Flexibility**: Support absolute, relative, and environment variable paths

---

## Non-Functional Requirements

### NFR1: Performance
- Directory scan should complete in <5 seconds for directories with 1000+ files
- No UI freezing during scan
- Lazy loading for large file lists

### NFR2: Reliability
- Graceful handling of permission denied errors
- Symlink detection and handling (don't infinitely recurse)
- Network path timeouts (if accessing network drives)
- Failed imports don't corrupt corpus.yaml

### NFR3: Security
- Don't follow symlinks that lead outside project root (optionally configurable)
- Validate paths don't escape intended directory
- No file execution or interpretation
- Respect filesystem permissions

### NFR4: Usability
- Clear UI for path selection (file browser preferred over text input)
- Helpful error messages (not technical jargon)
- Preview before committing
- Ability to cancel before saving changes
- Support for copy/paste paths

---

## Acceptance Criteria

### AC1: Users Can Add Directory Sources
```gherkin
Given a user is on the Corpus Management page
When they click "Add Directory" button
Then they can select a directory from their filesystem
And they can see preview of files that will be imported
And they can confirm import
```

### AC2: Directory Scanning Works
```gherkin
Given a directory with 50 PDF, DOCX, TXT, and MD files
When user selects that directory
Then Bloginator scans and discovers all supported files
And shows count and breakdown by format
And completes in <5 seconds
```

### AC3: Recursion Works Correctly
```gherkin
Given a directory with subdirectories containing documents
When "Recurse subdirectories" is enabled
Then all documents at any depth are discovered
And subdirectory structure is preserved in source name (optional)
When recursion is disabled
Then only top-level documents are included
```

### AC4: YAML Configuration Updated
```gherkin
Given directory is imported
When import completes
Then corpus.yaml is updated with new source entry
And path points to the actual directory location
And source is marked enabled by default
And existing entries are preserved
```

### AC5: Path Validation Works
```gherkin
Given user selects invalid path
When validation runs
Then error message displays: "Directory not found" or "Permission denied"
And import is blocked
When user selects valid directory
Then path is normalized and validated
And import can proceed
```

### AC6: Conflicts Detected
```gherkin
Given directory path already exists in corpus.yaml
When user attempts to import same directory
Then warning displays: "Directory already exists in corpus as '{source_name}'"
And user can cancel or overwrite
```

---

## Out of Scope (Phase 2+)

- Real-time directory watching for file changes
- Automatic re-indexing when directory contents change
- Selective file inclusion via advanced filters
- Remote directory access (S3, Google Drive, etc.)
- Symlink following to external sources
- Directory exclusion patterns (gitignore-style)

---

## Dependencies

### External APIs/Libraries
- Streamlit - file browser or path input widget
- pathlib - filesystem operations
- YAML library - configuration management

### Internal APIs
- `corpus_config.CorpusConfig` - YAML management
- Extraction pipeline - must handle arbitrary filesystem paths

### Infrastructure
- Filesystem with read permissions
- No special mounting or network requirements (local only initially)

---

## Success Metrics

1. **Usability**: Users can import directory sources in <30 seconds
2. **Performance**: Directory scan <5 seconds for 1000+ files
3. **Accuracy**: 100% of discoverable documents are identified
4. **Reliability**: No data loss or corruption
5. **Adoption**: Directory import used for 40%+ of new sources

---

## Future Enhancements

- Watch directory for changes and auto-reindex
- Exclude patterns (similar to `.gitignore`)
- Symlink resolution and smart following
- Network path support (SMB/NFS)
- Cloud storage integration
- Directory versioning (track content changes over time)
- Incremental updates (only process new/modified files)
