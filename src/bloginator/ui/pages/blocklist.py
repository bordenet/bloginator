"""Blocklist management page for Bloginator Streamlit UI."""

import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from bloginator.models.blocklist import (
    BlocklistCategory,
    BlocklistEntry,
    BlocklistPatternType,
)
from bloginator.safety.blocklist import BlocklistManager


def show():
    """Display the blocklist management page."""

    st.header("🚫 Blocklist Management")

    st.markdown(
        """
        Manage terms and patterns to prevent from appearing in generated content.
        This helps avoid leaking proprietary names, confidential projects, or sensitive information.
        """
    )

    # Initialize blocklist manager
    blocklist_file = Path(".bloginator/blocklist.json")
    manager = BlocklistManager(blocklist_file)

    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["View/Manage Entries", "Add New Entry", "Check Content"])

    with tab1:
        show_manage_entries(manager)

    with tab2:
        show_add_entry(manager)

    with tab3:
        show_check_content(manager)


def show_manage_entries(manager: BlocklistManager):
    """Show and manage existing blocklist entries."""

    st.subheader("Blocklist Entries")

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Entries", manager.get_entry_count())
    with col2:
        company_count = len(manager.get_entries_by_category(BlocklistCategory.COMPANY_NAME))
        st.metric("Company Names", company_count)
    with col3:
        product_count = len(manager.get_entries_by_category(BlocklistCategory.PRODUCT_NAME))
        st.metric("Product Names", product_count)

    st.markdown("---")

    # Category filter
    categories = ["All"] + [c.value for c in BlocklistCategory]
    selected_category = st.selectbox(
        "Filter by Category",
        options=categories,
        index=0,
        help="Filter entries by category",
    )

    # Get filtered entries
    if selected_category == "All":
        entries = manager.entries
    else:
        entries = manager.get_entries_by_category(selected_category)

    if not entries:
        st.info("No blocklist entries found. Add your first entry in the 'Add New Entry' tab.")
        return

    # Display entries in a table-like format
    st.markdown(f"**Showing {len(entries)} entries**")

    for entry in entries:
        with st.expander(
            f"🔒 {entry.pattern} ({entry.category})",
            expanded=False,
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Pattern:** `{entry.pattern}`")
                st.markdown(f"**Type:** {entry.pattern_type.value}")
                st.markdown(f"**Category:** {entry.category.value}")
                st.markdown(f"**Added:** {entry.added_date.strftime('%Y-%m-%d %H:%M')}")
                if entry.notes:
                    st.markdown(f"**Notes:** {entry.notes}")
                else:
                    st.caption("*No notes provided*")

            with col2:
                # Delete button
                if st.button(
                    "🗑️ Delete",
                    key=f"delete_{entry.id}",
                    help="Remove this entry from the blocklist",
                ):
                    if manager.remove_entry(entry.id):
                        st.success(f"Deleted entry: {entry.pattern}")
                        st.rerun()
                    else:
                        st.error("Failed to delete entry")


def show_add_entry(manager: BlocklistManager):
    """Show form for adding new blocklist entries."""

    st.subheader("Add New Blocklist Entry")

    st.markdown(
        """
        Create a new blocklist entry to prevent specific terms or patterns from appearing
        in generated content.
        """
    )

    with st.form("add_entry_form"):
        # Pattern input
        pattern = st.text_input(
            "Pattern to Block *",
            placeholder="e.g., Acme Corp, Project Falcon, etc.",
            help="The exact term, phrase, or regex pattern to block",
        )

        # Pattern type selection
        pattern_type = st.selectbox(
            "Pattern Type *",
            options=[
                BlocklistPatternType.EXACT,
                BlocklistPatternType.CASE_INSENSITIVE,
                BlocklistPatternType.REGEX,
            ],
            format_func=lambda x: {
                BlocklistPatternType.EXACT: "Exact Match (case-sensitive)",
                BlocklistPatternType.CASE_INSENSITIVE: "Case-Insensitive Match",
                BlocklistPatternType.REGEX: "Regular Expression",
            }[x],
            help="How to match the pattern in text",
        )

        # Category selection
        category = st.selectbox(
            "Category *",
            options=list(BlocklistCategory),
            format_func=lambda x: x.value.replace("_", " ").title(),
            help="Type of content being blocked",
        )

        # Notes
        notes = st.text_area(
            "Notes (optional)",
            placeholder="Explain why this term should be blocked...",
            help="Optional explanation for why this pattern is blocked",
            max_chars=500,
        )

        # Submit button
        submitted = st.form_submit_button("Add to Blocklist", type="primary")

        if submitted:
            if not pattern:
                st.error("Pattern is required")
            else:
                # Create new entry
                entry = BlocklistEntry(
                    id=str(uuid.uuid4()),
                    pattern=pattern.strip(),
                    pattern_type=pattern_type,
                    category=category,
                    added_date=datetime.now(),
                    notes=notes.strip(),
                )

                # Test if it's a valid regex pattern
                if pattern_type == BlocklistPatternType.REGEX:
                    import re

                    try:
                        re.compile(pattern)
                    except re.error as e:
                        st.error(f"Invalid regex pattern: {e}")
                        return

                # Add to blocklist
                manager.add_entry(entry)
                st.success(f"✓ Added '{pattern}' to blocklist")

                # Show example test
                st.markdown("---")
                st.markdown("**Test your new entry:**")
                test_text = st.text_input(
                    "Enter test text to verify the pattern matches correctly",
                    key="test_after_add",
                )
                if test_text:
                    matches = entry.matches(test_text)
                    if matches:
                        st.warning(f"✓ Pattern matched: {matches}")
                    else:
                        st.info("No matches found in test text")


def show_check_content(manager: BlocklistManager):
    """Show content validation against blocklist."""

    st.subheader("Check Content for Violations")

    st.markdown(
        """
        Validate text content against the blocklist to check for any blocked terms or patterns.
        """
    )

    # Content input
    content = st.text_area(
        "Content to Check",
        placeholder="Paste content here to check for blocklist violations...",
        height=200,
        help="Enter any text to validate against the blocklist",
    )

    # Check button
    if st.button("🔍 Check for Violations", type="primary", disabled=not content):
        if not content:
            st.warning("Please enter content to check")
            return

        # Validate
        result = manager.validate_text(content)

        st.markdown("---")

        # Display results
        if result["is_valid"]:
            st.success("✓ No violations found! Content is safe.")
        else:
            st.error(f"✗ Found {len(result['violations'])} violation(s)")

            st.markdown("**Violations:**")

            for i, violation in enumerate(result["violations"], 1):
                with st.container():
                    st.markdown(
                        f"""
                        <div class="error-box">
                        <strong>Violation {i}:</strong> {violation['pattern']}<br>
                        <strong>Category:</strong> {violation['category']}<br>
                        <strong>Matched text:</strong> {', '.join(violation['matches'])}<br>
                        <strong>Notes:</strong> {violation['notes'] or 'No notes'}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("")

            # Provide suggestions
            st.markdown("---")
            st.markdown("**Recommended Actions:**")
            st.markdown("- Remove or replace the blocked terms before publishing")
            st.markdown("- Review the blocklist entries if any seem incorrect")
            st.markdown("- Consider using generic terms instead of proprietary names")

    # Quick stats
    st.markdown("---")
    st.markdown("**Blocklist Statistics**")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Patterns", manager.get_entry_count())
    with col2:
        exact_count = len(
            [e for e in manager.entries if e.pattern_type == BlocklistPatternType.EXACT]
        )
        st.metric("Exact Match", exact_count)
    with col3:
        regex_count = len(
            [e for e in manager.entries if e.pattern_type == BlocklistPatternType.REGEX]
        )
        st.metric("Regex Patterns", regex_count)
