"""Predict, then observe (spec 4.2 / 16.6 predict_prompt).

The controls of a scene stay locked until the learner commits a prediction (or
explicitly skips). After committing, the verdict compares predicted vs
observed and the prediction is stored in SQLite.
"""

from __future__ import annotations

import streamlit as st

from tutor.models.content import Predict
from tutor.ui import state
from tutor.ui.components import layout


def _key(scope: str) -> str:
    return f"pred__{scope}"


def committed(scope: str) -> str | None:
    """The committed option id, ``"__skipped"``, or ``None``."""
    return st.session_state.get(_key(scope))


def is_unlocked(scope: str, predict: Predict | None) -> bool:
    return predict is None or state.mode() == "exam" or committed(scope) is not None


def clear(scope: str) -> None:
    st.session_state.pop(_key(scope), None)


def prompt(scope: str, lesson_id: str, predict: Predict | None) -> None:
    """Render the prediction block (nothing in exam mode)."""
    if predict is None or state.mode() == "exam":
        return
    done = committed(scope)
    labels = {o.id: o.label for o in predict.options}
    if done is None:
        layout.kicker("Predict first — commit before you touch anything")
        with st.container(key=f"box-predict-{scope}"):
            st.markdown(f"**{predict.question}**")
            with st.container(horizontal=True, vertical_alignment="bottom"):
                choice = st.segmented_control("Your prediction", [o.id for o in predict.options],
                                              format_func=lambda i: labels[i], key=f"{_key(scope)}__choice",
                                              label_visibility="collapsed")
                if st.button("Commit prediction", type="primary", disabled=choice is None, key=f"{_key(scope)}__go"):
                    st.session_state[_key(scope)] = choice
                    state.service().record_prediction(f"{lesson_id}/{scope}", choice, predict.correct)
                    st.rerun()
                if st.button("Skip", type="tertiary", key=f"{_key(scope)}__skip",
                             help="Predictions make the result stick. Skipping unlocks the controls anyway."):
                    st.session_state[_key(scope)] = "__skipped"
                    st.rerun()
            st.caption("The controls unlock once you commit — guessing wrong is part of the point.")
        return
    observed = labels[predict.correct]
    if done == "__skipped":
        kind, tag, head = "miss", "Skipped — here is what happens", f"Observed: **{observed}**."
    elif done == predict.correct:
        kind, tag, head = "hit", "Prediction confirmed", f"You predicted **{labels[done]}** — observed: **{observed}**."
    else:
        kind, tag, head = "miss", "Surprise — look closer", f"You predicted **{labels[done]}**, but observed: **{observed}**."
    layout.box(kind, f"{head}  \n{predict.reveal}", title=tag)
