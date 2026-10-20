"""Oral drill with examiner follow-ups, and paper-first whiteboard practice (spec 8.2–8.4)."""

from __future__ import annotations

import streamlit as st

from tutor.ui import state
from tutor.ui.components import layout
from tutor.ui.components.oral import oral_dock, whiteboard_drill

PRIORITY = {"very_high": "★★★", "high": "★★", "medium": "★"}


def render() -> None:
    layout.page_header("Practice", "Oral & whiteboard",
                       "Answer out loud, then tick what you really said. Draw on paper, then compare.")
    bundle = state.bundle()
    st.session_state.setdefault("oral_tab", "Oral drill")
    tab = st.segmented_control("Mode", ["Oral drill", "Whiteboard", "Mock exam"], key="oral_tab", required=True)
    if tab == "Oral drill":
        qs = sorted(bundle.oral.values(), key=lambda q: ({"very_high": 0, "high": 1, "medium": 2}[q.priority], q.id))
        qid = st.selectbox("Question", [q.id for q in qs],
                           format_func=lambda i: f"{PRIORITY[bundle.oral[i].priority]}  {bundle.oral[i].question}",
                           key="oral_pick")
        oral_dock(bundle.oral[qid], scope=f"oralpage_{qid}")
    elif tab == "Whiteboard":
        wid = st.selectbox("Prompt", list(bundle.whiteboard), format_func=lambda i: bundle.whiteboard[i].prompt,
                           key="wb_pick")
        whiteboard_drill(bundle.whiteboard[wid], scope=f"wbpage_{wid}")
    else:
        st.info("The timed two-topic mock exam (about 20 minutes, with follow-ups and a report) is part of the "
                "review-engine milestone. Until then: pick two ★★★ questions above, start the timer, and answer "
                "both within 20 minutes — including one follow-up each.", icon=":material/schedule:")
