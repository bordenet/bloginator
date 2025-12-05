# How to Request Blog Sample Generation for Testing

## Quick Prompt

Use this concise prompt when you want Claude to generate blog samples in mock LLM mode:

```text
Generate end-to-end blog samples in mock LLM mode (you as the LLM) for these topics:

[Paste your topic list here with title, keywords, and thesis for each]

Run them in parallel using run-e2e.sh --generate-only, respond to LLM requests automatically,
and provide a quality assessment summary including:
- Topic alignment (does content match the requested subject?)
- Word counts
- Any systematic issues discovered

Generated blogs go to output/generated/cli_blog_*/
```

## Example Usage

```text
Generate end-to-end blog samples in mock LLM mode (you as the LLM) for these topics:

1. **What Great Hiring Managers Actually Do**
   Keywords: recruiting, interviewing, hiring manager
   Thesis: Great hiring managers own the process by calibrating expectations,
           selecting skilled interviewers, and making objective final decisions.

2. **Daily Stand-Up Meetings That Don't Suck**
   Keywords: agile, ritual, best-practices, stand-up
   Thesis: Effective 15-minute daily stand-ups stay focused and energizing
           by avoiding status reports and tangent debates.

Run them in parallel using run-e2e.sh --generate-only, respond to LLM requests automatically,
and provide a quality assessment summary.
```

## What Claude Will Do

1. **Verify Mock Mode**: Check `.env` has `BLOGINATOR_LLM_MOCK=assistant`
2. **Launch Generators**: Start `run-e2e.sh --generate-only` for each blog in parallel
3. **Auto-Respond**: Run `scripts/respond-to-llm-requests.py` in a loop to handle LLM requests
4. **Monitor Progress**: Track generation status for all blogs
5. **Quality Assessment**: Review generated content and report:
   - Topic alignment issues
   - Content quality observations
   - Systematic problems (e.g., topic drift)
   - Word counts and metadata

## Directory Structure

Generated blogs appear in:

```text
output/generated/cli_blog_YYYYMMDD_HHMMSS/
├── outline.md
├── draft.md
└── history.json
```

## Notes

- **Mock LLM Mode**: Claude acts as the LLM backend (no Anthropic API key needed)
- **Parallel Execution**: Multiple blogs generate simultaneously for speed
- **Auto-Response**: Claude reads `.bloginator/llm_requests/` and writes to `.bloginator/llm_responses/`
- **Testing Focus**: This workflow is for assessing LLM prompt quality, not production use

# Sample Corpus Test Cases

These test cases use content from the `test-corpus/Engineering_Culture` repository.
They are organized into three categories based on expected signal quality.

---

## Category A: Exact Match (High Signal Baseline)

**Purpose:** Titles match corpus document names exactly. Expect 80-95% coverage
and output that closely mirrors the source document. These are our baseline tests
to verify the pipeline doesn't introduce noise or hallucination.

**Expected Behavior:** Generated blog should be nearly identical to source.

### A1. What Dashboards are Good For

**Keywords:** dashboard, observability, monitoring
**Corpus Source:** `EngFundamentals/What_Dashboards_are_Good_For.md`
**Expected Coverage:** 85-95%
**Validation:** Output structure and key points should match source document closely.

---

### A2. The Road to an SLA

**Keywords:** SLA, SLO, SLI, reliability
**Corpus Source:** `EngFundamentals/The_Road_to_an_SLA.md`
**Expected Coverage:** 85-95%
**Validation:** Output should cover the same journey from SLI→SLO→SLA as source.

---

### A3. Understanding Conway's Law

**Keywords:** Conway's Law, organization, architecture
**Corpus Source:** `Culture/Understanding_Conways_Law.md`
**Expected Coverage:** 85-95%
**Validation:** Output should explain Conway's Law with same examples as source.

---

### A4. Constructive Feedback: The SBI Model

**Keywords:** feedback, SBI, communication
**Corpus Source:** `Culture/Constructive_Feedback_SBI_Model.md`
**Expected Coverage:** 85-95%
**Validation:** Output should explain Situation-Behavior-Impact model as in source.

---

### A5. SOA and Microservices

**Keywords:** SOA, microservices, architecture
**Corpus Source:** `EngFundamentals/SOA_and_Microservices.md`
**Expected Coverage:** 85-95%
**Validation:** Output should compare architectures with same tradeoffs as source.

---

## Category B: Similar Topics (Synthesized Content)

**Purpose:** Titles are related but not identical to corpus. Expect 50-80% coverage
with synthesized content drawing from multiple sources. Tests the system's ability
to compose coherent content from related materials.

**Expected Behavior:** Good quality blog synthesized from corpus materials.

### B1. Building Dashboards That Drive Action

**Keywords:** dashboard, observability, metrics, SLI
**Corpus Source:** `EngFundamentals/How_to_Construct_a_Useful_Dashboard.md`, `EngFundamentals/What_Dashboards_are_Good_For.md`
**Expected Coverage:** 50-75%
**Validation:** Should synthesize from both dashboard documents into coherent guidance.

---

### B2. Writing Effective One-Pagers and PR-FAQs

**Keywords:** one-pager, PR-FAQ, planning, documentation
**Corpus Source:** `SDLC/The_One-Pager.md`, `SDLC/The_PR-FAQ.md`, `SDLC/Project_Planning_Mechanisms:_Documents.md`
**Expected Coverage:** 50-75%
**Validation:** Should synthesize planning document guidance from multiple sources.

---

### B3. Building Self-Correcting Systems with Mechanisms

**Keywords:** mechanisms, process, automation, self-correcting
**Corpus Source:** `SDLC/Mechanisms:_Building_Self-Correcting_Systems.md`
**Expected Coverage:** 60-80%
**Validation:** Should expand on mechanisms concept with practical examples.

---

## Category C: Deliberate Mismatch (Negative Tests)

**Purpose:** Topics have NO relation to the engineering corpus. The system
MUST reject these or produce empty/minimal output. Tests that we don't
hallucinate content when corpus doesn't support the topic.

**Expected Behavior:** REJECTION or <10% coverage with clear warning.

### C1. Training Your First Puppy

**Keywords:** puppy, training, dog, obedience
**Corpus Source:** NONE (engineering corpus has no pet content)
**Expected Coverage:** <10%
**Expected Outcome:** System should REJECT with "insufficient corpus coverage" error.

---

### C2. Best Recipes for Sourdough Bread

**Keywords:** sourdough, bread, baking, fermentation
**Corpus Source:** NONE (engineering corpus has no cooking content)
**Expected Coverage:** <10%
**Expected Outcome:** System should REJECT with "insufficient corpus coverage" error.

---

### C3. Cryptocurrency Investment Strategies

**Keywords:** crypto, bitcoin, investment, blockchain
**Corpus Source:** NONE (engineering corpus has no finance content)
**Expected Coverage:** <10%
**Expected Outcome:** System should REJECT with "insufficient corpus coverage" error.

---

## Test Matrix Summary

| Category | Count | Expected Coverage | Expected Outcome |
|----------|-------|-------------------|------------------|
| A: Exact Match | 5 | 85-95% | Near-identical to source |
| B: Similar | 3 | 50-80% | Good synthesized content |
| C: Mismatch | 3 | <10% | REJECT / No output |

**Total: 11 test cases** covering the full spectrum from high-signal baseline
to deliberate rejection tests.
