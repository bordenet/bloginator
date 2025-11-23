# LLM Prompts

This directory contains all LLM prompts used by Bloginator for content generation.

## Purpose

Externalizing prompts enables:
- **Optimization**: Automated tools can experiment with prompt variations
- **Version Control**: Track prompt changes and their impact on output quality
- **Transparency**: Clear visibility into what instructions are sent to LLMs
- **Tuning**: Iterative improvement of voice matching and quality

## Structure

```
prompts/
├── outline/          # Outline generation prompts
├── draft/            # Draft generation prompts
├── refinement/       # Content refinement prompts
└── README.md         # This file
```

## Format

Prompts are stored as YAML files with the following structure:

```yaml
# Metadata
name: "prompt-name"
version: "1.0.0"
description: "What this prompt does"
context: "When and why this prompt is used"

# The actual prompt
system_prompt: |
  System-level instructions for the LLM...

user_prompt_template: |
  User prompt with {{variables}} for substitution...

# Configuration
parameters:
  temperature: 0.7
  max_tokens: 2000

# Quality criteria
quality_criteria:
  - "No em-dashes or AI slop"
  - "Matches corpus voice"
  - "Factually grounded in sources"
```

## Variables

Prompts use Jinja2 template syntax for variable substitution:

- `{{title}}` - Document title
- `{{keywords}}` - List of keywords
- `{{thesis}}` - Thesis statement
- `{{classification}}` - Content classification
- `{{audience}}` - Target audience
- `{{context}}` - Retrieved corpus content
- `{{max_words}}` - Target word count

## Optimization

The prompt optimization framework (`src/bloginator/optimization/`) uses these prompts to:

1. Generate test content with different prompt variations
2. Score results against quality criteria
3. Iteratively improve prompts based on scores
4. Track performance metrics over time

See `docs/PROMPT_OPTIMIZATION.md` for details.
