# TODO: LLM Prompt Tuning

## Date: 2024-12-04

## Issue: Topic Drift in Blog Generation

### Problem Statement

During end-to-end testing with 7 diverse blog topics, ALL generated content defaulted to dashboard/SLI/observability topics regardless of the provided title, keywords, and thesis.

### Test Results

**Requested Topics:**
1. What Great Hiring Managers Actually Do (recruiting/interviewing)
2. How Strong Interviewers Shape Hiring Decisions (interviewing/feedback)
3. How to Run Smarter Interview Loops (interview process)
4. Daily Stand-Up Meetings That Don't Suck (agile/stand-ups)
5. Running an Effective Sprint Planning Session (sprint planning)
6. Running a Fast, Calm Incident Response (incident management)
7. The Role of the Incident Commander (incident commander)

**Actual Generated Content:**
- All 7 blogs generated content about dashboards, SLIs, golden signals, latency metrics, and observability
- Title and thesis were preserved in metadata but ignored in content generation
- Keywords were not reflected in actual content
- Clear evidence that search results from corpus are overwhelming the topic specification

### Technical Details

- **Generation Mode**: Mock LLM (Claude as backend)
- **Word Counts**: 806-1,431 words per blog
- **Voice Scores**: 0.00 (expected - no training samples)
- **Citations**: 5 per blog
- **Speed**: ~2 minutes for all 7 blogs in parallel

### Root Cause Analysis

The LLM generation prompts are not adequately constraining the output to match the specified topic. The semantic search results from the corpus appear to be dominating the generation, causing content to drift toward whatever topics exist in the indexed corpus (in this case, dashboard/observability content).

### Required Fixes

1. **Outline Generation Prompt**
   - Add stronger topic constraint instructions
   - Emphasize title/keywords/thesis MUST be reflected in outline
   - Penalize deviation from specified topic
   - Request explicit topic validation in outline structure

2. **Draft Generation Prompt**
   - Reinforce topic alignment requirement
   - Instruct LLM to filter corpus results by relevance to topic
   - Add instruction to ignore unrelated search results
   - Request topic coherence check before each section

3. **Search Strategy**
   - Consider adjusting search query construction from title/keywords
   - May need to filter search results by relevance threshold
   - Could implement pre-generation corpus relevance check

### Success Criteria

Re-run the same 7 test cases and verify:
- ✅ Content directly addresses the specified topic (not dashboards)
- ✅ Section headings relate to the title
- ✅ Keywords appear naturally in content
- ✅ Thesis is reflected in arguments presented
- ✅ Citations are relevant to the topic

### Testing Protocol

Use the test prompt from `docs/HOW_TO_ASK_FOR_SAMPLES.md` to generate blog samples in mock LLM mode for quality assessment.

### Next Steps

1. Review current outline and draft generation prompt templates
2. Identify where topic constraints are weak or missing
3. Implement prompt improvements
4. Re-test with same 7 blog specifications
5. Compare before/after results
6. Iterate until topic alignment is achieved
