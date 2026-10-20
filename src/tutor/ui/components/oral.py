"""Oral drill with examiner follow-ups, and paper-first whiteboard practice (spec 8.2–8.4)."""

from __future__ import annotations

import html
import time
from datetime import datetime

import streamlit as st

from tutor.engine.mastery import Attempt
from tutor.engine.oral import checklist_complete, coverage, select_followups
from tutor.models.content import OralQuestion, WhiteboardPrompt
from tutor.ui import state
from tutor.ui.svg.core import as_img
from tutor.ui.svg.figures import FIGURES


def _k(scope: str, what: str) -> str:
    return f"oral__{scope}__{what}"


@st.fragment(run_every=1)
def _ticker(start_key: str, limit_s: int | None, stop_key: str) -> None:
    start = st.session_state.get(start_key)
    if start is None:
        return
    end = st.session_state.get(stop_key) or time.time()
    el = int(end - start)
    txt = f"⏱ {el // 60:02d}:{el % 60:02d}"
    if limit_s:
        left = limit_s - el
        txt += f"  ·  {'over by' if left < 0 else 'left'} {abs(left) // 60:02d}:{abs(left) % 60:02d}"
    st.markdown(f'<span class="mst-readout">{txt}</span>', unsafe_allow_html=True)


def timer(scope: str, limit_s: int | None = None) -> None:
    start_key, stop_key = _k(scope, "t0"), _k(scope, "t1")
    c1, c2 = st.columns([1, 3], vertical_alignment="center")
    with c1:
        if st.session_state.get(start_key) is None:
            if st.button("Start timer", key=_k(scope, "tstart"), icon=":material/timer:"):
                st.session_state[start_key] = time.time()
                st.rerun()
    with c2:
        if st.session_state.get(start_key) is not None and st.session_state.get(stop_key) is None:
            _ticker(start_key, limit_s, stop_key)
        elif st.session_state.get(stop_key):
            el = int(st.session_state[stop_key] - st.session_state[start_key])
            st.markdown(f'<span class="mst-readout">⏱ {el // 60:02d}:{el % 60:02d} (stopped)</span>', unsafe_allow_html=True)


def _elapsed(scope: str) -> float | None:
    t0 = st.session_state.get(_k(scope, "t0"))
    if t0 is None:
        return None
    return (st.session_state.get(_k(scope, "t1")) or time.time()) - t0


def _reset(scope: str) -> None:
    for k in list(st.session_state.keys()):
        if isinstance(k, str) and k.startswith(f"oral__{scope}__"):
            del st.session_state[k]


def oral_dock(q: OralQuestion, scope: str) -> None:
    st.markdown('<p class="mst-kicker">Oral drill · say it out loud</p>', unsafe_allow_html=True)
    with st.container(key=f"box-note-oq-{scope}"):
        st.markdown(f"**{q.question}**")
    timer(scope)
    revealed = st.session_state.get(_k(scope, "revealed"), False)
    if not revealed:
        st.caption("Answer aloud as if facing the examiner (about 2 minutes). Then reveal the answer structure.")
        if st.button("Reveal answer structure", type="primary", key=_k(scope, "reveal")):
            st.session_state[_k(scope, "revealed")] = True
            if st.session_state.get(_k(scope, "t0")) and not st.session_state.get(_k(scope, "t1")):
                st.session_state[_k(scope, "t1")] = time.time()
            st.rerun()
        return

    with st.expander("Answer structure", expanded=True):
        for part in q.structure:
            st.markdown(f"**{part.label.capitalize()}.** {part.text}")
    st.markdown("**Tick the points you actually said:**")
    ticked = {p.id for p in q.expected_points if st.checkbox(p.text, key=_k(scope, f"pt_{p.id}"))}
    cov = coverage(q, ticked)
    st.progress(cov, text=f"{len(ticked)} of {len(q.expected_points)} points ({cov:.0%}) — solid needs 80 %")
    fups = select_followups(q, ticked)
    followup_done = False
    if fups:
        f = fups[0]
        st.markdown('<p class="mst-kicker">Examiner follow-up</p>', unsafe_allow_html=True)
        with st.container(key=f"box-predict-fu-{scope}"):
            st.markdown(f"“{f.ask}”")
        if f.hint:
            with st.expander("Hint / expected direction"):
                st.markdown(f.hint)
        followup_done = st.checkbox("I answered the follow-up aloud", key=_k(scope, "fup"))
        if len(fups) > 1:
            st.caption("Further follow-ups the examiner might ask: " + " · ".join(x.ask for x in fups[1:3]))
    saved = st.session_state.get(_k(scope, "saved"))
    if not saved:
        if st.button("Save this attempt", type="primary", key=_k(scope, "save")):
            st.session_state[_k(scope, "saved")] = True
            state.service().record(
                Attempt(datetime.now(), "oral", q.id, q.concepts[0], "explain", None,
                        {"ticked": sorted(ticked), "total": len(q.expected_points), "followup": followup_done},
                        _elapsed(scope), state.mode()),
                success=len(ticked) == len(q.expected_points),
            )
            st.rerun()
    else:
        st.success("Attempt saved. It counts towards the *explain* skill.", icon=":material/check_circle:")
        if q.traps:
            st.markdown("**Exam traps** (shown after your attempt):")
            for t in q.traps:
                st.markdown(f"- {t}")
        st.button("Try again", key=_k(scope, "again"), on_click=_reset, args=(scope,))


def whiteboard_drill(w: WhiteboardPrompt, scope: str) -> None:
    bundle = state.bundle()
    st.markdown(f'<p class="mst-kicker">Whiteboard · paper first ({w.skill})</p>', unsafe_allow_html=True)
    with st.container(key=f"box-note-wb-{scope}"):
        st.markdown(f"**{w.prompt}**")
    st.caption("Use paper or a real whiteboard — that is the motor skill the exam needs.")
    timer(scope, w.time_limit_s)
    if not st.session_state.get(_k(scope, "revealed")):
        if st.button("I'm done — reveal the reference", type="primary", key=_k(scope, "reveal")):
            st.session_state[_k(scope, "revealed")] = True
            if st.session_state.get(_k(scope, "t0")) and not st.session_state.get(_k(scope, "t1")):
                st.session_state[_k(scope, "t1")] = time.time()
            st.rerun()
        return
    c1, c2 = st.columns([3, 2])
    with c1:
        if w.reference_figure:
            st.html(as_img(FIGURES[w.reference_figure]([])))
    with c2:
        if w.reference_derivation:
            d = bundle.derivations[w.reference_derivation]
            for s in d.steps:
                st.latex(s.latex)
    st.markdown("**Checklist — tick what your drawing/derivation really contains:**")
    ticked = {p.id for p in w.checklist if st.checkbox(p.text, key=_k(scope, f"pt_{p.id}"))}
    unaided = st.checkbox("I did this without looking at notes", key=_k(scope, "unaided"), value=True)
    if not st.session_state.get(_k(scope, "saved")):
        if st.button("Save this attempt", type="primary", key=_k(scope, "save")):
            st.session_state[_k(scope, "saved")] = True
            state.service().record(
                Attempt(datetime.now(), "whiteboard", w.id, w.concepts[0], w.skill, None,
                        {"ticked": sorted(ticked), "total": len(w.checklist), "unaided": unaided},
                        _elapsed(scope), state.mode()),
                success=checklist_complete(w, ticked),
            )
            st.rerun()
    else:
        st.success(f"Saved. It counts towards the *{w.skill}* skill.", icon=":material/check_circle:")
        st.button("Try again", key=_k(scope, "again"), on_click=_reset, args=(scope,))
