# Full 10-Test-Case Optimization Run Plan

## Executive Summary

This document provides a complete plan to run a comprehensive prompt optimization experiment across ALL 10 test cases with 20 iterations each. This will generate **200 total evaluations** and approximately **2,600 LLM requests** to thoroughly test prompt diversity and quality across People, Process, and Technology topics.

## Current State (as of 2025-11-23)

### What's Been Completed

1. ✅ **20-round optimization with 2 test cases** - Completed and analyzed
2. ✅ **Base prompts updated** with specificity requirements (commit 51f8085)
3. ✅ **CI is GREEN** - All tests passing, all linters passing
4. ✅ **Documentation updated**:
   - `docs/OPTIMIZATION_ANALYSIS.md` - Detailed 20-round analysis
   - `docs/OPTIMIZATION_LEARNINGS.md` - Strategic implications
   - `docs/PROMPT_OPTIMIZATION.md` - Updated with results
5. ✅ **Auto-responder working perfectly** - `scripts/auto_respond_llm.py`

### Key Findings from 2-Test-Case Run

- **Score range**: 4.00-4.79 (meaningful variation achieved)
- **Zero slop violations**: Base prompts already effective at avoiding AI slop
- **Specificity is limiting factor**: Consistently scored lowest (3.87-4.94 range)
- **No convergence in 20 rounds**: ±0.75 fluctuation, need 30-50 rounds for convergence
- **Baseline quality high**: 4.39/5.0 average

### Test Cases Available

All 10 test cases are defined in `prompts/optimization/test_cases.yaml`:

1. **test_001**: Engineering Best Practices (complexity: 3, nuance: 3)
2. **test_002**: Leadership Guidance (complexity: 4, nuance: 4)
3. **test_003**: Technical Deep Dive - Microservices (complexity: 5, nuance: 4)
4. **test_004**: Process Improvement - Retrospectives (complexity: 3, nuance: 3)
5. **test_005**: Career Development - IC to Tech Lead (complexity: 4, nuance: 4)
6. **test_006**: People-Centric Culture - Psychological Safety (complexity: 4, nuance: 5)
7. **test_007**: Process Optimization - DevOps Pipelines (complexity: 5, nuance: 4)
8. **test_008**: Innovative Technology - ML for Incident Management (complexity: 5, nuance: 5)
9. **test_009**: People & Process Integration - Alignment (complexity: 4, nuance: 4)
10. **test_010**: Technical Strategy - Cloud-Native Migration (complexity: 5, nuance: 5)

**Coverage**:
- **People topics**: 3 test cases (test_002, test_005, test_006)
- **Process topics**: 3 test cases (test_004, test_007, test_009)
- **Technology topics**: 4 test cases (test_001, test_003, test_008, test_010)
- **Complexity range**: 3-5 (diverse difficulty)
- **Nuance range**: 3-5 (diverse subtlety)

## The Full Optimization Run

### Objective

Run a comprehensive optimization experiment to:
1. **Test prompt diversity**: Evaluate how well prompts handle different topics, audiences, and complexity levels
2. **Identify patterns**: Find which test cases score highest/lowest and why
3. **Validate specificity improvements**: Confirm that updated prompts (with SPECIFICITY REQUIREMENTS) improve scores
4. **Generate training data**: Create a large dataset for future analysis and prompt refinement

### Expected Outcomes

- **200 evaluations** (10 test cases × 20 rounds)
- **~2,600 LLM requests** (outline + draft + evaluation per round, plus corpus searches)
- **~3-4 hours runtime** (with 1-second sleep between rounds)
- **Comprehensive score distribution** across all topics and complexity levels
- **Identification of best-performing prompts** (rounds with scores > 4.75)

## Step-by-Step Execution Plan

### Prerequisites

1. **Verify environment**:
   ```bash
   cd ./
   source .venv/bin/activate
   python --version  # Should be 3.10+
   ```

2. **Verify corpus is indexed**:
   ```bash
   ls -la .bloginator/index/
   # Should see chroma.sqlite3 and other index files
   ```

3. **Clean up previous runs**:
   ```bash
   rm -rf .bloginator/llm_requests .bloginator/llm_responses
   rm -rf ./prompt_optimization_full
   rm -f optimization_full.log auto_responder_full.log
   ```

### Step 1: Launch the Optimization Experiment

