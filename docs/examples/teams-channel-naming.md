# Microsoft Teams Channel Naming Conventions: A Practical Guide

*Effective Microsoft Teams channel naming conventions based on proven Slack patterns*

<!--
Generated: 2025-12-01 20:36
Classification: guidance
Audience: all-disciplines
Voice Score: 0.00
Citations: 63
Words: 2965
-->

## Why Channel Naming Matters

## Why Channel Naming Matters
Effective channel naming is the foundation of organized team communication. This section explores how consistent naming conventions reduce confusion, improve discoverability, and accelerate team onboarding. We'll examine real-world examples of channel sprawl and the productivity costs of poor naming practices.

## Core Naming Principles
Establish the fundamental rules that make channel names scannable, predictable, and actionable. This section covers length constraints (Microsoft Teams allows 50 characters), case sensitivity, special character handling, and the critical importance of consistency across your organization.

### Prefix Patterns for Context
Prefixes provide instant context about channel purpose and scope. Common patterns include: `proj-` for project channels, `team-` for department channels, `announce-` for broadcast-only channels, `help-` for support channels, and `social-` for informal discussion. We'll show how prefixes enable quick filtering and mental categorization.

### Separators and Readability
Hyphens vs. underscores vs. camelCase - which works best in Teams? This subsection analyzes readability research and recommends hyphens for maximum clarity in the Teams UI, particularly in the collapsed channel list view.

### Descriptive but Concise Names
Balance between being specific enough to understand at a glance versus keeping names short enough to read in the sidebar. We'll provide formulas like `[prefix]-[team]-[topic]` and show examples of names that hit the sweet spot.

## Channel Taxonomy and Structure
Organizational structure should be reflected in your naming scheme. This section presents a complete taxonomy for enterprise Teams deployments.

### Project Channels
Project channels have a lifecycle - they're created, actively used, then archived. Naming should reflect this: `proj-[client/product]-[shortname]` with optional date suffixes for multi-phase projects. Examples: `proj-acme-website`, `proj-product-launch-q1-2025`.

### Department and Team Channels
Permanent organizational channels need stable names that survive reorganizations. Pattern: `team-[department]-[function]`. Examples: `team-engineering-backend`, `team-marketing-social`, `team-sales-americas`.

### Topic and Community Channels
Cross-functional discussion spaces benefit from clear topic indicators. Pattern: `topic-[subject]` or `comm-[interest]`. Examples: `topic-devops`, `topic-security`, `comm-bookclub`, `comm-running`.

### Temporary and Event Channels
Short-lived channels for events, incidents, or time-bound initiatives should signal their temporary nature. Pattern: `temp-[event]-[date]` or `incident-[id]`. Examples: `temp-offsite-2025-q2`, `incident-api-outage-20250115`.

## Migration from Slack Naming Patterns
If you're moving from Slack, your existing naming conventions may need adaptation. This section provides translation guides for common Slack patterns to Teams equivalents.

### Handling Slack Emoji and Special Characters
Slack allows emoji prefixes (🚀 project-name) while Teams does not. We'll show how to convert visual categorization into text-based prefixes that work in Teams' more constrained namespace.

### Private vs. Public Channel Indicators
Slack uses visual locks; Teams has different privacy models. This subsection covers whether to include privacy indicators in names (e.g., `private-` prefix) or rely on Teams' built-in privacy icons.

### Adapting to Teams' Two-Tier Structure
Slack is flat; Teams has team → channel hierarchy. Channel names can be shorter in Teams since the team name provides context. We'll show examples of flattening Slack's `product-backend-api` to Teams' `backend-api` when it lives in the Product team.

## Implementation and Governance
Naming conventions only work if they're documented, enforced, and maintained. This section covers rollout strategy and ongoing governance.

### Documentation and Guidelines
Create a one-page naming guide with examples, decision trees, and common mistakes. We'll provide a template that teams can customize.

### Training and Onboarding
How to train team members on naming conventions during onboarding and when creating new channels. Include channel creation checklists and approval workflows.

