"""Leitner spaced review (spec 8.6): boxes 1–5 with intervals 1, 3, 7, 14, 30 days."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta

INTERVALS_DAYS = (1, 3, 7, 14, 30)
MAX_BOX = len(INTERVALS_DAYS)

# rough minutes per item type for the "Today's review" estimate
MINUTES = {"concept": 1.5, "problem": 2.0, "oral": 4.0, "whiteboard": 6.0, "derivation": 3.0}


@dataclass(frozen=True)
class ReviewItem:
    item_type: str  # concept | problem | oral | whiteboard | derivation
    item_id: str
    box: int
    due: date


def interval_for(box: int) -> int:
    return INTERVALS_DAYS[max(1, min(box, MAX_BOX)) - 1]


def after_result(item: ReviewItem | None, item_type: str, item_id: str, success: bool, today: date) -> ReviewItem:
    """New Leitner state after one review.

    * A new item starts in box 1; a success moves it up one box, a failure
      drops it to box 1.
    * The next due date is ``today + interval(new box)``.
    """
    box = item.box if item else 1
    new_box = min(box + 1, MAX_BOX) if success else 1
    due = today + timedelta(days=interval_for(new_box))
    if item is None:
        return ReviewItem(item_type, item_id, new_box, due)
    return replace(item, box=new_box, due=due)


def schedule_prerequisites(
    existing: dict[tuple[str, str], ReviewItem], prereq_concepts: list[str], today: date
) -> list[ReviewItem]:
    """Concept items to add (or pull forward to today) after a failure."""
    out: list[ReviewItem] = []
    for cid in prereq_concepts:
        cur = existing.get(("concept", cid))
        if cur is None:
            out.append(ReviewItem("concept", cid, 1, today))
        elif cur.due > today:
            out.append(replace(cur, box=1, due=today))
    return out


def due_items(items: list[ReviewItem], today: date) -> list[ReviewItem]:
    return sorted((i for i in items if i.due <= today), key=lambda i: (i.due, i.box, i.item_type, i.item_id))


def estimate_minutes(items: list[ReviewItem]) -> int:
    total = sum(MINUTES.get(i.item_type, 2.0) for i in items)
    return int(round(total))
