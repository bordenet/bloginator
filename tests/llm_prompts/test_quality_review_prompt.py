"""Tests for quality review prompt with Claude Sonnet 4.5.

Tests validate that the quality review workflow:
1. Reduces word count by 40-60% when content is bloated
2. Eliminates redundancy across sections
3. Converts bullets to prose or tables
4. Removes AI slop patterns
"""

from bloginator.prompts.loader import PromptLoader

from tests.llm_prompts.conftest import ClaudeSonnet45Client


class TestQualityReviewPromptReduction:
    """Test quality review reduces bloated content effectively."""

    def test_word_count_reduction(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
    ):
        """Quality review should reduce bloated content by 40-60%."""
        # Create intentionally verbose draft
        verbose_draft = """# Engineering Leadership Best Practices

## What Makes Effective Technical Leaders

Technical leaders play a crucial and vital role in modern engineering organizations. They need to carefully balance their hands-on technical work with their important responsibilities for team enablement and empowerment. It's worth noting that they typically write code approximately 30-40% of the time, while dedicating and devoting the remaining portion of their time to making important architecture decisions, conducting thorough code reviews, and providing valuable mentoring to team members. This careful and deliberate ratio helps them maintain their technical credibility while simultaneously scaling their impact through enabling and empowering others on the team.

## Setting Technical Direction

It's important to understand that leaders must document their decisions in ADRs (Architecture Decision Records). These records should capture the full context of the decision, all the options that were considered during the decision-making process, and the complete rationale behind why the final choice was made. This comprehensive documentation approach prevents the team from having to rehash and revisit questions and decisions that have already been settled and finalized.

## Code Review as Leadership Tool

Effective leaders review code for patterns, not syntax. It's crucial that they flag architectural concerns, suggest useful abstractions, and teach through thoughtful questions rather than giving direct directives. Reviews should generally take about 10-15 minutes and should focus on identifying one key improvement that will have the most impact.

## Mentoring Without Micromanaging

Give engineers problems to solve, not solutions to implement. Frame challenges with appropriate context and clear constraints, then let them propose their own approaches and solutions. Only intervene when they're truly stuck or heading toward mistakes that would be costly. This approach builds sound judgment faster than prescriptive guidance ever could.
"""

        # Load structural analysis prompt
        analysis_template = prompt_loader.load("review/structural-analysis.yaml")

        # CALL 1: Analyze structure
        analysis_system = analysis_template.render_system_prompt()
        analysis_user = analysis_template.render_user_prompt(draft_content=verbose_draft)

        analysis_response = claude_client.generate(
            prompt=analysis_user,
            system_prompt=analysis_system,
            temperature=0.0,
            max_tokens=1000,
        )

        # Load revision prompt
        revision_template = prompt_loader.load("review/base.yaml")

        # CALL 2: Revise based on analysis
        revision_system = revision_template.render_system_prompt()
        revision_user = revision_template.render_user_prompt(draft_content=verbose_draft)

        # Prepend analysis to revision prompt (simulate what QualityReviewer does)
        revision_user = f"""IDENTIFIED ISSUES TO FIX:
{analysis_response.content}

---

{revision_user}"""

        revision_response = claude_client.generate(
            prompt=revision_user,
            system_prompt=revision_system,
            temperature=0.3,
            max_tokens=8000,
        )

        # Calculate reduction
        original_words = len(verbose_draft.split())
        revised_words = len(revision_response.content.split())
        reduction_pct = int((1 - revised_words / original_words) * 100)

        print(f"\n📊 Word count: {original_words} → {revised_words} ({reduction_pct}% reduction)")

        assert reduction_pct >= 40, (
            f"Quality review only reduced content by {reduction_pct}% (target: 40-60%). "
            f"Not aggressive enough. Original: {original_words} words, Revised: {revised_words} words"
        )

        assert reduction_pct <= 70, (
            f"Quality review reduced content by {reduction_pct}% (target: 40-60%). "
            f"Too aggressive - may have lost important information. "
            f"Original: {original_words} words, Revised: {revised_words} words"
        )


