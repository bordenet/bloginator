"""Mock response generation utilities for testing."""


def detect_outline_request(prompt: str) -> bool:
    """Check if prompt is requesting an outline.

    Only checks the prompt's opening instruction line, not the full text --
    source material and formatting guidance quoted later in the prompt can
    otherwise contain any of these words incidentally and misroute the mock.

    Args:
        prompt: User prompt

    Returns:
        True if outline request detected
    """
    outline_keywords = [
        "outline",
        "structure",
        "organize",
        "table of contents",
    ]
    first_line = prompt.strip().split("\n", 1)[0].lower()
    return any(keyword in first_line for keyword in outline_keywords)


def detect_draft_request(prompt: str) -> bool:
    """Check if prompt is requesting draft content.

    Only checks the prompt's opening instruction line -- see
    detect_outline_request for why.

    Args:
        prompt: User prompt

    Returns:
        True if draft request detected
    """
    draft_keywords = [
        "write",
        "draft",
        "paragraph",
        "expand",
        "content for",
    ]
    first_line = prompt.strip().split("\n", 1)[0].lower()
    return any(keyword in first_line for keyword in draft_keywords)


def detect_topic_validation_request(prompt: str) -> bool:
    """Check if prompt is requesting topic validation.

    Args:
        prompt: User prompt

    Returns:
        True if topic validation request detected
    """
    validation_keywords = [
        "validation task",
        "requested topic",
        "validation rules",
        "respond with exactly",
    ]
    return any(keyword in prompt.lower() for keyword in validation_keywords)


def detect_quality_review_request(prompt: str) -> bool:
    """Check if prompt is requesting quality review.

    Args:
        prompt: User prompt

    Returns:
        True if quality review request detected
    """
    review_keywords = [
        "review this blog",
        "quality review",
        "revise",
        "ruthless",
        "senior editor",
        "original draft",
    ]
    return any(keyword in prompt.lower() for keyword in review_keywords)


def generate_mock_outline(prompt: str) -> str:
    """Generate mock outline response.

    Args:
        prompt: Outline generation prompt

    Returns:
        Markdown outline structure
    """
    # Extract title if present
    title = "Engineering Best Practices"
    if "title:" in prompt.lower():
        lines = prompt.split("\n")
        for line in lines:
            if "title:" in line.lower():
                title = line.split(":", 1)[1].strip()
                break

    return f"""## Introduction
Brief overview of {title.lower()} and why this topic matters for engineering teams.

## Background and Context
Historical perspective and industry trends that make this topic relevant today.

### Evolution Over Time
How practices and approaches have changed in recent years.

### Current State
Where the industry stands today on this topic.

## Core Principles
The fundamental concepts and principles that guide effective implementation.

### Key Concept 1
First major principle with practical implications.

### Key Concept 2
Second major principle and how it applies in practice.

## Practical Implementation
Concrete steps and strategies for putting these principles into action.

### Getting Started
Initial steps and foundational approaches.

### Advanced Techniques
More sophisticated methods for experienced practitioners.

## Common Challenges
Obstacles teams typically encounter and how to address them.

## Conclusion
Summary of key takeaways and recommendations for moving forward.
"""


_STOPWORDS = {
    "the",
    "a",
    "an",
    "to",
    "of",
    "for",
    "and",
    "or",
    "in",
    "on",
    "how",
    "this",
    "that",
    "properly",
}


def generate_mock_draft(prompt: str) -> str:
    """Generate mock draft content.

    Args:
        prompt: Draft generation prompt

    Returns:
        Realistic paragraph content, or an ERROR message if the requested
        section topic shares no meaningful words with the supplied source
        material (mirrors a real model refusing to draft from unrelated
        sources).
    """
    lines = prompt.split("\n")

    # "Title:" is the authoritative section name; fall back to the generic
    # "section:" phrase only if no title line is present.
    section = "this topic"
    for line in lines:
        if line.lower().strip().startswith("title:"):
            section = line.split(":", 1)[1].strip().lower()
            break
    else:
        for line in lines:
            if "section:" in line.lower():
                remainder = line.split(":", 1)[1].strip()
                if remainder:
                    section = remainder.lower()
                    break

    # Extract the source material block to check topic grounding.
    source_material = ""
    if "source material:" in prompt.lower():
        source_material = prompt.lower().split("source material:", 1)[1]

    title_words = {w for w in section.split() if len(w) > 3 and w not in _STOPWORDS}
    if title_words and source_material and not any(w in source_material for w in title_words):
        return (
            "ERROR: The provided source material does not appear to match the "
            f"requested topic ({section}). Cannot draft grounded content."
        )

    # Generate realistic content (kept under the brevity limit tested elsewhere)
    return f"""When considering {section}, successful teams tend to focus on a few key areas.

First, clear communication channels and expectations help ensure everyone stays aligned
on goals and approach, with documentation as a critical reference point.

Second, iterative processes let teams learn and adapt as they progress, favoring
incremental improvement over upfront perfection.

Third, measuring outcomes and gathering feedback creates accountability and enables
data-driven decisions.

These principles, applied consistently, form the foundation for sustainable success,
though specifics will vary with team context and constraints.
"""


def generate_mock_quality_review(prompt: str) -> str:
    """Generate mock quality-reviewed blog content.

    Simulates the output of a senior editor who has ruthlessly cut verbosity.

    Args:
        prompt: Quality review prompt containing original draft

    Returns:
        Revised, concise blog content
    """
    return """# Engineering Leadership Best Practices

## What Makes Effective Technical Leaders

Technical leaders balance hands-on work with team enablement. They write code 30-40% of the time while dedicating the rest to architecture decisions, code reviews, and mentoring. This ratio maintains credibility while scaling impact through others.

## Setting Technical Direction

| Artifact | Audience | Update Frequency |
|----------|----------|------------------|
| Tech vision | Executives | Quarterly |
| Architecture docs | Engineers | Per major change |
| Decision records | Team | Per significant choice |

Leaders document decisions in ADRs (Architecture Decision Records) that capture context, options considered, and rationale. This prevents rehashing settled questions.

## Code Review as Leadership Tool

Effective leaders review code for patterns, not syntax. They flag architectural concerns, suggest abstractions, and teach through questions rather than directives. Reviews should take 10-15 minutes and focus on one key improvement.

## Mentoring Without Micromanaging

Give engineers problems, not solutions. Frame challenges with context and constraints, then let them propose approaches. Intervene only when they're stuck or heading toward costly mistakes. This builds judgment faster than prescriptive guidance.

## Making Technical Decisions Stick

Decisions need three elements: clear owner, written rationale, and rollback criteria. Document in ADRs, communicate in team meetings, and reference in code reviews. When teams deviate, point to the ADR rather than relitigating.
"""


def generate_mock_topic_validation(prompt: str) -> str:
    """Generate mock topic validation response.

    Always returns "VALID" for testing to allow outline generation to proceed.

    Args:
        prompt: Topic validation prompt

    Returns:
        "VALID" to indicate corpus matches topic
    """
    return "VALID"


def generate_generic_response() -> str:
    """Generate generic fallback response.

    Returns:
        Generic text content
    """
    return """This is a mock response generated for testing purposes.
In a real scenario, this would be replaced by actual LLM-generated content
based on the specific prompt and context provided. The mock client is designed
to simulate realistic responses without requiring an actual language model service.
"""
