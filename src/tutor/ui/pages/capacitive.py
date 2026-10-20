"""Capacitive Sensor Lab (C4–C7, milestone M3).

Six guided steps: membrane mechanics → capacitance → C(x) → current (barometer vs
microphone) → small-signal and harmonics → pull-in. Every step draws the same physical
capacitor; figure, equation strip, readouts and plots come from ONE simulation result
(tutor.sim.capacitive).
"""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from tutor.sim import capacitive as cap
from tutor.sim.units import format_si
from tutor.ui import state
from tutor.ui.components import controls as C
from tutor.ui.components import equation, inspector, layout, plots
from tutor.ui.components.derivation import stepper
from tutor.ui.components.equation import q
from tutor.ui.components.feedback import break_it_banner
from tutor.ui.pages import _lesson as L
from tutor.ui.svg import cap_figures as F
from tutor.ui.svg.core import as_img

LESSON_ID = "capacitive_lab"
G = cap.DEFAULT  # 1 mm², d = 2 µm, 2 × 2.5 kN/m
GREY = "#a8a294"  # colour of a neglected equation term (spec 16.10)
K_CHOICES = [2500.0, 5000.0, 10000.0]
F_CHOICES = [1.0, 10.0, 50.0]  # barometer bias frequency, kHz
V_PI = cap.pullin_voltage(G)

DEFAULTS = {
    "membrane": {"p": 1.0, "k": 2500.0},
    "capacitance": {"g": 2.0, "A": 1.0, "V": 5.0},
    "cx": {"p": 2.5, "tangent": True},
    "current": {"mode": "barometer", "V0": 1.0, "p": 1.0, "f": 10.0, "dc": False, "Vb": 10.0, "a": 0.1},
    "smallsignal": {"a": 0.1, "order": 1},
    "pullin": {"mode": "voltage", "V": 25.0, "xs": 0.2},
}


def render() -> None:
    lesson = state.bundle().lessons[LESSON_ID]
    layout.page_header("Capacitive Sensor Lab", "Capacitive pressure sensor",
                       "From a membrane on springs to C(x), barometer and microphone, harmonics and pull-in.")
    scenes = {s.id: s for s in lesson.scenes}
    deep = st.query_params.get("scene")
    if "cap_scene" not in st.session_state:
        st.session_state["cap_scene"] = deep if deep in scenes else lesson.scenes[0].id
    scene = scenes[st.session_state["cap_scene"]]
    layout.sensor_map(scene.map_stage or lesson.map_stage,
                      "pressure → membrane deflection" if scene.map_stage == "primary_transducer" else lesson.map_note)
    sid = st.segmented_control("Step", list(scenes), format_func=lambda i: scenes[i].short, key="cap_scene",
                               required=True)
    scene = scenes[sid]
    st.markdown(f"## {scene.title}")
    inspector.term_chips(scene.concepts)
    {"membrane": _membrane, "capacitance": _capacitance, "cx": _cx, "current": _current, "smallsignal": _small,
     "pullin": _pullin}[sid](lesson, scene)


# ------------------------------------------------------------------------------- helpers


def _setup(scene) -> tuple[str, dict]:
    scope = f"cap_{scene.id}"
    defaults = DEFAULTS[scene.id]
    C.ensure_defaults(scope, defaults)
    return scope, defaults


def _banner(lesson, bid: str) -> None:
    break_it_banner({b.id: b for b in lesson.break_it}[bid])


def _derive_picker(scope: str, options: list[str]):
    def derive() -> None:
        bundle = state.bundle()
        key = f"{scope}__deriv"
        if st.session_state.get(key) not in options:
            st.session_state[key] = options[0]
        did = (st.segmented_control("Derivation", options, key=key, required=True,
                                    format_func=lambda d: bundle.derivations[d].title)
               if len(options) > 1 else options[0])
        stepper(bundle.derivations[did], scope=scope)

    return derive


def _um(x: float) -> str:
    return format_si(x, "m", 3)


def _x_of_p(p_kpa: float, k: float = G.k) -> float:
    return cap.displacement(p_kpa * 1e3, cap.Geometry(A=G.A, d=G.d, k=k))


# ------------------------------------------------------------------------------- 0 · membrane


