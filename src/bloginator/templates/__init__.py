"""Document templates for common use cases."""

__all__ = ["TEMPLATES", "get_template", "list_templates"]

from pathlib import Path


# Get the directory containing template files
TEMPLATES_DIR = Path(__file__).parent

# Template catalog
TEMPLATES: dict[str, dict[str, str]] = {
    "blog_post": {
        "name": "Blog Post",
        "description": "Technical blog post with introduction, body, and conclusion",
        "category": "content",
        "file": "blog_post.json",
    },
    "job_description": {
        "name": "Job Description",
        "description": "Engineering job description with role overview, responsibilities, and requirements",
        "category": "hiring",
        "file": "job_description.json",
    },
    "career_ladder": {
        "name": "Career Ladder",
        "description": "Engineering career progression framework with levels and expectations",
        "category": "career",
        "file": "career_ladder.json",
    },
    "engineering_playbook": {
        "name": "Engineering Playbook",
        "description": "Team playbook with practices, processes, and principles",
        "category": "documentation",
        "file": "engineering_playbook.json",
    },
    "technical_design": {
        "name": "Technical Design Doc",
        "description": "Technical design document with problem, solution, and alternatives",
        "category": "technical",
        "file": "technical_design.json",
    },
    "onboarding_guide": {
        "name": "Onboarding Guide",
        "description": "New engineer onboarding guide with timeline and resources",
        "category": "documentation",
        "file": "onboarding_guide.json",
    },
    "project_proposal": {
        "name": "Project Proposal",
        "description": "Project proposal with objectives, scope, and success metrics",
        "category": "project",
        "file": "project_proposal.json",
    },
    "performance_review": {
        "name": "Performance Review",
        "description": "Engineering performance review framework",
        "category": "career",
        "file": "performance_review.json",
    },
    "architecture_doc": {
        "name": "Architecture Document",
        "description": "System architecture documentation with components and patterns",
        "category": "technical",
        "file": "architecture_doc.json",
    },
    "team_charter": {
        "name": "Team Charter",
        "description": "Team charter with mission, values, and ways of working",
        "category": "documentation",
        "file": "team_charter.json",
    },
    "incident_postmortem": {
        "name": "Incident Postmortem",
        "description": "Post-incident review with timeline, impact, and action items",
        "category": "operations",
        "file": "incident_postmortem.json",
    },
    "rfp_response": {
        "name": "RFP Response",
        "description": "Request for Proposal response with capabilities and approach",
        "category": "business",
        "file": "rfp_response.json",
    },
}


def get_template(template_id: str) -> dict | None:
    """Load a template by ID.

    Args:
        template_id: Template identifier

    Returns:
        Template data as dict, or None if not found
    """
    if template_id not in TEMPLATES:
        return None

    template_meta = TEMPLATES[template_id]
    template_file = TEMPLATES_DIR / template_meta["file"]

    if not template_file.exists():
        return None

    import json

    with template_file.open() as f:
        data = json.load(f)

    # Add metadata
    data["template_id"] = template_id
    data["template_name"] = template_meta["name"]
    data["template_description"] = template_meta["description"]

    return data


def list_templates(category: str | None = None) -> dict[str, dict[str, str]]:
    """List available templates.

    Args:
        category: Optional category filter

    Returns:
        Dictionary of templates
    """
    if category:
        return {k: v for k, v in TEMPLATES.items() if v["category"] == category}

    return TEMPLATES
