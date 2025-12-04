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

# Current battery of test cases

## Recruiting & Interviewing Series

### 1. What Great Hiring Managers Actually Do

**Keywords:** recruiting, interviewing  
**Audience:** hiring managers, leads  
**Summary:** Defines the hiring manager’s central role as the process owner. Covers how they calibrate expectations, select interviewers, and make final decisions objectively.  
**Sections:**

- Purpose and impact of the hiring manager
- Translating business needs into hiring criteria
- Partnering with recruiters and interviewers
- Common pitfalls (micromanagement, unclear bar)
- How to build a consistent hiring rhythm

---

### 2. How Strong Interviewers Shape Hiring Decisions

**Keywords:** recruiting, interviewing, loops  
**Audience:** interviewers, tech leads  
**Summary:** Explains what good interviewers actually do: prepare thoroughly, ask consistent questions, and document crisp, behavioral evidence tied to competencies.  
**Sections:**

- Purpose of the interviewer in the loop
- Pre-interview preparation checklist
- Writing strong feedback tied to competencies
- Dos and don’ts in interviewer behavior
- Measuring interviewer effectiveness over time

---

### 3. How to Run Smarter Interview Loops

**Keywords:** interviewing, recruiting, pre-loop brief, post-loop debrief  
**Audience:** interview coordinators, hiring managers, interviewers  
**Summary:** Describes how structured interview loops improve signal quality and candidate experience. Covers how to conduct pre-brief and post-brief meetings effectively.  
**Sections:**

- Anatomy of a clean interview loop
- Structuring pre-brief sessions to align questions
- Keeping candidates comfortable and informed
- Running objective post-loop debriefs
- Loop-level documentation and decision hygiene

---

## Agile Rituals Series

### 4. Daily Stand-Up Meetings That Don’t Suck

**Keywords:** agile, ritual, best-practices, stand-up  
**Audience:** software teams, scrum masters  
**Summary:** Provides best practices for running 15-minute daily stand-ups that remain focused, consistent, and energizing.  
**Sections:**

- Purpose of the stand-up
- Common anti-patterns (status reports, tangent debates)
- How to facilitate efficiently in 15 minutes
- Techniques for distributed/hybrid teams
- Example agenda and checklist

---

### 5. Running an Effective Sprint Planning Session

**Keywords:** agile, ritual, sprint planning, best-practices  
**Audience:** engineering teams, product managers  
**Summary:** Explains how to structure sprint planning meetings that yield clear commitments, realistic estimates, and shared context.  
**Sections:**

- Objectives of sprint planning
- The pre-work: backlog readiness and story sizing
- Recommended flow and time allocation
- Identifying blockers early
- Linking sprint goals to performance metrics

---

## Operational Excellence Series

### 6. Running a Fast, Calm Incident Response

**Keywords:** oe, incident-management  
**Audience:** on-call engineers, SREs  
**Summary:** Explores how teams use Slack and bots to manage incidents efficiently while maintaining composure and focus.  
**Sections:**

- Anatomy of a production incident
- Roles and escalation paths
- Using Slack and automation effectively
- Real-time communication principles
- Recovery vs. resolution mindset

---

### 7. The Role of the Incident Commander

**Keywords:** oe, incident-management, incident commander  
**Audience:** engineers, tech leads  
**Summary:** Deep dive into the “Incident Commander” role — the single thread of authority who drives incident mitigation and decision-making.  
**Sections:**

- Responsibilities and behaviors of an IC
- Delegation patterns and support roles (comms, scribe)
- Maintaining calm authority under pressure
- When to hand off command
