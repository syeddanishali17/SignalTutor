"""Mock exam draws two verified lecture topics, never supplemental or lecture 3."""

import random

from tutor.engine import mock_exam
from tutor.engine.oral import coverage
from tutor.models.loader import load_or_raise


def test_pool_is_verified_course_only():
    bundle = load_or_raise()
    pool = mock_exam.eligible_questions(bundle.oral, bundle.concepts)
    assert len(pool) >= 2
    for q in pool:
        concept = bundle.concepts[q.concepts[0]]
        assert concept.status == "verified"
        assert concept.track in mock_exam.COURSE_TRACKS
        assert q.priority == "very_high"


def test_pair_has_two_concepts():
    bundle = load_or_raise()
    pool = mock_exam.eligible_questions(bundle.oral, bundle.concepts)
    for seed in range(12):
        a, b = mock_exam.choose_pair(pool, random.Random(seed))
        assert a.concepts[0] != b.concepts[0]


def test_pass_needs_coverage_and_followup():
    bundle = load_or_raise()
    q = next(iter(mock_exam.eligible_questions(bundle.oral, bundle.concepts)))
    all_ids = {p.id for p in q.expected_points}
    assert coverage(q, all_ids) == 1
    assert mock_exam.passed(q, all_ids, True)
    assert not mock_exam.passed(q, set(), True)
    if q.followups:
        assert not mock_exam.passed(q, all_ids, False)


def test_paper_prompt_shares_a_concept():
    bundle = load_or_raise()
    q = bundle.oral["derive_quarter"]
    paper = mock_exam.paper_for(q, bundle.whiteboard)
    assert paper is not None
    assert set(paper.concepts) & set(q.concepts)
