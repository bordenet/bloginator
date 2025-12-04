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
