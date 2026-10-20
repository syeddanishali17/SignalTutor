"""Dev gallery (spec 16.6): every visual primitive in isolation, in several states.

Hidden from learner navigation unless TUTOR_DEV=1.
"""

from __future__ import annotations


import streamlit as st

from tutor.sim import bridge, circuits
from tutor.ui.components import layout
from tutor.ui.components.feedback import failure_banner
from tutor.ui.svg import figures
from tutor.ui.svg.core import as_img


def _show(title: str, svg: str) -> None:
    st.markdown(f"**{title}**")
    st.html(as_img(svg, max_width=640))


def render() -> None:
    layout.page_header("Development", "Dev gallery", "Visual primitives in isolation. Not part of learner navigation.",
                       show_mode=False)
    layout.sensor_map("electrical_transducer", "sensor_system_map component")
    c1, c2 = st.columns(2)
    with c1:
        _show("Bridge · quarter · R1 selected", figures.bridge(bridge.simulate("quarter", 5, 350, 0.01), "quarter", selected="R1"))
        _show("Bridge · full · diamond · meter selected",
              figures.bridge(bridge.simulate("full", 5, 350, 0.01), "full", layout="diamond", selected="meter"))
        _show("Bridge · loaded meter (R_in = 3R)", figures.bridge(bridge.simulate("quarter", 5, 350, 0.05, R_meter=1050), "quarter"))
        _show("Bridge · symbolic (derivation figure)", figures.FIGURES["bridge_quarter"](["R1", "R4", "I2"]))
    with c2:
        d = circuits.divider(9, 1e3, 2e3)
        _show("Divider · ground at mid · R2 selected",
              figures.divider(9, 1e3, 2e3, d.Vout, d.I, I_max=3e-3, selected="R2", reference="mid"))
        dl = circuits.divider(9, 1e3, 2e3, 1e3)
        _show("Divider · loaded", figures.divider(9, 1e3, 2e3, dl.Vout, dl.I, I_max=6e-3, R_load=1e3))
        _show("Ohm loop · switch open", figures.ohm_loop(5, 1e3, 0, 1e-2, closed=False))
        _show("KCL · negative branch", figures.kcl_junction(5e-3, 7e-3, -2e-3, 1e-2, selected="I2"))
        _show("Potential ladder · ref = A", figures.potential_ladder({"A": 7, "B": 3, "C": 0}, "A", selected="meter"))
    failure_banner("Example failure banner", "cause text", "condition text", "consequence text", "recovery text")
    st.markdown(" ".join(layout.badge_html(s, "compute") for s in ("not_started", "shaky", "solid", "exam_ready")),
                unsafe_allow_html=True)