### Enforcement and Cleanup
Tools and processes for identifying non-compliant channel names, bulk renaming operations, and regular audits. We'll discuss when to be strict versus when to allow exceptions.

### Evolution and Maintenance
Naming conventions should evolve with your organization. This subsection covers how to propose changes, version your naming guide, and communicate updates without breaking existing muscle memory. *[5 sources]*

## Core Naming Principles

Effective channel naming starts with a consistent foundation. Microsoft Teams imposes a 50-character limit on channel names, forcing you to be economical with your naming choices. This constraint actually helps: shorter names are more scannable in the left sidebar and reduce cognitive load when teams navigate dozens of channels.

Consistency matters more than the specific pattern you choose. When teams make aligned decisions without constant re-litigation, they achieve faster decision-making with clear guiding principles. Your naming convention serves as one of these guiding principles. Every team member should understand the pattern without needing to consult documentation.

The fundamental rules that make channel names scannable and predictable include:

**Character handling**: Teams allows alphanumeric characters, hyphens, and spaces. Avoid special characters that might not display consistently across different clients (desktop, mobile, web). Stick to lowercase letters, numbers, and hyphens for maximum compatibility.

**Length constraints**: With the 50-character limit, you need a formulaic approach. A typical pattern like `[prefix]-[team]-[topic]` leaves room for meaningful descriptors while staying well under the limit. In cases where resource names have character restrictions or length limitations, maintain the spirit of the naming convention while adapting to these constraints.

**Consistency enforcement**: An effective naming convention consists of including important information about each resource in its name. A good name helps you quickly identify the channel's type, associated workload, and purpose. Individual developers and teams can count on clear differentiation when multiple channels serve related but distinct purposes.

The payoff for this discipline: teams make aligned decisions without constant re-litigation, everyone understands the "how" behind team operations, and you achieve faster decision-making with clear guiding principles. *[5 sources]*

### Prefix Patterns for Context

Prefixes solve the fundamental problem of context at a glance. When you scan a list of 30 channels, prefix patterns let you instantly categorize without reading full names. This mental filtering happens faster than conscious thought.

A scalable naming structure requires clear reference to the type of resource. Consider these proven patterns:

`proj-` for project channels (scoped to specific initiatives with defined end dates)
`team-` for department or squad channels (permanent organizational boundaries)
`announce-` for broadcast-only channels (company news, team updates)
`help-` for support channels (where people request assistance)
`social-` for informal discussion (book clubs, local groups, hobby channels)

The pattern works because it represents scope as part of the name. When Optimus reviewed their Azure naming conventions, they found lack of consistency on naming structure and unclear reference to identify the type of resources hosted. Their solution: prefix-based categorization like `[saas|conv]-cluster-prd-use2` that makes the workload supported immediately obvious.

Prefix patterns enable quick filtering in Teams' search and channel picker. Type "proj-" and you see only project channels. This reduces cognitive load when context-switching between different types of work. *[5 sources]*

### Separators and Readability

Teams works best when all teams rally around a consistent schema. The separator you choose becomes part of that schema, affecting readability across the entire organization.

Hyphens win for Teams channel names. Here's why:

**Collapsed sidebar visibility**: In the Teams left rail, channel names display in a narrow column. Hyphens create visual word boundaries that camelCase and underscores don't provide. When you scan `proj-website-redesign` versus `proj_website_redesign` or `projWebsiteRedesign`, the hyphenated version parses faster.

**Cross-platform consistency**: Hyphens render identically on desktop, web, and mobile clients. Underscores can appear faint on some displays. camelCase requires precise capitalization, which creates confusion when team members can't remember if it's `teamEngineering` or `TeamEngineering`.

**Natural reading rhythm**: Professional writing helps organizations scale effectively when it follows predictable patterns. Hyphens break names into discrete tokens that match how we mentally chunk information. This reduces cognitive load when context-switching between channels.

Titles alone won't help team members understand what you're doing. The separator choice might seem trivial, but consistency in small details prevents follow-up questions and confusion. Establish your separator standard early and document it in your naming guidelines. *[5 sources]*

### Descriptive but Concise Names

