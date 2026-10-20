"""Study service: one place that turns a learner action into stored state.

Recording an attempt
1. stores the attempt,
2. moves the item *and* its concept through the Leitner boxes,
3. on failure, queues the concept's unmastered prerequisites for today,
4. refreshes the cached mastery states.

Framework-independent: the Streamlit layer only calls these methods.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Callable

from tutor.engine import mastery as M
from tutor.engine.concept_graph import ConceptGraph
from tutor.engine.scheduler import ReviewItem, after_result, due_items, estimate_minutes, schedule_prerequisites
from tutor.models.content import ContentBundle
from tutor.persistence.repo import Repo


class StudyService:
    def __init__(self, repo: Repo, bundle: ContentBundle, graph: ConceptGraph, clock: Callable[[], datetime] = datetime.now):
        self.repo = repo
        self.bundle = bundle
        self.graph = graph
        self.clock = clock

    def today(self) -> date:
        return self.clock().date()

    def record(self, attempt: M.Attempt, success: bool) -> list[str]:
        """Store an attempt and update review state. Returns concept ids newly queued for review."""
        today = attempt.ts.date()
        self.repo.record_attempt(attempt)
        for item_type, item_id in ((attempt.item_type, attempt.item_id), ("concept", attempt.concept_id)):
            cur = self.repo.review_item(item_type, item_id)
            self.repo.upsert_review(after_result(cur, item_type, item_id, success, today))
        queued: list[str] = []
        if not success:
            states = self.mastery()
            mastered = {cid for cid, s in states.items() if M.is_mastered(s)}
            prereqs = self.graph.unmastered_prerequisites(attempt.concept_id, mastered)
            existing = {(i.item_type, i.item_id): i for i in self.repo.review_items()}
            for item in schedule_prerequisites(existing, prereqs, today):
                self.repo.upsert_review(item)
                queued.append(item.item_id)
        self.repo.cache_mastery(self.mastery_for(attempt.concept_id), self.clock())
        return queued

    def review_concept(self, concept_id: str, success: bool) -> None:
        """A self-checked recall of a concept with no auto-graded item: moves only the concept's box."""
        today = self.today()
        cur = self.repo.review_item("concept", concept_id)
        self.repo.upsert_review(after_result(cur, "concept", concept_id, success, today))

    def mastery_for(self, concept_id: str) -> dict[str, dict[str, M.State]]:
        return M.concept_states(self.repo.attempts(concept_id))

    def mastery(self) -> dict[str, dict[str, M.State]]:
        return M.concept_states(self.repo.attempts())

    def due(self, today: date | None = None) -> list[ReviewItem]:
        return due_items(self.repo.review_items(), today or self.today())

    def due_summary(self, today: date | None = None) -> tuple[list[ReviewItem], int]:
        items = self.due(today)
        return items, estimate_minutes(items)

    def record_prediction(self, lesson_id: str, prediction: str, actual: str) -> None:
        self.repo.record_prediction(lesson_id, prediction, actual, self.clock())
