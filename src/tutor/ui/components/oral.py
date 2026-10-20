"""Oral drill with examiner follow-ups, and paper-first whiteboard practice (spec 8.2–8.4)."""

from __future__ import annotations

import random
import time
from datetime import datetime

import streamlit as st

from tutor.engine import mock_exam
from tutor.engine.mastery import Attempt
from tutor.engine.oral import checklist_complete, coverage, missed_points, select_followups
from tutor.models.content import ContentBundle, OralQuestion, WhiteboardPrompt
from tutor.ui import state
from tutor.ui.components import prose
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
            st.markdown(f"**{part.label.capitalize()}.**")
            prose.show(part.text)
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


_GROUPS = (
    ("Explain it", ("definition", "motivation", "mechanism", "key equation")),
    ("Physical interpretation", ("physical meaning", "application")),
    ("Assumptions", ("assumptions",)),
    ("Limitations", ("limitations",)),
)


def mock_session(bundle: ContentBundle) -> None:
    """15-minute, two-topic oral. Not a quiz: speak, then a hidden checklist, then paper."""
    st.markdown('<p class="mst-kicker">Mock oral exam · two topics · 15 minutes</p>', unsafe_allow_html=True)
    st.caption("Verified material only. Say the answer aloud before you reveal anything. "
               "Draw and derive on paper. A weak topic goes back into today's review.")
    if "mock_ids" not in st.session_state:
        pool = mock_exam.eligible_questions(bundle.oral, bundle.concepts)
        if len(pool) < 2:
            st.warning("Not enough verified course questions to run a mock exam yet.")
            return
        st.markdown("This practice is **15 minutes** and two topics, each with a follow-up and, "
                    "where one exists, a paper derivation or drawing.")
        if st.button("Start mock exam", type="primary", icon=":material/timer:"):
            rng = random.Random()
            a, b = mock_exam.choose_pair(pool, rng)
            st.session_state["mock_ids"] = [a.id, b.id]
            st.session_state["mock_i"] = 0
            st.session_state["mock_t0"] = time.time()
            st.session_state[_k("mock_clock", "t0")] = st.session_state["mock_t0"]
            st.session_state["mock_done"] = False
            st.rerun()
        return

    if st.session_state.get("mock_done"):
        _mock_report(bundle)
        return

    ids = st.session_state["mock_ids"]
    i = st.session_state.get("mock_i", 0)
    q = bundle.oral[ids[i]]
    scope = f"mock_{q.id}"
    timer("mock_clock", mock_exam.LIMIT_S)
    st.markdown(f"### Topic {i + 1} of {len(ids)}")
    with st.container(key=f"box-note-mockq-{q.id}"):
        st.markdown(f"**{q.question}**")
    if not st.session_state.get(_k(scope, "revealed")):
        st.caption("Answer aloud: what it is, the equation, what it means physically, the assumptions, and where it fails. "
                   "About five minutes. Do not open the points yet.")
        if st.button("I've said my answer — show the points", type="primary", key=_k(scope, "reveal")):
            st.session_state[_k(scope, "revealed")] = True
            st.rerun()
        return

    _mock_revealed(bundle, q, scope, last=i == len(ids) - 1)