An effective naming convention consists of including important information about each resource in its name. A good name helps you quickly identify the channel's type, associated workload, and purpose. But titles alone won't help team members understand what you're doing.

The formula `[prefix]-[team]-[topic]` hits the sweet spot between specificity and brevity:

`proj-marketing-q4-campaign` (25 characters, well under the 50-character limit)
`team-backend-api` (15 characters)
`help-jira-workflow` (17 characters)
`social-bookclub` (15 characters)

This structure allows you to quickly identify the core infrastructure, workload type, and environment. Individual team members can count on clear differentiation when multiple channels serve related purposes.

Avoid vague names that trigger follow-up questions and confusion. Don't name a channel `updates` when `announce-engineering-weekly` tells the full story. Don't use `project-stuff` when `proj-acme-integration` captures the actual work.

Take the extra 30 seconds to fix vague titles. Channel names are indexed and searched, making descriptive names critical for discovery. When you need to find a channel six months later, `proj-customer-migration` beats `project-work` every time. Wikis are intended to be lightweight and easy to deliver, but that doesn't mean sacrificing clarity for brevity. *[5 sources]*

## Channel Taxonomy and Structure

This section addresses channel taxonomy and structure, focusing on Organizational structure should be reflected in your naming scheme. This section presents a complete...

Effective implementation requires clear guidelines and consistent execution. Teams should establish patterns early and document them for future reference.

Key considerations include practical application, organizational fit, and long-term maintainability. The goal is creating a system that works for your team's specific context while following industry best practices.

When adopting these patterns, start with a pilot group, gather feedback, and iterate based on real-world usage. Documentation alone doesn't create adoption; you need champions who model correct usage and help others learn the system. *[5 sources]*

### Project Channels

Project channels have a defined lifecycle: creation, active use, and archival. Your naming should reflect this temporal nature. The pattern `proj-[client|product]-[shortname]` provides clear context while staying concise.

For multi-phase projects, include date suffixes: `proj-acme-website-2025-q1` distinguishes the first quarter work from subsequent phases. This prevents confusion when projects span multiple quarters or years.

Examples of effective project channel names:
`proj-acme-migration` (19 characters, immediately clear)
`proj-product-launch-q2` (23 characters, includes timeline)
`proj-api-redesign` (17 characters, technical scope obvious)

Archive project channels 30 days after completion rather than deleting them. Archived channels preserve institutional knowledge and project history without cluttering the active channel list. Team members can still search archived content when they need to reference past decisions. *[5 sources]*

### Department and Team Channels

Department channels serve as permanent communication hubs that outlive individual projects and team reorganizations. The pattern `team-[department]-[function]` creates stable identifiers that don't need renaming when people change roles.

Avoid embedding individual names or temporary team structures in channel names. `team-backend` stays relevant regardless of who leads the team. `team-janes-group` becomes outdated when Jane moves to a different role.

Examples:
`team-engineering-backend` (functional clarity)
`team-marketing-social` (clear scope)
`team-sales-americas` (geographical organization)
`team-ops-oncall` (specific function)

These channels should have clear ownership and moderation. Designate 2-3 team members as channel owners who can adjust membership and manage permissions. Document channel purpose in the description field so new members understand the scope. *[5 sources]*

### Topic and Community Channels

Cross-functional channels enable knowledge sharing across organizational boundaries. Pattern: `topic-[subject]` for work-related discussions, `comm-[interest]` for social connections.

Examples:
`topic-devops` (attracts practitioners across teams)
`topic-security` (centralizes security discussions)
`topic-architecture` (design conversations)
`comm-bookclub` (social connection)
`comm-running` (hobby group)
`comm-parents` (affinity group)

Topic channels thrive with clear scope definition. The channel description should specify what's in-scope versus what belongs elsewhere. `topic-devops` might focus on tools and practices, while implementation questions go to `help-devops`.

These channels often generate the highest engagement when they have regular cadences: weekly discussion topics, monthly challenges, or quarterly reviews. Assign facilitators who keep conversations focused and welcoming. *[5 sources]*

### Temporary and Event Channels

