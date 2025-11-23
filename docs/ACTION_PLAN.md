# Bloginator Action Plan (Post “Solid A” Pass)

This document summarizes the next set of high‑value improvements now that:
- `main` is pushed (HEAD: `0775a39caa8a42e004bf2b3dbc7c4b00d503e242`), and
- GitHub Actions **Tests** and **Lint and type check** workflows for that commit have both completed with `conclusion: success`.

---

## 1. Optional‑Extras Coverage

**Objective:** Fully exercise code guarded by optional dependencies in at least one environment and keep CI behavior predictable.

### 1.1 PDF Export (ReportLab)
- [ ] Create or use an environment with `reportlab` installed (e.g. `pip install bloginator[export]`).
- [ ] Unskip and run PDF tests:
  - `tests/unit/export/test_docx_and_pdf_exporter.py`
- [ ] Verify `_REPORTLAB_AVAILABLE` paths in `pdf_exporter.py` execute without flakiness.
- [ ] If behavior is stable, consider:
  - [ ] Adding `export` extras to the CI install matrix (e.g. `pip install ".[dev,export]"`) in **tests** and/or **lint** workflows.

### 1.2 Web / FastAPI Routes
- [ ] Create or use an environment with `bloginator[web]` installed.
- [ ] Run `tests/unit/web/test_routes.py` to exercise:
  - `src/bloginator/web/app.py`
  - `src/bloginator/web/routes/*.py`
- [ ] Fix any issues surfaced by these tests while maintaining MyPy cleanliness.
- [ ] Decide whether CI should install `web` extras by default or via a dedicated, slower job.

### 1.3 Streamlit UI
- [ ] Ensure `tests/unit/export/test_ui_utils.py` runs and passes in an environment with `streamlit` installed.
- [ ] Consider adding a minimal smoke test for the main Streamlit entrypoint(s):
  - e.g. verify that the app module imports and constructs its layout without hitting runtime errors.

---

## 2. Coverage Improvements in Core Workflows

**Objective:** Raise overall project coverage (currently ~47%) by targeting high‑value, low‑coverage modules.

### 2.1 CLI Commands
- [ ] Add focused tests for CLI entrypoints that are currently light on coverage, e.g. in `tests/unit/cli/`:
  - `draft.py`
  - `extract_config.py`
  - `extract_single.py`
  - `history.py`
  - `outline.py`
  - `search.py`
  - `serve.py`
  - `template.py`
- [ ] Prefer end‑to‑end style tests that:
  - Invoke the Typer/FastAPI/CLI interfaces with realistic args.
  - Assert on exit codes and key side effects (e.g., output files, console output, API responses).

### 2.2 Utilities and Supporting Modules
- [ ] Improve coverage for selected low‑coverage utilities:
  - `src/bloginator/utils/checksum.py`
  - `src/bloginator/utils/parallel.py` (esp. error/edge paths)
- [ ] Add regression tests around any previously bug‑prone behavior identified during usage.

### 2.3 UI and Web Integration
- [ ] In an extras‑enabled environment, add tests that:
  - Exercise basic happy‑path web flows (e.g. index page, simple search route).
  - Confirm that template rendering works with realistic template and corpus configs.

---

## 3. Static Analysis Tightening

**Objective:** Carefully expand and refine static analysis without introducing noise.

### 3.1 MyPy Scope Extensions
- [ ] Consider adding remaining web modules to the enforced MyPy list once they are clean:
  - `src/bloginator/web/routes/app.py`
  - `src/bloginator/web/routes/corpus.py`
  - `src/bloginator/web/routes/documents.py`
  - `src/bloginator/web/routes/main.py`
- [ ] After they type‑check cleanly, update both:
  - `scripts/fast-quality-gate.sh`
  - `.github/workflows/lint.yml`
  to include `src/bloginator/web` in the MyPy invocation.

### 3.2 Ruff Rule Set Review
- [ ] Review current Ruff configuration in `pyproject.toml`.
- [ ] Gradually enable additional rule families that add signal without churn, e.g.:
  - `SIM` (simplifications)
  - `PERF` (performance‑related hints)
  - Selected `B`/`C` rules where they match project style.
- [ ] Run Ruff in fix‑mode locally, verify no behavioral changes, and then promote to CI.

---

## 4. Documentation and Developer Experience

**Objective:** Keep documentation accurate, minimal, and principal‑engineer‑grade.

### 4.1 Coverage and Quality Story
- [ ] Periodically re‑run:
  - `pytest --cov=src/bloginator --cov-report=term-missing`
- [ ] Update the README coverage badge when coverage materially moves (e.g. +3–5 points).
- [ ] Ensure README’s quick‑start instructions stay in sync with actual CLI behavior and supported Python versions.

### 4.2 Developer Guide & Future Work
- [ ] Cross‑link this `ACTION_PLAN.md` from `docs/DEVELOPER_GUIDE.md` and/or `docs/FUTURE_WORK.md`.
- [ ] Periodically prune completed items from this plan and migrate long‑term ideas into `docs/FUTURE_WORK.md`.

---

## 5. Operational Guardrails

**Objective:** Keep the repo easy to trust and easy to change.

- [ ] Continue to treat `scripts/fast-quality-gate.sh` as the local source of truth; keep it aligned with CI.
- [ ] Before any significant refactor:
  - Run the full fast gate locally.
  - Add or update tests around the most critical flows you’ll touch (extraction, search, generation, export).
- [ ] When new optional features or integrations are added:
  - Wire them into the extras/feature-flag pattern used for exporters, UI, and web.
  - Add tests that skip cleanly when the extra is absent and run thoroughly when it is present.
