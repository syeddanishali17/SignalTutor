"""Wheatstone Bridge Lab (C3, milestone M1).

Six guided steps share one picture language: step 0 shows the physical sensor
(pressure → strain → ΔR), then the bridge is built from two dividers.
In every step the figure, equation strip, readouts, plots and failure banners
come from ONE simulation result (spec 19: no visual disagreement).
"""

from __future__ import annotations

import math

import numpy as np
import streamlit as st

from tutor.sim import bridge
from tutor.sim.circuits import InvalidCircuit
from tutor.sim.units import format_si
from tutor.ui import state
from tutor.ui.components import controls as C
from tutor.ui.components import equation, inspector, layout, plots
from tutor.ui.components.derivation import stepper
from tutor.ui.components.equation import q
from tutor.ui.components.feedback import break_it_banner, invalid_state
from tutor.ui.pages import _lesson as L
from tutor.ui.svg import figures

LESSON_ID = "wheatstone_lab"
V0_MAX = 10.0
EPS_MAX_UE = 2000
G_CHOICES = [2.0, 100.0]
RIN_CHOICES = [math.inf, 10000.0, 1000.0, 100.0, 30.0, 10.0, 3.0, 1.0]  # R_in / R
MODE_LABEL = {"balanced": "balanced (no gauge)", "quarter": "quarter (1 gauge)", "full": "full (4 gauges)"}
XI_PER_PA = 5e-9  # illustrative membrane factor ξ: 100 kPa → 500 µε
P_MAX_KPA = 200

DEFAULTS = {
    "sensor": {"p": 100, "G": 2.0},
    "build": {"V0": 5.0, "R4": 1.0, "R3": 1.0, "layout": "dividers", "currents": True},
    "quarter": {"V0": 5.0, "eps": 500, "G": 2.0, "R": 350.0, "layout": "dividers", "currents": True, "err": False},
    "full": {"V0": 5.0, "eps": 500, "G": 2.0, "R": 350.0, "layout": "dividers", "currents": True},
    "temperature": {"V0": 5.0, "dT": 20, "mode": "full", "eps": 0, "G": 2.0, "alpha": 0.1, "layout": "dividers",
                    "currents": False},
    "loading": {"V0": 5.0, "rin": 10.0, "mode": "quarter", "eps": 500, "G": 2.0, "R": 350.0, "layout": "dividers",
                "currents": True},
}


def _g(v: float) -> str:
    return "metal foil, G = 2" if v == 2.0 else "silicon, G = 100"


def _rin(v: float) -> str:
    return "∞ (ideal)" if math.isinf(v) else f"{v:g} × R"


def _r(v: float) -> str:
    """Resistance in Ω with enough digits to show a 0.1 % change."""
    return f"{v:.6g}"


def render() -> None:
    lesson = state.bundle().lessons[LESSON_ID]
    layout.page_header("Wheatstone Bridge Lab", "Wheatstone bridge",
                       "From a bending membrane to quarter and full bridges — with the lecture's derivation.")
    scenes = {s.id: s for s in lesson.scenes}
    deep = st.query_params.get("scene")
    if "wb_scene" not in st.session_state:
        st.session_state["wb_scene"] = deep if deep in scenes else lesson.scenes[0].id
    scene = scenes[st.session_state["wb_scene"]]
    layout.sensor_map(scene.map_stage or lesson.map_stage,
                      "pressure → membrane strain" if scene.map_stage == "primary_transducer" else lesson.map_note)
    sid = st.segmented_control("Step", list(scenes), format_func=lambda i: scenes[i].short, key="wb_scene", required=True)
    scene = scenes[sid]
    st.markdown(f"## {scene.title}")
    inspector.term_chips(scene.concepts)
    if sid == "sensor":
        _sensor(lesson, scene)
    else:
        _scene(lesson, scene)


# ------------------------------------------------------------------------------- step 0


