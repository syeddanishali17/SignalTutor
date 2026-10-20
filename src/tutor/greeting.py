"""Optional personal greeting. Only the exact query ``for=lara`` returns text."""

from __future__ import annotations

from collections.abc import Mapping

LARA = "You can do this, Lara."


def message_for(query: Mapping[str, str]) -> str | None:
    value = query.get("for")
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    if value == "lara":
        return LARA
    return None
