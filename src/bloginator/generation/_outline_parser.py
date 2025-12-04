"""Parsing for outline generation responses."""

from bloginator.models.outline import OutlineSection
from bloginator.search import SearchResult


def parse_outline_response(content: str) -> list[OutlineSection]:
    """Parse LLM outline response into OutlineSection objects.

    Args:
        content: LLM generated outline text

    Returns:
        List of top-level OutlineSection objects
    """
    sections = []
    current_section: OutlineSection | None = None
    current_subsection: OutlineSection | None = None

    lines = content.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Main section (## Heading)
        if line.startswith("## "):
            if current_section:
                sections.append(current_section)
            title = line[3:].strip()
            current_section = OutlineSection(title=title)
            current_subsection = None

        # Subsection (### Heading)
        elif line.startswith("### "):
            if current_section:
                title = line[4:].strip()
                current_subsection = OutlineSection(title=title)
                current_section.subsections.append(current_subsection)

        # Description text (for current section/subsection)
        elif current_subsection:
            current_subsection.description += " " + line if current_subsection.description else line
        elif current_section:
            current_section.description += " " + line if current_section.description else line

    # Add final section
    if current_section:
        sections.append(current_section)

    return sections


def build_outline_from_corpus(
    results: list[SearchResult],
    keywords: list[str],
    num_sections: int = 5,
) -> list[OutlineSection]:
    """Build outline directly from corpus search results.

    This is a fallback when LLM outline generation produces hallucinations.
    Extracts natural sections based on actual corpus content.

    Args:
        results: Search results from corpus
        keywords: Keywords to focus on
        num_sections: Target number of sections

    Returns:
        List of OutlineSection objects based on corpus content
    """
    sections = []

    # Extract first heading or natural topic boundaries from each result
    for result in results[:num_sections]:
        # Try to extract a meaningful title from the content
        lines = result.content.split("\n")
        title = "Untitled Section"

        # Look for markdown headings
        for line in lines[:5]:
            if line.startswith("##"):
                title = line.replace("##", "").strip()
                break
            elif line.startswith("#"):
                title = line.replace("#", "").strip()
                break

        # Use first non-empty line as fallback
        if title == "Untitled Section":
            for line in lines:
                if line.strip() and not line.startswith(("[", ">")):
                    title = line.strip()[:80]  # Limit length
                    break

        # Extract description from first 100 chars
        description = result.content[:150].replace("\n", " ").strip()
        if len(description) > 100:
            description = description[:100] + "..."

        # Create section with keyword awareness
        section = OutlineSection(
            title=title,
            description=description,
        )
        sections.append(section)

        if len(sections) >= num_sections:
            break

    return sections if sections else []