def _sensor(lesson, scene) -> None:
    scope = "wb_sensor"
    defaults = DEFAULTS["sensor"]
    C.ensure_defaults(scope, defaults)
    unlocked = L.top(scope, lesson, scene)
    p_kpa, G = C.value(scope, "p"), C.value(scope, "G")
    eps = XI_PER_PA * p_kpa * 1e3
    x = bridge.dR_rel_from_strain(G, eps)
    res = L.resolved(scope, scene)
    svg = figures.membrane(p_kpa, P_MAX_KPA, eps, x, selected=res.highlight)
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([3, 2.4, 1.2])
        with c1:
            C.slider(scope, "p", "p — pressure on the membrane", 0, P_MAX_KPA, 10, "%d kPa", disabled=not unlocked)
        with c2:
            C.segmented(scope, "G", "Gauge type", G_CHOICES, fmt=_g, disabled=not unlocked)
        with c3:
            C.reset_button(scope, defaults)
    equation.strip(
        scope, scene,
        law=r"[[x]] = [[G]]\,[[eps]] = [[G]]\,[[xi]]\,[[p]]",
        numbers=(rf"= {G:g}\times\left({XI_PER_PA * 1e9:g}\times10^{{-9}}\,\text{{Pa}}^{{-1}}\right)"
                 rf"\times\left({p_kpa:g}\times10^{{3}}\,\text{{Pa}}\right)"),
        result=rf"\frac{{\Delta R}}{{R}} = \pm{x * 100:.3g}\,\%",
        selectable=["p", "xi", "eps", "G", "x"],
        caption=f"Strain on each gauge: ±{eps * 1e6:.0f} µε. On a 350 Ω gauge that is ΔR = ±{x * 350:.3g} Ω — "
                "far too small to read with an ohmmeter. Next step: a circuit that turns this into a clean voltage.",
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — strain along the membrane surface (illustrative clamped-plate profile)")
        r = np.linspace(-1, 1, 201)
        nu = 0.3
        shape = (3 + nu) * r**2 - (1 + nu)  # radial surface strain on the pressed face (clamped plate), unscaled
        r_rim = 0.8
        f_rim = (3 + nu) * r_rim**2 - (1 + nu)
        r_mid = float(np.sqrt(((1 + nu) - f_rim) / (3 + nu)))  # where the strain is exactly −(rim strain)
        scale = eps / f_rim  # gauges at r_rim read exactly +ε, at r_mid exactly −ε
        e_max = XI_PER_PA * P_MAX_KPA * 1e3 * 1e6
        fig = plots.figure("position across the membrane (rim … centre … rim)", "surface strain ε (µε)",
                           (-1.05, 1.05), (-1.75 * e_max, 2.6 * e_max))
        plots.line(fig, r, shape * scale * 1e6, "surface strain", color=plots.COLORS["ink"])
        fig.add_hline(y=0, line=dict(color="#b9b2a2"))
        for pos, name, col in ((-r_rim, "R₁", plots.COLORS["plus"]), (-r_mid, "R₄", plots.COLORS["minus"]),
                               (r_mid, "R₂", plots.COLORS["minus"]), (r_rim, "R₃", plots.COLORS["plus"])):
            fig.add_vline(x=pos, line=dict(color=col, dash="dot"))
            fig.add_annotation(x=pos, y=1, yref="paper", text=name, showarrow=False, yanchor="bottom",
                               font=dict(color=col, size=13))
        if eps:
            for y_val, col in ((eps * 1e6, plots.COLORS["plus"]), (-eps * 1e6, plots.COLORS["minus"])):
                fig.add_hline(y=y_val, line=dict(color=col, dash="dash", width=1))
        plots.show(fig, key="wb_sensor_plot")
        st.caption("Stretched near the rim (+), squeezed near the centre (−). The gauges sit exactly where the two "
                   "strains are equal and opposite (dashed lines) — the full bridge relies on that.")
    L.deeper(scope, lesson, scene)


# ------------------------------------------------------------------------------- bridge steps


def _scene(lesson, scene) -> None:
    sid = scene.id
    scope = f"wb_{sid}"
    defaults = DEFAULTS[sid]
    C.ensure_defaults(scope, defaults)
    unlocked = L.top(scope, lesson, scene)
    v = {k: C.value(scope, k) for k in defaults}

    # ---- one simulation result for everything below ---------------------------------
    try:
        res, mode, x = _simulate(sid, v)
    except InvalidCircuit as exc:
        invalid_state(str(exc))
        return
    sel_res = L.resolved(scope, scene)
    svg = figures.bridge(res, mode, layout=v["layout"], selected=sel_res.highlight, show_currents=v["currents"],
                         thermal=sid == "temperature" and v["dT"] > 0, legend=True)

    def note() -> None:
        if sid == "quarter" and state.mode() != "exam":
            st.caption("The gauge sits in the upper-left arm so that the lecture's $V_2 = I_2 R$ holds. "
                       "The lecture-2 drawing puts it lower-left, which flips the sign — known issue K9 (Sources page).")

    L.main_row(scope, scene, svg, below_visual=note)
    _tray(scope, sid, defaults, unlocked, v)
    _equation(scope, scene, res, mode, x, v)
    _banners(lesson, sid, res, mode, x, v)
    _consequence(sid, res, mode, x, v)

    deriv_default = "full_bridge" if sid in ("full", "temperature") else "quarter_bridge"

    def derive() -> None:
        bundle = state.bundle()
        key = f"{scope}__deriv"
        st.session_state.setdefault(key, deriv_default)
        did = st.segmented_control("Derivation", lesson.derivations, key=key, required=True,
                                   format_func=lambda d: bundle.derivations[d].title)
        stepper(bundle.derivations[did], scope=scope)

    L.deeper(scope, lesson, scene, derive=derive)


def _simulate(sid: str, v: dict) -> tuple[bridge.BridgeResult, str, float]:
    if sid == "build":
        arms = bridge.Arms(R1=1e3, R2=1e3, R3=v["R3"] * 1e3, R4=v["R4"] * 1e3)
        return bridge.solve(v["V0"], arms), "balanced", 0.0
    x = bridge.dR_rel_from_strain(v["G"], v["eps"] * 1e-6)
    mode = {"quarter": "quarter", "full": "full"}.get(sid, v.get("mode", "quarter"))
    R = v.get("R", 350.0)
    thermal = v["alpha"] / 100 * v["dT"] if sid == "temperature" else 0.0
    r_meter = v["rin"] * R if sid == "loading" else math.inf
    return bridge.simulate(mode, v["V0"], R, x, thermal, r_meter), mode, x


# ------------------------------------------------------------------------------- controls


def _tray(scope: str, sid: str, defaults: dict, unlocked: bool, v: dict) -> None:
    dis = not unlocked
    with st.container(key="tray"):
        L.tray_header(dis)
        if sid == "build":
            c1, c2 = st.columns(2)
            with c1:
                C.slider(scope, "V0", "V₀ · bridge supply", 0.0, V0_MAX, 0.5, "%.1f V", disabled=dis)
            with c2:
                C.slider(scope, "R4", "R₄ · bottom of the LEFT divider", 0.5, 2.0, 0.05, "%.2f kΩ", disabled=dis,
                         help="R1 = R2 = 1 kΩ. Balanced when R1/R4 = R2/R3.")
        else:
            cols = st.columns(3)
            with cols[0]:
                C.slider(scope, "V0", "V₀ · bridge supply", 0.0, V0_MAX, 0.5, "%.1f V", disabled=dis)
            if sid == "temperature":
                with cols[1]:
                    C.slider(scope, "dT", "ΔT · gauges warm up by", 0, 50, 1, "%d K", disabled=dis)
                with cols[2]:
                    C.segmented(scope, "mode", "Bridge", ["quarter", "full"], fmt=lambda m: MODE_LABEL[m], disabled=dis)
            elif sid == "loading":
                with cols[1]:
                    C.select_slider(scope, "rin", "R_in · meter input resistance", RIN_CHOICES, _rin, disabled=dis)
                with cols[2]:
                    C.segmented(scope, "mode", "Bridge", ["quarter", "full"], fmt=lambda m: MODE_LABEL[m], disabled=dis)
            else:
                with cols[1]:
                    C.slider(scope, "eps", "ε · strain on each gauge", 0, EPS_MAX_UE, 50, "%d µε", disabled=dis)
                with cols[2]:
                    C.segmented(scope, "G", "Gauge type", G_CHOICES, fmt=_g, disabled=dis,
                                help="Silicon's large G makes ΔR/R big enough to see the quarter bridge's nonlinearity.")
        with st.expander("More controls"):
            m1, m2, m3 = st.columns(3)
            with m1:
                C.segmented(scope, "layout", "Drawing", ["dividers", "diamond"],
                            fmt=lambda s: "two dividers" if s == "dividers" else "textbook diamond", disabled=dis)
            with m2:
                C.toggle(scope, "currents", "Show branch currents", disabled=dis)
            with m3:
                if sid == "build":
                    C.slider(scope, "R3", "R₃ · bottom of the RIGHT divider", 0.5, 2.0, 0.05, "%.2f kΩ", disabled=dis)
                elif sid in ("temperature", "loading"):
                    C.slider(scope, "eps", "ε · strain on each gauge", 0, EPS_MAX_UE, 50, "%d µε", disabled=dis)
                else:
                    C.select_slider(scope, "R", "R · nominal gauge resistance", [120.0, 350.0, 1000.0],
                                    lambda r: f"{r:g} Ω", disabled=dis)
            if sid == "temperature":
                C.slider(scope, "alpha", "α · temperature coefficient (illustrative)", 0.0, 0.3, 0.01, "%.2f %%/K", disabled=dis)
            if sid == "quarter":
                C.toggle(scope, "err", "Also plot the approximation error", disabled=dis)
        C.reset_button(scope, defaults)


# ------------------------------------------------------------------------------- equation


def _equation(scope: str, scene, res: bridge.BridgeResult, mode: str, x: float, v: dict) -> None:
    sid = scene.id
    a = res.arms
    law = r"[[out]] = [[V0]]\left(\frac{[[R4]]}{[[left]]} - \frac{[[R3]]}{[[right]]}\right)"
    law_beginner = (r"[[out]] = [[V0]]\left(\underbrace{\frac{[[R4]]}{[[left]]}}_{\text{left divider's share}}"
                    r" - \underbrace{\frac{[[R3]]}{[[right]]}}_{\text{right divider's share}}\right)")
    numbers = (rf"= {v['V0']:g}\,\text{{V}}\cdot\left(\frac{{{_r(a.R4)}}}{{{_r(a.R1)} + {_r(a.R4)}}} - "
               rf"\frac{{{_r(a.R3)}}}{{{_r(a.R2)} + {_r(a.R3)}}}\right)")
    if sid == "loading":
        ideal = bridge.solve(res.V0, a)
        result = (rf"\begin{{aligned}}&\text{{ideal meter: }}{q(ideal.Vout, 'V', 4)}\\"
                  rf"&\text{{real meter: }}{q(res.Vout, 'V', 4)}\end{{aligned}}")
    else:
        result = rf"V_2 - V_1 = {q(res.Vout, 'V', 4)}"
    caption = "Exact two-divider form, valid for every bridge (resistances in Ω). "
    if mode == "quarter" and sid in ("quarter", "temperature", "loading") and x > 0:
        approx = bridge.quarter_approx(res.V0, x)
        caption += (rf"Lecture form for small changes: $-\tfrac14\,\tfrac{{\Delta R}}{{R}}\,V_0 = "
                    rf"{q(approx, 'V', 4)}$ (overestimates by $\tfrac12\,\Delta R/R = {x / 2 * 100:.3g}\,\%$).")
    elif mode == "full" and x > 0:
        caption += (rf"Lecture form: $|V_\text{{out}}| = \tfrac{{\Delta R}}{{R}}\,V_b = G\,\varepsilon\,V_b = "
                    rf"{q(abs(bridge.full_output(res.V0, x)), 'V', 4)}$ — exact.")
    elif sid == "build":
        ok = bridge.balance_condition(a, rel_tol=1e-9)
        caption += (rf"Balance condition $R_1/R_4 = R_2/R_3$: ${a.R1 / a.R4:.3g}$ vs ${a.R2 / a.R3:.3g}$ → "
                    + ("**balanced**." if ok else "not balanced."))
    if sid == "loading":
        caption = "The two-divider formula assumes *no* meter current — exactly what the real meter breaks here."
    selectable = ["out", "V0", "R1", "R2", "R3", "R4", "left", "right"]
    equation.strip(scope, scene, law, numbers, result, law_beginner=law_beginner, selectable=selectable,
                   caption=caption, stacked=True)


# ------------------------------------------------------------------------------- banners


def _banners(lesson, sid: str, res: bridge.BridgeResult, mode: str, x: float, v: dict) -> None:
    by_id = {b.id: b for b in lesson.break_it}
    if sid == "quarter" and x >= 0.04:
        break_it_banner(by_id["big_strain"])
    if sid == "temperature" and mode == "quarter" and v["dT"] > 0:
        apparent = v["alpha"] / 100 * v["dT"] / v["G"]
        b = by_id["temp_quarter"]
        st.markdown(f"**Apparent strain right now:** {apparent * 1e6:,.0f} µε from heat alone "
                    f"(α·ΔT / G = {v['alpha']:.2f} %/K × {v['dT']} K / {v['G']:g}).")
        break_it_banner(b)
    if sid == "loading" and not math.isinf(res.R_meter) and res.R_meter < 10 * res.arms.R1 * 1.0001:
        break_it_banner(by_id["loading"])


# ------------------------------------------------------------------------------- consequence plots


def _consequence(sid: str, res: bridge.BridgeResult, mode: str, x: float, v: dict) -> None:
    with st.container(key="consequence"):
        if sid == "build":
            layout.kicker("Consequence — output as R₄ moves away from balance")
            r4 = np.linspace(0.5, 2.0, 151)
            r3 = v["R3"]
            out = [bridge.solve(res.V0, bridge.Arms(1e3, 1e3, r3 * 1e3, k * 1e3)).Vout for k in r4]
            fig = plots.figure("left bottom resistor R₄ (kΩ)", "bridge output V₂ − V₁ (V)", (0.45, 2.05), (-1.8, 1.8))
            plots.line(fig, r4, out, f"V₀ = {res.V0:g} V", color=plots.COLORS["ink"])
            plots.point(fig, v["R4"], res.Vout, format_si(res.Vout, "V", 3))
            fig.add_vline(x=r3, line=dict(color=plots.COLORS["muted"], dash="dash"))
            fig.add_annotation(x=r3, y=1.65, text="balanced: R₄ = R₃·R₁/R₂", showarrow=False, xanchor="left", xshift=6,
                               font=dict(size=11, color=plots.COLORS["muted"]))
            plots.show(fig, key="wb_build_plot")
            st.caption("Zero output whenever both dividers have the same ratio — not only when all four are equal.")
            return

        if sid in ("quarter", "full"):
            layout.kicker("Consequence — output vs relative change ΔR/R (fixed axes)")
            xmax = v["G"] * EPS_MAX_UE * 1e-6
            xs = np.linspace(0, xmax, 200)
            V0 = res.V0
            ymin = -xmax * V0_MAX * 1e3 * 1.08
            fig = plots.figure("relative change of each gauge ΔR/R (%)", "V₂ − V₁ (mV)", (0, xmax * 100 * 1.02),
                               (ymin, -ymin * 0.06))
            plots.line(fig, xs * 100, [bridge.quarter_exact(V0, t) * 1e3 for t in xs], "quarter, exact",
                       color=plots.COLORS["ink"], label_y_shift=8)
            plots.line(fig, xs * 100, [bridge.quarter_approx(V0, t) * 1e3 for t in xs], "quarter, −¼(ΔR/R)V₀ approx.",
                       color=plots.COLORS["volt"], dash="dash", label_y_shift=-8)
            plots.line(fig, xs * 100, [bridge.full_output(V0, t) * 1e3 for t in xs], "full bridge (exact)",
                       color=plots.COLORS["plus"], dash="dashdot")
            plots.point(fig, x * 100, res.Vout * 1e3, format_si(res.Vout, "V", 3),
                        color=plots.COLORS["plus"] if mode == "full" else plots.COLORS["ink"])
            plots.show(fig, key=f"wb_{sid}_plot")
            q_val = bridge.quarter_exact(V0, x)
            f_val = bridge.full_output(V0, x)
            c1, c2, c3 = st.columns(3)
            c1.metric("Quarter bridge", format_si(q_val, "V", 4))
            c2.metric("Full bridge", format_si(f_val, "V", 4))
            c3.metric("Full ÷ quarter", f"{f_val / q_val:.3f}×" if q_val else "—",
                      help="Exactly 4 for small ΔR/R; slightly less as the quarter bridge's nonlinearity grows.")
            if sid == "quarter" and v.get("err"):
                fig2 = plots.figure("ΔR/R (%)", "approximation error (%)", (0, xmax * 100 * 1.02), (0, xmax * 50 * 1.1),
                                    height=230)
                plots.line(fig2, xs * 100, xs * 50, "error = (ΔR/R)/2", color=plots.COLORS["volt"])
                plots.point(fig2, x * 100, x * 50, f"{x * 50:.3g} %")
                plots.show(fig2, key="wb_err_plot")
            return

        if sid == "temperature":
            layout.kicker("Consequence — output vs temperature rise (strain held fixed)")
            dts = np.arange(0, 51)
            alpha = v["alpha"] / 100
            V0, R = res.V0, 350.0
            qv = [bridge.simulate("quarter", V0, R, x, alpha * t).Vout * 1e3 for t in dts]
            fv = [bridge.simulate("full", V0, R, x, alpha * t).Vout * 1e3 for t in dts]
            # fixed for the primary controls (V₀ up to its max, ΔT up to 50 K, current strain);
            # only the advanced α control rescales the axis
            lo = min(bridge.simulate("quarter", V0_MAX, R, x, max(alpha, 1e-4) * 50).Vout * 1e3, -1.0)
            fig = plots.figure("gauge temperature rise ΔT (K)", "V₂ − V₁ (mV)", (0, 52), (lo * 1.05, max(-lo * 0.15, 1)))
            plots.line(fig, dts, qv, "quarter bridge", color=plots.COLORS["ink"])
            plots.line(fig, dts, fv, "full bridge", color=plots.COLORS["plus"], dash="dashdot", label_y_shift=10)
            plots.point(fig, v["dT"], res.Vout * 1e3, format_si(res.Vout, "V", 3))
            plots.show(fig, key="wb_temp_plot")
            st.caption("Flat line = compensated. The quarter bridge's slope is pure temperature error.")
            return

        if sid == "loading":
            layout.kicker("Consequence — reading as a fraction of the ideal value")
            ratios = np.logspace(0, 4, 120)
            ideal = bridge.solve(res.V0, res.arms).Vout
            R = v["R"]
            if abs(ideal) < 1e-15:
                st.info("Set a non-zero strain to see the loading effect (a balanced bridge reads 0 V either way).")
                return
            frac = [bridge.solve(res.V0, res.arms, k * R).Vout / ideal * 100 for k in ratios]
            fig = plots.figure("meter input resistance R_in / R", "reading (% of ideal)", (0, 4), (0, 105))
            fig.update_xaxes(type="log", range=[0, 4.05])
            plots.line(fig, ratios, frac, "simulated", color=plots.COLORS["ink"], x_log=True, label_y_shift=10)
            plots.line(fig, ratios, [k / (k + 1) * 100 for k in ratios], "R_in/(R_in+R) estimate",
                       color=plots.COLORS["volt"], dash="dash", label_y_shift=-12, x_log=True)
            if not math.isinf(v["rin"]):
                plots.point(fig, v["rin"], res.Vout / ideal * 100, f"{res.Vout / ideal * 100:.1f} %")
            plots.show(fig, key="wb_load_plot")
            st.caption(f"Ideal meter → 100 %. Current through the meter now: {format_si(res.I_meter, 'A')}.")
