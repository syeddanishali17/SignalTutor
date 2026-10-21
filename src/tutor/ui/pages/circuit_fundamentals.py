"""Continuous-scroll handbook: no scene state, mastery, grading or storage."""

from __future__ import annotations

import html

import streamlit as st

from tutor.ui.components import diagram, layout, prose
from tutor.ui.pages.circuit_reference import SECTIONS, SUMMARY
from tutor.ui.svg.reference_figures import figure


def render() -> None:
    layout.page_header("Signal Tutor · circuit reference", "Basic Circuit Fundamentals",
                       "Circuit rules, equations, diagrams and worked examples in one place. Scroll or jump to a section.",
                       show_mode=False)
    st.markdown('<span id="handbook-top"></span>', unsafe_allow_html=True)
    links = [(s.anchor, s.title) for s in SECTIONS] + [("formula-summary", "Formula Summary")]
    st.markdown('<nav class="mst-reference-index" aria-label="Circuit fundamentals quick jumps">' +
                ''.join(f'<a href="#{a}" target="_self">{html.escape(t)}</a>' for a, t in links) + '</nav>',
                unsafe_allow_html=True)
    st.caption("Ideal lumped circuits unless stated otherwise. Next step marks supplemental material. "
               "Symbols are defined locally; read the assumptions before applying a shortcut. "
               "This reference does not record learner progress.")
    st.caption("Animated markers guide the eye along static curves; they do not represent electron speed.")
    with st.container(key="handbook"):
        for i, section in enumerate(SECTIONS):
            st.header(section.title, anchor=section.anchor)
            for entry in section.entries:
                st.subheader(entry.title)
                prose.show(entry.meaning)
                for eq in entry.equations:
                    st.latex(eq)
                if entry.where:
                    prose.show("**Where** · " + entry.where)
                if entry.figure == "chain":
                    layout.sensor_map(None)
                elif entry.figure:
                    diagram.show(figure(entry.figure), max_width=960)
                    if entry.figure == "divider":
                        st.caption("Vout is measured from the midpoint to ground; no load is attached.")
                if entry.note:
                    prose.show(entry.note)
                if entry.example:
                    with st.container(key=f"reference-example-{section.anchor}-{section.entries.index(entry)}"):
                        st.markdown("**Worked example**")
                        for label, equation in zip(("Given", "Use", "Substitute", "Result"), entry.example):
                            st.latex(r"\begin{aligned}\text{" + label + r"}\quad & " + equation + r"\end{aligned}")
            if (i + 1) % 3 == 0:
                st.markdown('[↑ Back to top](#handbook-top)')
        st.header("Formula Summary", anchor="formula-summary")
        for index, (title, equations) in enumerate(SUMMARY):
            # Summary names repeat section names; reserve jump IDs for sections.
            st.subheader(title, anchor=f"summary-{index}")
            for eq in equations:
                st.latex(eq)
        st.markdown('[↑ Back to top](#handbook-top)')
    with st.expander("Further reading & source-status notes"):
        st.markdown("Independently written reference and generated diagrams. Standard circuit relationships can be "
                    "checked against [OpenStax: DC circuits](https://openstax.org/books/university-physics-volume-2/pages/10-introduction), "
                    "[inductance](https://openstax.org/books/university-physics-volume-2/pages/14-introduction) and "
                    "[AC circuits](https://openstax.org/books/university-physics-volume-2/pages/15-introduction), and "
                    "[Analog Devices' amplifier tutorials](https://wiki.analog.com/university/courses/tutorials/index). "
                    "Project source issues K1–K10 remain open; see Sources & known issues. "
                    "Generic circuit identities here do not certify those source-specific forms.")