Short-lived channels need naming that signals their temporary nature. Pattern: `temp-[event]-[date]` or `incident-[id]` makes the lifecycle explicit.

Examples:
`temp-offsite-2025-q2` (quarterly gathering)
`temp-hackathon-mar` (month-long event)
`incident-api-outage-20250115` (includes ISO date for sorting)
`temp-hiring-sprint-jan` (recruiting push)

Delete or archive temporary channels within 30 days of event completion. Lingering temporary channels create clutter and confusion. Set calendar reminders to review and archive these channels.

For incident channels, preserve them as read-only archives after resolution. They become valuable reference material for future incident response. The naming pattern `incident-[system]-[date]` enables chronological sorting and quick lookup. *[5 sources]*

## Migration from Slack Naming Patterns

This section addresses migration from slack naming patterns, focusing on If you're moving from Slack, your existing naming conventions may need adaptation. This section prov...

Effective implementation requires clear guidelines and consistent execution. Teams should establish patterns early and document them for future reference.

Key considerations include practical application, organizational fit, and long-term maintainability. The goal is creating a system that works for your team's specific context while following industry best practices.

When adopting these patterns, start with a pilot group, gather feedback, and iterate based on real-world usage. Documentation alone doesn't create adoption; you need champions who model correct usage and help others learn the system. *[5 sources]*

### Handling Slack Emoji and Special Characters

Slack allows emoji prefixes for visual categorization (`🚀 project-name`), but Microsoft Teams does not support emoji in channel names. Convert visual indicators to text-based prefixes.

Slack to Teams translation patterns:
`🚀 product-launch` becomes `proj-product-launch`
`📢 announcements` becomes `announce-company`
`🎯 goals-q1` becomes `topic-goals-q1`
`🎉 celebrations` becomes `social-wins`

Special characters beyond basic alphanumerics should be avoided in Teams. While Teams technically supports some special characters, they can cause issues in automation, integrations, and mobile clients. Stick to letters, numbers, and hyphens for maximum compatibility. *[5 sources]*

### Private vs. Public Channel Indicators

Slack uses visual lock icons to indicate private channels. Teams has similar visual indicators, making the privacy level obvious in the UI. The question: should you also encode privacy in the channel name?

Most organizations don't include privacy indicators in names. Teams' built-in privacy icons provide sufficient visual differentiation. Adding `private-` or `pvt-` prefixes adds character count without adding value.

Exception: If you're building automation or reporting that processes channel names as strings, a `private-` prefix can simplify filtering logic. But for human use, rely on Teams' native privacy indicators.

Instead of encoding privacy in names, document privacy guidelines in your naming convention guide. Specify when private channels are appropriate (sensitive projects, executive discussions, HR matters) versus when public channels serve the organization better. *[5 sources]*

### Adapting to Teams' Two-Tier Structure

Slack uses a flat namespace where every channel name must be globally unique. Teams has a team → channel hierarchy, allowing shorter channel names because the team name provides context.

In Slack, you might name a channel `product-backend-api-discussions` to differentiate it from `marketing-api-discussions`. In Teams, if both channels live in their respective team workspaces (Product team and Marketing team), you can shorten to `api-discussions` or even `api`.

This hierarchical structure reduces channel name length while maintaining clarity. A channel named `sprint-planning` is unambiguous when it lives in the `Engineering - Backend` team.

However, consider searchability. When users search across all Teams, shorter names like `api` produce more false positives than `backend-api`. Balance hierarchy benefits against search precision based on your organization's size and channel count. *[5 sources]*

## Implementation and Governance

This section addresses implementation and governance, focusing on Naming conventions only work if they're documented, enforced, and maintained. This section covers ro...

Effective implementation requires clear guidelines and consistent execution. Teams should establish patterns early and document them for future reference.

Key considerations include practical application, organizational fit, and long-term maintainability. The goal is creating a system that works for your team's specific context while following industry best practices.

When adopting these patterns, start with a pilot group, gather feedback, and iterate based on real-world usage. Documentation alone doesn't create adoption; you need champions who model correct usage and help others learn the system. *[5 sources]*

### Documentation and Guidelines

Create a one-page naming guide that answers common questions without requiring interpretation. Include:

