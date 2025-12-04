# Handoff Prompt: TASK 11 & 12 Refactoring

## Current Status
- **8/10 tasks complete (80% done)**
- **Last commit:** 64aafcc (docs update for TASK 10)
- **TASK 10 just completed:** draft.py split into 5 focused modules (all <250 lines)

## What to Do Next

Resume the file size refactoring using the exact same pattern from TASK 10.

### Pattern to Follow (from TASK 10)
1. Create dedicated helper modules with underscore prefix (`_module_name.py`)
2. Extract non-Click-decorator functions to helper modules
3. Keep orchestrator (main file) with Click command only
4. Add proper type annotations (Path, object, specific model types)
5. Update existing tests to import from new module locations
6. Run `./scripts/fast-quality-gate.sh` before each commit
7. Update `docs/REFACTORING_PROGRESS.md` when done
8. Commit with: `git commit -m "refactor: TASK N - [description]"`

### TASK 11: Refactor template_manager.py (421 lines)

**Target:**
- Create: `src/bloginator/services/_template_storage.py` (~160 lines) - file I/O
- Modify: `src/bloginator/services/template_manager.py` (~220 lines) - TemplateManager logic
- Both files must be <250 lines

**Functions to Extract:**
- `_save_template()`
- `_load_template_from_disk()`
- `_delete_template_from_disk()`
- File listing/discovery logic

**Tests to Update:**
- Update any mocks/patches that reference old import paths
- All existing tests should continue to pass

**Quality Gates:**
```bash
mypy src/bloginator/services/_template*.py
./scripts/fast-quality-gate.sh
pytest tests/unit/services/test_template_manager.py -xvs
```

### TASK 12: Refactor outline.py (406 lines)

**Target:**
- Create: `src/bloginator/cli/_outline_formatter.py` (~120 lines) - output formatting
- Modify: `src/bloginator/cli/outline.py` (~250 lines) - Click command
- Both files must be <250 lines

**Functions to Extract:**
- `_format_outline_output()`
- `_write_outline_files()`
- All non-command functions

**Tests to Update:**
- Update any mocks/patches that reference old import paths
- All existing tests should continue to pass

**Quality Gates:**
```bash
mypy src/bloginator/cli/_outline*.py
./scripts/fast-quality-gate.sh
pytest tests/unit/cli/test_outline_cli.py -xvs
```

## Key Resources

- **Implementation plan:** `docs/plans/2025-12-03-refactor-large-files.md` (section for TASK 10 shows exact pattern)
- **Progress tracker:** `docs/REFACTORING_PROGRESS.md` (update after each task)
- **Python style guide:** `docs/PYTHON_STYLE_GUIDE.md` (100-char lines, type annotations required)
- **TASK 9 as reference:** Commit 748eee8 shows similar extraction pattern

## Type Annotations Checklist

When adding type annotations, import from:
- `from pathlib import Path`
- `from bloginator.models.draft import Draft` (if needed)
- `from bloginator.models.outline import Outline` (if needed)
- Specific types from models package as needed

## Git Workflow

```bash
# 1. Create and check new module
git status
git add src/bloginator/.../*.py
git add tests/unit/.../*.py

# 2. Run quality gates
./scripts/fast-quality-gate.sh

# 3. Commit
git commit -m "refactor: TASK N - [description]"

# 4. Update docs
# - Edit docs/REFACTORING_PROGRESS.md
# - Add completed task with ✅ marker
# - Update Current Progress line

# 5. Commit docs update
git commit -m "docs: update REFACTORING_PROGRESS.md - TASK N complete"
```

## Success Criteria (Per Task)

- [ ] All files <400 lines (target <250 for components)
- [ ] No circular imports
- [ ] All existing tests pass
- [ ] New type annotations added (Draft, Path, object where appropriate)
- [ ] Test mocks updated to new module paths
- [ ] `./scripts/fast-quality-gate.sh` passes
- [ ] `mypy` clean
- [ ] Commit message includes "refactor: TASK N"
- [ ] Progress document updated with ✅ marker

## Final Verification (After Both Tasks)

```bash
# Check no files exceed 400 lines
find src/bloginator/cli src/bloginator/services -name "*.py" -exec wc -l {} \; | awk '$1 > 400'

# Verify tests pass
pytest tests/unit/cli/test_*_cli.py tests/unit/services/test_template*.py -xvs

# Full quality gate
./scripts/fast-quality-gate.sh
```

## Notes

- TASK 10 created 5 modules from draft.py - use this as exact pattern reference
- Both tasks (11 & 12) are independent - can be done in any order
- Update progress document **immediately after each task** to preserve state
- If continuing in new context, read `docs/REFACTORING_PROGRESS.md` first

---

**When done with both tasks:**
- 10/10 complete (100%)
- Update final success section in progress document
- Verify zero files exceed 400 lines in the entire codebase
- Close this handoff document
