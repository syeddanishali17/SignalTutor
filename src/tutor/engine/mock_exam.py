"""Two-topic mock oral exam.

Picks only questions whose primary concept is verified course material
(lecture 1 or 2). Supplemental foundations and an empty lecture-3 track
are never drawn. The session itself lives in the UI; this module only
chooses topics and scores what the learner ticked.
"""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence

from tutor.engine.mastery import ORAL_THRESHOLD
from tutor.engine.oral import coverage, missed_points
from tutor.models.content import Concept, OralQuestion, WhiteboardPrompt

COURSE_TRACKS = frozenset({"course_l01", "course_l02"})
LIMIT_S = 15 * 60


def eligible_questions(
    oral: Mapping[str, OralQuestion], concepts: Mapping[str, Concept]
) -> list[OralQuestion]:
    """Very-high-priority questions on verified lecture-1/2 concepts."""
    out: list[OralQuestion] = []
    for q in oral.values():
        if q.priority != "very_high" or not q.concepts:
            continue
        concept = concepts.get(q.concepts[0])
        if concept is None or concept.status != "verified" or concept.track not in COURSE_TRACKS:
            continue
        out.append(q)
    return sorted(out, key=lambda q: q.id)


def choose_pair(questions: Sequence[OralQuestion], rng: random.Random) -> tuple[OralQuestion, OralQuestion]:
    """Two questions with different primary concepts."""
    if len(questions) < 2:
        raise ValueError("A mock exam needs at least two verified course questions")
    order = list(questions)
    rng.shuffle(order)
    first = order[0]
    for other in order[1:]:
        if other.concepts[0] != first.concepts[0]:
            return first, other
    raise ValueError("Verified questions do not cover two different concepts")


def paper_for(question: OralQuestion, whiteboard: Mapping[str, WhiteboardPrompt]) -> WhiteboardPrompt | None:
    """A paper drawing or derivation that shares a concept with the question, if one exists."""
    wanted = set(question.concepts)
    hits = [w for w in whiteboard.values() if wanted & set(w.concepts)]
    if not hits:
        return None
    hits.sort(key=lambda w: (0 if w.skill == "derive" else 1, w.id))
    return hits[0]


def passed(question: OralQuestion, ticked: set[str], followup_done: bool) -> bool:
    """Solid oral bar: 80 % of the points, and the follow-up if the question has one."""
    if coverage(question, ticked) < ORAL_THRESHOLD:
        return False
    if question.followups and not followup_done:
        return False
    return True


def report_lines(question: OralQuestion, ticked: set[str]) -> list[str]:
    return missed_points(question, ticked)
