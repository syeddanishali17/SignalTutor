from datetime import date, datetime, timedelta

import pytest

from tutor.engine import mastery as M
from tutor.engine.concept_graph import ConceptGraph
from tutor.engine.scheduler import ReviewItem, after_result, due_items, estimate_minutes, schedule_prerequisites
from tutor.engine.study import StudyService
from tutor.models.content import Concept
from tutor.models.loader import load_or_raise
from tutor.persistence.repo import Repo

T0 = datetime(2026, 11, 2, 10, 0)


def att(days: float, correct=None, item_type="problem", skill="compute", checklist=None, concept="c"):
    return M.Attempt(T0 + timedelta(days=days), item_type, "item", concept, skill, correct, checklist or {})


# --- Leitner -----------------------------------------------------------------------


def test_leitner_up_and_down():
    today = date(2026, 11, 2)
    it = after_result(None, "problem", "p", True, today)
    assert (it.box, it.due) == (2, today + timedelta(days=3))
    it = after_result(it, "problem", "p", True, today)
    assert (it.box, it.due) == (3, today + timedelta(days=7))
    it = after_result(it, "problem", "p", False, today)
    assert (it.box, it.due) == (1, today + timedelta(days=1))
    for _ in range(10):
        it = after_result(it, "problem", "p", True, today)
    assert (it.box, it.due) == (5, today + timedelta(days=30))


def test_due_and_estimate():
    today = date(2026, 11, 2)
    items = [ReviewItem("problem", "a", 1, today), ReviewItem("oral", "b", 2, today - timedelta(days=1)),
             ReviewItem("concept", "c", 3, today + timedelta(days=1))]
    due = due_items(items, today)
    assert [i.item_id for i in due] == ["b", "a"]
    assert estimate_minutes(due) == 6


def test_prerequisites_pulled_forward():
    today = date(2026, 11, 2)
    existing = {("concept", "x"): ReviewItem("concept", "x", 4, today + timedelta(days=10))}
    out = schedule_prerequisites(existing, ["x", "y"], today)
    assert {(i.item_id, i.box, i.due) for i in out} == {("x", 1, today), ("y", 1, today)}


# --- mastery rules (spec section 9) ---------------------------------------------------------


def test_compute_states():
    assert M.skill_state([], "compute") == "not_started"
    assert M.skill_state([att(0, True), att(0, False)], "compute") == "shaky"
    four_of_five = [att(0, True), att(0, False), att(0, True), att(0, True), att(0, True)]
    assert M.skill_state(four_of_five, "compute") == "solid"
    assert M.skill_state(four_of_five + [att(6.9, True)], "compute") == "solid"
    assert M.skill_state(four_of_five + [att(7.0, True)], "compute") == "exam_ready"
    # falling below 4/5 again makes it shaky
    assert M.skill_state(four_of_five + [att(8, False), att(8, False)], "compute") == "shaky"


def test_derive_states():
    full = {"ticked": ["a", "b"], "total": 2}
    assert M.skill_state([att(0, False, "derivation", "derive")], "derive") == "shaky"
    assert M.skill_state([att(0, True, "derivation", "derive")], "derive") == "solid"
    two_days = [att(0, None, "whiteboard", "derive", full), att(1, None, "whiteboard", "derive", full)]
    assert M.skill_state(two_days, "derive") == "exam_ready"
    same_day = [att(0, None, "whiteboard", "derive", full), att(0.1, None, "whiteboard", "derive", full)]
    assert M.skill_state(same_day, "derive") == "solid"


def test_explain_states():
    good = {"ticked": list("abcd"), "total": 5, "followup": True}
    weak = {"ticked": ["a"], "total": 5}
    assert M.skill_state([att(0, None, "oral", "explain", weak)], "explain") == "shaky"
    assert M.skill_state([att(0, None, "oral", "explain", {**good, "followup": False})], "explain") == "solid"
    assert M.skill_state([att(0, None, "oral", "explain", good), att(2, None, "oral", "explain", good)], "explain") == "exam_ready"
    assert M.skill_state([att(0, None, "oral", "explain", good), att(2, None, "oral", "explain", good),
                          att(3, None, "oral", "explain", weak)], "explain") == "shaky"