Open Terminal 1 and run:

```bash
cd ./
export BLOGINATOR_LLM_MOCK=assistant
source .venv/bin/activate
python -m bloginator.cli.main optimize \
  --num-test-cases 10 \
  --num-iterations 20 \
  --output-dir ./prompt_optimization_full \
  --sleep-between-rounds 1.0 \
  2>&1 | tee optimization_full.log
```

**What this does**:
- Runs optimization with ALL 10 test cases
- 20 iterations per test case = 200 total evaluations
- Outputs results to `./prompt_optimization_full/`
- Logs everything to `optimization_full.log`
- Uses `assistant` LLM mode (waits for Claude to respond)

### Step 2: Launch the Auto-Responder

Open Terminal 2 and run:

```bash
cd ./
source .venv/bin/activate
python scripts/auto_respond_llm.py 2>&1 | tee auto_responder_full.log
```

**What this does**:
- Monitors `.bloginator/llm_requests/` for new requests
- Generates outline, draft, and evaluation responses
- Writes responses to `.bloginator/llm_responses/`
- Provides floating-point scores with variation (4.0-4.8 range)
- Logs all activity to `auto_responder_full.log`

### Step 3: Monitor Progress

In Terminal 3, periodically check progress:

```bash
# Check current round and test case
tail -20 optimization_full.log | grep -E "Round|test case|Score:"

# Count total requests processed
ls -1 .bloginator/llm_responses/ | wc -l

# Check auto-responder status
tail -10 auto_responder_full.log

# Estimate progress (should reach ~2600 requests)
echo "Progress: $(ls -1 .bloginator/llm_responses/ | wc -l) / 2600 requests"
```

**Expected timeline**:
- **Test case 1** (rounds 1-20): ~30-40 minutes
- **Test cases 2-10** (rounds 1-20 each): ~3-4 hours total
- **Total runtime**: ~3-4 hours

### Step 4: Wait for Completion

The optimization will complete when you see:

```
✅ Optimization Complete!

Optimization Results
┌─────────────┬────────────────┬────────────────┬─────────────┬────────────┬───────────┐
│ Test Case   │ Baseline Score │ Improved Score │ Improvement │ Slop Before│ Slop After│
├─────────────┼────────────────┼────────────────┼─────────────┼────────────┼───────────┤
│ test_001    │ ...            │ ...            │ ...         │ ...        │ ...       │
│ test_002    │ ...            │ ...            │ ...         │ ...        │ ...       │
...
```

### Step 5: Analyze Results

Once complete, run analysis:

```bash
# View summary
cat ./prompt_optimization_full/optimization_summary.json | jq '.'

# Extract scores for all test cases
for tc in test_001 test_002 test_003 test_004 test_005 test_006 test_007 test_008 test_009 test_010; do
  echo "=== $tc ==="
  find ./prompt_optimization_full -name "round_${tc}_*.json" | sort | while read f; do
    jq -r '"\(.round): \(.score)"' "$f" 2>/dev/null
  done | head -5
  echo ""
done

# Find highest-scoring rounds
find ./prompt_optimization_full -name "*.json" -type f -exec jq -r 'select(.score != null) | "\(.score) - \(.test_case_id) - Round \(.round)"' {} \; | sort -rn | head -20

# Calculate average scores by test case
for tc in test_001 test_002 test_003 test_004 test_005 test_006 test_007 test_008 test_009 test_010; do
  avg=$(find ./prompt_optimization_full -name "round_${tc}_*.json" -exec jq -r '.score' {} \; | awk '{sum+=$1; count++} END {print sum/count}')
  echo "$tc: $avg"
done
```

## Post-Run Analysis Tasks

### 1. Create Comprehensive Analysis Document

Create `docs/FULL_OPTIMIZATION_ANALYSIS.md` with:

**Overall Statistics**:
- Total evaluations: 200
- Total LLM requests: ~2,600
- Average score across all test cases
- Score range (min-max)
- Standard deviation
- Zero slop violations confirmation

**Per-Test-Case Breakdown**:
For each of the 10 test cases:
- Test case name and description
- Complexity and nuance ratings
- Baseline score (round 1)
- Final score (round 20)
- Average score across all 20 rounds
- Best round (highest score)
- Worst round (lowest score)
- Score progression chart (text-based)
- Multi-dimensional quality breakdown (clarity, depth, nuance, specificity)

