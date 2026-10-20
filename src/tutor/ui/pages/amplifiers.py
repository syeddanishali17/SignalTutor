"""Amplifier Lab (C4, milestone M2).

Six guided steps: the bridge signal is a few mV of
*difference* on 2.5 V of *common mode* (plus mains pickup) → a bare op-amp
saturates → negative feedback → approach 1 (non-inverting, saturates on the
common mode) → approach 2 (difference amplifier: matching and loading) →
approach 3 (instrumentation amplifier).

Every figure value comes from the MNA solver (tutor.sim.network); the time
plots use the same solver (INA) or the closed forms that the tests check
against it (spec 19: no visual disagreement).
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from tutor.sim import amplifiers as amp
from tutor.sim.units import format_si
from tutor.ui import state
from tutor.ui.components import controls as C
from tutor.ui.components import equation, inspector, layout, plots
from tutor.ui.components.derivation import stepper
from tutor.ui.components.equation import q
from tutor.ui.components.feedback import break_it_banner
from tutor.ui.pages import _lesson as L
from tutor.ui.svg import amp_figures as F

LESSON_ID = "amplifier_lab"
RAIL = amp.RAIL
VCM = 2.5  # bridge midpoint level, V0/2 for a 5 V bridge
T_SNAP = 0.025  # s — signal (10 Hz) and pickup (50 Hz) both peak here; the picture shows this instant
A_CHOICES = [1e3, 1e4, 1e5, 1e6]
NI_GAINS = {2: 1e3, 11: 10e3, 101: 100e3}  # gain → R1 with R2 = 1 kΩ
NI_R2 = 1e3
DA_K = [1, 10, 100]
INA_R2 = 10e3
INA_R = 10e3
INA_R1 = [100e3, 20e3, 10e3, 5e3, 2e3, 1e3, 500.0, 200.0]

DEFAULTS = {
    "problem": {"vd": 2.0, "pick": 0.3, "show": "common"},
    "opamp": {"vd": 50, "A": 1e5},
    "feedback": {"vin": 0.5, "fb": "negative", "gain": 11, "A": 1e5},
    "noninv": {"src": "bridge", "gain": 101, "vtest": 50, "vd": 1.0},
    "diffamp": {"k": 100, "vd": 1.0, "mis": 0.0, "pick": 0.3},
    "ina": {"R1": 1e3, "vd": 5.0, "view": "diff", "probe": "stage1", "mis": 0.0, "pick": 0.3},
}


A_LABEL = {1e3: "1 000", 1e4: "10 000", 1e5: "100 000", 1e6: "1 000 000"}


def _A(a: float) -> str:
    return A_LABEL.get(a, f"{a:g}")


def _ohm(r: float) -> str:
    return format_si(r, "Ω", 3)


def _tex_num(x: float, sig: int = 3) -> str:
    """A plain number as LaTeX; very small or large values in scientific notation."""
    if x == 0 or 1e-3 <= abs(x) < 1e4:
        return f"{x:.{sig}g}"
    mant, exp = f"{x:.{sig - 1}e}".split("e")
    return rf"{mant}\times10^{{{int(exp)}}}"


def render() -> None:
    lesson = state.bundle().lessons[LESSON_ID]
    layout.page_header("Amplifier Lab", "Op-amps and the instrumentation amplifier",
                       "Why a bridge needs a special amplifier — three approaches, built and broken.")
    scenes = {s.id: s for s in lesson.scenes}
    deep = st.query_params.get("scene")
    if "amp_scene" not in st.session_state:
        st.session_state["amp_scene"] = deep if deep in scenes else lesson.scenes[0].id
    scene = scenes[st.session_state["amp_scene"]]
    layout.sensor_map(lesson.map_stage, lesson.map_note)
    sid = st.segmented_control("Step", list(scenes), format_func=lambda i: scenes[i].short, key="amp_scene",
                               required=True)
    scene = scenes[sid]
    st.markdown(f"## {scene.title}")
    inspector.term_chips(scene.concepts)
    {"problem": _problem, "opamp": _opamp, "feedback": _feedback, "noninv": _noninv, "diffamp": _diffamp,
     "ina": _ina}[sid](lesson, scene)


def _setup(scene) -> tuple[str, dict]:
    scope = f"amp_{scene.id}"
    defaults = DEFAULTS[scene.id]
    C.ensure_defaults(scope, defaults)
    return scope, defaults


def _derive_picker(scope: str, lesson, options: list[str]):
    def derive() -> None:
        bundle = state.bundle()
        key = f"{scope}__deriv"
        if st.session_state.get(key) not in options:
            st.session_state[key] = options[0]
        did = st.segmented_control("Derivation", options, key=key, required=True,
                                   format_func=lambda d: bundle.derivations[d].title) if len(options) > 1 else options[0]
        stepper(bundle.derivations[did], scope=scope)

    return derive


def _banner(lesson, bid: str) -> None:
    break_it_banner({b.id: b for b in lesson.break_it}[bid])


# ------------------------------------------------------------------------------- 0 · the problem


def _problem(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    vd = C.value(scope, "vd") * 1e-3
    pick = C.value(scope, "pick")
    show = C.value(scope, "show")
    v1 = VCM + pick - vd / 2
    v2 = VCM + pick + vd / 2
    res = L.resolved(scope, scene)
    L.main_row(scope, scene, F.interference(v1, v2, pick, selected=res.highlight, show=show))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2.4, 2.4, 2, 1])
        with c1:
            C.slider(scope, "vd", "V_d · bridge signal (peak)", 0.0, 5.0, 0.25, "%.2f mV", disabled=not unlocked)
        with c2:
            C.slider(scope, "pick", "v_pickup · mains pickup on each wire (peak)", 0.0, 1.0, 0.05, "%.2f V",
                     disabled=not unlocked)
        with c3:
            C.segmented(scope, "show", "Show", ["common", "diff"],
                        fmt=lambda s: "common mode" if s == "common" else "differential", disabled=not unlocked)
        with c4:
            C.reset_button(scope, defaults)
    equation.strip(
        scope, scene,
        law=(r"[[V2]] - [[V1]] = \left([[Vcm]] + \tfrac{[[Vd]]}{2} + [[pick]]\right)"
             r" - \left([[Vcm]] - \tfrac{[[Vd]]}{2} + [[pick]]\right) = [[Vd]]"),
        numbers=rf"= {v2:.5f}\,\text{{V}} - {v1:.5f}\,\text{{V}}",
        result=rf"V_2 - V_1 = {q(v2 - v1, 'V', 3)}",
        selectable=["V1", "V2", "Vcm", "Vd", "pick"],
        caption="Snapshot at t = 25 ms, where both the signal and the pickup peak (the dotted line in the plots). "
                "The pickup appears in both brackets and cancels.",
        stacked=True,
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — what the two wires carry over 100 ms")
        t = amp.time_axis(0.1, 600)
        w1, w2 = amp.bridge_like_inputs(t, VCM, vd, pick)
        c1, c2 = st.columns(2)
        with c1:
            fig = plots.figure("time (ms)", "each wire (V)", (0, 100), (VCM - 1.15, VCM + 1.15), height=260)
            plots.line(fig, t * 1e3, w2, "V₂", color=plots.COLORS["volt"], label_y_shift=8)
            plots.line(fig, t * 1e3, w1, "V₁", color=plots.COLORS["cur"], dash="dash", label_y_shift=-8)
            fig.add_vline(x=T_SNAP * 1e3, line=dict(color=plots.COLORS["muted"], dash="dot"))
            plots.show(fig, key="amp_problem_wires")
            st.caption("The two wires lie on top of each other: 2.5 V plus the 50 Hz pickup, the same on both.")
        with c2:
            fig = plots.figure("time (ms)", "V₂ − V₁ (mV)", (0, 100), (-5.5, 5.5), height=260)
            plots.line(fig, t * 1e3, (w2 - w1) * 1e3, "difference", color=plots.COLORS["plus"])
            fig.add_vline(x=T_SNAP * 1e3, line=dict(color=plots.COLORS["muted"], dash="dot"))
            plots.show(fig, key="amp_problem_diff")
            st.caption("Their difference is the clean 10 Hz bridge signal — no 2.5 V, no 50 Hz.")
        if pick > 0 and vd > 0:
            st.markdown(f"The pickup is **{pick / vd:,.0f} ×** bigger than the signal — and still harmless, *if* the "
                        "amplifier truly reads only the difference.")
    L.deeper(scope, lesson, scene)


# ------------------------------------------------------------------------------- 1 · open loop


def _opamp(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    vd = C.value(scope, "vd") * 1e-6
    A = C.value(scope, "A")
    v_minus = VCM
    v_plus = VCM + vd
    v_out = amp.open_loop(v_plus, v_minus, A, RAIL)
    res = L.resolved(scope, scene)
    L.main_row(scope, scene, F.opamp_open(v_plus, v_minus, v_out, RAIL, selected=res.highlight))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([3, 2.4, 1])
        with c1:
            C.slider(scope, "vd", "V₊ − V₋ · input difference", -500, 500, 10, "%d µV", disabled=not unlocked)
        with c2:
            C.select_slider(scope, "A", "A_d · open-loop gain", A_CHOICES, _A, disabled=not unlocked)
        with c3:
            C.reset_button(scope, defaults)
    sat = abs(A * vd) > RAIL
    equation.strip(
        scope, scene,
        law=r"[[Vout]] = [[Ad]]\,\left([[diff]]\right)\quad\text{(limited to } [[rail]]\text{)}",
        numbers=rf"= {_tex_num(A)}\times\left({vd * 1e6:g}\,\mu\text{{V}}\right) = {q(A * vd, 'V', 3)}",
        result=(rf"V_\text{{out}} = {q(v_out, 'V', 3)}" + (r"\ \text{(rail!)}" if sat else "")),
        selectable=["Vout", "Ad", "Vp", "Vm", "diff", "rail"],
        caption=f"Linear only while |V₊ − V₋| < V_s/A_d = {format_si(RAIL / A, 'V', 3)}. Outside that window "
                "the output sits at a rail.",
        stacked=True,
    )
    if sat:
        _banner(lesson, "open_loop_rail")
    with st.container(key="consequence"):
        layout.kicker("Consequence — output vs input difference (fixed axes)")
        x = np.linspace(-500, 500, 801)
        fig = plots.figure("input difference V₊ − V₋ (µV)", "V_out (V)", (-520, 520), (-17, 17))
        plots.line(fig, x, [amp.open_loop(k * 1e-6, 0.0, A, RAIL) for k in x], f"A_d = {_A(A)}",
                   color=plots.COLORS["ink"])
        for y in (RAIL, -RAIL):
            fig.add_hline(y=y, line=dict(color=plots.COLORS["minus"], dash="dash", width=1))
        fig.add_annotation(x=-500, y=RAIL, text="rail +V_s", showarrow=False, yshift=10, xanchor="left",
                           font=dict(size=11, color=plots.COLORS["minus"]))
        plots.point(fig, vd * 1e6, v_out, format_si(v_out, "V", 3))
        plots.show(fig, key="amp_opamp_plot")
        st.caption("Almost a vertical line: the op-amp is a comparator, not a measuring amplifier — until we add "
                   "feedback.")
    L.deeper(scope, lesson, scene)


# ------------------------------------------------------------------------------- 2 · feedback


def _feedback(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    vin, fb, G, A = (C.value(scope, k) for k in ("vin", "fb", "gain", "A"))
    R1, R2 = NI_GAINS[G], NI_R2
    beta = R2 / (R1 + R2)
    if fb == "negative":
        r = amp.non_inverting(vin, R1, R2, A, RAIL)
        v_out, v_fb, sat = r.v_out, r.v_minus, r.saturated
    else:
        v_out = amp.positive_feedback_output(vin, RAIL)
        v_fb, sat = beta * v_out, (1 if v_out > 0 else -1)
    res = L.resolved(scope, scene)
    L.main_row(scope, scene, F.noninv(vin, v_out, v_fb, R1, R2, selected=res.highlight, feedback=fb, sat=sat))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2.6, 2.2, 2.2, 1])
        with c1:
            C.slider(scope, "vin", "V_in · input voltage", -2.0, 2.0, 0.05, "%.2f V", disabled=not unlocked)
        with c2:
            C.segmented(scope, "fb", "Feed back to", ["negative", "positive"],
                        fmt=lambda s: "− input (negative)" if s == "negative" else "+ input (positive)",
                        disabled=not unlocked)
        with c3:
            C.segmented(scope, "gain", "R₁ · feedback resistor (R₂ = 1 kΩ)", list(NI_GAINS),
                        fmt=lambda g: _ohm(NI_GAINS[g]), disabled=not unlocked)
        with c4:
            C.reset_button(scope, defaults)
        with st.expander("More controls"):
            C.select_slider(scope, "A", "A_d · open-loop gain", A_CHOICES, _A, disabled=not unlocked,
                            help="A smaller A_d makes the virtual short less perfect: V₊ − V₋ = V_out / A_d.")
    if fb == "negative":
        diff = vin - v_fb
        equation.strip(
            scope, scene,
            law=(r"[[Vm]] = \frac{[[R2]]}{[[R1]] + [[R2]]}\,[[Vout]],\qquad"
                 r"[[diff]] = \frac{[[Vout]]}{[[Ad]]}"),
            numbers=(rf"V_- = {q(v_fb, 'V', 5)},\quad V_\text{{out}} = {q(v_out, 'V', 4)}"),
            result=(rf"V_+ - V_- = {q(diff, 'V', 3)}" if sat == 0 else r"\text{saturated — no virtual short}"),
            selectable=["Vout", "Vm", "Vp", "diff", "R1", "R2", "Ad"],
            caption=(f"The loop settles where the op-amp needs only {format_si(abs(diff), 'V', 2)} of input difference: "
                     "V₊ ≈ V₋, the **virtual short**. Closed-loop gain "
                     f"{amp.noninv_gain_finite(R1, R2, A):.4g} (ideal 1 + R₁/R₂ = {1 + R1 / R2:g})."),
            stacked=True,
        )
    else:
        equation.strip(
            scope, scene,
            law=r"[[Vout]] = [[Ad]]\,\left(\beta\,[[Vout]] - [[Vin]]\right)",
            numbers=r"\beta A_d \gg 1:\ \text{any error grows}",
            result=rf"V_\text{{out}} = {q(v_out, 'V', 3)}\ \text{{(rail)}}",
            selectable=["Vout", "Ad", "Vin"],
            caption="With the fed-back fraction on the + input, a tiny rise of the output raises V₊, which raises the "
                    "output further — it runs to a rail and stays there.",
            stacked=True,
        )
        _banner(lesson, "positive_feedback")
    with st.container(key="consequence"):
        layout.kicker("Consequence — output vs input (fixed axes)")
        x = np.linspace(-2, 2, 401)
        fig = plots.figure("V_in (V)", "V_out (V)", (-2.05, 2.05), (-17, 17))
        g = amp.noninv_gain_finite(R1, R2, A)
        plots.line(fig, x, [amp.clamp(g * k, RAIL) for k in x], f"negative feedback, gain {1 + R1 / R2:g}",
                   color=plots.COLORS["ink"], label_at=-1.0, label_y_shift=14)
        plots.line(fig, x, [amp.positive_feedback_output(k, RAIL) for k in x], "positive feedback",
                   color=plots.COLORS["minus"], dash="dash", label_at=-1.9, label_y_shift=-12)
        plots.point(fig, vin, v_out, format_si(v_out, "V", 3))
        plots.show(fig, key="amp_fb_plot")
        st.caption("Negative feedback: a straight line with slope 1 + R₁/R₂ — set by two resistors, not by the "
                   "op-amp. Positive feedback: only the two rails.")
    L.deeper(scope, lesson, scene, derive=_derive_picker(scope, lesson, ["non_inverting"]))


# ------------------------------------------------------------------------------- 3 · approach 1


def _noninv(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    src, G, vtest, vd = (C.value(scope, k) for k in ("src", "gain", "vtest", "vd"))
    R1, R2 = NI_GAINS[G], NI_R2
    vin = VCM + vd * 1e-3 / 2 if src == "bridge" else vtest * 1e-3
    r = amp.non_inverting(vin, R1, R2)
    res = L.resolved(scope, scene)
    L.main_row(scope, scene, F.noninv(vin, r.v_out, r.v_minus, R1, R2, selected=res.highlight, source=src,
                                      sat=r.saturated))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2.4, 2.2, 2.6, 1])
        with c1:
            C.segmented(scope, "src", "Input", ["bridge", "test"],
                        fmt=lambda s: "bridge node V₂" if s == "bridge" else "small test signal", disabled=not unlocked)
        with c2:
            C.segmented(scope, "gain", "Gain 1 + R₁/R₂", list(NI_GAINS), fmt=str, disabled=not unlocked)
        with c3:
            if src == "bridge":
                C.slider(scope, "vd", "V_d · strain signal of the bridge", 0.0, 5.0, 0.25, "%.2f mV",
                         disabled=not unlocked, help="The node sits at 2.5 V + V_d/2.")
            else:
                C.slider(scope, "vtest", "test signal amplitude", 0, 500, 10, "%d mV", disabled=not unlocked)
        with c4:
            C.reset_button(scope, defaults)
    ideal = (1 + R1 / R2) * vin
    equation.strip(
        scope, scene,
        law=r"[[Vout]] = \left([[gain]]\right)[[Vin]]",
        numbers=rf"= {1 + R1 / R2:g}\times {q(vin, 'V', 5)} = {q(ideal, 'V', 4)}",
        result=(rf"V_\text{{out}} = {q(r.v_out, 'V', 4)}" + (r"\ \text{(rail!)}" if r.saturated else "")),
        selectable=["Vout", "gain", "R1", "R2", "Vin", "Vm"],
        caption=(f"Saturated: the divider gives V₋ = V_out·R₂/(R₁ + R₂) = {format_si(r.v_minus, 'V', 4)}, far from "
                 f"V₊ = {format_si(vin, 'V', 4)} — the virtual short is gone because the loop cannot correct any more."
                 if r.saturated else
                 "Virtual short: V₋ = V_in, and the R₁–R₂ divider gives V₋ = V_out·R₂/(R₁ + R₂)."),
        stacked=True,
    )
    if r.saturated:
        _banner(lesson, "cm_saturation")
    with st.container(key="consequence"):
        layout.kicker("Consequence — input and output over 100 ms (output axis = the full rail range)")
        t = amp.time_axis(0.1, 400)
        if src == "bridge":
            _, w_in = amp.bridge_like_inputs(t, VCM, vd * 1e-3, 0.0)
        else:
            w_in = vtest * 1e-3 * np.sin(2 * np.pi * 10 * t)
        g = amp.noninv_gain_finite(R1, R2, amp.A_DEFAULT)
        w_out = np.clip(g * w_in, -RAIL, RAIL)
        fig = plots.figure("time (ms)", "voltage (V)", (0, 100), (-17, 17), height=280)
        plots.line(fig, t * 1e3, w_in, "V_in", color=plots.COLORS["volt"], dash="dash", label_y_shift=-10)
        plots.line(fig, t * 1e3, w_out, "V_out", color=plots.COLORS["ink"], label_y_shift=10)
        for y in (RAIL, -RAIL):
            fig.add_hline(y=y, line=dict(color=plots.COLORS["minus"], dash="dot", width=1))
        plots.show(fig, key="amp_ni_plot")
        if src == "bridge":
            st.caption(f"The output would need {format_si(ideal, 'V', 4)} — it is stuck at the rail, and the "
                       f"{vd:g} mV strain signal (a {format_si(g * vd * 1e-3, 'V', 3)} wiggle at most) is gone.")
        else:
            st.caption("A small signal around 0 V is amplified cleanly (until it reaches the rails).")
    L.deeper(scope, lesson, scene, derive=_derive_picker(scope, lesson, ["non_inverting"]))


# ------------------------------------------------------------------------------- 4 · approach 2


def _diffamp(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    k, vd, mis, pick = (C.value(scope, c) for c in ("k", "vd", "mis", "pick"))
    R = (1e3, k * 1e3, 1e3, k * 1e3 * (1 + mis / 100))
    v1 = VCM + pick - vd * 1e-3 / 2
    v2 = VCM + pick + vd * 1e-3 / 2
    r = amp.difference_amp(v1, v2, *R)
    a_d, a_cm = amp.diffamp_gains(*R)
    res = L.resolved(scope, scene)
    L.main_row(scope, scene, F.diffamp(v1, v2, r.v_out, R, selected=res.highlight, i1=r.i_in1, i2=r.i_in2,
                                       sat=r.saturated))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2.2, 2.4, 2.6, 1])
        with c1:
            C.segmented(scope, "k", "Gain R₂/R₁ = R₄/R₃", DA_K, fmt=str, disabled=not unlocked)
        with c2:
            C.slider(scope, "vd", "V_d · bridge signal (peak)", 0.0, 5.0, 0.25, "%.2f mV", disabled=not unlocked)
        with c3:
            C.slider(scope, "mis", "R₄ mismatch", -5.0, 5.0, 0.1, "%+.1f %%", disabled=not unlocked,
                     help="R₄ = (R₂/R₁)·R₃·(1 + mismatch). 0 % = perfectly matched.")
        with c4:
            C.reset_button(scope, defaults)
        with st.expander("More controls"):
            C.slider(scope, "pick", "v_pickup · mains pickup on both inputs (peak)", 0.0, 1.0, 0.05, "%.2f V",
                     disabled=not unlocked)
    numbers = (rf"= {v2:.5f}\cdot\frac{{{R[3]:.6g}}}{{{R[2]:.6g} + {R[3]:.6g}}}\left(1 + {k:g}\right)"
               rf" - {v1:.5f}\cdot {k:g}")
    equation.strip(
        scope, scene,
        law=(r"[[Vout]] = [[V2]]\,\frac{[[R4]]}{[[R3]] + [[R4]]}\left(1 + \frac{[[R2]]}{[[R1]]}\right)"
             r" - [[V1]]\,\frac{[[R2]]}{[[R1]]}"),
        law_beginner=(r"[[Vout]] = \underbrace{[[V2]]\,\frac{[[R4]]}{[[R3]] + [[R4]]}\left(1 + \frac{[[R2]]}{[[R1]]}\right)}"
                      r"_{\text{what } V_2 \text{ adds}} - \underbrace{[[V1]]\,\frac{[[R2]]}{[[R1]]}}_{\text{what } V_1 \text{ takes away}}"),
        numbers=numbers,
        result=(rf"\begin{{aligned}}&V_\text{{out}} = {q(r.v_out, 'V', 4)}\\&A_{{cm}} = {_tex_num(a_cm, 3)}\end{{aligned}}"),
        selectable=["Vout", "V1", "V2", "R1", "R2", "R3", "R4", "gain", "Acm"],
        caption=(r"Resistances in Ω, voltages in V, snapshot at t = 25 ms. Matched ($R_2/R_1 = R_4/R_3$): both "
                 r"coefficients equal $R_2/R_1$ and only $\frac{R_2}{R_1}(V_2 - V_1)$ survives. "
                 + (f"CMRR = {amp.cmrr_db(a_d, a_cm):.0f} dB." if a_cm else "CMRR = ∞ (ideal match).")),
        stacked=True,
    )
    if abs(mis) >= 0.1:
        _banner(lesson, "mismatch")
    with st.container(key="consequence"):
        layout.kicker("Consequence — output over 100 ms: wanted signal vs what leaks through (fixed axes)")
        t = amp.time_axis(0.1, 600)
        w1, w2 = amp.bridge_like_inputs(t, VCM, vd * 1e-3, pick)
        out = np.clip(np.array([amp.diffamp_ideal(a, b, *R) for a, b in zip(w1, w2)]), -RAIL, RAIL)
        wanted = k * (w2 - w1)
        fig = plots.figure("time (ms)", "V_out (mV)", (0, 100), (-700, 700), height=280)
        plots.line(fig, t * 1e3, wanted * 1e3, "wanted: (R₂/R₁)·V_d", color=plots.COLORS["plus"], dash="dash",
                   label_y_shift=-10)
        plots.line(fig, t * 1e3, out * 1e3, "actual output", color=plots.COLORS["ink"], label_y_shift=10)
        fig.add_vline(x=T_SNAP * 1e3, line=dict(color=plots.COLORS["muted"], dash="dot"))
        plots.show(fig, key="amp_da_plot")
        c1, c2, c3 = st.columns(3)
        c1.metric("Common mode leaking out", format_si(a_cm * (VCM + pick), "V", 3),
                  help="A_cm × (2.5 V + pickup) at the snapshot.")
        c2.metric("Current drawn from V₁", format_si(r.i_in1, "A", 3),
                  help="The op-amp draws nothing — this flows through R₁. A real bridge would be loaded by it.")
        c3.metric("Current drawn from V₂", format_si(r.i_in2, "A", 3), help="Flows through R₃ and R₄.")
        st.caption("Matched: the two curves coincide. Mistune R₄ by 1 % and 2.5 V × A_cm shifts and wobbles the "
                   "output by about as much as the signal. And the input currents load the bridge (Break it tab).")
    L.deeper(scope, lesson, scene, derive=_derive_picker(scope, lesson, ["difference_amp"]))


# ------------------------------------------------------------------------------- 5 · instrumentation amplifier


@st.cache_data(show_spinner=False, max_entries=64)
def _ina_traces(R1: float, vd: float, pick: float, mis: float, n: int = 160) -> dict[str, np.ndarray]:
    """Run the full MNA solve at every time sample (saturation included)."""
    t = amp.time_axis(0.1, n)
    w1, w2 = amp.bridge_like_inputs(t, VCM, vd, pick)
    rs = [amp.instrumentation_amp(a, b, R1, INA_R2, INA_R, mis) for a, b in zip(w1, w2)]
    return {"t": t, "in1": w1, "in2": w2, "o1": np.array([r.v_o1 for r in rs]), "o2": np.array([r.v_o2 for r in rs]),
            "out": np.array([r.v_out for r in rs])}


def _ina(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    R1, vd_mV, view, probe, mis, pick = (C.value(scope, c) for c in ("R1", "vd", "view", "probe", "mis", "pick"))
    vd = vd_mV * 1e-3 if view == "diff" else 0.0
    v1 = VCM + pick - vd / 2
    v2 = VCM + pick + vd / 2
    mis_f = mis / 100
    r = amp.instrumentation_amp(v1, v2, R1, INA_R2, INA_R, mis_f)
    G = amp.ina_gain_ideal(R1, INA_R2)
    sel = L.resolved(scope, scene)
    i_max = 5e-3 / min(INA_R1)  # the largest current any setting produces → full arrow speed
    L.main_row(scope, scene, F.ina(r, R1, INA_R2, INA_R, selected=sel.highlight, view=view, probe=probe,
                                   mismatch=mis_f, i_max=i_max), ratio=(7, 3))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2.8, 2.2, 2.4, 1])
        with c1:
            C.select_slider(scope, "R1", "R₁ · gain resistor", INA_R1,
                            lambda v: f"{_ohm(v)} → gain {amp.ina_gain_ideal(v, INA_R2):g}", disabled=not unlocked)
        with c2:
            C.segmented(scope, "view", "Input", ["common", "diff"],
                        fmt=lambda s: "pure common mode" if s == "common" else "+ strain signal", disabled=not unlocked)
        with c3:
            C.segmented(scope, "probe", "Probe", ["in", "stage1", "out"],
                        fmt={"in": "inputs", "stage1": "after stage 1", "out": "output"}.get, disabled=not unlocked)
        with c4:
            C.reset_button(scope, defaults)
        with st.expander("More controls"):
            m1, m2, m3 = st.columns(3)
            with m1:
                C.slider(scope, "vd", "V_d · bridge signal (peak)", 0.0, 5.0, 0.25, "%.2f mV", disabled=not unlocked)
            with m2:
                C.slider(scope, "pick", "v_pickup · mains pickup (peak)", 0.0, 1.0, 0.05, "%.2f V", disabled=not unlocked)
            with m3:
                C.slider(scope, "mis", "Stage-2 resistor mismatch", -5.0, 5.0, 0.1, "%+.1f %%", disabled=not unlocked)
    equation.strip(
        scope, scene,
        law=r"[[Vout]] = [[Vo2]] - [[Vo1]] = \left([[gain]]\right)\left([[V2]] - [[V1]]\right)",
        law_beginner=(r"[[Vout]] = [[Vo2]] - [[Vo1]] = \underbrace{\left([[gain]]\right)}_{\text{set by } R_1 \text{ alone}}"
                      r"\underbrace{\left([[V2]] - [[V1]]\right)}_{\text{bridge signal}}"),
        numbers=(rf"= \left(1 + \frac{{2\times{INA_R2 / 1e3:g}\,\text{{k}}\Omega}}{{{q(R1, 'Ω', 3)}}}\right)"
                 rf"\times {q(vd, 'V', 3)}"),
        result=(rf"\begin{{aligned}}&V_{{o1}} = {q(r.v_o1, 'V', 4)}\\&V_{{o2}} = {q(r.v_o2, 'V', 4)}\\"
                rf"&V_\text{{out}} = {q(r.v_out, 'V', 4)}\end{{aligned}}"),
        selectable=["Vout", "Vo1", "Vo2", "gain", "R1", "R2", "V1", "V2", "VA", "VB", "I"],
        caption=(f"Snapshot at t = 25 ms. Current through R₁ and both R₂: {format_si(r.i_R1, 'A', 3)}. "
                 f"Ideal gain {G:g}; simulated V_out/V_d = {r.v_out / vd:.4g}." if vd else
                 "Pure common mode: no current in R₁, so the stage-1 outputs equal the inputs and stage 2 cancels them."),
        stacked=True,
    )
    if r.saturated.get("U1") or r.saturated.get("U2"):
        _banner(lesson, "stage1_rail")
    if abs(mis) >= 0.1:
        _banner(lesson, "mismatch")
    with st.container(key="consequence"):
        label = {"in": "at the inputs", "stage1": "after stage 1", "out": "at the output"}[probe]
        layout.kicker(f"Consequence — the probe {label}, over 100 ms")
        tr = _ina_traces(R1, vd, pick, mis_f)
        tms = tr["t"] * 1e3
        if probe == "out":  # V_out has no "two wires": its common part is whatever is not the wanted signal
            diff = tr["out"]
            common = tr["out"] - G * (tr["in2"] - tr["in1"])
            n_c, n_d = "common part left in V_out", "V_out"
        else:
            a, b = ("in1", "in2") if probe == "in" else ("o1", "o2")
            diff = tr[b] - tr[a]
            common = (tr[a] + tr[b]) / 2
            n_c, n_d = ("(V₁ + V₂)/2", "V₂ − V₁") if probe == "in" else ("(V_o1 + V_o2)/2", "V_o2 − V_o1")
        c1, c2 = st.columns(2)
        with c1:
            fig = plots.figure("time (ms)", "common part (V)", (0, 100), (-0.6, 4.6), height=250)
            plots.line(fig, tms, common, n_c, color=plots.COLORS["volt"], label_at=2, label_y_shift=16)
            fig.add_vline(x=T_SNAP * 1e3, line=dict(color=plots.COLORS["muted"], dash="dot"))
            plots.show(fig, key="amp_ina_cm")
        with c2:
            fig = plots.figure("time (ms)", "difference (mV)", (0, 100), (-560, 560), height=250)
            plots.line(fig, tms, diff * 1e3, n_d, color=plots.COLORS["plus"], label_at=2, label_y_shift=16)
            fig.add_vline(x=T_SNAP * 1e3, line=dict(color=plots.COLORS["muted"], dash="dot"))
            plots.show(fig, key="amp_ina_diff")
        m1, m2, m3 = st.columns(3)
        m1.metric("Common part (average)", format_si(float(np.mean(common)), "V", 3))
        m2.metric("50 Hz pickup in it (peak)", format_si(float(np.ptp(common)) / 2, "V", 2))
        m3.metric("Difference (peak)", format_si(float(np.max(np.abs(diff))), "V", 3))
        st.caption({
            "in": "Inputs: 2.5 V plus 50 Hz pickup, shared by both wires; the bridge signal is only a few mV — "
                  "a flat line on this scale.",
            "stage1": "After stage 1: the common part is untouched (gain 1) — same 2.5 V, same 50 Hz. The difference "
                      f"has grown {G:g}×.",
            "out": "Output: the common part is gone (stage 2); only the amplified 10 Hz bridge signal is left.",
        }[probe] + " Same axes for every probe position.")
        layout.kicker("The three approaches side by side")
        st.markdown(
            "| | rejects common mode | loads the bridge | gain set by |\n"
            "|---|---|---|---|\n"
            "| 1 · non-inverting | **no** — saturates | no (+ input) | $R_1/R_2$ |\n"
            "| 2 · difference amp | only if $R_2/R_1 = R_4/R_3$ exactly | **yes** (input resistors) | two resistors together |\n"
            "| 3 · instrumentation amp | yes (stage 2) | no (+ inputs only) | **one** resistor $R_1$ |"
        )
    L.deeper(scope, lesson, scene, derive=_derive_picker(scope, lesson, ["ina_common_mode", "ina_differential"]))
