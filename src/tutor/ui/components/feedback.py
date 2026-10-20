"""Failure banners and grading feedback (spec 16.6 failure_banner, 16.14)."""

from __future__ import annotations

import streamlit as st

from tutor.engine.problems import Grade
from tutor.models.content import BreakIt
from tutor.ui.components import layout


def failure_banner(title: str, cause: str, condition: str, consequence: str, recovery: str) -> None:
    """Cause / when / effect / fix — Markdown + LaTeX allowed in every field."""
    layout.box(
        "fail",
        f"**Cause:** {cause}  \n**When:** {condition}  \n**Effect:** {consequence}  \n**Fix:** {recovery}",
        title=f"⚠ {title}",
    )


def break_it_banner(b: BreakIt) -> None:
    failure_banner(b.title, b.cause, b.condition, b.consequence, b.recovery)


def invalid_state(message: str) -> None:
    """Physical explanation instead of NaN / blank plots / exceptions."""
    layout.box("fail", message, title="⚠ Not a physical state")


def grade_feedback(g: Grade) -> None:
    if g.status == "invalid":
        st.info(g.message, icon=":material/edit:")
        return
    if g.status == "correct":
        st.success(g.message, icon=":material/check_circle:")
        return
    body = f"**{g.message}**"
    if g.expected:
        body += f"  \nExpected: **{g.expected}**"
    if g.misconception_text:
        body += f"  \n\n**Likely misconception:** “{g.misconception_text}”  \n{g.correction}"
    st.error(body, icon=":material/cancel:")
