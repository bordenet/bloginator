"""Mock response generation utilities for testing."""


def detect_outline_request(prompt: str) -> bool:
    """Check if prompt is requesting an outline.

    Args:
        prompt: User prompt

    Returns:
        True if outline request detected
    """
    outline_keywords = [
        "outline",
        "section",
        "structure",
        "organize",
        "table of contents",
    ]
    return any(keyword in prompt.lower() for keyword in outline_keywords)


def detect_draft_request(prompt: str) -> bool:
    """Check if prompt is requesting draft content.

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
    return any(keyword in prompt.lower() for keyword in draft_keywords)


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


def generate_mock_draft(prompt: str) -> str:
    """Generate mock draft content.

    Args:
        prompt: Draft generation prompt

    Returns:
        Realistic paragraph content
    """
    # Extract section title if present
    section = "this topic"
    if "section:" in prompt.lower() or "title:" in prompt.lower():
        lines = prompt.split("\n")
        for line in lines:
            if "section:" in line.lower() or "title:" in line.lower():
                section = line.split(":", 1)[1].strip().lower()
                break

    # Generate realistic content
    return f"""When considering {section}, it's important to understand both the theoretical
foundations and practical applications. Based on established best practices and real-world
experience, successful teams tend to focus on a few key areas.

First, establishing clear communication channels and expectations helps ensure everyone is
aligned on goals and approach. This includes both synchronous and asynchronous methods,
with documentation serving as a critical reference point.

Second, building iterative processes allows teams to learn and adapt as they progress.
Rather than trying to achieve perfection upfront, successful practitioners embrace
incremental improvement and continuous refinement. This approach reduces risk while
maintaining forward momentum.

Third, measuring outcomes and gathering feedback creates accountability and enables
data-driven decision making. Teams that regularly assess their progress and adjust based
on results tend to achieve better outcomes than those that operate on assumptions alone.

These principles, when applied consistently and thoughtfully, form the foundation for
sustainable success in this domain. The specific implementation details will vary based
on team context, organizational culture, and technical constraints, but the underlying
concepts remain broadly applicable across different environments and scenarios.
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