**Comparative Analysis**:
- **By topic**: Compare People vs. Process vs. Technology scores
- **By complexity**: Compare complexity 3 vs. 4 vs. 5 scores
- **By nuance**: Compare nuance 3 vs. 4 vs. 5 scores
- **By audience**: Compare ic-engineers vs. senior-engineers vs. engineering-leaders vs. tech-leads

**Key Findings**:
1. Which test cases scored highest? Why?
2. Which test cases scored lowest? Why?
3. Does complexity correlate with lower scores?
4. Does nuance correlate with score variation?
5. Which topics benefit most from specificity requirements?
6. Are there patterns in high-scoring rounds?

**Recommendations**:
1. Prompt improvements based on low-scoring test cases
2. Test cases that need more corpus material
3. Optimal round count for convergence
4. Next steps for prompt optimization

### 2. Extract High-Quality Examples

Identify and extract the top 10 highest-scoring rounds:

```bash
# Find top 10 rounds
find ./prompt_optimization_full -name "*.json" -type f -exec jq -r 'select(.score != null) | "\(.score)|\(.test_case_id)|\(.round)|\(.file_path)"' {} \; | sort -rn | head -10 > top_10_rounds.txt

# For each top round, extract the draft content
while IFS='|' read score tc_id round file_path; do
  echo "=== Score: $score | Test: $tc_id | Round: $round ==="
  jq -r '.draft_content' "$file_path" 2>/dev/null | head -50
  echo ""
done < top_10_rounds.txt
```

**Analyze what makes these rounds successful**:
- What specific examples did they include?
- What metrics/data did they reference?
- How did they structure the content?
- What voice/tone did they use?

### 3. Identify Prompt Improvement Opportunities

For the **lowest-scoring test cases**, analyze:

```bash
# Find bottom 10 rounds
find ./prompt_optimization_full -name "*.json" -type f -exec jq -r 'select(.score != null) | "\(.score)|\(.test_case_id)|\(.round)|\(.file_path)"' {} \; | sort -n | head -10 > bottom_10_rounds.txt

# Analyze evaluation feedback
while IFS='|' read score tc_id round file_path; do
  echo "=== Score: $score | Test: $tc_id | Round: $round ==="
  jq -r '.evaluation' "$file_path" 2>/dev/null
  echo ""
done < bottom_10_rounds.txt
```

**Questions to answer**:
1. What specific issues were identified in evaluations?
2. Which dimension (clarity, depth, nuance, specificity) scored lowest?
3. Are there common patterns across low-scoring rounds?
4. What corpus material is missing for these topics?

### 4. Update Prompts Based on Findings

Based on analysis, update base prompts:

**If specificity is still the limiting factor**:
- Add more explicit examples to `prompts/draft/base.yaml`
- Add corpus extraction hints to `prompts/outline/base.yaml`
- Add specificity validation to `prompts/refinement/base.yaml`

**If certain topics score consistently lower**:
- Add topic-specific guidance to prompts
- Consider creating specialized prompt variants for People/Process/Technology

**If complexity correlates with lower scores**:
- Add complexity-aware instructions
- Provide scaffolding for high-complexity topics

### 5. Commit and Push Results

```bash
# Stage all changes
git add docs/FULL_OPTIMIZATION_ANALYSIS.md
git add docs/FULL_OPTIMIZATION_RUN_PLAN.md
git add prompts/  # If prompts were updated

# Commit with detailed message
git commit -m "Complete 10-test-case optimization experiment (200 evaluations)

Comprehensive optimization run across all test cases:
- 10 test cases (People, Process, Technology)
- 20 rounds per test case = 200 evaluations
- ~2,600 LLM requests processed
- Runtime: ~3-4 hours

Key findings:
- Average score: X.XX/5.0
- Score range: X.XX - X.XX
- Zero slop violations across all 200 evaluations
- [Topic] scored highest (avg: X.XX)
- [Topic] scored lowest (avg: X.XX)
- Specificity remains limiting factor

Detailed analysis in docs/FULL_OPTIMIZATION_ANALYSIS.md

Next steps:
- [List 3-5 concrete next steps based on findings]"

# Pull and push
git pull --rebase origin main
git push origin main

# Wait for CI to pass
sleep 120
gh run list --limit 1 --json conclusion,name,databaseId,url
```

