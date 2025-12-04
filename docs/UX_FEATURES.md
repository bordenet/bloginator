# Real-Time Skip Tracking UX Features

## Feature Overview

The Corpus Management page in Streamlit now displays real-time skip tracking during both extraction and indexing operations. Users get live visibility into:
- Which file/document is currently being processed
- Which files are being skipped and why
- Running count of skipped items

## Extract Tab

### Current File Display
- **Location**: Top of progress area
- **Updates**: With every output line from the CLI
- **Format**: `📄 Current: /path/to/file.pdf`
- **Behavior**: Shows the file path being actively processed
- **Use Case**: Understand which file extraction is taking a long time

### Skipped Files List
- **Location**: Scrollable text area below current file
- **Updates**: Whenever a skip event is detected
- **Format**:
  ```
  Skipped Files
  • /path/to/file1.md (already_extracted)
  • /path/to/~$temp.docx (temp_file)
  • /path/to/.DS_Store (ignore_pattern)
  ```
- **Scroll Behavior**: Automatically scrolls to show new items
- **Height**: 300 pixels (can scroll for many items)

### Skip Event Format
Each skip event from the CLI follows this pattern:
```
[SKIP] /full/path/to/file.extension (skip_reason)
```

**Skip Reasons Include:**
- `already_extracted` - File was previously extracted
- `temp_file` - Temporary file (e.g., ~$filename)
- `ignore_pattern` - Matches ignore patterns (.DS_Store, etc.)
- `unsupported_extension` - File type not supported
- `path_not_found` - Source file not found
- `empty_content` - File has no extractable content
- `url_source` - URL-based source skipped

### Completion Summary
- **Final Message**: Shows total count of skipped files
- **Example**: `📋 15 file(s) skipped (see list above)`

## Index Tab

### Current Document Display
- **Location**: Top of progress area
- **Updates**: With every output line from the CLI
- **Format**: `🔨 Current: document_042.json`
- **Behavior**: Shows the document being actively indexed
- **Use Case**: Track indexing progress and identify slow documents

### Skipped Documents List
- **Location**: Scrollable text area below current document
- **Updates**: Whenever a skip event is detected
- **Format**:
  ```
  Skipped Documents
  • document_001.json (unchanged_document)
  • document_003.json (unchanged_document)
  ```
- **Scroll Behavior**: Automatically scrolls to show new items
- **Height**: 300 pixels (can scroll for many items)

### Skip Reasons for Indexing
- `unchanged_document` - Document content hasn't changed since last index
- Other extraction-related reasons if re-indexing partial corpus

### Completion Summary
- **Final Message**: Shows total count of skipped documents
- **Example**: `📋 3 document(s) skipped (see list above)`

## Technical Implementation

### Output Parsing
The UI parses CLI output line-by-line:
- Lines starting with `[SKIP]` are parsed as skip events
- Other lines update the "Current" display
- No regex needed - simple string prefix check

### Real-Time Updates
- **Subprocess Streaming**: Uses `subprocess.Popen` with line-buffering
- **Live Rendering**: Updates Streamlit containers as output arrives
- **No Blocking**: UI remains responsive during processing

### Container Management
- **Empty Containers**: Pre-allocated with `st.empty()`
- **Info Boxes**: Used for "Current File/Document"
- **Text Areas**: Used for scrollable skip lists
- **Key Management**: Dynamic keys prevent Streamlit warnings

## User Experience Benefits

1. **Transparency**: See exactly what's being processed
2. **Debugging**: Identify which files cause extraction issues
3. **Progress Tracking**: Monitor long-running operations
4. **Feedback**: Understand why files were skipped
5. **Performance**: Identify bottlenecks in extraction/indexing

## Example Workflows

### Extraction with Mixed Output
```
📄 Current: /Users/matt/Documents/file_123.pdf

Skipped Files:
• /Users/matt/Documents/file_001.md (already_extracted)
• /Users/matt/.DS_Store (ignore_pattern)
• /Users/matt/Documents/~$temp.docx (temp_file)
```

### Indexing with Many Documents
```
🔨 Current: document_087.json

Skipped Documents:
• document_045.json (unchanged_document)
• document_046.json (unchanged_document)
• document_047.json (unchanged_document)
• document_048.json (unchanged_document)
• document_049.json (unchanged_document)
• ... and 95 more
```

## Testing Coverage

All features tested with 12 comprehensive test cases:
- ✅ Skip event parsing from `[SKIP]` prefix
- ✅ Multiple skip events accumulation
- ✅ Current file/document detection
- ✅ Absolute path handling
- ✅ Long path preservation
- ✅ Display updates
- ✅ Empty and large skip lists
- ✅ Format integrity

See `tests/unit/ui/test_corpus_management.py::TestRealTimeSkipEventParsing` for details.