def _mock_revealed(bundle: ContentBundle, q: OralQuestion, scope: str, last: bool) -> None:
    for title, labels in _GROUPS:
        parts = [p for p in q.structure if p.label in labels]
        if not parts:
            continue
        with st.expander(title, expanded=title == "Explain it"):
            for part in parts:
                st.markdown(f"**{part.label.capitalize()}.**")
                prose.show(part.text)
    st.markdown("**Tick only the points you actually said:**")
    ticked = {p.id for p in q.expected_points if st.checkbox(p.text, key=_k(scope, f"pt_{p.id}"))}
    cov = coverage(q, ticked)
    st.progress(cov, text=f"{len(ticked)} of {len(q.expected_points)} points ({cov:.0%})")
    fups = select_followups(q, ticked, limit=2)
    followup_done = False
    if fups:
        st.markdown('<p class="mst-kicker">Examiner follow-up</p>', unsafe_allow_html=True)
        for n, f in enumerate(fups):
            with st.container(key=f"box-predict-mf-{scope}-{n}"):
                st.markdown(f"“{f.ask}”")
            if f.hint:
                with st.expander("Expected direction"):
                    st.markdown(f.hint)
        followup_done = st.checkbox("I answered the follow-up aloud", key=_k(scope, "fup"))
    paper = mock_exam.paper_for(q, bundle.whiteboard)
    paper_ok = True
    if paper is not None:
        st.markdown(f'<p class="mst-kicker">On paper · {paper.skill}</p>', unsafe_allow_html=True)
        with st.container(key=f"box-note-mp-{scope}"):
            st.markdown(f"**{paper.prompt}**")
        st.caption("Use paper or a whiteboard. The reference stays hidden until you ask for it.")
        if st.session_state.get(_k(scope, "paper_ref")):
            if paper.reference_derivation and paper.reference_derivation in bundle.derivations:
                for s in bundle.derivations[paper.reference_derivation].steps:
                    st.latex(s.latex)
            if paper.reference_figure and paper.reference_figure in FIGURES:
                st.html(as_img(FIGURES[paper.reference_figure]([])))
        elif st.button("Show the paper reference", key=_k(scope, "showref")):
            st.session_state[_k(scope, "paper_ref")] = True
            st.rerun()
        paper_ticks = {p.id for p in paper.checklist if st.checkbox(p.text, key=_k(scope, f"wb_{p.id}"))}
        paper_ok = checklist_complete(paper, paper_ticks)
        st.session_state[_k(scope, "paper_ticks")] = sorted(paper_ticks)
        st.session_state[_k(scope, "paper_id")] = paper.id
    st.session_state[_k(scope, "ticked")] = sorted(ticked)
    st.session_state[_k(scope, "followup")] = followup_done
    label = "Finish and see the report" if last else "Next topic"
    if st.button(label, type="primary", key=_k(scope, "next")):
        if last:
            _save_mock(bundle)
            st.session_state["mock_t1"] = time.time()
            st.session_state["mock_done"] = True
        else:
            st.session_state["mock_i"] = st.session_state.get("mock_i", 0) + 1
        st.rerun()
    if paper is not None and not paper_ok:
        st.caption("The paper checklist is still incomplete — you can continue, and the report will say so.")


def _save_mock(bundle: ContentBundle) -> None:
    queued: list[str] = []
    for qid in st.session_state["mock_ids"]:
        q = bundle.oral[qid]
        scope = f"mock_{q.id}"
        ticked = set(st.session_state.get(_k(scope, "ticked"), []))
        followup_done = bool(st.session_state.get(_k(scope, "followup")))
        ok = mock_exam.passed(q, ticked, followup_done)
        newly = state.service().record(
            Attempt(datetime.now(), "oral", q.id, q.concepts[0], "explain", None,
                    {"ticked": sorted(ticked), "total": len(q.expected_points), "followup": followup_done},
                    _elapsed("mock_clock"), "exam"),
            success=ok,
        )
        queued.extend(newly)
        pid = st.session_state.get(_k(scope, "paper_id"))
        if pid and pid in bundle.whiteboard:
            w = bundle.whiteboard[pid]
            pt = set(st.session_state.get(_k(scope, "paper_ticks"), []))
            state.service().record(
                Attempt(datetime.now(), "whiteboard", w.id, w.concepts[0], w.skill, None,
                        {"ticked": sorted(pt), "total": len(w.checklist), "unaided": True},
                        _elapsed("mock_clock"), "exam"),
                success=checklist_complete(w, pt),
            )
    st.session_state["mock_queued"] = sorted(set(queued))


def _mock_report(bundle: ContentBundle) -> None:
    t0 = st.session_state.get("mock_t0")
    t1 = st.session_state.get("mock_t1") or time.time()
    if t0:
        el = int(t1 - t0)
        st.markdown(f'<span class="mst-readout">Finished in {el // 60:02d}:{el % 60:02d}</span>', unsafe_allow_html=True)
    st.markdown("### Missed points")
    for qid in st.session_state["mock_ids"]:
        q = bundle.oral[qid]
        scope = f"mock_{q.id}"
        ticked = set(st.session_state.get(_k(scope, "ticked"), []))
        missed = missed_points(q, ticked)
        cov = coverage(q, ticked)
        st.markdown(f"**{q.question}** — {cov:.0%}")
        if missed:
            for line in missed:
                st.markdown(f"- {line}")
        else:
            st.markdown("- Every expected point was ticked.")
        if q.traps:
            st.caption("Traps: " + " · ".join(q.traps))
    queued = st.session_state.get("mock_queued") or []
    if queued:
        names = ", ".join(bundle.concepts[c].title for c in queued if c in bundle.concepts)
        st.markdown(f"Sent back to today's review (prerequisites that are not solid yet): **{names}**.")
    else:
        st.markdown("Nothing extra was added to today's review. Topics you missed still come back on their own Leitner interval.")
    if st.button("New mock exam"):
        for key in list(st.session_state.keys()):
            if isinstance(key, str) and (key.startswith("mock_") or key.startswith("oral__mock_")):
                del st.session_state[key]
        st.rerun()
