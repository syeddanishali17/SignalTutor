"""Foundation Playground (spec 16.3): the app's visual grammar on the simplest circuits.

Order matters for a learner with no circuit background:
loop (what flows) → voltage (difference) → Ohm (push / opposition) → divider →
ground → KCL → read a circuit. Every scene: predict → see → name → numbers.
"""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from tutor.sim import circuits
from tutor.sim.units import format_si
from tutor.ui import state
from tutor.ui.components import controls as C
from tutor.ui.components import equation, inspector, layout, plots
from tutor.ui.components.equation import q
from tutor.ui.components.feedback import failure_banner
from tutor.ui.pages import _lesson as L
from tutor.ui.svg import figures

LESSON_ID = "foundation_playground"
R_STEPS_K = [0.5, 1.0, 2.0, 4.0, 8.0]  # powers of two: "double R" is one step


def _kohm(v: float) -> str:
    return f"{v:g} kΩ"


def render() -> None:
    lesson = state.bundle().lessons[LESSON_ID]
    layout.page_header("Foundation Playground", "Voltage, current, resistance, ground",
                       "Seven short scenes, no circuit knowledge needed. The same picture language is used everywhere after this.")
    layout.sensor_map(lesson.map_stage, lesson.map_note)
    scenes = {s.id: s for s in lesson.scenes}
    deep = st.query_params.get("scene")
    if "pg_scene" not in st.session_state:
        st.session_state["pg_scene"] = deep if deep in scenes else lesson.scenes[0].id
    sid = st.segmented_control("Scene", list(scenes), format_func=lambda i: scenes[i].short, key="pg_scene",
                               required=True)
    scene = scenes[sid]
    st.markdown(f"## {scene.title}")
    inspector.term_chips(scene.concepts)
    {
        "loop": scene_loop,
        "voltage_difference": scene_voltage,
        "current_resistance": scene_ohm,
        "divider": scene_divider,
        "ground": scene_ground,
        "junction": scene_kcl,
        "read_circuit": scene_read,
    }[sid](lesson, scene)


# ---------------------------------------------------------------------------- 1 loop


def scene_loop(lesson, scene) -> None:
    scope = "pgL"
    defaults = {"V": 5.0, "closed": True}
    C.ensure_defaults(scope, defaults)
    unlocked = L.top(scope, lesson, scene)
    V, closed = C.value(scope, "V"), C.value(scope, "closed")
    R = 1e3
    I = circuits.ohm_current(V, R) if closed else 0.0
    res = L.resolved(scope, scene)
    svg = figures.ohm_loop(V, R, I, 12e-3, closed=closed, selected=res.highlight, meters=True)
    L.main_row(scope, scene, svg)

    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([3, 2, 1.3])
        with c1:
            C.slider(scope, "V", "Battery voltage V", 0.0, 12.0, 0.5, "%.1f V", disabled=not unlocked)
        with c2:
            C.toggle(scope, "closed", "Switch closed (loop complete)", disabled=not unlocked)
        with c3:
            C.reset_button(scope, defaults)

    reading = q(I, "A") if closed else r"0\,\text{A}"
    equation.strip(
        scope, scene,
        law=r"I_{A_1} = I_{A_2} = I_{A_3}",
        numbers=rf"= {reading} = {reading} = {reading}",
        result=r"\text{same everywhere}" if closed else r"\text{loop open: } I = 0",
        selectable=["I"],
        caption="Nothing is used up on the way round: the same charge per second passes every point of one loop.",
    )
    L.deeper(scope, lesson, scene)


# ---------------------------------------------------------------------------- 2 voltage