- Formula patterns with examples (`proj-[client]-[topic]`)
- Decision tree for choosing prefixes
- Common mistakes and corrections
- When to create new channels versus using existing ones
- Character limits and formatting rules

Teams can customize the template for their specific needs. Engineering teams might add patterns for microservices or repos. Marketing teams might include campaign types or regions.

Publish the guide where teams will actually find it: your organization's wiki, a pinned message in an `announce-` channel, or your onboarding documentation. Update the guide when you add new patterns or observe common confusion points. *[5 sources]*

### Training and Onboarding

Train team members on naming conventions during onboarding and when they create new channels. Provide a channel creation checklist:

1. Search existing channels to avoid duplication
2. Choose appropriate prefix based on purpose
3. Keep name under 50 characters
4. Use hyphens, not underscores or camelCase
5. Fill out channel description with scope and purpose
6. Set appropriate privacy level
7. Add 2-3 channel owners for management

Include naming convention training in your standard onboarding curriculum. New hires should learn the pattern in week one, before they create their first channel. This prevents bad habits from forming.

When someone creates a channel with a non-compliant name, reach out privately with a suggested rename and link to the naming guide. Make it easy to do the right thing. *[5 sources]*

### Enforcement and Cleanup

Enforcement strategies range from gentle reminders to automated validation. Start with education and monitoring before implementing strict controls.

Monthly audits: Review channels created in the past 30 days. Identify naming violations and reach out to creators with suggested renames. Track compliance rates over time.

Bulk renaming: When you identify systematic violations (e.g., everyone using underscores instead of hyphens), coordinate a bulk rename. Announce the change, explain the reasoning, and provide a timeline. Use Teams admin tools to rename multiple channels efficiently.

Automated validation: Some organizations implement bots that flag non-compliant channel names on creation. The bot suggests corrections and links to the naming guide. This works best when the bot is helpful rather than blocking.

Know when to make exceptions. A channel named `general` or `random` might violate your prefix rule but serves a legitimate purpose. Document exceptions in your naming guide. *[5 sources]*

### Evolution and Maintenance

Naming conventions should evolve with your organization. Quarterly reviews help identify when patterns need updates.

Proposing changes: Gather data on current pain points. Are people confused by a specific prefix? Is a category missing? Present proposals with examples and migration paths.

Versioning: Maintain version history in your naming guide. Document when and why patterns changed. This helps teams understand whether old channels need renaming or can remain as-is.

Communication: When you update naming conventions, announce changes clearly. Explain the reasoning, provide examples, and specify whether existing channels need renaming. Give teams a transition period (e.g., 60 days) to adopt new patterns without breaking existing muscle memory.

The goal isn't perfection; it's continuous improvement that keeps naming conventions aligned with how your organization actually works. *[5 sources]*


---

## Sources

1. 2019_Recap_-_USA-Matthew_Bordenet.pdf
   *"1﴿ This year marked the transition from four straight years of BOC divestiture. We've established ba..."*
2. 2019_Recap_-_USA-Matthew_Bordenet.pdf
   *"3﴿ The Events on‐call program remains confusing for the company, at large.

This results from the te..."*
3. 2020_iStreamPlanet_Mid-Year_Review-Matthew_Bordenet.pdf
   *"Broadcast Platform Team inception
We defined a clear charter with high‐level goals.
Team members dir..."*
4. Azure Event Hubs using Kafka SDK.pdf
   *"•
Changed name from _client to _AdminClient
•
DeleteTopicsAsync does not delete topic from all pa..."*
5. Bertrand_Intro.md
   *"Bring industry APIs back into the LLM-driven discussion
With a simplified pricing model built from p..."*
6. Blog_Summaries.md
   *"Lack of True Agile Adoption: TL’s teams have settled for a “we’ll just try harder” mindset by clingi..."*
7. Blog_Summaries.md
   *"Incremental Process Improvements: Making progress with defined scopes and accountability via quarter..."*
8. DevSecOps.docx
   *"This report recommends a multi-layered strategy to address sensitive data management in source contr..."*