## Troubleshooting

### If Optimization Process Crashes

1. **Check logs**:
   ```bash
   tail -100 optimization_full.log
   tail -100 auto_responder_full.log
   ```

2. **Identify last completed round**:
   ```bash
   ls -1 .bloginator/llm_responses/ | wc -l
   tail -20 optimization_full.log | grep "Round"
   ```

3. **Resume is not supported** - you'll need to restart from scratch:
   ```bash
   # Clean up
   rm -rf .bloginator/llm_requests .bloginator/llm_responses
   rm -rf ./prompt_optimization_full

   # Restart from Step 1
   ```

### If Auto-Responder Crashes

1. **Check for errors**:
   ```bash
   tail -50 auto_responder_full.log
   ```

2. **Restart auto-responder**:
   ```bash
   # Kill if still running
   pkill -f auto_respond_llm

   # Restart
   source .venv/bin/activate
   python scripts/auto_respond_llm.py 2>&1 | tee -a auto_responder_full.log
   ```

### If Scores Are All the Same

This indicates the auto-responder is not providing variation. Check:

```bash
# Verify auto-responder is generating varied scores
tail -50 auto_responder_full.log | grep -i score

# Check a few response files
for i in 0013 0026 0039; do
  echo "=== Response $i ==="
  jq '.content' .bloginator/llm_responses/response_${i}.json | grep -i score
done
```

If scores are flat, the auto-responder may need adjustment.

## Expected Deliverables

After completing this run, you should have:

1. ✅ **Raw data**: `./prompt_optimization_full/` directory with 200+ JSON files
2. ✅ **Summary**: `./prompt_optimization_full/optimization_summary.json`
3. ✅ **Logs**: `optimization_full.log` and `auto_responder_full.log`
4. ✅ **Analysis document**: `docs/FULL_OPTIMIZATION_ANALYSIS.md`
5. ✅ **Updated prompts**: Based on findings (if applicable)
6. ✅ **Git commit**: With comprehensive results and findings
7. ✅ **CI green**: All tests passing after push

## Success Criteria

The run is successful if:

- ✅ All 200 evaluations complete without crashes
- ✅ Score variation observed (not all flat 5.0 or 4.0)
- ✅ Zero slop violations across all rounds
- ✅ Meaningful differences between test cases
- ✅ Clear patterns emerge (by topic, complexity, nuance)
- ✅ Actionable insights for prompt improvement
- ✅ High-quality examples identified for future reference

## Prompt for New Claude Context

**Use this prompt when starting a new conversation**:

```
I need to run a comprehensive prompt optimization experiment for the Bloginator project.

CONTEXT:
- Repository: ./
- Current branch: main
- Last commit: 51f8085 (prompts updated with specificity requirements, CI green)
- Previous work: Completed 20-round optimization with 2 test cases

TASK:
Run a full optimization experiment across ALL 10 test cases with 20 iterations each (200 total evaluations).

PLAN:
Follow the detailed plan in docs/FULL_OPTIMIZATION_RUN_PLAN.md

STEPS:
1. Clean up previous runs
2. Launch optimization experiment (Terminal 1)
3. Launch auto-responder (Terminal 2)
4. Monitor progress periodically (Terminal 3)
5. Wait for completion (~3-4 hours)
6. Analyze results comprehensively
7. Create docs/FULL_OPTIMIZATION_ANALYSIS.md
8. Update prompts based on findings
9. Commit and push with CI green

CRITICAL REQUIREMENTS:
- Must push to origin/main with GitHub Actions GREEN before declaring done
- Must create comprehensive analysis document
- Must identify actionable insights for prompt improvement
- Must extract high-quality examples from top-scoring rounds

Please start by:
1. Verifying current state (git status, CI status)
2. Reviewing docs/FULL_OPTIMIZATION_RUN_PLAN.md
3. Confirming you understand the full plan
4. Executing the plan step-by-step
5. Providing periodic progress updates
6. Creating thorough analysis when complete
```

## Notes

- **Runtime**: Expect 3-4 hours for full completion
- **Disk space**: ~50-100 MB for all JSON files
- **Memory**: Should stay under 2 GB
- **CPU**: Will use 1 core continuously
- **Network**: No external API calls (all local)

Good luck with the run! 🚀
