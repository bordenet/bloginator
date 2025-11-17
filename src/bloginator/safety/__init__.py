"""Safety and blocklist validation module.

This module handles:
- Blocklist management (proprietary terms, NDAs, trade secrets)
- Content validation against blocklists
- Pattern matching (exact, case-insensitive, regex)
- Violation reporting
"""

from bloginator.safety.blocklist import BlocklistManager


__all__ = ["BlocklistManager"]