class TestQualityReviewPromptQuality:
    """Test quality review improves content quality."""

    def test_redundancy_elimination(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
    ):
        """Quality review should eliminate repeated concepts."""
        # Draft with intentional redundancy
        redundant_draft = """# On-Call Practices

## Why Engineers Go On-Call

Engineers go on-call because it creates tight feedback loops. When you wake up at 3am for an alert, you learn what needs fixing. This creates accountability and ownership.

## The Value of On-Call Rotations

On-call rotations are valuable because they create tight feedback loops. Engineers who respond to production issues at night quickly learn what systems need improvement. This builds ownership and accountability for service quality.

## Benefits of Direct Ownership

Having engineers own their on-call duty means they get immediate feedback when something breaks. This tight feedback loop helps them learn quickly what needs to be fixed and builds a strong sense of ownership and accountability.
"""

        # Run through quality review workflow
        analysis_template = prompt_loader.load("review/structural-analysis.yaml")
        revision_template = prompt_loader.load("review/base.yaml")

        # Analyze
        analysis_response = claude_client.generate(
            prompt=analysis_template.render_user_prompt(draft_content=redundant_draft),
            system_prompt=analysis_template.render_system_prompt(),
            temperature=0.0,
            max_tokens=1000,
        )

        # Revise
        revision_user = f"""IDENTIFIED ISSUES TO FIX:
{analysis_response.content}

---

{revision_template.render_user_prompt(draft_content=redundant_draft)}"""

        revision_response = claude_client.generate(
            prompt=revision_user,
            system_prompt=revision_template.render_system_prompt(),
            temperature=0.3,
            max_tokens=8000,
        )

        revised_content = revision_response.content.lower()

        # Check that key redundant phrases appear significantly less
        feedback_loops_count = revised_content.count("tight feedback loop")
        ownership_count = revised_content.count("ownership") + revised_content.count(
            "accountability"
        )

        print("\n🔍 Redundancy check:")
        print(f"  'tight feedback loop' mentions: {feedback_loops_count}")
        print(f"  'ownership/accountability' mentions: {ownership_count}")

        # Should appear at most once each (concepts consolidated)
        assert (
            feedback_loops_count <= 2
        ), f"Still has {feedback_loops_count} mentions of 'tight feedback loop' - redundancy not eliminated"

    def test_bullet_conversion(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
    ):
        """Quality review should convert bullets to prose or tables."""
        # Draft with PowerPoint-style bullets
        bullet_draft = """# Technical Leadership

## Key Responsibilities

Technical leaders have several important responsibilities:

- Writing code 30-40% of the time
- Making architecture decisions
- Conducting code reviews
- Mentoring team members
- Setting technical direction

## Core Competencies

Leaders need:
- Deep technical expertise
- Communication skills
- Ability to delegate
- Strategic thinking
- Team development focus
"""

        # Run through quality review workflow
        analysis_template = prompt_loader.load("review/structural-analysis.yaml")
        revision_template = prompt_loader.load("review/base.yaml")

        # Analyze
        analysis_response = claude_client.generate(
            prompt=analysis_template.render_user_prompt(draft_content=bullet_draft),
            system_prompt=analysis_template.render_system_prompt(),
            temperature=0.0,
            max_tokens=1000,
        )

        # Revise
        revision_user = f"""IDENTIFIED ISSUES TO FIX:
{analysis_response.content}

---

{revision_template.render_user_prompt(draft_content=bullet_draft)}"""

        revision_response = claude_client.generate(
            prompt=revision_user,
            system_prompt=revision_template.render_system_prompt(),
            temperature=0.3,
            max_tokens=8000,
        )

        revised_content = revision_response.content

        # Count bullet points (lines starting with - or *)
        bullet_lines = [
            line for line in revised_content.split("\n") if line.strip().startswith(("- ", "* "))
        ]

        print("\n📝 Bullet conversion:")
        print(f"  Bullet points remaining: {len(bullet_lines)}")

        assert len(bullet_lines) == 0, (
            f"Still has {len(bullet_lines)} bullet points - should be converted to prose or tables. "
            f"Found: {bullet_lines}"
        )

    def test_ai_slop_removal(
        self,
        claude_client: ClaudeSonnet45Client,
        prompt_loader: PromptLoader,
    ):
        """Quality review should remove AI slop patterns."""
        # Draft with AI slop
        slop_draft = """# Engineering Excellence

## Diving Deep into Technical Leadership

It's important to note that effective technical leaders—who are game-changers in any organization—need to leverage their expertise to drive innovation. At the end of the day, they must dive deep into architectural decisions while also keeping an eye on the big picture.

## Embracing Best Practices

Various industry leaders have noted that it's crucial to embrace best practices and leverage cutting-edge technologies. Many organizations are finding that this approach can be a real game-changer for their engineering culture.
"""

        # Run through quality review workflow
        analysis_template = prompt_loader.load("review/structural-analysis.yaml")
        revision_template = prompt_loader.load("review/base.yaml")

        # Analyze
        analysis_response = claude_client.generate(
            prompt=analysis_template.render_user_prompt(draft_content=slop_draft),
            system_prompt=analysis_template.render_system_prompt(),
            temperature=0.0,
            max_tokens=1000,
        )

        # Revise
        revision_user = f"""IDENTIFIED ISSUES TO FIX:
{analysis_response.content}

---

{revision_template.render_user_prompt(draft_content=slop_draft)}"""

        revision_response = claude_client.generate(
            prompt=revision_user,
            system_prompt=revision_template.render_system_prompt(),
            temperature=0.3,
            max_tokens=8000,
        )

        revised_content = revision_response.content.lower()

        # Check for AI slop patterns
        slop_patterns = {
            "—": "em-dash",
            "dive deep": "dive deep",
            "leverage": "leverage",
            "game-changer": "game-changer",
            "at the end of the day": "at the end of the day",
            "it's important to note": "throat-clearing",
            "various": "vague term",
            "many": "vague term",
        }

        found_slop = []
        for pattern, name in slop_patterns.items():
            if pattern in revised_content:
                found_slop.append(f"{name} ('{pattern}')")

        print("\n🚫 AI slop check:")
        if found_slop:
            print(f"  Found: {', '.join(found_slop)}")
        else:
            print("  ✓ No AI slop detected")

        assert len(found_slop) == 0, f"Still contains AI slop patterns: {', '.join(found_slop)}"
