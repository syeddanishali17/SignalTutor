"""Creator signature, defined once and shared by the app footer, the home page and exports.

Pure Python (no Streamlit) so the one-pager exporter can use it too.
"""

from __future__ import annotations

APP_NAME = "Modern Sensor Tutor"
CREATOR = "Danish"
SIGNATURE = f"{APP_NAME} · Built by {CREATOR}"
SIGNATURE_SHORT = f"Built by {CREATOR}"


def signature(short: bool = False) -> str:
    """The signature line; ``short`` where space is tight."""
    return SIGNATURE_SHORT if short else SIGNATURE
