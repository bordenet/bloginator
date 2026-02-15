# Terminal Output Issues

> **When to load:** When terminal capture fails or returns empty

## ⚠️ TERMINAL OUTPUT CAPTURE ISSUES

After spawning many terminal sessions (60+), VS Code terminal output capture can fail.
Commands execute successfully but programmatic reads return empty.

**Workaround: Use file-based output:**
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

