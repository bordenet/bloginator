# Batch Mode Implementation Plan

## Overview

Add `--batch` flag to `bloginator draft` command that generates all LLM requests upfront,
waits for all responses, then processes them. This eliminates the serial request/response
blocking that makes assistant mode extremely slow.

## Problem Statement

Current assistant mode workflow:
1. Generate request 1 → Wait for response 1 → Process
2. Generate request 2 → Wait for response 2 → Process
3. ... (18 sections = 18 serial waits)

This requires ~2 minutes per section manually = 36+ minutes per blog.

## Solution: Batch Mode

New workflow with `--batch`:
1. Generate ALL 18 request files upfront
2. Wait for ALL 18 response files to appear
3. Process all responses at once

Claude can read all 18 requests in a single context window and write all responses
in one pass (~5 minutes total).

## Implementation Details

### 1. Modify AssistantLLMClient

Add batch mode support to `src/bloginator/generation/_llm_assistant_client.py`:

```python
class AssistantLLMClient(LLMClient):
    def __init__(self, ..., batch_mode: bool = False):
        self.batch_mode = batch_mode
        self.pending_requests: list[dict] = []

    def generate(self, prompt, ...) -> LLMResponse:
        if self.batch_mode:
            return self._generate_batch_request(prompt, ...)
        else:
            return self._generate_serial(prompt, ...)  # existing logic

    def _generate_batch_request(self, prompt, ...) -> LLMResponse:
        """Write request file but return placeholder. Actual content filled later."""
        # Write request file
        # Return placeholder LLMResponse with request_id for later lookup

    def collect_batch_responses(self) -> dict[int, LLMResponse]:
        """Wait for all response files and return mapping of request_id -> response."""
        # Wait for all response files to appear
        # Read and return all responses
```

### 2. Modify DraftGenerator

Add batch-aware generation to `src/bloginator/generation/draft_generator.py`:

```python
def generate(self, outline, ..., batch_mode: bool = False) -> Draft:
    if batch_mode and isinstance(self.llm_client, AssistantLLMClient):
        return self._generate_batch(outline, ...)
    else:
        return self._generate_serial(outline, ...)  # existing logic

def _generate_batch(self, outline, ...) -> Draft:
    # Phase 1: Generate all request files
    self.llm_client.batch_mode = True
    section_placeholders = []
    for section in outline.get_all_sections():
        placeholder = self._generate_section(section, ...)  # writes request file
        section_placeholders.append((section, placeholder))

    # Phase 2: Wait for all responses
    responses = self.llm_client.collect_batch_responses()

    # Phase 3: Build draft with actual content
    # Map responses back to sections and build final Draft object
```

### 3. Add CLI Flag

Modify `src/bloginator/cli/draft.py`:

```python
@click.option("--batch", is_flag=True, help="Batch mode: generate all requests upfront")
def draft(..., batch: bool):
    ...
    generator = DraftGenerator(llm_client=llm_client, ...)
    draft_obj = generator.generate(outline, ..., batch_mode=batch)
```

### 4. Environment Variable

Support `BLOGINATOR_BATCH_MODE=true` as alternative to CLI flag.

## File Changes Required

| File | Change |
|------|--------|
| `src/bloginator/generation/_llm_assistant_client.py` | Add batch mode logic |
| `src/bloginator/generation/draft_generator.py` | Add `_generate_batch()` method |
| `src/bloginator/cli/draft.py` | Add `--batch` flag |
| `tests/unit/generation/test_assistant_client_batch.py` | New test file |

## Testing Strategy

1. **Unit tests**: Mock file I/O, verify request files generated correctly
2. **Integration test**: Generate batch requests, manually create responses, verify draft
3. **E2E validation**: Full SDE career ladder draft with Claude as LLM

## Success Criteria (Validated 2024-12-07)

- [x] `bloginator draft --batch` generates all request files before waiting
- [x] Command waits for all response files (with timeout)
- [x] `--batch-timeout SECONDS` flag added (default: 1800s = 30min)
- [x] Draft quality matches serial mode (2618 words, 12 citations, 0.56 voice)
- [x] Graceful degradation: 80% threshold, placeholders for missing responses
- [x] JSON schema validation with error handling for malformed responses
- [x] Duplicate response detection ("Response N updated (overwrite)")
- [x] Progress shows "Claude thinking... (5-10min typical)"
- [x] `BLOGINATOR_BATCH_MODE` env var honored
- [x] Test coverage maintained (6 batch mode tests passing)
- [ ] Documentation updated (needs README update)
- [ ] Changelog entry added
- [ ] CI pipeline green
- [ ] PR merged to main

## Features Implemented

1. **Batch Request Generation**: All 17 requests generated upfront in ~5 seconds
2. **30-Minute Default Timeout**: Configurable via `--batch-timeout` flag
3. **80% Response Threshold**: Graceful degradation with placeholder content
4. **JSON Schema Validation**: Required: `content`; Optional: `request_id`, `tokens_used`, `error`
5. **Progress Visibility**: Elapsed/remaining time, response counts every 15 seconds
6. **Table Generation**: LLM prompt updated for selective table formatting

## E2E Validation

```bash
# Command used:
BLOGINATOR_LLM_MOCK=assistant bloginator draft \
  --index .bloginator/chroma \
  --outline blogs/sde-career-ladder-outline.json \
  -o blogs/career-ladders/02-sde-career-ladder-tables.md \
  --batch --batch-timeout 30

# Results:
Total Sections: 17
Total Words: 2618
Total Citations: 12
Voice Score: 0.56
Tables Generated: 4 (level comparison, timeline, four quadrants, metrics)
```

## Rollback

If batch mode fails, existing serial mode (`--batch` omitted) continues to work unchanged.
