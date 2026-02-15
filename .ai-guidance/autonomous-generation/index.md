# Autonomous Generation Index

> **When to load:** Overview of autonomous blog generation modules

## Sub-Modules

| Module | Description |
|--------|-------------|
| [pipeline.md](pipeline.md) | Full generation workflow |
| [synthesis.md](synthesis.md) | Content synthesis rules |
| [voice-matching.md](voice-matching.md) | Voice matching & deduplication |
| [batch-topics.md](batch-topics.md) | Batch processing multiple topics |

## Quick Reference

| Step | Action |
|------|--------|
| 1 | Pick topic from `corpus/blog-topics.yaml` |
| 2 | Run `bloginator outline` with batch mode |
| 3 | Read requests, synthesize from sources |
| 4 | Run `bloginator draft` with batch mode |
| 5 | Read requests, synthesize from sources |
| 6 | Verify output (word count, citations, no slop) |

