"""Source integrity (spec 11): formula registry with checks and the known-issues register."""

from __future__ import annotations

import html

import streamlit as st

from tutor.engine import dims
from tutor.ui import state
from tutor.ui.components import layout
from tutor.ui.components.equation import formula_card


def render() -> None:
    layout.page_header("Reference", "Sources & known issues",
                       "Never silently corrected: every doubtful written form is listed here with the reason.")
    bundle = state.bundle()
    tab = st.segmented_control("View", ["Known issues", "Formula registry"], key="src_tab", required=True,
                               default="Known issues")
    if tab == "Known issues":
        st.caption("Status stays open until the written form and the proposed form have been checked by hand.")
        sev_order = {"high": 0, "medium": 1, "low": 2}
        for k in sorted(bundle.known_issues.values(), key=lambda k: (sev_order[k.severity], k.id)):
            with st.container(border=True):
                st.markdown(
                    f'<span class="mst-chip needs_review">{k.severity}</span><b>{k.id}</b> · {html.escape(k.location)}'
                    f' <span class="mst-muted">· {k.status}</span>', unsafe_allow_html=True)
                st.caption("As written")
                st.latex(k.lecture_form)
                st.caption("Proposed")
                st.latex(k.proposed_form)
                st.markdown(f"**Why:** {k.reason}")
                st.caption(f"Found by: {k.found_by}" + (f" · formulas: {', '.join(k.formulas)}" if k.formulas else ""))
    else:
        st.caption("Dimension checks run on the machine form with the app's own parser (no eval).")
        for f in bundle.formulas.values():
            with st.container(border=True):
                formula_card(f, show_meaning=False)
                checks = []
                for label, chk in (("written form", f.lecture_check), ("canonical form", f.canonical_check)):
                    if chk is None:
                        continue
                    ok, msg = dims.check(chk.expr, chk.symbols, chk.result_unit)
                    checks.append(f"{'✓' if ok else '✗'} {label}: {msg}")
                if checks:
                    st.caption(" · ".join(checks))
