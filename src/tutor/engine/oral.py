"""Oral drill and examiner follow-up question trees (spec 8.2, 8.3)."""

from __future__ import annotations

from tutor.models.content import Followup, OralQuestion, WhiteboardPrompt


def coverage(question: OralQuestion, ticked: set[str]) -> float:
    """Fraction of expected points the learner hit (the self-rating; no 1–5 guess)."""
    ids = [p.id for p in question.expected_points]
    if not ids:
        return 0.0
    return sum(1 for i in ids if i in ticked) / len(ids)


def missed_points(question: OralQuestion, ticked: set[str]) -> list[str]:
    return [p.text for p in question.expected_points if p.id not in ticked]


def select_followups(question: OralQuestion, ticked: set[str], limit: int | None = None) -> list[Followup]:
    """Deterministic follow-up tree: probe missing points first, then the always-asked ones."""
    targeted = [f for f in question.followups if f.when_missing and f.when_missing not in ticked]
    always = [f for f in question.followups if f.always]
    out = targeted + always
    return out[:limit] if limit is not None else out


def checklist_complete(prompt: WhiteboardPrompt, ticked: set[str]) -> bool:
    return all(p.id in ticked for p in prompt.checklist)
