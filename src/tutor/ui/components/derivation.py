"""Derivation stepper (spec 16.7): one whiteboard step at a time.

Each step shows what changed, why it is allowed, which law it uses and which
assumption is active, next to the figure with the relevant parts highlighted.
Styles: worked (beginner) → faded (course; pick the missing line) → hidden
(exam; reveal only after deriving on paper).
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from tutor.engine.mastery import Attempt
from tutor.models.content import Derivation
from tutor.ui import state
from tutor.ui.components import prose
from tutor.ui.svg.core import as_img
from tutor.ui.svg.figures import FIGURES

STYLES = {"worked": "Worked", "faded": "Faded", "hidden": "Hidden (exam)"}
DEFAULT_STYLE = {"beginner": "worked", "course": "faded", "exam": "hidden"}


def _k(d: Derivation, scope: str, what: str) -> str:
    return f"der__{scope}__{d.id}__{what}"


def stepper(d: Derivation, scope: str) -> None:
    style_key = _k(d, scope, "style")
    st.session_state.setdefault(style_key, DEFAULT_STYLE[state.mode()])
    top_l, top_r = st.columns([3, 2], vertical_alignment="bottom")
    with top_l:
        st.markdown(f"### {d.title}")
        st.caption(f"Source: {d.source}")
    with top_r:
        style = st.segmented_control("Derivation style", list(STYLES), format_func=lambda s: STYLES[s],
                                     key=style_key, required=True)
    if style == "hidden" and not st.session_state.get(_k(d, scope, "revealed")):
        st.info("Derive it on paper first. Reveal the steps only when you are done.", icon=":material/edit_note:")
        if st.button("Reveal the derivation", key=_k(d, scope, "reveal")):
            st.session_state[_k(d, scope, "revealed")] = True
            st.rerun()
        return

    n = len(d.steps)
    idx_key = _k(d, scope, "i")
    st.session_state.setdefault(idx_key, 0)
    i = max(0, min(st.session_state[idx_key], n - 1))
    step = d.steps[i]
    solved: dict[str, bool] = st.session_state.setdefault(_k(d, scope, "solved"), {})
    first_try: dict[str, bool] = st.session_state.setdefault(_k(d, scope, "first"), {})
    faded_here = style == "faded" and step.fade is not None and not solved.get(step.id)

    st.markdown(f'<p class="mst-kicker">Step {i + 1} of {n} · {d.title}</p>', unsafe_allow_html=True)
    st.progress((i + 1) / n)
    beginner = state.mode() == "beginner"
    left, right = st.columns([1, 1], gap="medium")
    with left:
        st.html(as_img(FIGURES[d.figure](step.highlight)))
        if step.highlight:
            st.caption("Lit up in the circuit: " + ", ".join(_pretty(h) for h in step.highlight))
    with right:
        with st.container(key=f"derivstep-{scope}-{d.id}"):
            # earlier lines faded, current line emphasised: building up a whiteboard
            for prev in d.steps[max(0, i - 2) : i]:
                if style == "faded" and prev.fade and not solved.get(prev.id):
                    continue
                st.latex(r"\color{#9aa1ac}{" + prev.latex + "}")
            if faded_here:
                assert step.fade is not None
                st.markdown(f"**Your turn:** {step.fade.prompt}")
                opts = list(range(len(step.fade.options)))
                pick = st.radio("Pick the next line", opts, index=None, key=_k(d, scope, f"pick_{step.id}"),
                                format_func=lambda j: r"$\displaystyle " + step.fade.options[j].latex + "$",
                                label_visibility="collapsed")
                if st.button("Check step", type="primary", key=_k(d, scope, f"chk_{step.id}"), disabled=pick is None):
                    ok = pick == step.fade.correct
                    first_try.setdefault(step.id, ok)
                    if ok:
                        solved[step.id] = True
                        _maybe_record(d, scope, style)
                        st.rerun()
                    else:
                        st.error("Not this one. Look at what is lit up in the circuit, and the hint below.",
                                 icon=":material/cancel:")
                st.caption(f"Hint: {step.why}")
            else:
                st.latex(step.annotated if (beginner and step.annotated) else step.latex)
        if not faded_here:
            st.markdown("**What changed:**")
            prose.show(step.changed)
            st.markdown("**Why it is allowed:**")
            prose.show(step.why)
            if step.law:
                st.markdown(f'<span class="mst-chip">law</span> {step.law}', unsafe_allow_html=True)
            if step.assumption:
                st.markdown(f'<span class="mst-chip needs_review">assumption</span> {step.assumption}',
                            unsafe_allow_html=True)
            else:
                st.caption("Assumption used: none new in this step.")

    b1, b2, b3 = st.columns([1, 1, 3])
    b1.button("◀ Back", key=_k(d, scope, "back"), disabled=i == 0, on_click=_go, args=(idx_key, i - 1),
              use_container_width=True)
    b2.button("Next ▶", key=_k(d, scope, "next"), disabled=i == n - 1 or faded_here, on_click=_go,
              args=(idx_key, i + 1), type="primary", use_container_width=True)
    if style == "faded":
        faded_ids = [s.id for s in d.steps if s.fade]
        done = sum(1 for s in faded_ids if solved.get(s))
        b3.caption(f"Faded steps solved: {done} of {len(faded_ids)}"
                   + (" — recorded towards the *derive* skill." if st.session_state.get(_k(d, scope, "recorded")) else ""))


_PRETTY = {"meter": "the meter", "I1": "$I_1$", "I2": "$I_2$", "V0": "$V_0$", "V1": "$V_1$", "V2": "$V_2$"}


def _pretty(h: str) -> str:
    if h in _PRETTY:
        return _PRETTY[h]
    if len(h) == 2 and h[0] in "RVI" and h[1].isdigit():
        return f"${h[0]}_{h[1]}$"
    return h


def _go(key: str, i: int) -> None:
    st.session_state[key] = i


def _maybe_record(d: Derivation, scope: str, style: str) -> None:
    if style != "faded" or st.session_state.get(_k(d, scope, "recorded")):
        return
    solved = st.session_state[_k(d, scope, "solved")]
    faded = [s.id for s in d.steps if s.fade]
    if all(solved.get(s) for s in faded):
        first = st.session_state[_k(d, scope, "first")]
        correct = all(first.get(s, False) for s in faded)
        st.session_state[_k(d, scope, "recorded")] = True
        state.service().record(
            Attempt(datetime.now(), "derivation", d.id, d.concept, "derive", correct, mode=state.mode()),
            success=correct,
        )
