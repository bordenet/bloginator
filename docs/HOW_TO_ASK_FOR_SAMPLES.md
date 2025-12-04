# How to Request Blog Sample Generation for Testing

## Quick Prompt

Use this concise prompt when you want Claude to generate blog samples in mock LLM mode:

```
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

```
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
3. **Auto-Respond**: Run `scripts/auto_respond.py` in a loop to handle LLM requests
4. **Monitor Progress**: Track generation status for all blogs
5. **Quality Assessment**: Review generated content and report:
   - Topic alignment issues
   - Content quality observations
   - Systematic problems (e.g., topic drift)
   - Word counts and metadata

## Directory Structure

Generated blogs appear in:
```
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

These test cases directly mirror content from the `test-corpus/Engineering_Culture` repository.
Anyone cloning the repo can run these to validate the end-to-end pipeline.

## Engineering Fundamentals Series

### 1. Building Dashboards That Drive Action

**Keywords:** dashboard, observability, metrics, SLI
**Audience:** engineers, SREs, tech leads
**Corpus Source:** `EngFundamentals/How_to_Construct_a_Useful_Dashboard.md`, `EngFundamentals/What_Dashboards_are_Good_For.md`
**Summary:** Explains how to construct dashboards that surface actionable insights rather than vanity metrics. Covers SLI selection, layout principles, and avoiding dashboard sprawl.
**Sections:**

- What dashboards are actually good for
- Selecting meaningful SLIs and metrics
- Dashboard layout and hierarchy principles
- Common anti-patterns (vanity metrics, too many charts)
- Maintaining dashboards over time

---

### 2. The Road to a Meaningful SLA

**Keywords:** SLA, SLO, SLI, reliability, service-level
**Audience:** engineers, product managers, SREs
**Corpus Source:** `EngFundamentals/The_Road_to_an_SLA.md`
**Summary:** Walks through the journey from defining SLIs to establishing SLOs and committing to SLAs. Covers the relationship between these concepts and how to set realistic targets.
**Sections:**

- Understanding SLI, SLO, and SLA relationships
- Choosing the right indicators for your service
- Setting realistic objectives based on data
- Communicating SLAs to stakeholders
- Error budgets and tradeoffs

---

### 3. SOA and Microservices: Choosing the Right Architecture

**Keywords:** SOA, microservices, architecture, distributed-systems
**Audience:** engineers, architects, tech leads
**Corpus Source:** `EngFundamentals/SOA_and_Microservices.md`
**Summary:** Compares service-oriented architecture with microservices, helping teams understand when each approach fits. Covers tradeoffs, organizational implications, and migration strategies.
**Sections:**

- What SOA and microservices actually mean
- When to choose monolith vs. distributed
- Organizational implications (Conway's Law connection)
- Migration strategies and pitfalls
- Operational complexity tradeoffs

---

## Engineering Culture Series

### 4. Understanding Conway's Law in Practice

**Keywords:** Conway's Law, organization, architecture, team-structure
**Audience:** engineers, managers, architects
**Corpus Source:** `Culture/Understanding_Conways_Law.md`
**Summary:** Explores how organizational structure shapes system architecture and vice versa. Provides practical guidance for aligning teams and systems.
**Sections:**

- What Conway's Law actually says
- How team boundaries become system boundaries
- Inverse Conway Maneuver: designing teams for desired architecture
- Real-world examples and anti-patterns
- Practical steps for alignment

---

### 5. Giving Effective Feedback with the SBI Model

**Keywords:** feedback, SBI, communication, culture
**Audience:** managers, leads, all engineers
**Corpus Source:** `Culture/Constructive_Feedback_SBI_Model.md`
**Summary:** Introduces the Situation-Behavior-Impact model for delivering clear, constructive feedback that drives improvement without defensiveness.
**Sections:**

- Why feedback often fails
- The SBI model explained
- Structuring feedback conversations
- Receiving feedback effectively
- Building a feedback culture

---

## SDLC Series

### 6. Building Self-Correcting Systems with Mechanisms

**Keywords:** mechanisms, process, automation, self-correcting
**Audience:** engineers, managers, tech leads
**Corpus Source:** `SDLC/Mechanisms:_Building_Self-Correcting_Systems.md`
**Summary:** Explains how to design processes and systems that automatically detect and correct problems, reducing reliance on heroics and manual intervention.
**Sections:**

- What makes a mechanism effective
- Self-correcting vs. self-reporting systems
- Examples of engineering mechanisms
- Designing new mechanisms
- Measuring mechanism effectiveness

---

### 7. Writing Effective One-Pagers and PR-FAQs

**Keywords:** one-pager, PR-FAQ, planning, documentation
**Audience:** engineers, product managers, tech leads
**Corpus Source:** `SDLC/The_One-Pager.md`, `SDLC/The_PR-FAQ.md`, `SDLC/Project_Planning_Mechanisms:_Documents.md`
**Summary:** Covers the purpose and structure of one-pagers and PR-FAQs as planning mechanisms. Explains when to use each and how to write them effectively.
**Sections:**

- Purpose of planning documents
- One-pager structure and best practices
- PR-FAQ structure and best practices
- Choosing between document types
- Common pitfalls and how to avoid them