def scene_voltage(lesson, scene) -> None:
    scope = "pgA"
    defaults = {"phiA": 7.0, "phiB": 3.0, "ref": "C", "lift": False}
    C.ensure_defaults(scope, defaults)
    unlocked = L.top(scope, lesson, scene)
    phiA, phiB = C.value(scope, "phiA"), C.value(scope, "phiB")
    ref, lift = C.value(scope, "ref"), C.value(scope, "lift")
    shift = 2.0 if lift else 0.0
    pots = {"A": phiA + shift, "B": phiB + shift, "C": 0.0}
    res = L.resolved(scope, scene)
    svg = figures.potential_ladder(pots, ref, selected=res.highlight)
    L.main_row(scope, scene, svg)

    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2 = st.columns(2)
        with c1:
            C.slider(scope, "phiA", "φ_A — potential of node A (from C)", 0.0, 10.0, 0.5, "%.1f V", disabled=not unlocked)
            C.segmented(scope, "ref", "Which node do we call 0 V?", ["A", "B", "C"], disabled=not unlocked)
        with c2:
            C.slider(scope, "phiB", "φ_B — potential of node B (from C)", 0.0, 10.0, 0.5, "%.1f V", disabled=not unlocked)
            C.toggle(scope, "lift", "Lift A and B together by +2 V", disabled=not unlocked)
        C.reset_button(scope, defaults)

    rel = circuits.relabel_potentials(pots, ref)
    vab = pots["A"] - pots["B"]
    equation.strip(
        scope, scene,
        law=r"[[VAB]] = [[phiA]] - [[phiB]]",
        numbers=rf"= ({rel['A']:+.1f}\,\text{{V}}) - ({rel['B']:+.1f}\,\text{{V}})",
        result=rf"V_{{AB}} = {vab:+.1f}\,\text{{V}}",
        selectable=["phiA", "phiB", "VAB"],
        caption=f"Potentials are written relative to node {ref}. Change the reference: the bracket stays the same.",
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — the same two nodes, three different references")
        rows = []
        for r in ("A", "B", "C"):
            rl = circuits.relabel_potentials(pots, r)
            rows.append(f"| node {r} = 0 V | {rl['A']:+.1f} V | {rl['B']:+.1f} V | {rl['C']:+.1f} V | "
                        f"**{rl['A'] - rl['B']:+.1f} V** |")
        st.markdown("| reference | $\\varphi_A$ | $\\varphi_B$ | $\\varphi_C$ | $V_{AB}$ |\n|---|---|---|---|---|\n"
                    + "\n".join(rows))
        st.caption("Every label changes with the reference; the last column never does.")
    L.deeper(scope, lesson, scene)


# ---------------------------------------------------------------------------- 3 Ohm


def scene_ohm(lesson, scene) -> None:
    scope = "pgB"
    defaults = {"V": 6.0, "R": 2.0, "closed": True}
    C.ensure_defaults(scope, defaults)
    unlocked = L.top(scope, lesson, scene)
    V, Rk, closed = C.value(scope, "V"), C.value(scope, "R"), C.value(scope, "closed")
    R = Rk * 1e3
    I = circuits.ohm_current(V, R) if closed else 0.0
    i_max = 12.0 / (R_STEPS_K[0] * 1e3)
    res = L.resolved(scope, scene)
    svg = figures.ohm_loop(V, R, I, i_max, closed=closed, selected=res.highlight)
    L.main_row(scope, scene, svg)

    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([2, 2, 1.3])
        with c1:
            C.slider(scope, "V", "V — battery voltage (the push)", 0.0, 12.0, 0.5, "%.1f V", disabled=not unlocked)
        with c2:
            C.select_slider(scope, "R", "R — resistance (each step doubles it)", R_STEPS_K, _kohm, disabled=not unlocked)
        with c3:
            C.toggle(scope, "closed", "Switch closed", disabled=not unlocked)
            C.reset_button(scope, defaults)

    if closed:
        equation.strip(
            scope, scene,
            law=r"[[I]] = \frac{[[V]]}{[[R]]}",
            law_beginner=r"[[I]] = \frac{\overbrace{[[V]]}^{\text{numerator: the push}}}"
                         r"{\underbrace{[[R]]}_{\text{denominator: the opposition}}}",
            numbers=rf"I = \frac{{{q(V, 'V')}}}{{{q(R, 'ohm')}}}",
            result=rf"I = {q(I, 'A')}",
            selectable=["I", "V", "R"],
            caption="Bigger numerator → bigger current. Bigger denominator → smaller current.",
        )
    else:
        equation.strip(scope, scene, law=r"I = 0", numbers=r"\text{no closed path}", result=r"I = 0\,\text{A}")

    with st.container(key="consequence"):
        layout.kicker("Consequence — each resistor is a straight line on a current–voltage graph")
        fig = plots.figure("voltage across the resistor V (V)", "current I (mA)", (0, 12.5), (0, 25))
        for rk in R_STEPS_K:
            is_now = abs(rk - Rk) < 1e-9
            ys = [0, min(12 / rk, 25)]
            xs = [0, 12 if 12 / rk <= 25 else 25 * rk]
            plots.line(fig, xs, ys, f"{rk:g} kΩ", color=plots.COLORS["cur"] if is_now else "#c9c3b6",
                       width=3.4 if is_now else 1.4,
                       label_y_shift=8 if rk == 4 else -8 if rk == 8 else 0)
        if closed:
            plots.point(fig, V, I * 1e3, format_si(I, "A"), color=plots.COLORS["volt"])
        plots.show(fig, key="pgB_plot")
        st.caption("Steeper line = smaller R. Doubling R halves the steepness, so at the same V the current halves.")
    L.deeper(scope, lesson, scene)


# ---------------------------------------------------------------------------- 4 divider


def scene_divider(lesson, scene) -> None:
    scope = "pgC"
    defaults = {"Vin": 9.0, "R1": 1.0, "R2": 2.0, "load": False, "RL": 10.0}
    C.ensure_defaults(scope, defaults)
    unlocked = L.top(scope, lesson, scene)
    Vin, R1k, R2k = C.value(scope, "Vin"), C.value(scope, "R1"), C.value(scope, "R2")
    load, RLk = C.value(scope, "load"), C.value(scope, "RL")
    RL = RLk * 1e3 if load else math.inf
    res_c = circuits.divider(Vin, R1k * 1e3, R2k * 1e3, RL)
    ideal = circuits.divider(Vin, R1k * 1e3, R2k * 1e3)
    res = L.resolved(scope, scene)
    svg = figures.divider(Vin, res_c.R1, res_c.R2, res_c.Vout, res_c.I, I_max=12 / 1e3, selected=res.highlight,
                          R_load=RL if load else None)
    L.main_row(scope, scene, svg)

    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns(3)
        with c1:
            C.slider(scope, "Vin", "V_in — supply", 0.0, 12.0, 0.5, "%.1f V", disabled=not unlocked)
        with c2:
            C.slider(scope, "R1", "R₁ — top resistor", 0.5, 10.0, 0.5, "%.1f kΩ", disabled=not unlocked)
        with c3:
            C.slider(scope, "R2", "R₂ — bottom resistor (to ground)", 0.5, 10.0, 0.5, "%.1f kΩ", disabled=not unlocked)
        with st.expander("More controls — break it"):
            C.toggle(scope, "load", "Connect a meter (a 'load') to the output", disabled=not unlocked)
            C.select_slider(scope, "RL", "R_load — the meter's own input resistance",
                            [0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 1000.0], _kohm, disabled=not (unlocked and load))
        C.reset_button(scope, defaults)

    equation.strip(
        scope, scene,
        law=r"[[Vout]] = [[Vin]]\,\frac{[[R2]]}{[[total]]}",
        law_beginner=r"[[Vout]] = [[Vin]]\cdot\frac{\overbrace{[[R2]]}^{\text{the resistor we measure across}}}"
                     r"{\underbrace{[[total]]}_{\text{total resistance of the path}}}",
        numbers=rf"= {q(Vin, 'V')}\cdot\frac{{{R2k:g}\,\text{{k}}\Omega}}{{{R1k:g}\,\text{{k}}\Omega + {R2k:g}\,\text{{k}}\Omega}}",
        result=rf"V_\text{{out}} = {q(ideal.Vout, 'V')}" + (rf"\;\;(\text{{with meter: }} {q(res_c.Vout, 'V')})" if load else ""),
        selectable=["Vout", "Vin", "R1", "R2", "total"],
        caption="The fraction is a pure share between 0 and 1: 'own resistance over total resistance'."
        if not load else "With a meter connected the formula's 'nothing connected' assumption is broken — the picture shows the real, lower value.",
    )
    if load and RL < 10 * res_c.R2:
        failure_banner("Loading the divider", "The meter draws current and sits side by side (in parallel) with $R_2$.",
                       f"$R_\\text{{load}} = {RLk:g}\\,\\text{{k}}\\Omega$ is less than $10\\times R_2 = {10 * R2k:g}\\,\\text{{k}}\\Omega$.",
                       f"$V_\\text{{out}}$ drops from {ideal.Vout:.2f} V to {res_c.Vout:.2f} V "
                       f"({(res_c.Vout / ideal.Vout - 1) * 100:+.1f} %).",
                       "Measure with an input of much higher resistance.")
    with st.container(key="consequence"):
        layout.kicker("Consequence — V_out as R₂ changes (R₁ and V_in fixed)")
        fig = plots.figure("bottom resistor R₂ (kΩ)", "V_out (V)", (0, 10.5), (0, 12.5))
        r2 = np.linspace(0.05, 10, 200)
        plots.line(fig, r2, Vin * r2 / (R1k + r2), "formula (nothing connected)", color=plots.COLORS["ink"])
        if load:
            rp = r2 * RLk / (r2 + RLk)
            plots.line(fig, r2, Vin * rp / (R1k + rp), "with meter", color=plots.COLORS["plus"], dash="dash",
                       label_y_shift=-14)
        plots.point(fig, R2k, res_c.Vout, f"{res_c.Vout:.2f} V")
        fig.add_hline(y=Vin, line=dict(color="#b9b2a2", dash="dot"))
        fig.add_annotation(x=0.3, y=Vin, text="V_in", showarrow=False, yshift=9, font=dict(size=11, color="#6b7280"))
        plots.show(fig, key="pgC_plot")
    L.deeper(scope, lesson, scene)


# ---------------------------------------------------------------------------- 5 ground


def scene_ground(lesson, scene) -> None:
    scope = "pgD"
    defaults = {"Vin": 9.0, "ref": "bottom"}
    C.ensure_defaults(scope, defaults)
    unlocked = L.top(scope, lesson, scene)
    Vin, ref = C.value(scope, "Vin"), C.value(scope, "ref")
    res_c = circuits.divider(Vin, 1e3, 2e3)
    res = L.resolved(scope, scene)
    svg = figures.divider(Vin, res_c.R1, res_c.R2, res_c.Vout, res_c.I, I_max=12 / 3e3, selected=res.highlight,
                          reference=ref)
    L.main_row(scope, scene, svg)

    names = {"top": "top node", "mid": "middle (output) node", "bottom": "bottom node"}
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2 = st.columns([3, 2])
        with c1:
            C.segmented(scope, "ref", "Which node is ground (0 V)?", ["top", "mid", "bottom"], fmt=lambda n: names[n],
                        disabled=not unlocked)
        with c2:
            C.slider(scope, "Vin", "V_in — supply", 0.0, 12.0, 0.5, "%.1f V", disabled=not unlocked)
        C.reset_button(scope, defaults)

    pots = {"top": Vin, "mid": res_c.Vout, "bottom": 0.0}
    rel = circuits.relabel_potentials(pots, ref)
    equation.strip(
        scope, scene,
        law=r"\varphi_\text{node}^\text{new} = \varphi_\text{node}^\text{old} - [[ref]]",
        numbers=rf"\varphi_\text{{top}} = {Vin:.1f}\,\text{{V}} - {pots[ref]:.1f}\,\text{{V}}",
        result=rf"\varphi_\text{{top}} = {rel['top']:+.1f}\,\text{{V}}",
        selectable=["ref"],
        caption="Subtracting the same number from every node cannot change any difference.",
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — what changes, what doesn't")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Node potentials** (depend on the reference)")
            st.markdown("\n".join(f"- {names[n]}: **{rel[n]:+.2f} V**" for n in ("top", "mid", "bottom")))
        with c2:
            st.markdown("**Differences and current** (never change)")
            st.markdown(f"- across $R_1$: **{rel['top'] - rel['mid']:+.2f} V**\n"
                        f"- across $R_2$: **{rel['mid'] - rel['bottom']:+.2f} V**\n"
                        f"- current: **{format_si(res_c.I, 'A')}**")
    L.deeper(scope, lesson, scene)


# ---------------------------------------------------------------------------- 6 KCL


def scene_kcl(lesson, scene) -> None:
    scope = "pgE"
    defaults = {"Iin": 5.0, "I1": 2.0}
    C.ensure_defaults(scope, defaults)
    unlocked = L.top(scope, lesson, scene)
    Iin, I1 = C.value(scope, "Iin") * 1e-3, C.value(scope, "I1") * 1e-3
    I2 = circuits.kcl_remaining([Iin], [I1])
    res = L.resolved(scope, scene)
    svg = figures.kcl_junction(Iin, I1, I2, I_max=12e-3, selected=res.highlight)
    L.main_row(scope, scene, svg)

    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2 = st.columns(2)
        with c1:
            C.slider(scope, "Iin", "I_in — current into the node", 0.0, 10.0, 0.5, "%.1f mA", disabled=not unlocked)
        with c2:
            C.slider(scope, "I1", "I₁ — current out through branch 1", 0.0, 12.0, 0.5, "%.1f mA", disabled=not unlocked)
        C.reset_button(scope, defaults)

    equation.strip(
        scope, scene,
        law=r"[[I2]] = [[Iin]] - [[I1]]",
        numbers=rf"I_2 = {Iin * 1e3:.1f}\,\text{{mA}} - {I1 * 1e3:.1f}\,\text{{mA}}",
        result=rf"I_2 = {I2 * 1e3:+.1f}\,\text{{mA}}",
        selectable=["Iin", "I1", "I2"],
        caption="A negative $I_2$ means the current in branch 2 flows *into* the node — watch its arrow flip.",
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — total in vs total out (always equal)")
        into = Iin + max(0.0, -I2)
        out = I1 + max(0.0, I2)
        fig = plots.figure("", "current (mA)", (-0.5, 1.5), (0, 15), height=240)
        fig.add_trace(go.Bar(x=[0], y=[Iin * 1e3], marker_color=plots.COLORS["cur"], width=0.5, text=["I_in"],
                             textposition="inside"))
        if I2 < 0:
            fig.add_trace(go.Bar(x=[0], y=[-I2 * 1e3], marker_color="#7aa7d6", width=0.5, text=["I₂ (in)"],
                                 textposition="inside"))
        fig.add_trace(go.Bar(x=[1], y=[I1 * 1e3], marker_color=plots.COLORS["cur"], width=0.5, text=["I₁"],
                             textposition="inside", marker_pattern_shape="/"))
        if I2 > 0:
            fig.add_trace(go.Bar(x=[1], y=[I2 * 1e3], marker_color="#7aa7d6", width=0.5, text=["I₂"],
                                 textposition="inside", marker_pattern_shape="/"))
        fig.update_layout(barmode="stack")
        fig.update_xaxes(tickvals=[0, 1], ticktext=[f"into node: {into * 1e3:.1f} mA", f"out of node: {out * 1e3:.1f} mA"])
        plots.show(fig, key="pgE_plot")
    L.deeper(scope, lesson, scene)


# ---------------------------------------------------------------------------- 7 read


def scene_read(lesson, scene) -> None:
    scope = "pgF"
    L.top(scope, lesson, scene)
    res_c = circuits.divider(9.0, 1e3, 2e3)
    res = L.resolved(scope, scene)
    svg = figures.divider(9.0, res_c.R1, res_c.R2, res_c.Vout, res_c.I, I_max=12 / 3e3, selected=res.highlight,
                          show_levels=False)
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        layout.kicker("Your turn")
        st.markdown(
            "Cover the inspector and name, in order: **ground → source (+ side) → current path and direction → "
            "drop across each resistor → output terminal**. Then check yourself by clicking each part."
        )
    L.deeper(scope, lesson, scene)
