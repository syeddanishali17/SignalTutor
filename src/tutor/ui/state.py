"""Shared, cached resources and the teaching mode. The only Streamlit-aware glue."""

from __future__ import annotations

import streamlit as st

from tutor.engine.concept_graph import ConceptGraph
from tutor.engine.formula_view import Mode
from tutor.engine.study import StudyService
from tutor.models.content import ContentBundle
from tutor.models.loader import load_or_raise
from tutor.paths import DB_PATH
from tutor.persistence.repo import Repo

MODE_LABELS: dict[str, str] = {"beginner": "Beginner", "course": "Course", "exam": "Exam"}


@st.cache_resource(show_spinner=False)
def bundle() -> ContentBundle:
    return load_or_raise()


@st.cache_resource(show_spinner=False)
def graph() -> ConceptGraph:
    return ConceptGraph(bundle().concepts)


@st.cache_resource(show_spinner=False)
def repo() -> Repo:
    return Repo(DB_PATH)


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
