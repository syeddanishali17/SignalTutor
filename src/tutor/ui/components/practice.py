"""Auto-graded problem card (spec 8.1)."""

from __future__ import annotations

import html
import random
from datetime import datetime

import streamlit as st

from tutor.engine.mastery import Attempt
from tutor.engine.problems import Grade, generate, grade, render
from tutor.models.content import Problem
from tutor.ui import state
from tutor.ui.components import prose
from tutor.ui.components.feedback import grade_feedback

LEVEL = {1: "Recognise", 2: "Understand", 3: "Understand", 4: "Apply", 5: "Apply+"}


def _k(scope: str, pid: str, what: str) -> str:
    return f"pb__{scope}__{pid}__{what}"


def problem_card(p: Problem, scope: str, show_concept: bool = True) -> Grade | None:
    bundle = state.bundle()
    seed_key = _k(scope, p.id, "seed")
    if seed_key not in st.session_state:
        st.session_state[seed_key] = random.randrange(1_000_000)
    # A fresh frontend form identity prevents the browser retaining an old answer.
    instance_key = str(st.session_state.get(_k(scope, p.id, "revision"), 0))
    inst = generate(p, st.session_state[seed_key])
    res_key, rec_key = _k(scope, p.id, "grade"), _k(scope, p.id, "recorded")
    result: Grade | None = st.session_state.get(res_key)

    with st.container(border=True):
        concept = bundle.concepts[p.concept].title
        head = f"{LEVEL[p.level]} · {concept}" if show_concept else LEVEL[p.level]
        st.markdown(f'<p class="mst-kicker">{html.escape(head)}</p>', unsafe_allow_html=True)
        with st.container(key=f"box-problem-{scope}-{p.id}"):
            st.markdown(inst.text)

        if p.kind == "numeric":
            with st.form(_k(scope, p.id, "form") + instance_key, clear_on_submit=False, border=False):
                c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
                answer = c1.text_input("Your answer (with unit)", placeholder="e.g. 1.25 mV",
                                       key=_k(scope, p.id, "in") + instance_key)
                submitted = c2.form_submit_button("Check", type="primary", use_container_width=True)
            if submitted:
                result = grade(p, inst, answer, bundle)
        else:
            labels = {o.id: o.text for o in p.options}
            choice = st.radio("Your answer", [o.id for o in p.options], format_func=lambda i: labels[i],
                              index=None, key=_k(scope, p.id, "choice"), horizontal=p.kind == "direction")
            if st.button("Check", type="primary", key=_k(scope, p.id, "check"), disabled=choice is None):
                result = grade(p, inst, choice or "", bundle)

        if result is not None:
            st.session_state[res_key] = result
            if result.counts and not st.session_state.get(rec_key):
                st.session_state[rec_key] = True
                queued = state.service().record(
                    Attempt(datetime.now(), "problem", p.id, p.concept, p.skill, result.status == "correct",
                            mode=state.mode()),
                    success=result.status == "correct",
                )
                if queued:
                    names = ", ".join(bundle.concepts[c].title for c in queued if c in bundle.concepts)
                    st.session_state[_k(scope, p.id, "queued")] = names
            grade_feedback(result)
            if st.session_state.get(_k(scope, p.id, "queued")):
                st.caption("Added to today's review: " + st.session_state[_k(scope, p.id, "queued")])
            if result.counts:
                with st.expander("Worked solution", expanded=result.status != "correct"):
                    prose.show(render(p.solution, inst.params))
            if p.kind == "numeric" and result.counts:
                st.button("New numbers", key=_k(scope, p.id, "new"), icon=":material/casino:",
                          on_click=_new_instance, args=(scope, p.id))
            elif result.counts and result.status != "correct":
                st.caption("You can try another option — only the first attempt counts towards mastery.")
    return result


def _new_instance(scope: str, pid: str) -> None:
    revision_key = _k(scope, pid, "revision")
    old_revision = st.session_state.get(revision_key, 0)
    st.session_state.pop(_k(scope, pid, "in") + str(old_revision), None)
    st.session_state[revision_key] = old_revision + 1
    st.session_state[_k(scope, pid, "seed")] = random.randrange(1_000_000)
    for what in ("grade", "recorded", "in", "queued", "choice"):
        st.session_state.pop(_k(scope, pid, what), None)
