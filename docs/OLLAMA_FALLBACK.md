# Ollama Fallback to Assistant Mode

## Overview

When the Ollama server is unavailable, `scripts/run-e2e.sh` now automatically falls back to assistant mode (`BLOGINATOR_LLM_MOCK=assistant`), allowing the workflow to continue using Claude as the LLM backend instead of failing.

## Behavior

### Before (Old Behavior)
When Ollama was unavailable:
```
✗ Ollama not reachable at http://192.168.5.53:11434
Start Ollama with: ollama serve
➜ (script exits with error)
```

### After (New Behavior)
When Ollama is unavailable:
```
▸ Checking Ollama service...
⚠ Ollama not reachable at http://192.168.5.53:11434

Falling back to assistant mode (Claude will generate responses)...
✓ Switched to assistant mode

[workflow continues normally]
```

## Fallback Scenarios

The script automatically falls back to assistant mode in three scenarios:

### 1. Ollama Service Unreachable
When the server at `BLOGINATOR_LLM_BASE_URL` cannot be reached:
- Displays warning (not error)
- Sets `BLOGINATOR_LLM_MOCK=assistant`
- Continues with workflow

### 2. No Models Available
When Ollama is running but has no models:
- Displays warning
- Sets `BLOGINATOR_LLM_MOCK=assistant`
- Continues with workflow

### 3. Desired Model Not Found
When the configured model (e.g., `deepseek-r1:1.5b`) is not available:
- Displays warning and lists available models
- Sets `BLOGINATOR_LLM_MOCK=assistant`
- Continues with workflow

## Implementation Details

### Changes to `scripts/run-e2e.sh`

#### 1. Modified `step_check_ollama()` function
- Changed all Ollama failures from `exit 1` to `return 0`
- Automatically sets `export BLOGINATOR_LLM_MOCK="assistant"`
- Displays clear messages indicating the fallback

#### 2. Updated `run_bloginator()` function
- Ensures `BLOGINATOR_LLM_MOCK` is exported before calling bloginator
- This propagates the fallback setting to all subprocesses

### Console Messages

Users now see explicit feedback:
```
Falling back to assistant mode (Claude will generate responses)...
✓ Switched to assistant mode
```

This makes it clear:
1. What's happening (fallback is occurring)
2. Why (Ollama unavailable)
3. What will happen next (Claude will generate)

## Usage

### Automatic Fallback (Default)
Run the workflow normally. If Ollama is unavailable, it automatically falls back:
```bash
./scripts/run-e2e.sh --clean --restart
```

### Skip Ollama Check Explicitly
To bypass the Ollama check entirely:
```bash
./scripts/run-e2e.sh --skip-ollama --clean --restart
```

## Environment Configuration

The `.env` file controls the behavior:

```env
# LLM Provider (set to ollama initially)
BLOGINATOR_LLM_PROVIDER=ollama

# Ollama server address
BLOGINATOR_LLM_BASE_URL=http://192.168.5.53:11434

# Assistant mode (used as fallback)
BLOGINATOR_LLM_MOCK=assistant
```

When the fallback occurs, `BLOGINATOR_LLM_MOCK=assistant` is set at runtime, and bloginator uses Claude as the LLM backend via file-based request/response system.

## Request/Response Flow

When using assistant mode:

1. **Generate Outline**: bloginator writes outline request to `.bloginator/llm_requests/request_0001.json`
2. **Claude Responds**: Claude reads the request and writes response to `.bloginator/llm_responses/response_0001.json`
3. **Generate Draft**: bloginator writes draft requests, Claude responds
4. **Completion**: Final content is generated from the responses

Each request contains:
- The LLM prompt with corpus search results
- Context about what content needs to be generated
- Expected response format (JSON)

Each response contains:
- Generated content (prose)
- Token counts (for logging)
- Completion reason

## Benefits

1. **Graceful Degradation**: Workflow continues instead of failing
2. **User Clarity**: Explicit messages show what's happening
3. **No Configuration**: Automatic fallback requires no setup
4. **Consistent Quality**: Claude provides consistent content generation
5. **Development Flexibility**: Works in environments without local Ollama

## Troubleshooting

### Still Getting Ollama Errors?
Ensure your `.env` has:
```env
BLOGINATOR_LLM_MOCK=assistant
```

### Want to Force Ollama?
Remove the fallback by removing the changes to `step_check_ollama()`, or:
```bash
./scripts/run-e2e.sh --skip-ollama  # This skips the check entirely
```

### Check Current Mode
When the workflow runs, you'll see in the console:
- `✓ Ollama service verified` = Using Ollama
- `✓ Switched to assistant mode` = Using Claude fallback

## See Also

- [Bloginator LLM Configuration](../README.md#llm-configuration)
- [Assistant Mode Documentation](./ASSISTANT_LLM_MODE.md)