def _membrane(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    p, k = C.value(scope, "p"), C.value(scope, "k")
    geo = cap.Geometry(A=G.A, d=G.d, k=k)
    x = _x_of_p(p, k)
    h = cap.h_px(geo)
    res = L.resolved(scope, scene)
    svg = F.capacitor(x_rel=x / G.d, p_rel=p / 4, p_label=f"{p:g} kPa", source="none", show_circuit=False,
                      gap_value=_um(G.d - x), x_value=_um(x), selected=res.highlight)
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([3, 2.4, 1])
        with c1:
            C.slider(scope, "p", "p · pressure on the membrane", 0.0, 4.0, 0.1, "%.1f kPa", disabled=not unlocked)
        with c2:
            C.segmented(scope, "k", "k · stiffness of each spring", K_CHOICES, fmt=lambda v: f"{v / 1e3:g} kN/m",
                        disabled=not unlocked)
        with c3:
            C.reset_button(scope, defaults)
    equation.strip(
        scope, scene,
        law=r"[[x]] = [[H]]\,[[p]]",
        law_beginner=r"[[x]] = \underbrace{[[H]]}_{\text{metres per pascal}}\,\underbrace{[[p]]}_{\text{the push}}",
        numbers=(rf"= \frac{{10^{{-6}}\,\text{{m}}^2}}{{2\times{k:g}\,\text{{N/m}}}}\times {p * 1e3:g}\,\text{{Pa}}"),
        result=rf"x = {q(x, 'm', 3)}",
        selectable=["x", "H", "p", "A", "k"],
        caption=(f"H_p-x = A/(2k) = {h * 1e9:.3g} nm/Pa — the same at every pressure, so this stage is linear. "
                 f"The gap shrinks from d = 2 µm to d − x = {_um(G.d - x)}."),
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — deflection vs pressure for three spring stiffnesses (fixed axes)")
        ps = np.linspace(0, 4, 41)
        fig = plots.figure("pressure p (kPa)", "deflection x (µm)", (0, 4.1), (0, 0.9))
        for kk, col in zip(K_CHOICES, (plots.COLORS["ink"], plots.COLORS["cur"], plots.COLORS["muted"])):
            plots.line(fig, ps, [_x_of_p(v, kk) * 1e6 for v in ps], f"k = {kk / 1e3:g} kN/m", color=col,
                       width=3.4 if kk == k else 1.6, dash="solid" if kk == k else "dot")
        plots.point(fig, p, x * 1e6, _um(x))
        plots.show(fig, key="cap_membrane_plot")
        st.caption("Straight lines through zero: doubling the pressure doubles the deflection. Stiffer springs, "
                   "flatter line.")
    L.deeper(scope, lesson, scene)


# ------------------------------------------------------------------------------- 1 · capacitance


def _capacitance(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    g_um, A_mm2, V = C.value(scope, "g"), C.value(scope, "A"), C.value(scope, "V")
    Cv = cap.capacitance(cap.EPS0, A_mm2 * 1e-6, g_um * 1e-6)
    Q = cap.charge(Cv, V)
    res = L.resolved(scope, scene)
    svg = F.capacitor(x_rel=1 - g_um / 4.0, V=V, q_rel=min(1.0, Q / 1e-10), source="dc", show_d=False,
                      show_x=False, gap_value=f"{g_um:g} µm", area_rel=A_mm2 / 4.0, selected=res.highlight,
                      meter_label="no current (static)")
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2.4, 2.4, 2.4, 1])
        with c1:
            C.slider(scope, "g", "gap between the plates", 0.5, 4.0, 0.1, "%.1f µm", disabled=not unlocked)
        with c2:
            C.slider(scope, "A", "A · plate area", 0.25, 4.0, 0.25, "%.2f mm²", disabled=not unlocked)
        with c3:
            C.slider(scope, "V", "V · voltage across the plates", 0.0, 10.0, 0.5, "%.1f V", disabled=not unlocked)
        with c4:
            C.reset_button(scope, defaults)
    equation.strip(
        scope, scene,
        law=r"[[Q]] = [[C]]\,[[V]],\qquad [[C]] = \frac{[[eps]]\,[[A]]}{[[gap]]}",
        law_beginner=(r"[[Q]] = [[C]]\,[[V]],\qquad [[C]] = \frac{\overbrace{[[eps]]\,[[A]]}^{\text{more area: more } C}}"
                      r"{\underbrace{[[gap]]}_{\text{smaller gap: more } C}}"),
        numbers=(rf"C = \frac{{8.85\times10^{{-12}}\times{A_mm2:g}\times10^{{-6}}}}{{{g_um:g}\times10^{{-6}}}}\,\text{{F}}"
                 rf" = {q(Cv, 'F', 3)}"),
        result=rf"Q = {q(Q, 'C', 3)}",
        selectable=["Q", "C", "V", "eps", "A", "gap"],
        caption=f"About {Q / 1.602e-19:,.2g} electrons moved from one plate to the other. "
                "Change the voltage: Q changes, C does not.",
        stacked=True,
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — capacitance vs gap (fixed axes)")
        gs = np.linspace(0.5, 4.0, 120)
        fig = plots.figure("gap (µm)", "capacitance C (pF)", (0.4, 4.1), (0, 72))
        for aa, col in ((4.0, plots.COLORS["muted"]), (1.0, plots.COLORS["muted"])):
            if aa != A_mm2:
                plots.line(fig, gs, [cap.capacitance(cap.EPS0, aa * 1e-6, v * 1e-6) * 1e12 for v in gs],
                           f"A = {aa:g} mm²", color=col, width=1.4, dash="dot")
        plots.line(fig, gs, [cap.capacitance(cap.EPS0, A_mm2 * 1e-6, v * 1e-6) * 1e12 for v in gs],
                   f"A = {A_mm2:g} mm²", color=plots.COLORS["ink"], width=3.2)
        plots.point(fig, g_um, Cv * 1e12, format_si(Cv, "F", 3))
        plots.show(fig, key="cap_c_plot")
        st.caption("Not a straight line: halving the gap doubles C, and the curve shoots up as the gap closes. "
                   "This is exactly what makes the pressure sensor nonlinear.")
    L.deeper(scope, lesson, scene)


# ------------------------------------------------------------------------------- 2 · C(x)


def _cx(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    p, tangent = C.value(scope, "p"), C.value(scope, "tangent")
    x = _x_of_p(p)
    u = x / G.d
    Cx = cap.c_of_x(x)
    slope = cap.dc_dx(x)
    slope0 = cap.dc_dx(0.0)
    res = L.resolved(scope, scene)
    svg = F.capacitor(x_rel=u, p_rel=p / 9, p_label=f"{p:g} kPa", source="none", show_circuit=False,
                      gap_value=_um(G.d - x), x_value=_um(x), selected=res.highlight)
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([3.4, 2, 1])
        with c1:
            C.slider(scope, "p", "p · pressure (moves the membrane)", 0.0, 9.0, 0.25, "%.2f kPa",
                     disabled=not unlocked)
        with c2:
            C.toggle(scope, "tangent", "Show the tangent (local slope)", disabled=not unlocked)
        with c3:
            C.reset_button(scope, defaults)
    equation.strip(
        scope, scene,
        law=r"[[C]] = \frac{[[eps]]\,[[A]]}{[[d]] - [[x]]} = \frac{[[C0]]}{1 - [[u]]}",
        law_beginner=(r"[[C]] = \frac{[[eps]]\,[[A]]}{[[d]] - [[x]]} = \frac{\overbrace{[[C0]]}^{\text{at rest}}}"
                      r"{\underbrace{1 - [[u]]}_{\to\,0 \text{ as the gap closes}}}"),
        numbers=rf"= \frac{{{G.C0 * 1e12:.3g}\,\text{{pF}}}}{{1 - {u:.3f}}}",
        result=rf"C = {q(Cx, 'F', 4)}",
        selectable=["C", "C0", "u", "x", "d", "eps", "A", "dCdx"],
        caption=(f"Slope here: dC/dx = {slope * 1e6:.3g} pF/µm — {slope / slope0:.2f}× the slope at rest "
                 f"({slope0 * 1e6:.3g} pF/µm). The same push changes C more and more: no constant transfer function."),
        stacked=True,
    )
    if u >= 0.3:
        _banner(lesson, "big_deflection")
    with st.container(key="consequence"):
        layout.kicker("Consequence — C(x) against the straight-line idea (fixed axes)")
        us = np.linspace(0, 0.95, 200)
        fig = plots.figure("relative deflection x/d", "C / C₀", (0, 1.0), (0, 10.5))
        plots.line(fig, us, 1 / (1 - us), "exact C(x)/C₀", color=plots.COLORS["ink"], label_at=0.88)
        plots.line(fig, us, 1 + us, "small signal 1 + x/d", color=plots.COLORS["volt"], dash="dash",
                   label_y_shift=-10)
        if tangent:
            m = 1 / (1 - u) ** 2  # d(C/C0)/d(x/d)
            ts = np.linspace(max(0, u - 0.25), min(0.95, u + 0.25), 20)
            plots.line(fig, ts, 1 / (1 - u) + m * (ts - u), "tangent here", color=plots.COLORS["plus"], width=2,
                       label_y_shift=12)
        fig.add_vline(x=1 / 3, line=dict(color=plots.COLORS["muted"], dash="dot"))
        plots.point(fig, u, 1 / (1 - u), f"{Cx * 1e12:.3g} pF")
        plots.show(fig, key="cap_cx_plot")
        steps = [cap.c_of_x(_x_of_p(v)) * 1e12 for v in (0, 2.5, 5.0, 7.5)]
        c1, c2, c3 = st.columns(3)
        c1.metric("C(x) now", format_si(Cx, "F", 4))
        c2.metric("ΔC for 0 → 2.5 kPa", f"{steps[1] - steps[0]:.3g} pF")
        c3.metric("ΔC for 5 → 7.5 kPa", f"{steps[3] - steps[2]:.3g} pF",
                  help="The same 2.5 kPa step, at a smaller gap.")
        st.caption("Equal pressure steps, very unequal capacitance steps. The dotted line marks x = d/3, the limit "
                   "you will meet at pull-in.")
    L.deeper(scope, lesson, scene, derive=_derive_picker(scope, ["small_signal"]))


# ------------------------------------------------------------------------------- 3 · current


def _current(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    v = {k: C.value(scope, k) for k in defaults}
    baro = v["mode"] == "barometer"
    if baro:
        f = v["f"] * 1e3
        x = _x_of_p(v["p"])
        r = cap.barometer(v["V0"], f, x, periods=3, n=900)
        if v["dc"]:  # the learner's experiment: constant voltage on a slowly changing capacitor
            r = cap.current_terms(r.t, np.full_like(r.t, v["V0"]), r.x)
        amp = 0.0 if v["dc"] else cap.barometer_amplitude(v["V0"], f, x)
        amp_max = 2.0 * 2 * math.pi * f * cap.c_of_x(_x_of_p(6.0))
    else:
        f = 1e3
        x = 0.0
        r = cap.microphone(v["Vb"], f, v["a"] * G.d, periods=3, n=900)
        amp = float(np.max(np.abs(r.total)))
        amp_max = float(np.max(np.abs(cap.microphone_exact(r.t, 20.0, f, 0.4 * G.d))))
    sel_id = inspector.selected(scope)
    res = L.resolved(scope, scene)
    svg = F.capacitor(
        x_rel=x / G.d, V=1.0, q_rel=0.5, source="ac" if (baro and not v["dc"]) else "dc",
        p_rel=v["p"] / 6 if baro else None, p_label=f"{v['p']:g} kPa (slow)" if baro else "",
        osc_rel=0.0 if baro else v["a"], i_strength=min(1.0, amp / amp_max) if amp_max else 0.0,
        meter_label=(f"|I| = {format_si(amp, 'A', 3)}" if amp else "I = 0"),
        gap_value=_um(G.d - x) if baro else "d ± x₀", x_value=_um(x) if baro else "", selected=res.highlight)
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2.2, 2.4, 2.4, 1])
        with c1:
            C.segmented(scope, "mode", "Readout case", ["barometer", "microphone"],
                        fmt=lambda m: "barometer (slow p)" if m == "barometer" else "microphone (fast p)",
                        disabled=not unlocked)
        if baro:
            with c2:
                C.slider(scope, "V0", "V₀ · AC bias amplitude", 0.2, 2.0, 0.1, "%.1f V", disabled=not unlocked)
            with c3:
                C.slider(scope, "p", "p · static pressure", 0.0, 6.0, 0.25, "%.2f kPa", disabled=not unlocked)
        else:
            with c2:
                C.slider(scope, "Vb", "V_b · DC bias", 0.0, 20.0, 1.0, "%.0f V", disabled=not unlocked)
            with c3:
                C.slider(scope, "a", "x₀/d · sound amplitude", 0.0, 0.4, 0.02, "%.2f", disabled=not unlocked)
        with c4:
            C.reset_button(scope, defaults)
        if baro:
            with st.expander("More controls"):
                m1, m2 = st.columns(2)
                with m1:
                    C.segmented(scope, "f", "bias frequency f", F_CHOICES, fmt=lambda k: f"{k:g} kHz",
                                disabled=not unlocked)
                with m2:
                    C.toggle(scope, "dc", "Experiment: use a DC bias instead", disabled=not unlocked,
                             help="Constant V on a slowly changing capacitor — watch the current.")
    def rms(a: np.ndarray) -> str:
        val = float(np.sqrt(np.mean(a[5:-5] ** 2)))
        top = max(float(np.sqrt(np.mean(r.total[5:-5] ** 2))), 1e-30)
        return "≈ 0" if val < 1e-4 * top or val < 1e-15 else "= " + format_si(val, "A", 3)

    if baro:
        law = (r"[[I]] = [[CdV]] + \color{" + GREY + r"}{\underbrace{[[VdC]]}_{\approx\,0\ (\text{slow } p)}}")
        if v["dc"]:
            law = (r"[[I]] = \color{" + GREY + r"}{\underbrace{[[CdV]]}_{=\,0\ (\text{DC})}} + "
                   r"\color{" + GREY + r"}{\underbrace{[[VdC]]}_{\approx\,0}} = 0")
            numbers = r"\text{nothing changes} \Rightarrow \text{nothing flows}"
            result = r"I = 0"
        else:
            numbers = (rf"|I| = V_0\,\omega\,C = {v['V0']:g}\,\text{{V}}\times2\pi\times{v['f']:g}\,\text{{kHz}}"
                       rf"\times{cap.c_of_x(x) * 1e12:.3g}\,\text{{pF}}")
            result = rf"|I| = {q(amp, 'A', 3)}"
        selectable = ["I", "CdV", "VdC", "C", "dVdt", "dCdt", "V0", "omega"]
    else:
        law = (r"[[I]] = \color{" + GREY + r"}{\underbrace{[[CdV]]}_{=\,0\ (\text{DC})}} + [[VdC]]"
               r" = [[Vb]]\,[[dCdx]]\,[[dxdt]]")
        lin = cap.microphone_linear_amplitude(v["Vb"], f, v["a"] * G.d)
        numbers = rf"\text{{small signal: }} V_b\,\frac{{C_0}}{{d}}\,\omega\,x_0 = {q(lin, 'A', 3)}"
        result = rf"\text{{peak }}|I| = {q(amp, 'A', 3)}"
        selectable = ["I", "CdV", "VdC", "Vb", "dCdx", "dxdt", "dCdt"]
    equation.strip(scope, scene, law, numbers, result, selectable=selectable, stacked=True,
                   caption=(f"RMS of the two terms right now: C·dV/dt {rms(r.term_cdv)}, "
                            f"V·dC/dt {rms(r.term_vdc)}. The greyed term is the one this case "
                            "neglects."))
    if baro and v["dc"]:
        _banner(lesson, "dc_barometer")
    with st.container(key="consequence"):
        layout.kicker("Consequence — the same three periods: what changes, and the current it makes")
        tt = r.t * f
        c1, c2 = st.columns(2)
        with c1:
            if baro:
                fig = plots.figure("time (periods of the bias)", "bias V(t) (V)", (0, 3), (-2.3, 2.3), height=250)
                plots.line(fig, tt, r.v, "V(t)", color=plots.COLORS["volt"])
                fig2_title = "the capacitor barely changes (slow pressure)"
            else:
                fig = plots.figure("time (periods of the sound)", "deflection x/d", (0, 3), (-0.45, 0.45), height=250)
                plots.line(fig, tt, r.x / G.d, "x(t)/d", color=plots.COLORS["cur"])
                fig2_title = "the voltage is constant (DC bias)"
            plots.show(fig, key="cap_cur_drive")
            st.caption(f"What changes: {'the voltage' if baro else 'the gap'} — {fig2_title}.")
        with c2:
            scale = 1e6 if baro else 1e9
            unit = "µA" if baro else "nA"
            ymax = amp_max * scale * 1.1
            fig = plots.figure("time (periods)", f"current ({unit})", (0, 3), (-ymax, ymax), height=250)
            plots.line(fig, tt, r.term_cdv * scale, "C·dV/dt", color=plots.COLORS["cur"],
                       width=3.2 if baro else 1.4, label_y_shift=10)
            plots.line(fig, tt, r.term_vdc * scale, "V·dC/dt", color=plots.COLORS["plus"], dash="dash",
                       width=1.4 if baro else 3.2, label_y_shift=-10)
            plots.show(fig, key="cap_cur_terms")
            st.caption("Blue: current because V changes. Red dashed: current because C changes. Only one of them "
                       "matters in each case.")
        layout.kicker("Why two terms? Charge is a rectangle V × C")
        r1, r2 = st.columns([1.3, 2])
        with r1:
            hl = {sel_id} & {"CdV", "VdC"}
            st.html(as_img(F.product_rule(1, 1, 0.22 if baro else 0.0, 0.0 if baro else 0.18, selected=hl),
                             max_width=420))
        with r2:
            st.markdown(
                "Grow the height $V$ and a strip $C\\,\\Delta V$ appears on top; grow the width $C$ and a strip "
                "$V\\,\\Delta C$ appears at the side. Divided by the time it took:\n\n"
                "$$\\frac{dQ}{dt} = C\\,\\frac{dV}{dt} + V\\,\\frac{dC}{dt}$$\n\n"
                + ("**Barometer:** only the top strip grows — the voltage does the work."
                   if baro else "**Microphone:** only the side strip grows — the moving membrane does the work.")
            )
    L.deeper(scope, lesson, scene, derive=_derive_picker(
        scope, ["barometer_case", "microphone_case"] if baro else ["microphone_case", "barometer_case"]))


# ------------------------------------------------------------------------------- 4 · small signal


@st.cache_data(show_spinner=False, max_entries=64)
def _mic_wave(a: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    r = cap.microphone(10.0, 1e3, a * G.d, periods=4, n=4001) if a > 0 else None
    if r is None:
        t = np.linspace(0, 4e-3, 4001)
        return t, np.zeros_like(t), np.zeros(4)
    return r.t, r.total, cap.harmonics(r.total, r.t, 1e3, 4)


def _small(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    a, order = C.value(scope, "a"), C.value(scope, "order")
    exact = cap.geometric_exact(a)
    approx = cap.geometric_partial(a, order)
    err = cap.relative_error(a, order)
    t, cur, amps = _mic_wave(round(a, 4))
    lin_amp = cap.microphone_linear_amplitude(10.0, 1e3, a * G.d)
    res = L.resolved(scope, scene)
    svg = F.capacitor(x_rel=0.0, V=1.0, q_rel=0.5, source="dc", osc_rel=a,
                      i_strength=min(1.0, a / 0.4), meter_label="", gap_value="d ± x₀", selected=res.highlight)
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([3, 2.4, 1])
        with c1:
            C.slider(scope, "a", "x₀/d · how far the membrane swings", 0.0, 0.6, 0.02, "%.2f", disabled=not unlocked)
        with c2:
            C.segmented(scope, "order", "Keep terms up to", [1, 2, 3],
                        fmt=lambda n: {1: "1st order", 2: "2nd order", 3: "3rd order"}[n], disabled=not unlocked)
        with c3:
            C.reset_button(scope, defaults)
    terms = " + ".join(["1", "[[u]]"] + [rf"\left([[u]]\right)^{k}" for k in range(2, order + 1)])
    equation.strip(
        scope, scene,
        law=(r"\frac{1}{1 - [[u]]} = 1 + [[u]] + \left([[u]]\right)^2 + \left([[u]]\right)^3 + \dots"
             r" \;\approx\; " + terms),
        numbers=rf"\frac{{x}}{{d}} = {a:.2f}:\quad \frac{{1}}{{1 - {a:.2f}}} = {exact:.4f}",
        result=rf"{approx:.4f}\ \ (\text{{error }} {err * 100:.2g}\,\%)",
        selectable=["u", "x", "d"],
        caption=f"Relative error of the cut = the first dropped term, (x/d)^{order + 1} = {err * 100:.2g} % at the peak "
                "of the swing.",
        stacked=True,
    )
    if a >= 0.3:
        _banner(lesson, "big_deflection")
    with st.container(key="consequence"):
        layout.kicker("Consequence — exact curve vs the approximations, over the range the membrane swings")
        c1, c2 = st.columns(2)
        with c1:
            us = np.linspace(-0.6, 0.85, 300)
            fig = plots.figure("x/d", "1/(1 − x/d)", (-0.62, 0.88), (0.4, 7.0), height=280)
            if a > 0:
                fig.add_vrect(x0=-a, x1=a, fillcolor=plots.COLORS["volt"], opacity=0.10, line_width=0)
            plots.line(fig, us, 1 / (1 - us), "exact", color=plots.COLORS["ink"], width=3, label_at=0.8)
            for n, col in ((1, plots.COLORS["volt"]), (2, plots.COLORS["cur"]), (3, plots.COLORS["minus"])):
                plots.line(fig, us, cap.geometric_partial(us, n), f"order {n}", color=col,
                           width=3 if n == order else 1.3, dash="solid" if n == order else "dot")
            plots.point(fig, a, exact, f"error {err * 100:.2g} %", show_guides=False)
            plots.show(fig, key="cap_taylor_plot")
            st.caption("Shaded: the range the membrane swings through. Inside it, the approximation must be close.")
        with c2:
            fig = go.Figure()
            fig.add_bar(x=["ω", "2ω", "3ω", "4ω"], y=list(amps / amps[0]) if amps[0] else [0, 0, 0, 0],
                        marker_color=[plots.COLORS["ink"], plots.COLORS["plus"], plots.COLORS["volt"],
                                      plots.COLORS["muted"]],
                        text=[f"{v:.2f}" for v in (amps / amps[0] if amps[0] else [0, 0, 0, 0])],
                        textposition="outside")
            base = plots.figure("frequency", "amplitude / fundamental", (-0.5, 3.5), (0, 1.15), height=280)
            fig.update_layout(base.layout)
            fig.update_xaxes(type="category", range=None, title_text="component of the microphone current")
            plots.show(fig, key="cap_harm_plot")
            thd = cap.thd(amps) if amps[0] else 0.0
            st.caption(f"New frequencies appear as the swing grows. THD (supplemental) = {thd * 100:.2g} %.")
        layout.kicker("The microphone current over two periods: exact vs the straight-line model")
        tt = t * 1e3
        w = 2 * math.pi * 1e3
        lin = -lin_amp * np.sin(w * t)
        norm = max(lin_amp, 1e-30)
        fig = plots.figure("time (periods of the sound)", "current /<br>small-signal amplitude", (0, 2), (-4.5, 4.5),
                           height=250)
        mask = tt <= 2.0
        plots.line(fig, tt[mask], lin[mask] / norm, "small-signal", color=plots.COLORS["volt"], dash="dash",
                   label_y_shift=-16)
        plots.line(fig, tt[mask], cur[mask] / norm, "exact", color=plots.COLORS["ink"], label_y_shift=16)
        plots.show(fig, key="cap_mic_wave")
        st.caption("For a small swing the curves coincide. For a large one the exact current is lopsided: that "
                   "asymmetry IS the 2ω and 3ω content.")
    L.deeper(scope, lesson, scene, derive=_derive_picker(scope, ["small_signal", "microphone_case"]))


# ------------------------------------------------------------------------------- 5 · pull-in


def _v_needed(u: np.ndarray | float) -> np.ndarray | float:
    """Voltage that balances the springs at x = u·d (any x, stable or not)."""
    x = np.asarray(u, dtype=float) * G.d
    out = np.sqrt(2 * G.k_eff * x * (G.d - x) ** 2 / (G.eps * G.A))
    return float(out) if np.ndim(out) == 0 else out


def _pullin(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    mode, V, xs = C.value(scope, "mode"), C.value(scope, "V"), C.value(scope, "xs")
    f_ref = G.k_eff * G.d * 0.5  # 5 mN: scale for the force arrows
    if mode == "voltage":
        eqs = cap.equilibria(V)
        x_st = cap.stable_position(V)
        pulled = x_st is None
        x_now = G.d / 3 if pulled else x_st
        V_now = V
    else:
        eqs = []
        pulled = False
        x_now = xs * G.d
        V_now = _v_needed(xs)
    Fs = float(cap.spring_force(x_now))
    Fe = float(cap.electrostatic_force(V_now, x_now))
    res = L.resolved(scope, scene)
    note = ("held by feedback (voltage adjusted)" if mode == "feedback" else
            ("" if pulled else ("stable balance" if V > 0 else "")))
    svg = F.capacitor(x_rel=x_now / G.d, V=V_now, q_rel=min(1.0, V_now / 40), source="dc", pulled_in=pulled,
                      snap_from_rel=1 / 3, forces=None if pulled else (Fs / f_ref, Fe / f_ref),
                      gap_value=_um(G.d - x_now), x_value=_um(x_now), selected=res.highlight,
                      note=note, note_color=plots.COLORS["minus"])
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([2.6, 3, 1])
        with c1:
            C.segmented(scope, "mode", "Bias control", ["voltage", "feedback"],
                        fmt=lambda m: "constant voltage" if m == "voltage" else "feedback (supplemental)",
                        disabled=not unlocked)
        with c2:
            if mode == "voltage":
                C.slider(scope, "V", "V · bias voltage", 0.0, 45.0, 0.5, "%.1f V", disabled=not unlocked)
            else:
                C.slider(scope, "xs", "x/d · where the feedback holds the membrane", 0.0, 0.9, 0.02, "%.2f",
                         disabled=not unlocked)
        with c3:
            C.reset_button(scope, defaults)
    if pulled:
        result = r"\text{no balance} \Rightarrow \text{pull-in}"
    elif mode == "voltage":
        result = rf"\begin{{aligned}}&\text{{stable at}}\\&x = {q(x_now, 'm', 3)} = {x_now / G.d:.2f}\,d\end{{aligned}}"
    else:
        result = rf"V = {q(V_now, 'V', 3)}\ \text{{(set by the loop)}}"
    equation.strip(
        scope, scene,
        law=r"[[Fs]] = 2[[k]]\,[[x]] \qquad [[Fe]] = \frac{[[eps]]\,[[A]]\,[[V]]^2}{2\,([[gap]])^2}",
        law_beginner=(r"\underbrace{[[Fs]] = 2[[k]]\,[[x]]}_{\text{grows like } x} \qquad "
                      r"\underbrace{[[Fe]] = \frac{[[eps]]\,[[A]]\,[[V]]^2}{2\,([[gap]])^2}}_{\text{grows like } 1/\text{gap}^2}"),
        numbers=(rf"x = {x_now / G.d:.2f}\,d:\quad F_\text{{spring}} = {q(Fs, 'N', 3)},\ "
                 rf"F_\text{{el}} = {q(Fe, 'N', 3)}"),
        result=result,
        selectable=["Fs", "Fe", "k", "x", "V", "gap", "d", "eps", "A"],
        caption=(f"Pull-in voltage for this membrane (supplemental): V_PI = {V_PI:.1f} V, reached at x = d/3. "
                 + ("Above it there is no balance — the membrane snaps." if mode == "voltage" else
                    "A feedback loop lowers the voltage as the gap closes, so it can hold any x.")),
        stacked=True,
    )
    if pulled:
        _banner(lesson, "pull_in")
    with st.container(key="consequence"):
        layout.kicker("Consequence — the forces and the voltage needed to hold each position (same x/d as the picture)")
        us = np.linspace(0, 0.95, 400)
        c1, c2 = st.columns(2)
        with c1:
            fig = plots.figure("x/d", "force (mN)", (0, 0.97), (0, 12), height=290)
            plots.line(fig, us, cap.spring_force(us * G.d) * 1e3, "spring 2k·x", color=plots.COLORS["minus"],
                       label_at=0.8, label_y_shift=-12)
            fe = np.minimum(cap.electrostatic_force(V_now, us * G.d) * 1e3, 13)
            plots.line(fig, us, fe, f"pull at {V_now:.1f} V", color=plots.COLORS["plus"], label_at=0.45,
                       label_y_shift=14)
            fig.add_vline(x=1 / 3, line=dict(color=plots.COLORS["muted"], dash="dot"))
            fig.add_annotation(x=1 / 3, y=11.2, text="d/3", showarrow=False, xshift=14,
                               font=dict(color=plots.COLORS["muted"], size=12))
            for e in eqs:
                fig.add_trace(go.Scatter(x=[e.x / G.d], y=[cap.spring_force(e.x) * 1e3], mode="markers",
                                         marker=dict(size=13, symbol="circle" if e.stable else "circle-open",
                                                     color=plots.COLORS["ink"], line=dict(width=2.5)),
                                         hoverinfo="skip"))
                fig.add_annotation(x=e.x / G.d, y=cap.spring_force(e.x) * 1e3,
                                   text="stable" if e.stable else "unstable", showarrow=True, ax=0, ay=-30,
                                   font=dict(size=12))
            plots.show(fig, key="cap_force_plot")
            st.caption("Filled: stable crossing (the membrane rests here). Hollow: unstable (a nudge runs away).")
        with c2:
            fig = plots.figure("x/d", "voltage needed to hold x (V)", (0, 0.97), (0, 45), height=290)
            plots.line(fig, us, _v_needed(us), "balance voltage", color=plots.COLORS["ink"], label_at=0.62,
                       label_y_shift=12)
            fig.add_vrect(x0=1 / 3, x1=0.97, fillcolor=plots.COLORS["plus"], opacity=0.07, line_width=0)
            fig.add_annotation(x=0.65, y=42, text="reachable only with feedback", showarrow=False,
                               font=dict(size=12, color=plots.COLORS["plus"]))
            fig.add_vline(x=1 / 3, line=dict(color=plots.COLORS["muted"], dash="dot"))
            if mode == "voltage":
                fig.add_hline(y=V, line=dict(color=plots.COLORS["volt"], dash="dash"))
            plots.point(fig, x_now / G.d, V_now, f"{V_now:.1f} V", show_guides=False)
            plots.show(fig, key="cap_vneed_plot")
            st.caption(f"The curve peaks at x = d/3 with V_PI = {V_PI:.1f} V. A constant voltage above the peak "
                       "meets the curve nowhere: pull-in. Feedback can follow the curve down beyond d/3.")
    L.deeper(scope, lesson, scene, derive=_derive_picker(scope, ["pull_in"]))
