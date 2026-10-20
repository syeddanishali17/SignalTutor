from datetime import date

from tutor.greeting import LARA, message_for
from tutor.local_schedule import exam_date


def test_lara_greeting_is_exact_and_private():
    assert message_for({"for": "lara"}) == LARA
    assert message_for({}) is None
    assert message_for({"for": "Lara"}) is None
    assert message_for({"for": "lara-extra"}) is None
    assert "Lara" not in (message_for({"scene": "loop"}) or "")


def test_exam_date_is_absent_without_a_local_file(tmp_path):
    assert exam_date(tmp_path / "missing.yaml") is None
    path = tmp_path / "schedule.yaml"
    path.write_text("exam: 2028-03-01\n", encoding="utf-8")
    assert exam_date(path) == date(2028, 3, 1)
