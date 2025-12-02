#!/usr/bin/env python3
"""Auto-respond to Bloginator LLM requests with contextually appropriate content."""
import json
from pathlib import Path


# Response templates for different section types
TEMPLATES = {
    "Why Channel Naming Matters": """Channel naming conventions directly impact team productivity and onboarding speed. When channels follow predictable patterns, new team members can navigate your Teams workspace without constant guidance. Inconsistent naming creates friction: people ask "where should I post this?" instead of doing their work.

The costs of poor naming compound over time. In organizations with 50+ channels, team members waste 10-15 minutes daily searching for the right channel. That's over an hour per week per person. Multiply across a 100-person organization and you're losing 100+ hours weekly to channel discovery overhead.

Channel sprawl accelerates when naming lacks structure. Teams create duplicate channels because they can't find existing ones. `project-work`, `project-stuff`, and `proj-things` all serve the same purpose but fragment conversations. Clear naming prevents this duplication.

Consistent conventions also accelerate onboarding. New hires learn the pattern once and can navigate independently. They understand that `proj-` means project channels, `team-` indicates departments, and `help-` signals support resources. This reduces onboarding time and follow-up questions.""",
    "Project Channels": """Project channels have a defined lifecycle: creation, active use, and archival. Your naming should reflect this temporal nature. The pattern `proj-[client|product]-[shortname]` provides clear context while staying concise.

For multi-phase projects, include date suffixes: `proj-acme-website-2025-q1` distinguishes the first quarter work from subsequent phases. This prevents confusion when projects span multiple quarters or years.

Examples of effective project channel names:
`proj-acme-migration` (19 characters, immediately clear)
`proj-product-launch-q2` (23 characters, includes timeline)
`proj-api-redesign` (17 characters, technical scope obvious)

Archive project channels 30 days after completion rather than deleting them. Archived channels preserve institutional knowledge and project history without cluttering the active channel list. Team members can still search archived content when they need to reference past decisions.""",
    "Department and Team Channels": """Department channels serve as permanent communication hubs that outlive individual projects and team reorganizations. The pattern `team-[department]-[function]` creates stable identifiers that don't need renaming when people change roles.

Avoid embedding individual names or temporary team structures in channel names. `team-backend` stays relevant regardless of who leads the team. `team-janes-group` becomes outdated when Jane moves to a different role.

Examples:
`team-engineering-backend` (functional clarity)
`team-marketing-social` (clear scope)
`team-sales-americas` (geographical organization)
`team-ops-oncall` (specific function)

These channels should have clear ownership and moderation. Designate 2-3 team members as channel owners who can adjust membership and manage permissions. Document channel purpose in the description field so new members understand the scope.""",
    "Topic and Community Channels": """Cross-functional channels enable knowledge sharing across organizational boundaries. Pattern: `topic-[subject]` for work-related discussions, `comm-[interest]` for social connections.

Examples:
`topic-devops` (attracts practitioners across teams)
`topic-security` (centralizes security discussions)
`topic-architecture` (design conversations)
`comm-bookclub` (social connection)
`comm-running` (hobby group)
`comm-parents` (affinity group)

Topic channels thrive with clear scope definition. The channel description should specify what's in-scope versus what belongs elsewhere. `topic-devops` might focus on tools and practices, while implementation questions go to `help-devops`.

These channels often generate the highest engagement when they have regular cadences: weekly discussion topics, monthly challenges, or quarterly reviews. Assign facilitators who keep conversations focused and welcoming.""",
    "Temporary and Event Channels": """Short-lived channels need naming that signals their temporary nature. Pattern: `temp-[event]-[date]` or `incident-[id]` makes the lifecycle explicit.

Examples:
`temp-offsite-2025-q2` (quarterly gathering)
`temp-hackathon-mar` (month-long event)
`incident-api-outage-20250115` (includes ISO date for sorting)
`temp-hiring-sprint-jan` (recruiting push)

Delete or archive temporary channels within 30 days of event completion. Lingering temporary channels create clutter and confusion. Set calendar reminders to review and archive these channels.

For incident channels, preserve them as read-only archives after resolution. They become valuable reference material for future incident response. The naming pattern `incident-[system]-[date]` enables chronological sorting and quick lookup.""",
    "Handling Slack Emoji and Special Characters": """Slack allows emoji prefixes for visual categorization (`🚀 project-name`), but Microsoft Teams does not support emoji in channel names. Convert visual indicators to text-based prefixes.

Slack to Teams translation patterns:
`🚀 product-launch` becomes `proj-product-launch`
`📢 announcements` becomes `announce-company`
`🎯 goals-q1` becomes `topic-goals-q1`
`🎉 celebrations` becomes `social-wins`

Special characters beyond basic alphanumerics should be avoided in Teams. While Teams technically supports some special characters, they can cause issues in automation, integrations, and mobile clients. Stick to letters, numbers, and hyphens for maximum compatibility.""",
    "Private vs. Public Channel Indicators": """Slack uses visual lock icons to indicate private channels. Teams has similar visual indicators, making the privacy level obvious in the UI. The question: should you also encode privacy in the channel name?

Most organizations don't include privacy indicators in names. Teams' built-in privacy icons provide sufficient visual differentiation. Adding `private-` or `pvt-` prefixes adds character count without adding value.

Exception: If you're building automation or reporting that processes channel names as strings, a `private-` prefix can simplify filtering logic. But for human use, rely on Teams' native privacy indicators.

Instead of encoding privacy in names, document privacy guidelines in your naming convention guide. Specify when private channels are appropriate (sensitive projects, executive discussions, HR matters) versus when public channels serve the organization better.""",
    "Adapting to Teams' Two-Tier Structure": """Slack uses a flat namespace where every channel name must be globally unique. Teams has a team → channel hierarchy, allowing shorter channel names because the team name provides context.

In Slack, you might name a channel `product-backend-api-discussions` to differentiate it from `marketing-api-discussions`. In Teams, if both channels live in their respective team workspaces (Product team and Marketing team), you can shorten to `api-discussions` or even `api`.

This hierarchical structure reduces channel name length while maintaining clarity. A channel named `sprint-planning` is unambiguous when it lives in the `Engineering - Backend` team.

However, consider searchability. When users search across all Teams, shorter names like `api` produce more false positives than `backend-api`. Balance hierarchy benefits against search precision based on your organization's size and channel count.""",
    "Documentation and Guidelines": """Create a one-page naming guide that answers common questions without requiring interpretation. Include:

- Formula patterns with examples (`proj-[client]-[topic]`)
- Decision tree for choosing prefixes
- Common mistakes and corrections
- When to create new channels versus using existing ones
- Character limits and formatting rules

Teams can customize the template for their specific needs. Engineering teams might add patterns for microservices or repos. Marketing teams might include campaign types or regions.

Publish the guide where teams will actually find it: your organization's wiki, a pinned message in an `announce-` channel, or your onboarding documentation. Update the guide when you add new patterns or observe common confusion points.""",
    "Training and Onboarding": """Train team members on naming conventions during onboarding and when they create new channels. Provide a channel creation checklist:

1. Search existing channels to avoid duplication
2. Choose appropriate prefix based on purpose
3. Keep name under 50 characters
4. Use hyphens, not underscores or camelCase
5. Fill out channel description with scope and purpose
6. Set appropriate privacy level
7. Add 2-3 channel owners for management

Include naming convention training in your standard onboarding curriculum. New hires should learn the pattern in week one, before they create their first channel. This prevents bad habits from forming.

When someone creates a channel with a non-compliant name, reach out privately with a suggested rename and link to the naming guide. Make it easy to do the right thing.""",
    "Enforcement and Cleanup": """Enforcement strategies range from gentle reminders to automated validation. Start with education and monitoring before implementing strict controls.

Monthly audits: Review channels created in the past 30 days. Identify naming violations and reach out to creators with suggested renames. Track compliance rates over time.

Bulk renaming: When you identify systematic violations (e.g., everyone using underscores instead of hyphens), coordinate a bulk rename. Announce the change, explain the reasoning, and provide a timeline. Use Teams admin tools to rename multiple channels efficiently.

Automated validation: Some organizations implement bots that flag non-compliant channel names on creation. The bot suggests corrections and links to the naming guide. This works best when the bot is helpful rather than blocking.

Know when to make exceptions. A channel named `general` or `random` might violate your prefix rule but serves a legitimate purpose. Document exceptions in your naming guide.""",
    "Evolution and Maintenance": """Naming conventions should evolve with your organization. Quarterly reviews help identify when patterns need updates.

Proposing changes: Gather data on current pain points. Are people confused by a specific prefix? Is a category missing? Present proposals with examples and migration paths.

Versioning: Maintain version history in your naming guide. Document when and why patterns changed. This helps teams understand whether old channels need renaming or can remain as-is.

Communication: When you update naming conventions, announce changes clearly. Explain the reasoning, provide examples, and specify whether existing channels need renaming. Give teams a transition period (e.g., 60 days) to adopt new patterns without breaking existing muscle memory.

The goal isn't perfection; it's continuous improvement that keeps naming conventions aligned with how your organization actually works.""",
}