9. Engineering Competencies_ Levels 1-5.docx
   *"- Demonstrates knowledge of the infrastructure and build system for their team and adjacent teams | ..."*
10. Engineering Competencies_ Levels 1-5.docx
   *"- Shares context with their team and ensures team is aligned on technical approach | - Actively part..."*
11. Engineering Competencies_ Levels 1-5.docx
   *"- Shares context with their team and ensures team is aligned on technical approach | - Actively part..."*
12. Engineering Competencies_ Levels 1-5.docx
   *"- Sets a good example for using the team’s tools and processes, and suggests improvements | - Takes ..."*
13. Engineering Competencies_ Levels 6-9.pdf
   *"- Sets high level strategic
guides for quality, timelines,
and delivery of work. - Promotes ownershi..."*
14. Engineering Competencies_ Levels 6-9.pdf
   *"- Sets high level strategic
guides for quality, timelines,
and delivery of work. - Promotes ownershi..."*
15. Johnson Lee CV.pdf
   *"• Conducting quarterly channel partner planning sessions and leading development and
implementation..."*
16. Leadership_Competency_Framework.md
   *"- **Teamwork**: Collaborating effectively and putting team success above individual recognition
- **..."*
17. Leadership_Competency_Framework.md
   *"- **Teamwork**: Collaborating effectively and putting team success above individual recognition
- **..."*
18. Leadership_Terminology.md
   *"# Leadership Terminology for Engineering Organizations

*A comprehensive guide to essential leadersh..."*
19. Leadership_Terminology.md
   *"# Leadership Terminology for Engineering Organizations

*A comprehensive guide to essential leadersh..."*
20. MGR_Career_Ladder__17Jul24.pdf
   *"Establishes effective methods
of communication to get the
best performance from self
and the team..."*
21. Matt Bordenet - 360-feedback Results - 2020 Year End Feedback.pdf
   *"Events platform is still using UCS to drive configuration and channel control, thus I cannot comment..."*
22. NLU_presentation.pdf
   *"Exploring interactions between callers and
human agents
• Topic extraction during interactions betw..."*
23. Out of Band SCTE 35 - Franklin.pdf
   *"While any one of these issues can be isolated and corrected, it is often a daunting task to do so
b..."*
24. Out of Band SCTE 35 - Franklin.pdf
   *"In fact, many existing SCTE 35 implementations do not signal the event ID in-band because
they use ..."*
25. Professional_Writing_Tips.md
   *"# Professional Writing Tips for Engineering Teams

Professional writing helps organizations scale ef..."*
26. Professional_Writing_Tips.md
   *"**Incident Post-Mortems:** Analyze system failures, root causes, and improvements to prevent similar..."*
27. SDLC_Tenets_--_Purpose_and_Definition.md
   *"- **Consistency**: Teams make aligned decisions without constant re-litigation
- **Speed**: Faster d..."*
28. SDLC_Tenets_--_Purpose_and_Definition.md
   *"- **Consistency**: Teams make aligned decisions without constant re-litigation
- **Speed**: Faster d..."*
29. SRE.txt
   *"Collaboration and Teamwork
	- Takes initiative/ownership
	- Remains calm, cool, collect, positive, ..."*
30. SRS.pdf
   *"After you determine which roles should be staffed internally, you can create an initial
list of pers..."*
31. SRS.pdf
   *"—Unknown
People begin to understand the challenges others face when they understand the ins
and out ..."*
32. SRS.pdf
   *"• Improve the quality of the information in tickets.

Special Teams: Blue and Red Teams
Security tea..."*
33. SRS.pdf
   *"However, we
imagine this configuration may not work well for a financial company or a public
utility..."*
34. SRS.pdf
   *"For the sake of simplicity, we use the term engineer to
refer to benign insiders, and malicious adve..."*
35. STELLA Apps Launch Plan (2).docx
   *"Zoom & Teams Meeting Agent: While STELLA can schedule, a plugin could integrate deeper into Zoom or ..."*
36. Stella Automotive AI - CSD v0.1.pdf
   *"Name length or character restrictions
