"""Exercise actual state glue as well as independent Streamlit sessions."""

from types import SimpleNamespace

import pytest
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from streamlit.testing.v1 import AppTest

from tutor.ui import state


@pytest.mark.parametrize("env,secret,expected", [
    (None, {}, "local"),
    (None, {"TUTOR_STORAGE_MODE": "session"}, "session"),
    ("session", {}, "session"),
    ("local", {"TUTOR_STORAGE_MODE": "session"}, "local"),
])
def test_storage_configuration(monkeypatch, env, secret, expected):
    monkeypatch.setattr(st, "session_state", {})
    monkeypatch.setattr(st, "secrets", secret)
    monkeypatch.delenv("TUTOR_STORAGE_MODE", raising=False)
    if env is not None:
        monkeypatch.setenv("TUTOR_STORAGE_MODE", env)
    assert state.storage_mode() == expected


def test_missing_secrets_preserves_local_default(monkeypatch):
    class MissingSecrets:
        def get(self, *args):
            raise StreamlitSecretNotFoundError("No secrets file")

    monkeypatch.delenv("TUTOR_STORAGE_MODE", raising=False)
    monkeypatch.setattr(st, "session_state", {})
    monkeypatch.setattr(st, "secrets", MissingSecrets())
    assert state.storage_mode() == "local"


def test_bad_secret_does_not_fall_back_to_local(monkeypatch, tmp_path):
    monkeypatch.delenv("TUTOR_STORAGE_MODE", raising=False)
    monkeypatch.setattr(st, "session_state", {})
    monkeypatch.setattr(st, "secrets", {"TUTOR_STORAGE_MODE": "typo"})
    monkeypatch.setattr(state, "DB_PATH", tmp_path / "tutor.db")
    with pytest.raises(ValueError, match="TUTOR_STORAGE_MODE"):
        state.repo()
    assert not (tmp_path / "tutor.db").exists()


def _session_probe():
    from datetime import datetime

    import streamlit as st

    from tutor.engine.mastery import Attempt
    from tutor.ui import state

    if st.button("Record for this session"):
        state.set_mode("exam")
        state.repo().set_setting("preference", "only A")
        state.service().record(
            Attempt(datetime(2026, 10, 20), "problem", "test", "ohms_law", "compute", True), True
        )
    st.json({"count": state.repo().attempt_count(), "mode": state.mode(),
             "preference": state.repo().get_setting("preference"),
             "review": len(state.repo().review_items()), "mastery": state.service().mastery()})


def test_streamlit_sessions_keep_reruns_but_never_share_progress_or_mode(monkeypatch, tmp_path):
    import json

    monkeypatch.setenv("TUTOR_STORAGE_MODE", "session")
    monkeypatch.setattr(state, "DB_PATH", tmp_path / "never.db")
    a = AppTest.from_function(_session_probe, default_timeout=30).run()
    b = AppTest.from_function(_session_probe, default_timeout=30).run()
    a.button[0].click().run()
    a.run()  # keeps the repository through unrelated reruns
    b.run()
    assert not a.exception and not b.exception
    a_data, b_data = json.loads(a.json[0].value), json.loads(b.json[0].value)
    assert a_data["count"] == 1 and a_data["mode"] == "exam"
    assert a_data["review"] > 0 and a_data["mastery"]
    assert a_data["mastery"]["ohms_law"]["compute"] == "shaky"
    assert a_data["preference"] == "only A"
    assert b_data == {"count": 0, "mode": "beginner", "preference": None, "review": 0, "mastery": {}}
    assert not (tmp_path / "never.db").exists()


def test_public_today_does_not_read_private_schedule(monkeypatch):
    from tutor.ui.pages import home

    def unexpected_read():
        raise AssertionError("Public sessions must ignore private schedules")

    monkeypatch.setenv("TUTOR_STORAGE_MODE", "session")
    monkeypatch.setattr(home, "exam_date", unexpected_read)
    at = AppTest.from_function(_today, default_timeout=30).run()
    assert not at.exception
    assert all(m.label != "Days to your exam" for m in at.metric)


def _today():
    from tutor.ui.pages import home

    home.render()


def test_lara_toast_is_transient_nonblocking_and_does_not_return_on_later_reruns(monkeypatch):
    from tutor.ui.pages import home

    session = {}
    query = {"for": "lara"}
    toasts = []
    clock = SimpleNamespace(time=lambda: 100.0)
    monkeypatch.setattr(st, "session_state", session)
    monkeypatch.setattr(st, "query_params", query)
    monkeypatch.setattr(st, "toast", lambda text, **kw: toasts.append((text, kw)))
    monkeypatch.setattr(home, "time", clock)
    home._greet()
    assert toasts == [("You can do this, Lara.", {"icon": ":material/favorite:", "duration": 5})]
    clock.time = lambda: 106.0
    home._greet()
    query.clear()
    home._greet()
    query["for"] = "lara"
    home._greet()
    assert len(toasts) == 1
    assert session["_lara_at"] == 100.0
