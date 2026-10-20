"""Shared content resources and session-owned learner state."""

from __future__ import annotations

import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from tutor.engine.concept_graph import ConceptGraph
from tutor.engine.formula_view import Mode
from tutor.engine.study import StudyService
from tutor.models.content import ContentBundle
from tutor.models.loader import load_or_raise
from tutor.paths import DB_PATH
from tutor.persistence.repo import Repo
from tutor.persistence.storage import create_repo, validate_mode

MODE_LABELS: dict[str, str] = {"beginner": "Beginner", "course": "Course", "exam": "Exam"}


@st.cache_resource(show_spinner=False)
def bundle() -> ContentBundle:
    return load_or_raise()


@st.cache_resource(show_spinner=False)
def graph() -> ConceptGraph:
    return ConceptGraph(bundle().concepts)


def storage_mode() -> str:
    """Pin configuration for this session; config changes require a new session.

    An explicit environment variable wins over Community Cloud's root secret.
    Missing configuration preserves persistent local development behaviour.
    Invalid configuration fails rather than falling back to a shared database.
    """
    if "_storage_mode" not in st.session_state:
        value = os.environ.get("TUTOR_STORAGE_MODE")
        if value is None:
            try:
                value = st.secrets.get("TUTOR_STORAGE_MODE", "local")
            except StreamlitSecretNotFoundError:
                value = "local"
        st.session_state["_storage_mode"] = validate_mode(value)
    return st.session_state["_storage_mode"]


def repo() -> Repo:
    """Only content/graph may be globally cached. Learner storage belongs here."""
    if "_learner_repo" not in st.session_state:
        st.session_state["_learner_repo"] = create_repo(storage_mode(), DB_PATH)
    return st.session_state["_learner_repo"]


def service() -> StudyService:
    return StudyService(repo(), bundle(), graph())


def mode() -> Mode:
    if "mode" not in st.session_state:
        st.session_state["mode"] = repo().get_setting("mode", "beginner")
    return st.session_state["mode"]  # type: ignore[return-value]


def set_mode(m: str) -> None:
    st.session_state["mode"] = m
    repo().set_setting("mode", m)


def mastery_cached() -> dict[str, dict[str, str]]:
    """Mastery per concept, recomputed once per script run."""
    key = "_mastery_run"
    run_id = st.session_state.get("_run_counter", 0)
    cached = st.session_state.get(key)
    if cached and cached[0] == run_id:
        return cached[1]
    m = service().mastery()
    st.session_state[key] = (run_id, m)
    return m
