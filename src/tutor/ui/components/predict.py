"""Optional predictions, recorded independently of the live experiment."""

from __future__ import annotations

import streamlit as st

from tutor.models.content import Predict
from tutor.ui import state
from tutor.ui.components import layout


def _key(scope: str) -> str:
    return f"pred__{scope}"


def checked(scope: str) -> str | None:
    """The saved option id, or None when the learner has not checked it."""
    return st.session_state.get(_key(scope))


def prompt(scope: str, lesson_id: str, predict: Predict | None) -> None:
    """Offer a thinking aid without changing circuit state (hidden in exam mode)."""
    if predict is None or state.mode() == "exam":
        return
    labels = {o.id: o.label for o in predict.options}
    # Older sessions may contain a skipped sentinel; it is simply unanswered now.
    done = checked(scope)
    if done not in labels:
        done = None
    with st.expander("What do you expect?"):
        st.caption("Optional prediction · Try the live controls whenever you like.")
        if done is None:
            st.markdown(f"**{predict.question}**")
            choice = st.segmented_control("Your prediction", list(labels),
                                          format_func=labels.get, key=f"{_key(scope)}__choice")
            if st.button("Check prediction", disabled=choice is None, key=f"{_key(scope)}__go"):
                state.service().record_prediction(f"{lesson_id}/{scope}", choice, predict.correct)
                st.session_state[_key(scope)] = choice
                st.rerun()
            return
        expected = labels[predict.correct]
        if done == predict.correct:
            kind, tag = "hit", "Prediction matches the expected outcome"
        else:
            kind, tag = "miss", "Reconsider your prediction"
        layout.box(kind, f"You predicted **{labels[done]}**. Expected in this scenario: **{expected}**."
                   f"\n\n{predict.reveal}\n\nTest the idea with the live controls; "
                   "the diagram shows the current control values.", title=tag)