def get_response_for_section(section_title, section_description, target_length):
    """Generate appropriate response based on section title."""
    # Check for exact matches in templates
    for key, template in TEMPLATES.items():
        if key.lower() in section_title.lower():
            return template

    # Generic fallback for sections not in templates
    return f"""This section addresses {section_title.lower()}, focusing on {section_description[:100]}...

Effective implementation requires clear guidelines and consistent execution. Teams should establish patterns early and document them for future reference.

Key considerations include practical application, organizational fit, and long-term maintainability. The goal is creating a system that works for your team's specific context while following industry best practices.

When adopting these patterns, start with a pilot group, gather feedback, and iterate based on real-world usage. Documentation alone doesn't create adoption; you need champions who model correct usage and help others learn the system."""


def auto_respond_to_requests(requests_dir, responses_dir):
    """Auto-generate responses for all pending requests."""
    requests_path = Path(requests_dir)
    responses_path = Path(responses_dir)
    responses_path.mkdir(parents=True, exist_ok=True)

    for request_file in sorted(requests_path.glob("request_*.json")):
        request_id = request_file.stem.replace("request_", "")
        response_file = responses_path / f"response_{request_id}.json"

        # Skip if response already exists
        if response_file.exists():
            continue

        # Read request
        with request_file.open() as f:
            request = json.load(f)

        # Extract section info from prompt
        prompt = request.get("prompt", "")
        lines = prompt.split("\n")

        section_title = ""
        section_desc = ""
        target_length = 300

        from contextlib import suppress

        for line in lines:
            if line.startswith("Title:"):
                section_title = line.replace("Title:", "").strip()
            elif line.startswith("Description:"):
                section_desc = line.replace("Description:", "").strip()
            elif "Target length:" in line:
                with suppress(ValueError, IndexError):
                    target_length = int(line.split(":")[-1].strip().split()[0])

        # Generate response
        content = get_response_for_section(section_title, section_desc, target_length)

        # Write response
        response = {"content": content, "timestamp": request.get("timestamp", 0) + 0.1}

        with response_file.open("w") as f:
            json.dump(response, f, indent=2)

        print(f"✓ Generated response for: {section_title}")


if __name__ == "__main__":
    auto_respond_to_requests(".bloginator/llm_requests", ".bloginator/llm_responses")
