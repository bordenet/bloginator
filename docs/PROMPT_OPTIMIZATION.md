# Evolutionary Prompt Optimization Framework

## Executive Summary

This document describes the sophisticated evolutionary optimization apparatus for iteratively improving LLM prompts used in blog generation. The system uses AI-driven evaluation and strategic prompt mutations across multiple rounds to eliminate AI slop, match author voice, and improve content quality.

## Why: Requirements and Motivation

### Primary Objectives

1. **Eliminate AI Slop**: Remove telltale signs of AI-generated content
   - Critical violations: Em-dashes (—), flowery corporate jargon
   - Medium/Low violations: Hedging words, vague language

2. **Match Author Voice**: Ensure generated content sounds authentic
   - Analyze corpus to extract voice patterns
   - Score generated content against authentic voice
   - Iteratively adjust prompts to better match

3. **Improve Content Quality**: Enhance clarity, depth, nuance, and specificity
   - Target complexity levels (1-5 scale)
   - Target nuance levels (1-5 scale)
   - Provide concrete examples vs. abstract platitudes

4. **Scientific Rigor**: Conduct measurable, reproducible experiments
   - One variable change per round to isolate impact
   - Detailed logging of all decisions and outcomes
   - Convergence analysis to determine optimal round count

### Success Criteria

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| **Slop Elimination** | Critical violations per 1000 words | < 0.1 |
| **Voice Match** | Authenticity score (0-5) | > 4.0 |
| **Content Quality** | Composite score (clarity + depth + nuance + specificity) / 4 | > 4.0 |
| **Convergence** | Rounds until < 5% score change | < 30 rounds |
| **Improvement** | Final score - Baseline score | > +0.5 |

## What: System Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Optimization Controller                   │
│                      (PromptTuner)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Test     │  │ Content  │  │ AI       │
        │ Cases    │  │ Generator│  │ Evaluator│
        │ (YAML)   │  │          │  │          │
        └──────────┘  └──────────┘  └──────────┘
                              │             │
                              ▼             ▼
                      ┌──────────┐  ┌──────────┐
                      │ Outline  │  │ Meta     │
                      │ Draft    │  │ Prompt   │
                      │ Refine   │  │ (YAML)   │
                      └──────────┘  └──────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │ Slop         │
                      │ Detector     │
                      └──────────────┘
```

### Data Flow

1. **Initialization**
   - Load test cases from `prompts/optimization/test_cases.yaml`
   - Load meta-prompt from `prompts/optimization/meta_prompt.yaml`
   - Initialize LLM client (AssistantLLMClient for file-based communication)
   - Initialize corpus searcher with indexed documents

2. **Per-Round Execution**
   ```
   For each test case:
     For each round (1 to N):
       1. Generate outline using current prompts
       2. Generate draft using current prompts
       3. Detect slop violations
       4. Request AI evaluation via meta-prompt
       5. Parse evaluation JSON (score, violations, strategy)
       6. Log results and evolutionary strategy
       7. Sleep to avoid overwhelming LLM
       8. (Future) Apply prompt mutations based on strategy
   ```

3. **AI Evaluation Process**
   - Render meta-prompt with test case context and generated content
   - Submit to LLM (AI assistant via file-based communication)
   - Receive structured JSON evaluation with:
     - Numerical scores (0-5 scale)
     - Detailed violation analysis
     - Voice authenticity assessment
     - Content quality breakdown
     - **Evolutionary strategy** (which prompt to modify, how, and why)

4. **Results Aggregation**
   - Save per-round results: `round_{test_id}_r{num:03d}.json`
   - Save per-test-case summary: `result_{test_id}.json`
   - Save overall summary: `optimization_summary.json`
   - Calculate convergence metrics
   - Generate recommendations

### File-Based LLM Communication (AssistantLLMClient)

**Why**: Enables AI assistant (Claude) to act as the LLM without API keys or external services.

**How**:
1. Write request to `.bloginator/llm_requests/request_NNNN.json`
2. Poll for response file `.bloginator/llm_responses/response_NNNN.json`
3. Parse and return response

**Request Format**:
```json
{
  "request_id": 1,
  "model": "assistant-llm",
  "temperature": 0.3,
  "max_tokens": 3000,
  "system_prompt": null,
  "prompt": "...",
  "timestamp": 1234567890.123
}
```

**Response Format**:
```json
{
  "content": "...",
  "prompt_tokens": 500,
  "completion_tokens": 1500,
  "finish_reason": "stop"
}
```

## How: Implementation Details

### Test Cases

Defined in `prompts/optimization/test_cases.yaml`:
- 10 diverse test cases covering People, Process, Technology
- Each with complexity (1-5) and nuance (1-5) ratings
- Classifications: best-practice, guidance, culture, innovation
- Audiences: ic-engineers, senior-engineers, engineering-leaders, tech-leads

### Meta-Prompt

Defined in `prompts/optimization/meta_prompt.yaml`:
- Guides AI assistant in evaluating content
- Provides structured JSON output format
- Includes evolutionary strategy guidelines:
  - Rounds 1-20: Eliminate critical slop
  - Rounds 21-40: Voice matching
  - Rounds 41-60: Depth and nuance
  - Rounds 61-80: Specificity
  - Rounds 81-99: Fine-tuning

### Evolutionary Strategy

Each round produces a strategy with:
- `prompt_to_modify`: Which prompt file (outline/draft/refinement)
- `specific_changes`: Array of concrete modifications
  - `section`: Which part of the prompt
  - `current_issue`: What's wrong
  - `proposed_change`: Specific modification
  - `rationale`: Why this will help
- `priority`: high/medium/low
- `expected_impact`: Description of expected improvement

### Measurement and Analysis

**Per-Round Metrics**:
- Score (0-5)
- Violation counts by severity (critical, high, medium, low)
- Voice authenticity (0-5)
- Content quality dimensions (clarity, depth, nuance, specificity)

**Convergence Detection**:
- Track score changes between rounds
- Identify when changes drop below 5% threshold
- Recommend optimal round count

**Success Validation**:
- Compare final vs. baseline scores
- Verify violation reduction
- Confirm voice match improvement
- Validate content quality gains

## Execution Plan

### Phase 1: 99-Round Experiment (Current)
- Run with 2 test cases
- 2-second sleep between rounds
- Collect comprehensive data
- Determine optimal round count

### Phase 2: Analysis
- Run convergence analysis script
- Identify optimal round count
- Review evolutionary strategies
- Document prompt evolution

### Phase 3: Validation
- Re-run with optimal round count
- Verify improvements are reproducible
- Compare original vs. optimized prompts (git diff)
- Measure success criteria achievement

## Next Steps

1. ✅ Complete refactor with AI evaluation
2. ✅ Add sleep between rounds
3. ✅ Document architecture
4. ⏳ Execute 99-round experiment
5. ⏳ Analyze results and determine optimal rounds
6. ⏳ Show git diff of prompt evolution
7. ⏳ Validate success criteria
