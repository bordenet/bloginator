#!/usr/bin/env python3
"""Auto-responder for AssistantLLMClient requests during optimization experiments.

⚠️  DEPRECATED: This script generates template-based responses, not actual
    LLM-quality content. It was created for optimization experiments only.

    For production blog generation, use BLOGINATOR_LLM_MOCK=assistant mode
    with an AI assistant (Claude) providing responses. See docs/QUICK_START_GUIDE.md.

This script monitors .bloginator/llm_requests/ and automatically generates
responses for outline and draft generation requests. For evaluation requests,
it uses a simplified scoring model.

This enables running optimization experiments without manual intervention.
"""

import json
import sys
import time
import warnings
from pathlib import Path
from typing import Any


# Emit deprecation warning at import time
warnings.warn(
    "respond-to-llm-requests-with-llm.py is DEPRECATED. "
    "Use BLOGINATOR_LLM_MOCK=assistant mode with an AI assistant instead. "
    "See docs/QUICK_START_GUIDE.md for the recommended workflow.",
    DeprecationWarning,
    stacklevel=2,
)

# Print warning to stderr for visibility
print(
    "\n⚠️  WARNING: This script is DEPRECATED and produces template-based content.\n"
    "   For quality blog generation, use BLOGINATOR_LLM_MOCK=assistant mode.\n"
    "   See docs/QUICK_START_GUIDE.md for details.\n",
    file=sys.stderr,
)


def generate_outline_response(request: dict[str, Any]) -> str:
    """Generate a reasonable outline based on the request."""
    prompt = request.get("prompt", "")

    # Extract title from prompt
    title_line = [line for line in prompt.split("\n") if line.startswith("Title:")][0]
    title = title_line.replace("Title:", "").strip()

    # Generate a simple but reasonable outline
    outline = f"""## Introduction
Brief overview of {title.lower()} and why it matters.

### Context and Background
Establish the foundation and key concepts.

## Core Concepts
Deep dive into the fundamental principles and practices.

### Key Principles
Explore the essential guidelines and approaches.

### Common Patterns
Identify recurring themes and best practices.

## Practical Application
How to apply these concepts in real-world scenarios.

### Implementation Strategies
Concrete approaches for putting theory into practice.

### Avoiding Pitfalls
Common mistakes and how to prevent them.

## Advanced Considerations
Nuanced aspects and edge cases to consider.

### Scaling and Evolution
How practices adapt as systems and teams grow.

## Conclusion
Summary of key takeaways and next steps."""

    return outline


def generate_draft_response(request: dict[str, Any]) -> str:
    """Generate a reasonable draft section based on the request."""
    prompt = request.get("prompt", "")

    # Extract section info
    lines = prompt.split("\n")
    section_title = "Section"
    for line in lines:
        if line.startswith("Section:"):
            section_title = line.replace("Section:", "").strip()
            break

    # Generate content that avoids slop
    draft = f"""This section explores {section_title.lower()} in practical terms.

The key insight is that effective approaches balance theory with pragmatic constraints. Rather than pursuing abstract ideals, successful implementations focus on measurable outcomes and iterative improvement.

Consider a concrete example: when teams adopt new practices, they often encounter resistance. The solution isn't to force compliance through policy, but to demonstrate value through small wins. Start with a pilot project, measure results, and let success speak for itself.

Three specific strategies prove effective:

First, establish clear metrics before beginning. Without baseline measurements, you can't demonstrate improvement. Track both quantitative data (cycle time, defect rates) and qualitative feedback (team satisfaction, stakeholder confidence).

Second, create feedback loops that surface problems early. Weekly retrospectives, automated monitoring, and regular check-ins prevent small issues from becoming major obstacles. The goal is continuous adjustment, not perfect planning.

Third, document decisions and their rationale. Future team members will thank you. When someone asks "why did we do it this way?" the answer should be readily available, not lost to institutional memory.

The evidence supports this approach. Organizations that adopt these practices report measurable improvements in delivery speed and quality. More importantly, teams report higher satisfaction and lower burnout.

This isn't theoretical. It works because it respects how humans actually collaborate and learn."""

    return draft


def generate_evaluation_response(request: dict[str, Any]) -> dict[str, Any]:
    """Generate a simplified evaluation response."""
    # For now, return a moderate score with some variation
    import random

    random.seed(int(time.time() * 1000) % 10000)

    base_score = 4.0 + random.random() * 0.8  # 4.0-4.8 range

    evaluation = {
        "score": round(base_score, 2),
        "slop_violations": {"critical": [], "high": [], "medium": [], "low": []},
        "voice_analysis": {
            "authenticity_score": round(base_score, 2),
            "strengths": ["Direct language", "Concrete examples"],
            "concerns": [],
        },
        "content_quality": {
            "clarity": round(base_score + random.uniform(-0.2, 0.2), 2),
            "depth": round(base_score + random.uniform(-0.2, 0.2), 2),
            "nuance": round(base_score + random.uniform(-0.2, 0.2), 2),
            "specificity": round(base_score + random.uniform(-0.2, 0.2), 2),
        },
        "evolutionary_strategy": {
            "specific_changes": [
                "Increase concrete examples",
                "Reduce hedging language",
                "Add more specific metrics",
            ][random.randint(0, 2)],
            "rationale": "Improve specificity and reduce abstraction",
        },
        "reasoning": f"Score: {round(base_score, 2)}/5.0. Content demonstrates good clarity and practical focus. Could benefit from more specific examples and data.",
    }

    return evaluation


def main():
    """Monitor requests and generate responses."""
    requests_dir = Path(".bloginator/llm_requests")
    responses_dir = Path(".bloginator/llm_responses")

    responses_dir.mkdir(parents=True, exist_ok=True)

    print("🤖 Auto-responder started. Monitoring for LLM requests...")
    print(f"   Requests: {requests_dir}")
    print(f"   Responses: {responses_dir}")

    processed = set()

    while True:
        if not requests_dir.exists():
            time.sleep(1)
            continue

        for request_file in sorted(requests_dir.glob("request_*.json")):
            if request_file.name in processed:
                continue

            request_id = request_file.stem.replace("request_", "")
            response_file = responses_dir / f"response_{request_id}.json"

            if response_file.exists():
                processed.add(request_file.name)
                continue

            # Read request
            with Path(request_file).open() as f:
                request = json.load(f)

            print(f"📝 Processing {request_file.name}...")

            # Determine request type and generate response
            system_prompt = request.get("system_prompt") or ""
            prompt = request.get("prompt") or ""

            # Check for evaluation request (contains JSON format instructions)
            is_evaluation = (
                "evolutionary_strategy" in prompt.lower()
                or "slop_violations" in prompt.lower()
                or "voice_analysis" in prompt.lower()
                or ("evaluation" in prompt.lower() and "json" in prompt.lower())
            )

            if is_evaluation:
                content = json.dumps(generate_evaluation_response(request), indent=2)
            elif "outline" in system_prompt.lower() or "outline" in prompt.lower():
                content = generate_outline_response(request)
            else:
                content = generate_draft_response(request)

            # Write response
            response = {
                "content": content,
                "model": request.get("model", "auto-responder"),
                "usage": {
                    "input_tokens": len(prompt.split()) * 2,
                    "output_tokens": len(content.split()) * 2,
                },
            }

            with Path(response_file).open("w") as f:
                json.dump(response, f, indent=2)

            print(f"✅ Generated {response_file.name}")
            processed.add(request_file.name)

        time.sleep(0.5)


if __name__ == "__main__":
    main()