def test_draw_states():
    full = {"ticked": ["a", "b"], "total": 2}
    unaided = {**full, "unaided": True}
    assert M.skill_state([att(0, None, "whiteboard", "draw", {"ticked": ["a"], "total": 2})], "draw") == "shaky"
    assert M.skill_state([att(0, None, "whiteboard", "draw", full)], "draw") == "solid"
    assert M.skill_state([att(0, None, "whiteboard", "draw", full), att(7, None, "whiteboard", "draw", full)], "draw") == "solid"
    assert M.skill_state([att(0, None, "whiteboard", "draw", full), att(7, None, "whiteboard", "draw", unaided)], "draw") == "exam_ready"


# --- concept graph ------------------------------------------------------------------------------


def _c(cid, pre, track="electrical"):
    return Concept(id=cid, title=cid, track=track, prerequisites=pre, status="supplemental", one_liner="x")


def test_cycle_detection_and_order():
    g = ConceptGraph({"a": _c("a", []), "b": _c("b", ["a"]), "c": _c("c", ["b"])})
    assert g.find_cycle() is None
    assert g.path_to("c") == ["a", "b", "c"]
    g2 = ConceptGraph({"a": _c("a", ["c"]), "b": _c("b", ["a"]), "c": _c("c", ["b"])})
    cyc = g2.find_cycle()
    assert cyc is not None and cyc[0] == cyc[-1]
    g3 = ConceptGraph({"a": _c("a", ["missing"])})
    assert g3.undefined_references() == [("a", "missing")]


def test_real_graph_path_to_bridge():
    bundle = load_or_raise()
    g = ConceptGraph(bundle.concepts)
    path = g.path_to("wheatstone_full")
    assert path[-1] == "wheatstone_full"
    for i, cid in enumerate(path):
        for p in bundle.concepts[cid].prerequisites:
            assert path.index(p) < i, f"{p} must come before {cid}"
    assert "voltage_divider" in path and "gauge_factor" in path


# --- study service (persistence + scheduling + mastery together) -------------------------------------


def test_study_service_records_and_queues_prerequisites(tmp_path):
    bundle = load_or_raise()
    repo = Repo(tmp_path / "t.db")
    svc = StudyService(repo, bundle, ConceptGraph(bundle.concepts), clock=lambda: T0)
    a = M.Attempt(T0, "problem", "full_bridge_output", "wheatstone_full", "compute", False)
    queued = svc.record(a, success=False)
    assert set(queued) == {"wheatstone_quarter", "gauge_factor"}
    due = {(i.item_type, i.item_id) for i in svc.due(T0.date())}
    assert ("concept", "gauge_factor") in due
    item = repo.review_item("problem", "full_bridge_output")
    assert item is not None and item.box == 1
    assert svc.mastery()["wheatstone_full"]["compute"] == "shaky"
    # persistence across a new repo object (restart)
    repo2 = Repo(tmp_path / "t.db")
    assert len(repo2.attempts()) == 1
    repo2.set_setting("mode", "course")
    assert Repo(tmp_path / "t.db").get_setting("mode") == "course"


def test_repo_roundtrip_checklist(tmp_path):
    repo = Repo(tmp_path / "r.db")
    a = M.Attempt(T0, "oral", "why_bridge", "wheatstone_bridge", "explain", None,
                  {"ticked": ["a"], "total": 3, "followup": True}, 42.0, "practice")
    repo.record_attempt(a)
    (b,) = repo.attempts("wheatstone_bridge")
    assert b == a
    assert b.checklist_ratio == pytest.approx(1 / 3)
