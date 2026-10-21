"""Shared lesson-screen anatomy (spec 16.2), used by every interactive scene.

    problem → predict → [ visual | inspector ] → control tray → equation strip
    → consequence → [Why?] [Derive] [Break it] [Check] [Explain it]

Linking (spec 16.5): one selection per scene, resolved once per run into
(highlighted SVG parts, outlined controls, boxed equation terms) — so the
picture, the controls, the equation and the inspector always agree.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Callable

import streamlit as st

from tutor.engine.mastery import Attempt
from tutor.models.content import Lesson, Scene
from tutor.ui import state, theme
from tutor.ui.components import diagram, equation, inspector, layout, predict, prose
from tutor.ui.components.feedback import break_it_banner
from tutor.ui.components.oral import oral_dock, whiteboard_drill
from tutor.ui.components.practice import problem_card
from tutor.ui.svg.core import as_img


def top(scope: str, lesson: Lesson, scene: Scene) -> None:
    """Problem line and optional prediction; controls are always independent."""
    _dev_query_hooks(scope, scene)
    layout.problem_line(scene.problem)
    predict.prompt(scope, lesson.id, scene.predict)


def _dev_query_hooks(scope: str, scene: Scene) -> None:
    """TUTOR_DEV only: ``?sel=R1`` selects a part for screenshot QA without clicking."""
    if os.environ.get("TUTOR_DEV") != "1":
        return
    qp = st.query_params
    sel = qp.get("sel")
    ids = {i.id for i in scene.inspect} | {t.id for t in scene.terms}
    if sel and inspector.selected(scope) is None and sel in ids:
        st.session_state[inspector.sel_key(scope)] = sel


def resolved(scope: str, scene: Scene) -> inspector.Resolved:
    """The current selection, resolved — call before drawing the figure."""
    res = inspector.resolve(scene, inspector.selected(scope))
    if res.controls:
        theme.highlight_controls([f"ctl_{scope}_{c}" for c in res.controls])
    return res


def main_row(scope: str, scene: Scene, svg: str, below_visual: Callable[[], None] | None = None,
             ratio: tuple[float, float] = (3, 2)) -> None:
    with st.container(key="lessonrow"):
        left, right = st.columns(list(ratio), gap="medium")
        with left:
            with st.container(key="visual"):
                diagram.show(svg)
                if below_visual:
                    below_visual()
                st.caption("Select a part using the Parts controls or equation symbols.")
        with right:
            inspector.inspector_panel(scope, scene)
    with st.expander("Full-width diagram"):
        diagram.show(svg, max_width=1400)


def tray_header() -> None:
    layout.kicker("Controls")


def deeper(scope: str, lesson: Lesson, scene: Scene, derive: Callable[[], None] | None = None,
           extra_break: Callable[[], None] | None = None) -> None:
    labels = ["Why?"] + (["Derive"] if derive else []) + ["Break it", "Check", "Explain it"]
    key = f"deep__{scope}"
    if st.session_state.get(key) not in labels:
        st.session_state[key] = "Why?"
    tab = st.segmented_control("Go deeper", labels, key=key, required=True)
    if tab == "Why?":
        _why(scene)
        _formulas(lesson, scene)
    elif tab == "Derive" and derive:
        derive()
    elif tab == "Break it":
        _break(lesson, scene, extra_break)
    elif tab == "Check":
        _check(scope, lesson, scene)
    elif tab == "Explain it":
        _explain(scope, lesson, scene)


def _why(scene: Scene) -> None:
    bundle = state.bundle()
    if scene.notes_md:
        prose.show(scene.notes_md)
    if scene.analogy_note and state.mode() != "exam":
        layout.analogy(scene.analogy_note)
    layout.kicker("The ideas in this scene")
    for cid in scene.concepts:
        c = bundle.concepts[cid]
        with st.expander(c.title):
            inspector.concept_card(c, compact=True)
            if c.explanation:
                st.divider()
                prose.show(c.explanation)
            st.caption(f"Content status: {c.status} · source: {', '.join(c.source_refs) or '—'}")


def _formulas(lesson: Lesson, scene: Scene) -> None:
    bundle = state.bundle()
    fs = [bundle.formulas[f] for f in lesson.formulas if bundle.formulas[f].concept in scene.concepts]
    if not fs:
        return
    layout.kicker("Formulas in this scene (with source and status)")
    for f in fs:
        equation.formula_card(f)


def _break(lesson: Lesson, scene: Scene, extra: Callable[[], None] | None) -> None:
    items = [b for b in lesson.break_it if b.id in scene.break_it]
    if not items and extra is None:
        st.markdown("Nothing to break in this scene — the ideal model holds exactly here.")
    for b in items:
        break_it_banner(b)
    if extra:
        extra()


def _check(scope: str, lesson: Lesson, scene: Scene) -> None:
    bundle = state.bundle()
    pids = [pid for pid in lesson.problems if bundle.problems[pid].concept in scene.concepts]
    if not pids:
        st.markdown("No auto-graded problems for this scene yet.")
    for pid in pids:
        problem_card(bundle.problems[pid], scope=f"{scope}__check", show_concept=True)


def _explain(scope: str, lesson: Lesson, scene: Scene) -> None:
    """'Now explain this without the visual' (spec 16.15 #11)."""
    layout.kicker("Explain it without the picture")
    with st.container(key=f"box-note-explain-{scope}"):
        st.markdown(f"**{scene.explain.prompt}**")
    st.caption("Say it out loud (or to a friend). Then tick what you really covered.")
    key = f"explain__{scope}"
    ticked = [p for i, p in enumerate(scene.explain.points) if st.checkbox(p, key=f"{key}__{i}")]
    if st.session_state.get(f"{key}__saved"):
        st.success("Saved towards the *explain* skill.", icon=":material/check_circle:")
    elif st.button("Save", key=f"{key}__save", type="primary"):
        st.session_state[f"{key}__saved"] = True
        n = len(scene.explain.points)
        state.service().record(
            Attempt(datetime.now(), "oral", f"{lesson.id}/{scene.id}", scene.concepts[0], "explain", None,
                    {"ticked": ticked, "total": n, "followup": False}, None, state.mode()),
            success=len(ticked) == n,
        )
        st.rerun()
    bundle = state.bundle()
    related = [q for q in lesson.oral if set(bundle.oral[q].concepts) & set(scene.concepts)]
    wb = [w for w in lesson.whiteboard if set(bundle.whiteboard[w].concepts) & set(scene.concepts)]
    if related or wb:
        st.divider()
    for qid in related:
        with st.expander(f"Exam question with follow-ups: {bundle.oral[qid].question}"):
            oral_dock(bundle.oral[qid], scope=f"{scope}__{qid}")
    for wid in wb:
        with st.expander(f"Whiteboard: {bundle.whiteboard[wid].prompt}"):
            whiteboard_drill(bundle.whiteboard[wid], scope=f"{scope}__{wid}")
