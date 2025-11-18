# Verbose Logging Implementation Plan

## Overview
Add `--verbose` / `-v` flag support to bloginator CLI commands to show LLM request/response interactions with color-coded output following the STYLE_GUIDE.md display requirements.

## Requirements

### Display Format (from STYLE_GUIDE.md)
- **LLM Requests**: Light gray text on black background (`\033[37;40m`)
- **LLM Responses**: Yellow text on dark blue background (`\033[33;44m`)
- Minimize vertical space usage
- Show progress indicators during LLM generation

### Files to Modify

#### 1. `src/bloginator/cli/outline.py`
- Add `--verbose` flag (already has `--log-file`)
- Pass verbose flag to `OutlineGenerator`
- Log LLM interactions when verbose=True

#### 2. `src/bloginator/cli/draft.py`
- Add `--verbose` flag (already has `--log-file`)
- Pass verbose flag to `DraftGenerator`
- Log LLM interactions when verbose=True

#### 3. `src/bloginator/generation/llm_client.py`
- Add `verbose` parameter to `generate()` method
- When `verbose=True`, print:
  - **Request**: Full prompt in light gray on black
  - **Response**: Full generated text in yellow on dark blue
- Use ANSI escape codes for colors
- Detect TTY (disable colors if redirected to file)

#### 4. `src/bloginator/generation/outline_generator.py`
- Add `verbose` constructor parameter
- Pass to LLM client calls

#### 5. `src/bloginator/generation/draft_generator.py`
- Add `verbose` constructor parameter
- Pass to LLM client calls

#### 6. `test_e2e.sh`
- Add `-v` flag support
- Pass `--verbose` to `bloginator outline` and `bloginator draft` when specified

## Implementation Details

### Color Constants (add to llm_client.py)

```python
import sys

# ANSI color codes (only if stdout is a TTY)
if sys.stdout.isatty():
    COLOR_PROMPT = '\033[37;40m'      # Light gray on black
    COLOR_RESPONSE = '\033[33;44m'    # Yellow on dark blue
    COLOR_RESET = '\033[0m'
else:
    COLOR_PROMPT = ''
    COLOR_RESPONSE = ''
    COLOR_RESET = ''
```

### LLM Client Changes

```python
class OllamaClient(LLMClient):
    def __init__(self, ..., verbose: bool = False):
        self.verbose = verbose
        ...

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        if self.verbose:
            print(f"\n{COLOR_PROMPT}{'='*80}")
            print(f"LLM REQUEST (Ollama - {self.model})")
            print(f"{'='*80}")
            print(prompt)
            print(f"{'='*80}{COLOR_RESET}\n")

        response = # ... make request ...

        if self.verbose:
            print(f"\n{COLOR_RESPONSE}{'='*80}")
            print(f"LLM RESPONSE ({len(response.content)} chars)")
            print(f"{'='*80}")
            print(response.content)
            print(f"{'='*80}{COLOR_RESET}\n")

        return response
```

### CLI Changes (outline.py and draft.py)

```python
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show LLM request/response interactions"
)
def outline(..., verbose: bool):
    # Pass to generator
    generator = OutlineGenerator(
        llm_client=llm_client,
        searcher=searcher,
        min_coverage_sources=min_coverage,
        verbose=verbose,  # NEW
    )
```

### Generator Changes

```python
class OutlineGenerator:
    def __init__(self, ..., verbose: bool = False):
        self.verbose = verbose
        ...

    def generate(self, ...):
        # When calling LLM
        response = self.llm_client.generate(
            prompt=user_prompt,
            temperature=temperature,
            max_tokens=2000,
            verbose=self.verbose,  # Pass through
        )
```

### test_e2e.sh Changes

```bash
#!/bin/bash

# Parse arguments
VERBOSE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Pass --verbose to bloginator commands if set
VERBOSE_FLAG=""
if [[ "$VERBOSE" == true ]]; then
    VERBOSE_FLAG="--verbose"
fi

bloginator outline \
  --index "$INDEX_PATH" \
  --title "Building a DevOps Culture at Scale" \
  --keywords "devops,kubernetes,automation" \
  --output "$OUTLINE_OUTPUT" \
  --log-file "$OUTLINE_LOG" \
  $VERBOSE_FLAG  # Add verbose flag
```

## Testing

### Test 1: Verbose Output
```bash
./test_e2e.sh -v
```

**Expected:**
- Light gray text on black showing full LLM prompts
- Yellow text on dark blue showing full LLM responses
- Progress indicators between requests

### Test 2: Non-Verbose Output
```bash
./test_e2e.sh
```

**Expected:**
- No LLM request/response shown
- Only progress bars and summaries
- Minimal vertical space

### Test 3: Redirected Output
```bash
./test_e2e.sh -v > output.log 2>&1
```

**Expected:**
- No ANSI color codes in file
- Plain text output

## Files Summary

**Modified:**
1. `src/bloginator/cli/outline.py` - Add --verbose flag
2. `src/bloginator/cli/draft.py` - Add --verbose flag
3. `src/bloginator/generation/llm_client.py` - Add verbose logging
4. `src/bloginator/generation/outline_generator.py` - Pass verbose through
5. `src/bloginator/generation/draft_generator.py` - Pass verbose through
6. `test_e2e.sh` - Add -v flag parsing and pass to commands

**Total:** 6 files

## Estimated Complexity

**Medium** - Requires threading verbose parameter through multiple layers, but the changes are straightforward and follow existing patterns.

## Notes

- Follow existing logging patterns (already using `logger.info()` in CLI)
- Don't use verbose flag in log files (only stdout)
- Ensure color codes respect TTY detection
- Keep display compact (use same progress indicators as non-verbose)
- The verbose output should augment, not replace, existing progress indicators

## Example Output

```bash
$ ./test_e2e.sh -v

[Light gray on black]
================================================================================
LLM REQUEST (Ollama - mixtral:8x7b)
================================================================================
You are an expert technical writer creating a structured outline for a blog post.

Title: Building a DevOps Culture at Scale
Thesis: Effective DevOps culture requires both technical infrastructure AND organizational transformation

Keywords: devops, kubernetes, automation, culture, collaboration, ci-cd

Create a JSON outline with 5 main sections...
================================================================================
[Reset]

⠹ Generating outline structure... (this stays visible)

[Yellow on dark blue]
================================================================================
LLM RESPONSE (1,234 chars)
================================================================================
{
  "title": "Building a DevOps Culture at Scale",
  "sections": [
    {
      "title": "The Foundation: Infrastructure as Code",
      ...
    }
  ]
}
================================================================================
[Reset]

✓ Outline generated
```
