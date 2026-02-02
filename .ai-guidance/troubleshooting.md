# Troubleshooting

> **When to load:** When debugging terminal issues, process problems, or repetitive failures

---

## ⚠️ TERMINAL OUTPUT CAPTURE ISSUES ⚠️

After spawning many terminal sessions (60+), VS Code terminal output capture can fail.
Commands execute successfully but programmatic reads return empty.

**Workaround: Use file-based output instead of terminal capture:**
```bash
# Instead of reading terminal output directly:
python3 script.py > /tmp/output.txt 2>&1
# Then read /tmp/output.txt via the view tool
```

**Best practices:**
- Limit concurrent terminals to 3-5 sessions
- Use file redirection for any output you need to parse
- If terminal capture fails, dispose and recreate the terminal
- Consider `terminal.integrated.enablePersistentSessions: false` in VS Code settings

---

## ⚠️ EFFICIENCY: AVOID REPETITIVE DEBUGGING ⚠️

### Signs You're Going in Circles

- Running the same command 3+ times expecting different results
- Waiting for output that never comes
- Terminal capture returning empty strings repeatedly

### When This Happens

1. **STOP immediately** - Don't run the same thing again
2. **Diagnose the root cause** - Check file existence, process status, error logs
3. **Use file redirection** - `command > /tmp/out.txt 2>&1` then `view /tmp/out.txt`
4. **Ask for help** - Generate a Perplexity prompt if truly stuck

---

## ⛔ WHEN STUCK, ASK FOR PERPLEXITY HELP ⛔

**The moment you get blocked or find yourself going in circles, STOP immediately.**

Do NOT continue trying random approaches. Instead:
1. **Generate a detailed Perplexity.ai prompt** for the user to run
2. Include: what you've tried, why it failed, specific technical details, environment info
3. **Wait for the user to return with Perplexity's response** before continuing
4. Fresh external research often unblocks problems that training data cannot solve

This is essential because:
- Your training data may be outdated or incomplete
- Perplexity has access to current documentation and community solutions
- The user can quickly get targeted answers for macOS/API-specific issues
- It prevents wasted time on dead-end approaches

---

## Common Issues & Fixes

**Tests Fail with Import Errors:**
```bash
# Reinstall in editable mode
pip install -e ".[dev]" --force-reinstall

# Clear cache
rm -rf .pytest_cache/ __pycache__/

# Run tests again
pytest tests/ -x
```

**Type Checking Fails:**
```bash
# Check specific module
mypy src/bloginator/models --show-traceback

# Fix the issue instead of ignoring:
# Don't add type: ignore, fix the underlying type issue
```

**Pre-commit Hook Fails:**
```bash
# Check what pre-commit is doing
pre-commit run --all-files --verbose

# Fix issues
black src/ tests/
ruff check --fix src/ tests/

# Commit again
git commit -m "fix: formatting"
```
