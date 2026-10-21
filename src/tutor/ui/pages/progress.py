"""Progress: rule-based mastery states, weakest first (spec 9). No blended percentages."""

from __future__ import annotations

import html

import streamlit as st

from tutor.engine.mastery import RULES, SKILLS, STATE_LABEL, weakness_rank
from tutor.ui import state
from tutor.ui.components import layout


def render() -> None:
    layout.page_header("Reference", "Progress",
                       "Four skills per concept, four states each. The rules are below — no hidden scoring.")
    bundle = state.bundle()
    mastery = state.mastery_cached()

    with st.expander("How mastery works", expanded=not mastery):
        rows = "\n".join(f"| **{s}** | {RULES[s]['solid']} | {RULES[s]['exam_ready']} |" for s in SKILLS)
        st.markdown("| skill | → solid | → exam-ready |\n|---|---|---|\n" + rows)
        st.caption("Shaky = attempted but not yet solid. Not started = no attempt yet.")

    if not mastery:
        st.markdown('<p class="mst-muted">No attempts yet. Every problem, oral answer, faded derivation and whiteboard '
                    "drill you complete shows up here.</p>", unsafe_allow_html=True)
    else:
        counts = {k: 0 for k in STATE_LABEL}
        for skills in mastery.values():
            for s in skills.values():
                counts[s] += 1
        st.markdown(" ".join(f"{layout.badge_html(k)} × {v}" for k, v in counts.items()), unsafe_allow_html=True)
        st.markdown("### Weakest first")
        for cid, skills in sorted(mastery.items(), key=lambda kv: weakness_rank(kv[1])):
            title = bundle.concepts[cid].title if cid in bundle.concepts else cid
            badges = " ".join(layout.badge_html(skills[s], s) for s in SKILLS)
            st.markdown(f"**{html.escape(title)}**<br>{badges}", unsafe_allow_html=True)

    preds = state.repo().predictions()
    if preds:
        hits = sum(1 for p in preds if p[2] == p[3])
        made = sum(1 for p in preds if p[2] != "__skipped")
        st.markdown("### Predictions")
        st.markdown(f"You checked **{made}** predictions and got **{hits}** right. "
                    "Wrong predictions are where learning happens — revisit those scenes.")
    if state.storage_mode() == "session":
        st.caption(f"{state.repo().attempt_count()} attempts in this browser session. "
                   "Progress resets when the session or app restarts.")
    else:
        st.caption(f"{state.repo().attempt_count()} attempts stored locally in SQLite.")