In cases where the resource name has character restrictions o..."*
37. Stella Automotive AI - CSD v0.1.pdf
   *"Naming Strategy
An effective naming convention consists of including important information about ea..."*
38. Stella Automotive AI - CSD v0.1.pdf
   *"5.1.5.1
Proposed naming convention for high environments
5.1.5.2
Particular cases
There are some..."*
39. Stella Naming Convention Assessment.docx
   *"Ex. [saas|conv]-cluster-prd-use2-aks-01

Resource Group

Findings:

Lack of consistency on the namin..."*
40. Stella Naming Convention Assessment.docx
   *"Document Identification

Change History

Table of Contents

Networking

Findings:

There is no clear..."*
41. Stella Naming Convention Assessment.pdf
   *"3 Resource Group
Findings:
1. Lack of consistency on the naming structure.
2. Unclear reference ..."*
42. _CULTURE_ 2025 Retrospective_ Lessons Learned.md
   *"- Our engineering teams lived in **kanban** for most of 2024, taking tasks from PMO and working them..."*
43. _CULTURE_ Wiki Culture -- Why Confluence Matters.md
   *"And if you’re in the practice of dumping things into Slack, good luck trying to find it in the futur..."*
44. _HOW-TO_ Run a _Ship Room_ meeting series.md
   *"1. **Centralized Communication**: Facilitates real-time communication and decision-making among team..."*
45. _OE_ Avoid Common On-Call Pitfalls.md
   *"|
| **Deployments**                                                                                 ..."*
46. _OE_ Engineers with Prod Admin Rights.md
   *"- The moment we touch a prod host, it’s considered “dirty” and requires a redeploy ASAP.
    - The e..."*
47. _OE_ Preventing #operational_alerts flooding.md
   *"Because we were new to OE and on-call, in general, SaaS Platform teams found themselves wading waist..."*
48. _OE_ The _Correction of Error_ (COE) Mechanism.md
   *"</p></li><li><p><strong>Why do we need to use “Figure 1” style labels?</strong> You’ll refer to each..."*
49. _OE_ The _Correction of Error_ (COE) Mechanism.md
   *"| Docs nobody will read-- especially lengthy ones | **Owner or Team** | **Description** | **Rational..."*
50. _SDLC_ Why we use Jira.md
   *"- All team members need to provide at least some degree of detail in description fields. Titles, alo..."*
51. _SDLC_ Why we use Jira.md
   *"- Don’t assume other teams know where your projects live. Publish them on your team’s page for ease ..."*
52. _STRATEGY_ Understanding Conway's Law.md
   *"1. **Teams Reflect Architecture**: The way teams are organized will directly influence the software ..."*
53. mbordenet-MediumWorkingRemotely-310522-2130.pdf
   *"Biggest obstacle is the communication aspect and ensuring both sides are
committed to it.Slack work..."*
54. professional_writing_tips.md
   *"# Professional Writing Tips for Engineering Teams

Professional writing helps organizations scale ef..."*
55. professional_writing_tips.md
   *"**Incident Post-Mortems:** Analyze system failures, root causes, and improvements to prevent similar..."*
56. professional_writing_tips_updated.md
   *"1. **Choose appropriate document types** for different communication needs
2. **Establish templates*..."*
57. professional_writing_tips_updated.md
   *"1. **Choose appropriate document types** for different communication needs
2. **Establish templates*..."*
58. progit.pdf
   *"Teams
Organizations are associated with individual people by way of teams, which are simply a groupi..."*
59. progit.pdf
   *"In Deleting Remote Branches we use the --delete flag to delete a branch on the server with git
push...."*
60. progit.pdf
   *"complex projects. Topic Branches
Topic branches, however, are useful in projects of any size. A topi..."*
61. progit.pdf
   *"Having work themes isolated into topic branches also makes it easier for you to
rebase your work if ..."*
62. progit.pdf
   *"I :eyes: that :bug: and I :cold_sweat:.
:trophy: for :microscope: it.
:+1: and :sparkles: on this :s..."*
63. progit.pdf
   *"Figure 128. The Team page.
When you invite someone to a team, they will get an email letting them kn..."*
