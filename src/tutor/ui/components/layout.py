"""Page chrome: header with mode switch, sensor-system map, problem line, styled boxes.

Rendering policy: every learner-facing content string is Markdown that may
contain ``$LaTeX$``. It is rendered with ``st.markdown`` inside a keyed
container (styled by CSS through the ``st-key-…`` class), never interpolated
into raw HTML, so maths is always properly typeset.
"""

from __future__ import annotations

import html
import itertools

import streamlit as st

from tutor import branding
from tutor.engine.mastery import RULES, STATE_LABEL
from tutor.ui import state
from tutor.ui.components import prose

MAP_STAGES = [
    ("stimulus", "stimulus"),
    ("primary_transducer", "primary transducer"),
    ("electrical_transducer", "electrical transducer"),
    ("signal_conditioning", "signal conditioning"),
    ("adc", "ADC"),
    ("processing", "processing"),
    ("communication", "communication"),
]
_box_counter = itertools.count()


def page_header(kicker_text: str, title: str, subtitle: str | None = None, show_mode: bool = True) -> None:
    left, right = st.columns([5, 2], vertical_alignment="bottom")
    with left:
        st.markdown(f'<p class="mst-kicker">{html.escape(kicker_text)}</p>', unsafe_allow_html=True)
        st.markdown(f"# {title}")
        if subtitle:
            st.markdown(f'<p class="mst-muted">{subtitle}</p>', unsafe_allow_html=True)
    if show_mode:
        with right:
            mode_switch()


def mode_switch() -> None:
    current = state.mode()
    choice = st.segmented_control(
        "Teaching mode",
        options=list(state.MODE_LABELS),
        format_func=lambda m: state.MODE_LABELS[m],
        default=current,
        key="mode_switch",
        help="Beginner: plain words, labelled fractions, worked derivations, predictions. "
        "Course: lecture notation, faded derivations. "
        "Exam: scaffolding removed, derivations hidden until you reveal them.",
    )
    if choice and choice != current:
        state.set_mode(choice)
        st.rerun()


def sensor_map(stage: str | None, note: str | None = None) -> None:
    """stimulus → … → communication, current block highlighted (spec 7)."""
    parts = []
    passed = False
    for i, (key, label) in enumerate(MAP_STAGES):
        if key == stage:
            kind, marker, passed = " on", "▶ ", True
        elif passed:
            kind, marker = " later", ""
        else:
            kind, marker = "", ""
        parts.append(f'<span class="blk{kind}">{marker}{html.escape(label)}</span>')
        if i < len(MAP_STAGES) - 1:
            parts.append('<span class="arr">→</span>')
    if note:
        parts.append(f'<span class="note">You are here: <b>{html.escape(note)}</b></span>')
    st.markdown(f'<div class="mst-map" role="navigation" aria-label="Sensor system map">{"".join(parts)}</div>',
                unsafe_allow_html=True)


def kicker(text: str) -> None:
    st.markdown(f'<p class="mst-kicker">{html.escape(text)}</p>', unsafe_allow_html=True)


def problem_line(text_md: str, label: str = "The problem") -> None:
    kicker(label)
    with st.container(key=f"box-problem-{next(_box_counter)}"):
        st.markdown(text_md)


def box(kind: str, body_md: str, title: str | None = None) -> None:
    """Styled box with Markdown + LaTeX inside. kinds: hit, miss, flag, fail, analogy, note, plain."""
    with st.container(key=f"box-{kind}-{next(_box_counter)}"):
        if title:
            st.markdown(f'<p class="mst-boxtitle">{html.escape(title)}</p>', unsafe_allow_html=True)
        prose.show(body_md)


def analogy(text_md: str) -> None:
    box("analogy", text_md, title="Analogy — a picture, not the physics")


def flag(text_md: str) -> None:
    box("flag", "⚠ " + text_md)


def badge_html(skill_state: str, skill: str | None = None) -> str:
    label = STATE_LABEL.get(skill_state, skill_state)
    title = ""
    if skill and skill_state in ("solid", "exam_ready"):
        title = RULES[skill][skill_state]
    elif skill:
        title = "Next: " + RULES[skill]["solid"]
    prefix = f"{skill}: " if skill else ""
    return f'<span class="mst-badge {skill_state}" title="{html.escape(title)}">{html.escape(prefix + label)}</span>'


def footer() -> None:
    """Global app footer with the creator signature (shortened on narrow screens). Rendered after the page body."""
    st.markdown(f'<div class="mst-sign" role="contentinfo"><span class="long">{html.escape(branding.SIGNATURE)}</span>'
                f'<span class="short">{html.escape(branding.SIGNATURE_SHORT)}</span></div>', unsafe_allow_html=True)


def signature_inline(short: bool = False) -> None:
    """The signature as a quiet line inside a page (home/about)."""
    st.markdown(f'<p class="mst-sign-inline">{html.escape(branding.signature(short))}</p>', unsafe_allow_html=True)


def reset_box_counter() -> None:
    """Keep box keys stable across reruns (called once per script run)."""
    global _box_counter
    _box_counter = itertools.count()
