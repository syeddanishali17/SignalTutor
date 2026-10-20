"""How a formula is shown in each teaching mode.

Hard rule (spec 15): exam mode never shows a ``needs_review`` formula without
its flag. Every UI path renders formulas through :func:`view`, and a test
checks the rule for every formula and every mode.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tutor.models.content import Formula

Mode = Literal["beginner", "course", "exam"]
MODES: tuple[Mode, ...] = ("beginner", "course", "exam")


@dataclass(frozen=True)
class FormulaView:
    latex: str  # the form to display prominently
    flag: str | None  # warning text; never None for needs_review
    lecture_latex: str | None  # the original lecture form, shown for comparison
    badge: str  # short source/status badge


def view(f: Formula, mode: Mode) -> FormulaView:
    evidence = ", ".join(f.evidence) if f.evidence else "—"
    if f.status == "needs_review":
        assert f.canonical_form and f.issue  # guaranteed by the schema
        ref = f" ({f.known_issue})" if f.known_issue else ""
        flag = f"⚠ needs review{ref}: {f.issue}"
        lecture = f.lecture_form if mode != "exam" else None
        return FormulaView(f.canonical_form, flag, lecture, f"needs review · {f.source}")
    flag = None
    if f.known_issue and mode != "exam":
        flag = f"Linked source issue {f.known_issue} — see Sources."
    label = {"verified": "verified (notes)", "supplemental": "supplemental", "future": "future"}[f.status]
    return FormulaView(f.lecture_form, flag, None, f"{label} · {f.source} · checks: {evidence}")
