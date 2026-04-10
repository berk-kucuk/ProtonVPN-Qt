"""Flag utilities.

We intentionally generate flag emojis from ISO 3166-1 alpha-2 codes instead of
maintaining a partial mapping. This avoids a mixed UI where only some entries
have flags.
"""

from __future__ import annotations


def country_flag(code: str) -> str:
    """Return a flag emoji for a 2-letter country code, or '' if invalid."""
    if not code:
        return ""
    c = code.strip().upper()
    if len(c) != 2 or not c.isalpha():
        return ""

    # Regional indicator symbols are U+1F1E6 (A) .. U+1F1FF (Z)
    base = 0x1F1E6
    return chr(base + (ord(c[0]) - ord("A"))) + chr(base + (ord(c[1]) - ord("A")))

