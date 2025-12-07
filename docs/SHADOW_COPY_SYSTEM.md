# Shadow Copy System for Offline Corpus Access

## Product Requirements

### Problem
When traveling or disconnected from the network, corpus source files stored on:
- SMB network shares (NAS)
- OneDrive with Files-On-Demand

...become inaccessible, preventing extraction, re-indexing, or modification of the corpus.

### Solution
Maintain shadow copies of source files in `/tmp/bloginator/corpus_shadow/` during extraction.
These local copies enable full offline capability for corpus operations.

### Requirements
1. **Copy-on-Extract**: When `CORPUS_MAINTAIN_SHADOW_COPIES=true`, copy each successfully
   extracted file to the shadow directory
2. **Fallback Resolution**: When original paths are unavailable, automatically use shadow copies
3. **Safe Cleanup**: The cleanup script preserves shadow copies by default; explicit flag required
   to delete them with 10-second timeout confirmation

---

## Architecture

### Directory Structure

```
/tmp/bloginator/corpus_shadow/
├── smb/
│   └── <server>/
│       └── <share_path>/
│           └── <files...>
└── local/
    └── <absolute_path>/
        └── <files...>
```

### Components

| Module | Purpose |
|--------|---------|
| `src/bloginator/utils/shadow_copy.py` | Core utilities for shadow copy creation |
| `src/bloginator/config.py` | Configuration (env flag + root path) |
| `src/bloginator/cli/_smb_resolver.py` | SMB path resolution with shadow fallback |
| `src/bloginator/cli/_extract_config_helpers.py` | Local path resolution with shadow fallback |
| `src/bloginator/cli/_extract_files_engine.py` | Shadow copy creation during extraction |
| `scripts/purge-corpus-and-outputs.sh` | Cleanup with shadow copy protection |

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTRACTION FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. resolve_source_path()                                                    │
│     ├── Original path exists? → Use it                                       │
│     └── Original unavailable? → Check shadow copy → Use if exists            │
│                                                                              │
│  2. extract_source_files()                                                   │
│     └── After successful extraction:                                         │
│         if CORPUS_MAINTAIN_SHADOW_COPIES:                                    │
│             create_shadow_copy(source, shadow_path)                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variable

```bash
# .env
CORPUS_MAINTAIN_SHADOW_COPIES=true
```

### Config Access

```python
from bloginator.config import Config

if Config.CORPUS_MAINTAIN_SHADOW_COPIES:
    # Copy files during extraction

shadow_root = Config.SHADOW_COPY_ROOT  # Path("/tmp/bloginator/corpus_shadow")
```

---

## Usage

### Enable Shadow Copies

```bash
# Set in .env
CORPUS_MAINTAIN_SHADOW_COPIES=true

# Run extraction (creates shadow copies)
bloginator extract --config corpus/corpus.yaml -o /tmp/bloginator/output/extracted
```

### Offline Workflow

When disconnected, the system automatically falls back to shadow copies:

```bash
# Works offline if shadow copies exist
bloginator extract --config corpus/corpus.yaml -o /tmp/bloginator/output/extracted
bloginator index /tmp/bloginator/output/extracted -o /tmp/bloginator/chroma
```

### Cleanup Script

```bash
# Normal cleanup (preserves shadow copies)
./scripts/purge-corpus-and-outputs.sh -y

# Preview what would be deleted
./scripts/purge-corpus-and-outputs.sh --what-if

# DANGEROUS: Also wipe shadow copies (requires explicit confirmation)
./scripts/purge-corpus-and-outputs.sh --wipe-shadow-copies
```

---

## API Reference

### `shadow_copy.py`

| Function | Description |
|----------|-------------|
| `is_shadow_copy_enabled()` | Check if feature flag is enabled |
| `get_shadow_copy_root()` | Get shadow directory path |
| `build_shadow_path_for_local(path)` | Build shadow path for local file |
| `build_shadow_path_for_smb(url, path, root)` | Build shadow path for SMB file |
| `create_shadow_copy(source, shadow)` | Copy file to shadow location |
| `should_update_shadow_copy(source, shadow)` | Check if copy needs update |

### `_smb_resolver.py`

| Function | Description |
|----------|-------------|
| `_get_shadow_path_for_smb(url)` | Get existing shadow path for SMB URL |
| `resolve_smb_path(url, tracker)` | Resolve SMB with shadow fallback |

### `_extract_config_helpers.py`

| Function | Description |
|----------|-------------|
| `_get_shadow_path_for_local(path)` | Get existing shadow path for local path |
| `resolve_source_path(cfg, base, tracker, console)` | Resolve path with shadow fallback |

---

## Testing

```bash
# Run shadow copy tests
pytest tests/unit/cli/test_extract.py::TestShadowCopyForSMB -v
pytest tests/unit/cli/test_extract.py::TestShadowCopyForLocal -v
pytest tests/unit/cli/test_extract.py::TestShadowCopyCreation -v
```

---

## Limitations

1. **Disk space**: Shadow copies consume local disk space in `/tmp`
2. **Not synced**: Changes to shadow copies are not synced back to originals
3. **Manual refresh**: Shadow copies only update during extraction
4. **macOS /tmp**: On macOS, /tmp is cleared on reboot (symlink to /private/tmp)
