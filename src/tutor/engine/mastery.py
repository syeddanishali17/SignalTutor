"""Rule-based mastery states (spec section 9). No blended percentages.

Each (concept, skill) pair is one of ``not_started``, ``shaky``, ``solid``,
``exam_ready``. The rules are transparent and shown in the UI verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Literal

State = Literal["not_started", "shaky", "solid", "exam_ready"]
STATES: tuple[State, ...] = ("not_started", "shaky", "solid", "exam_ready")
SKILLS = ("compute", "derive", "explain", "draw")
STATE_LABEL = {"not_started": "not started", "shaky": "shaky", "solid": "solid", "exam_ready": "exam-ready"}

RULES = {
    "compute": {
        "solid": "4 of your last 5 auto-graded answers are correct.",
        "exam_ready": "Solid, and correct again 7 or more days after you first reached solid.",
    },
    "derive": {
        "solid": "A faded derivation answered correctly (or one complete paper derivation).",
        "exam_ready": "Full paper derivation with every checklist item ticked, on two separate days.",
    },
    "explain": {
        "solid": "Your latest oral answer hit at least 80 % of the checklist.",
        "exam_ready": "80 % or better including at least one follow-up, on two separate days (latest also ≥ 80 %).",
    },
    "draw": {
        "solid": "Whiteboard checklist complete once.",
        "exam_ready": "Complete again, unaided, 7 or more days after the first complete drawing.",
    },
}

ORAL_THRESHOLD = 0.8


@dataclass(frozen=True)
class Attempt:
    ts: datetime
    item_type: str  # problem | derivation | oral | whiteboard
    item_id: str
    concept_id: str
    skill: str
    correct: bool | None = None
    checklist: dict = field(default_factory=dict)  # {"ticked": [...], "total": n, "followup": bool, "unaided": bool}
    duration_s: float | None = None
    mode: str = "practice"

    @property
    def checklist_ratio(self) -> float:
        total = self.checklist.get("total") or 0
        return len(self.checklist.get("ticked", [])) / total if total else 0.0

    @property
    def checklist_complete(self) -> bool:
        total = self.checklist.get("total") or 0
        return total > 0 and len(self.checklist.get("ticked", [])) >= total


def _compute_state(attempts: list[Attempt]) -> State:
    graded = [a for a in attempts if a.item_type == "problem" and a.correct is not None]
    if not graded:
        return "not_started"
    graded.sort(key=lambda a: a.ts)

    def solid_at(i: int) -> bool:
        window = graded[max(0, i - 4) : i + 1]
        return sum(1 for a in window if a.correct) >= 4

    if not solid_at(len(graded) - 1):
        return "shaky"
    first_solid = next(i for i in range(len(graded)) if solid_at(i))
    t_solid = graded[first_solid].ts
    later_correct = any(a.correct and a.ts >= t_solid + timedelta(days=7) for a in graded[first_solid + 1 :])
    return "exam_ready" if later_correct else "solid"


def _derive_state(attempts: list[Attempt]) -> State:
    faded = [a for a in attempts if a.item_type == "derivation"]
    paper = [a for a in attempts if a.item_type == "whiteboard" and a.skill == "derive"]
    if not faded and not paper:
        return "not_started"
    complete_days = {a.ts.date() for a in paper if a.checklist_complete}
    if len(complete_days) >= 2:
        return "exam_ready"
    if any(a.correct for a in faded) or complete_days:
        return "solid"
    return "shaky"


def _explain_state(attempts: list[Attempt]) -> State:
    oral = sorted((a for a in attempts if a.item_type == "oral"), key=lambda a: a.ts)
    if not oral:
        return "not_started"
    if oral[-1].checklist_ratio < ORAL_THRESHOLD:
        return "shaky"
    good_days = {a.ts.date() for a in oral if a.checklist_ratio >= ORAL_THRESHOLD and a.checklist.get("followup")}
    return "exam_ready" if len(good_days) >= 2 else "solid"


def _draw_state(attempts: list[Attempt]) -> State:
    wb = sorted((a for a in attempts if a.item_type == "whiteboard" and a.skill == "draw"), key=lambda a: a.ts)
    if not wb:
        return "not_started"
    complete = [a for a in wb if a.checklist_complete]
    if not complete:
        return "shaky"
    first = complete[0].ts
    if any(a.checklist.get("unaided") and a.ts >= first + timedelta(days=7) for a in complete[1:]):
        return "exam_ready"
    return "solid"


_RULE_FUNCS = {"compute": _compute_state, "derive": _derive_state, "explain": _explain_state, "draw": _draw_state}


def skill_state(attempts: Iterable[Attempt], skill: str) -> State:
    return _RULE_FUNCS[skill](list(attempts))


def concept_states(attempts: Iterable[Attempt]) -> dict[str, dict[str, State]]:
    """{concept_id: {skill: state}} for every concept that has attempts."""
    by_concept: dict[str, list[Attempt]] = {}
    for a in attempts:
        by_concept.setdefault(a.concept_id, []).append(a)
    return {cid: {s: skill_state(lst, s) for s in SKILLS} for cid, lst in by_concept.items()}


def is_mastered(states: dict[str, State] | None) -> bool:
    """A concept counts as mastered for prerequisite gating when any skill is solid or better."""
    return bool(states) and any(s in ("solid", "exam_ready") for s in states.values())  # type: ignore[union-attr]


def weakness_rank(states: dict[str, State]) -> tuple[int, int]:
    """Sort key: concepts with the most shaky / not-started skills first."""
    order = {"shaky": 0, "not_started": 1, "solid": 2, "exam_ready": 3}
    vals = sorted(order[s] for s in states.values())
    return (vals[0], sum(vals))
