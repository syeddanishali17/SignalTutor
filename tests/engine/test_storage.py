"""Persistent local storage and private public-session storage use the same service."""

from datetime import datetime

import pytest

from tutor.engine.concept_graph import ConceptGraph
from tutor.engine.mastery import Attempt
from tutor.engine.study import StudyService
from tutor.models.loader import load_or_raise
from tutor.persistence.storage import create_repo


def _record(repo):
    bundle = load_or_raise()
    svc = StudyService(repo, bundle, ConceptGraph(bundle.concepts))
    attempt = Attempt(datetime(2026, 10, 20, 10), "problem", "test", "ohms_law", "compute", True)
    svc.record(attempt, success=True)
    svc.record_prediction("foundation_playground", "up", "up")
    repo.set_setting("mode", "exam")
    repo.set_setting("learner_preference", "A")
    return svc.mastery()


def test_local_mode_persists_across_repository_instances(tmp_path):
    path = tmp_path / "local" / "tutor.db"
    first = create_repo("local", path)
    mastery = _record(first)
    reopened = create_repo("local", path)
    assert path.is_file()
    assert reopened.attempts() == first.attempts()
    assert reopened.review_items() == first.review_items()
    assert reopened.predictions() == first.predictions()
    assert reopened.get_setting("mode") == "exam"
    bundle = load_or_raise()
    assert StudyService(reopened, bundle, ConceptGraph(bundle.concepts)).mastery() == mastery


def test_session_storage_isolates_every_learner_table_and_does_not_touch_local_data(tmp_path):
    path = tmp_path / "tutor.db"
    local = create_repo("local", path)
    local.set_setting("mode", "course")
    first = create_repo("session", path)
    second = create_repo("session", path)
    mastery = _record(first)
    assert mastery["ohms_law"]["compute"] == "shaky"
    assert first.attempt_count() == 1
    assert first.review_items()
    assert first.predictions()
    assert second.attempts() == []
    assert second.review_items() == []
    assert second.predictions() == []
    assert second.get_setting("mode", "beginner") == "beginner"
    assert second.get_setting("learner_preference") is None
    with first._conn() as a, second._conn() as b:
        assert a.execute("SELECT COUNT(*) FROM mastery").fetchone()[0] > 0
        assert b.execute("SELECT COUNT(*) FROM mastery").fetchone()[0] == 0
        assert a.execute("PRAGMA database_list").fetchone()[2] == ""  # RAM, no shared file
    second.set_setting("mode", "course")
    second.set_setting("learner_preference", "B")
    assert first.get_setting("mode") == "exam"
    assert first.get_setting("learner_preference") == "A"
    assert local.get_setting("mode") == "course"
    assert local.attempt_count() == 0
    fresh = create_repo("session", path)
    assert fresh.attempt_count() == 0
    assert fresh.get_setting("mode") is None


def test_session_mode_creates_no_data_directory(tmp_path):
    path = tmp_path / "unused" / "tutor.db"
    repo = create_repo("session", path)
    repo.set_setting("mode", "exam")
    assert not path.parent.exists()


@pytest.mark.parametrize("invalid", ["", "sessions", "SESSION"])
def test_invalid_mode_fails_without_creating_a_shared_file(tmp_path, invalid):
    path = tmp_path / "tutor.db"
    with pytest.raises(ValueError, match="TUTOR_STORAGE_MODE"):
        create_repo(invalid, path)
    assert not path.exists()
