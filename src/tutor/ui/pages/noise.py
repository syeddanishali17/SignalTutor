"""Noise Lab (C13, milestone M4).

One seeded signal generator (tutor.sim.noise) feeds every step: the clean signal, white
or 1/f noise, the time traces, the Welch PSD estimate and the band-limited check all come
from the same arrays. Intuition first (what noise looks like), then numbers (variance,
RMS), then the frequency view (spectrum, PSD), then the exam maths (band integral, the
1/2π and factor-2 traps).
"""

from __future__ import annotations

import math

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from tutor.sim import noise as nz
from tutor.sim.units import format_si
from tutor.ui import state
from tutor.ui.components import controls as C
from tutor.ui.components import equation, inspector, layout, plots
from tutor.ui.components.derivation import stepper
from tutor.ui.components.feedback import break_it_banner
from tutor.ui.pages import _lesson as L
from tutor.ui.svg import noise_figures as F

LESSON_ID = "noise_lab"
SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
S0_CHOICES = [1e-6, 3e-6, 1e-5, 3e-5, 1e-4]  # V²/Hz, white
S1_CHOICES = [1e-5, 3e-5, 1e-4, 3e-4, 1e-3]  # V², 1/f: S(f) = S1/f
F_EDGES = [1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0, 2000.0, 5000.0]
SPEC_F = (50.0, 120.0, 300.0)

DEFAULTS = {
    "noise": {"mode": "additive", "level": 0.06},
    "stats": {"level": 0.1, "n": 1000},
    "spectrum": {"a1": 1.0, "a2": 0.4, "a3": 0.2, "level": 0.2},
    "psd": {"kind": "white", "level": 1e-5, "asd": False},
    "band": {"kind": "white", "level": 1e-5, "f1": 100.0, "f2": 1000.0},
    "sides": {"kind": "white", "f1": 100.0, "f2": 400.0},
}


def _sci(v: float, unit: str = "") -> str:
    """1e-05 → '1×10⁻⁵ unit' (3×10⁻⁶, …) — readable without LaTeX."""
    if v == 0:
        return f"0 {unit}".strip()
    e = math.floor(math.log10(abs(v)))
    m = v / 10**e
    mant = f"{m:.3g}"
    body = f"10{str(e).translate(SUP)}" if mant == "1" else f"{mant}×10{str(e).translate(SUP)}"
    return f"{body} {unit}".strip()


def _tex_sci(v: float) -> str:
    if v == 0:
        return "0"
    e = math.floor(math.log10(abs(v)))
    m = v / 10**e
    if abs(m - round(m)) < 1e-9 and round(m) == 1:
        return rf"10^{{{e}}}"
    return rf"{m:.3g}\times10^{{{e}}}"


def render() -> None:
    lesson = state.bundle().lessons[LESSON_ID]
    layout.page_header("Noise Lab", "Noise and power spectral density",
                       "From random wiggles to the PSD, band-limited noise and the factor-2 trap.")
    scenes = {s.id: s for s in lesson.scenes}
    deep = st.query_params.get("scene")
    if "noise_scene" not in st.session_state:
        st.session_state["noise_scene"] = deep if deep in scenes else lesson.scenes[0].id
    layout.sensor_map(lesson.map_stage, lesson.map_note)
    sid = st.segmented_control("Step", list(scenes), format_func=lambda i: scenes[i].short, key="noise_scene",
                               required=True)
    scene = scenes[sid]
    st.markdown(f"## {scene.title}")
    inspector.term_chips(scene.concepts)
    {"noise": _noise, "stats": _stats, "spectrum": _spectrum, "psd": _psd, "band": _band,
     "sides": _sides}[sid](lesson, scene)


def _setup(scene) -> tuple[str, dict]:
    scope = f"nz_{scene.id}"
    defaults = DEFAULTS[scene.id]
    C.ensure_defaults(scope, defaults)
    return scope, defaults


def _banner(lesson, bid: str) -> None:
    break_it_banner({b.id: b for b in lesson.break_it}[bid])


def _derive(scope: str, options: list[str]):
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


# --- the one generator ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False, max_entries=16)
def _unit_white(n: int, seed: int = 11) -> np.ndarray:
    """Zero-mean, unit-σ white noise (seeded: the same draw every rerun)."""
    x = nz.white(n, 2.0, 1.0, seed)  # σ² = S0·fs/2 = 1
    return x / np.std(x)


@st.cache_data(show_spinner=False, max_entries=32)
def _noise_record(kind: str, level: float, seed: int = 21) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(x, f, S_welch) for white (level = S0) or 1/f (level = S1) noise at the generator's FS."""
    if kind == "white":
        x = nz.white(nz.N, nz.FS, level, seed)
    else:
        x = nz.pink(nz.N, nz.FS, level, seed)
    f, S = nz.welch_psd(x, nperseg=4096)
    return x, f, S


def _model(kind: str, level: float):
    if kind == "white":
        return lambda f: level + 0 * np.asarray(f, dtype=float)
    return lambda f: level / np.maximum(np.asarray(f, dtype=float), 0.5)


def _band_model_power(kind: str, level: float, f1: float, f2: float) -> float:
    return nz.white_band_power(level, f1, f2) if kind == "white" else float(nz.pink_band_power(level, f1, f2))


# ------------------------------------------------------------------------------- 0 · noise


def _noise(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    mode, level = C.value(scope, "mode"), C.value(scope, "level")
    t = np.linspace(0, 1.0, 1200)
    clean = nz.clean_measurement(t)
    n = level * _unit_white(len(t))
    out = nz.compose(clean, n, mode)
    res = L.resolved(scope, scene)
    L.main_row(scope, scene, F.chain(clean, n, out, mode=mode, selected=res.highlight,
                                     noise_label="noise n(t)" if mode == "additive" else "relative noise n(t)",
                                     noise_range=(-0.5, 0.5)))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([2.6, 3, 1])
        with c1:
            C.segmented(scope, "mode", "How the noise enters", ["additive", "multiplicative"],
                        fmt=lambda m: "additive  V + n" if m == "additive" else "multiplicative  V·(1 + n)",
                        disabled=not unlocked)
        with c2:
            C.slider(scope, "level", "noise size σ (in V, or relative for ×)", 0.0, 0.15, 0.01, "%.2f",
                     disabled=not unlocked)
        with c3:
            C.reset_button(scope, defaults)
    k = len(t) // 5
    s_lo = float(np.std(out[:k] - clean[:k]))
    s_hi = float(np.std(out[-k:] - clean[-k:]))
    law = r"[[Vm]] = [[V]] + [[n]]" if mode == "additive" else r"[[Vm]] = [[V]]\,\big(1 + [[n]]\big)"
    equation.strip(
        scope, scene, law=law,
        numbers=rf"\sigma \text{{ at }} {clean[:k].mean():.2f}\,\text{{V}}: {s_lo * 1e3:.3g}\,\text{{mV}}",
        result=rf"\sigma \text{{ at }} {clean[-k:].mean():.2f}\,\text{{V}}: {s_hi * 1e3:.3g}\,\text{{mV}}",
        selectable=["Vm", "V", "n"],
        caption=("Additive: the same spread everywhere." if mode == "additive" else
                 f"Multiplicative: the spread grows with the signal ({s_hi / max(s_lo, 1e-12):.1f}× larger at the top)."),
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — the measured output over time (fixed axes)")
        fig = plots.figure("time (s)", "voltage (V)", (0, 1.0), (-0.2, 1.6), height=280)
        plots.line(fig, t, out, "measured", color=plots.COLORS["cur"], width=1.2, label_y_shift=10)
        plots.line(fig, t, clean, "clean V(t)", color=plots.COLORS["ink"], width=3, label_y_shift=-12)
        plots.show(fig, key="nz_noise_plot")
        c1, c2 = st.columns(2)
        c1.metric("Spread (σ) on the first fifth", format_si(s_lo, "V", 2))
        c2.metric("Spread (σ) on the last fifth", format_si(s_hi, "V", 2))
    L.deeper(scope, lesson, scene)


# ------------------------------------------------------------------------------- 1 · stats


def _stats(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    level, n = C.value(scope, "level"), int(C.value(scope, "n"))
    x = level * _unit_white(10000, 31)[:n]
    mean, var = float(np.mean(x)), float(np.var(x))
    sd, r = math.sqrt(var), nz.rms(x)
    within = float(np.mean(np.abs(x - mean) <= sd)) if sd > 0 else 1.0
    res = L.resolved(scope, scene)
    L.main_row(scope, scene, F.chain(np.zeros(min(n, 600)), x[:600], x[:600], selected=res.highlight, show_sigma=True,
                                     out_range=(-0.6, 0.6), noise_range=(-0.6, 0.6), noise_label="noise n(t)"))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3 = st.columns([3, 2.4, 1])
        with c1:
            C.slider(scope, "level", "noise size (true σ)", 0.01, 0.2, 0.01, "%.2f V", disabled=not unlocked)
        with c2:
            C.segmented(scope, "n", "number of samples N", [100, 1000, 10000], fmt=lambda v: f"{v:,}",
                        disabled=not unlocked)
        with c3:
            C.reset_button(scope, defaults)
    equation.strip(
        scope, scene,
        law=(r"[[sigma2]] = \frac{1}{N}\sum_i \left(x_i - [[mean]]\right)^2,\qquad [[sigma]] = \sqrt{[[sigma2]]},"
             r"\qquad [[rms]] = \sqrt{\tfrac{1}{N}\textstyle\sum_i x_i^2}"),
        law_beginner=(r"[[sigma2]] = \underbrace{\frac{1}{N}\sum_i}_{\text{average of}} "
                      r"\underbrace{\left(x_i - [[mean]]\right)^2}_{\text{squared distance from the mean}},"
                      r"\qquad [[sigma]] = \sqrt{[[sigma2]]}"),
        numbers=rf"\bar x = {mean * 1e3:.2f}\,\text{{mV}},\quad \sigma^2 = {var * 1e6:.4g}\,\text{{mV}}^2",
        result=rf"\sigma = {sd * 1e3:.3g}\,\text{{mV}},\ V_\text{{rms}} = {r * 1e3:.3g}\,\text{{mV}}",
        selectable=["sigma2", "sigma", "mean", "rms"],
        caption=f"{within * 100:.0f} % of the {n:,} samples lie within ±σ of the mean (≈ 68 % for Gaussian noise). "
                "More samples → the estimate of σ settles at the true value.",
        stacked=True,
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — the distribution of the readings (fixed axes)")
        bins = np.linspace(-0.6, 0.6, 61)
        hist, edges = np.histogram(x, bins=bins, density=True)
        centers = (edges[:-1] + edges[1:]) / 2
        fig = go.Figure()
        fig.add_bar(x=centers, y=hist, marker_color=plots.COLORS["cur"], opacity=0.55, width=0.019)
        if level > 0:
            g = np.exp(-centers**2 / (2 * level**2)) / (level * math.sqrt(2 * math.pi))
            fig.add_scatter(x=centers, y=g, mode="lines", line=dict(color=plots.COLORS["ink"], width=2.5),
                            hoverinfo="skip")
        base = plots.figure("reading x (V)", "how often (density)", (-0.6, 0.6), (0, 42), height=270)
        fig.update_layout(base.layout)
        for v_, col in ((mean, plots.COLORS["ink"]), (mean + sd, plots.COLORS["volt"]), (mean - sd, plots.COLORS["volt"])):
            fig.add_vline(x=v_, line=dict(color=col, dash="dash", width=2))
        fig.add_annotation(x=mean + sd, y=40, text="+σ", showarrow=False, xshift=12, font=dict(color=plots.COLORS["volt"]))
        fig.add_annotation(x=mean - sd, y=40, text="−σ", showarrow=False, xshift=-12, font=dict(color=plots.COLORS["volt"]))
        plots.show(fig, key="nz_hist")
        st.caption("Bars: the measured readings. Line: the Gaussian bell with the true σ. The mean sits at 0 — "
                   "only the squares (variance) capture the size.")
    L.deeper(scope, lesson, scene)


# ------------------------------------------------------------------------------- 2 · spectrum


def _spectrum(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    a = [C.value(scope, k) for k in ("a1", "a2", "a3")]
    level = C.value(scope, "level")
    fs, n = 2000.0, 8000
    t = np.arange(n) / fs
    comps = [nz.sine(t, ak, fk) for ak, fk in zip(a, SPEC_F)]
    noise = level * _unit_white(n, 41)
    x = sum(comps) + noise
    f, A = nz.amplitude_spectrum(x, fs)
    floor = float(np.median(A[(f > 10) & (f < 500)])) * 3 if level > 0 else 0.0
    sel = inspector.selected(scope)
    res = L.resolved(scope, scene)
    L.main_row(scope, scene, F.spectrum(list(zip(SPEC_F, a)), selected=res.highlight, floor=floor))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        a_cols = st.columns(3)
        for i, (k, fk) in enumerate(zip(("a1", "a2", "a3"), SPEC_F)):
            with a_cols[i]:
                C.slider(scope, k, f"A{'₁₂₃'[i]} · sine at {fk:g} Hz", 0.0, 1.0, 0.05, "%.2f V", disabled=not unlocked)
        n_col, r_col = st.columns([4, 1])
        with n_col:
            C.slider(scope, "level", "noise σ", 0.0, 0.5, 0.05, "%.2f V", disabled=not unlocked)
        with r_col:
            C.reset_button(scope, defaults)
    equation.strip(
        scope, scene,
        law=r"x(t) = \sum_k [[A]]\,\sin\!\left(2\pi\,[[f]]\,t\right) + n(t)",
        numbers=(rf"= {a[0]:.2f}\sin(2\pi\cdot50t) + {a[1]:.2f}\sin(2\pi\cdot120t) + {a[2]:.2f}\sin(2\pi\cdot300t)"
                 r" + n(t)"),
        result=rf"{sum(1 for v in a if v > 0)}\ \text{{lines}} + \text{{floor}}",
        selectable=["A", "f"],
        caption="Click a line in the picture (or a part in the inspector) to see that sine on its own in the time "
                "trace below.",
        stacked=True,
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — the same signal in time, with the selected component drawn on its own")
        m = t <= 0.1
        fig = plots.figure("time (ms)", "voltage (V)", (0, 100), (-2.6, 2.6), height=260)
        plots.line(fig, t[m] * 1e3, x[m], "x(t)", color=plots.COLORS["muted"], width=1.4)
        idx = {"p1": 0, "p2": 1, "p3": 2}.get(sel or "")
        if idx is not None:
            # Label inside the window. At the right edge the 120 Hz tag was clipped.
            plots.line(fig, t[m] * 1e3, comps[idx][m], f"{SPEC_F[idx]:g} Hz",
                       color=(plots.COLORS["ink"], plots.COLORS["cur"], plots.COLORS["volt"])[idx], width=3,
                       label_at=42, label_y_shift=-14)
        plots.show(fig, key="nz_spec_time")
        if idx is None:
            st.caption("Tip: select Line 1, 2 or 3 in the inspector — its sine appears here.")
        else:
            st.caption(f"The {SPEC_F[idx]:g} Hz line is this sine: {SPEC_F[idx] * 0.1:g} full periods in 100 ms, "
                       f"amplitude {a[idx]:.2f} V.")
    L.deeper(scope, lesson, scene)


# ------------------------------------------------------------------------------- 3 · psd


def _psd(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    kind = C.value(scope, "kind")
    if st.session_state.get(C.wkey(scope, "level")) not in (S0_CHOICES if kind == "white" else S1_CHOICES):
        st.session_state[C.wkey(scope, "level")] = 1e-5 if kind == "white" else 1e-4
    unlocked = L.top(scope, lesson, scene)
    level, asd = C.value(scope, "level"), C.value(scope, "asd")
    x, f, S = _noise_record(kind, level)
    model = _model(kind, level)
    res = L.resolved(scope, scene)
    svg = F.psd_view(model, estimate=(f, S), selected=res.highlight, s_lo=1e-9, s_hi=1e-3,
                     label="white" if kind == "white" else "1/f",
                     s0_label=(f"S₀ = {_sci(level, 'V²/Hz')}" if kind == "white" else f"S₁/f, S₁ = {_sci(level, 'V²')}"))
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2.2, 3, 2, 1])
        with c1:
            C.segmented(scope, "kind", "Noise shape", ["white", "pink"],
                        fmt=lambda k: "white (flat)" if k == "white" else "1/f", disabled=not unlocked)
        with c2:
            choices = S0_CHOICES if kind == "white" else S1_CHOICES
            C.select_slider(scope, "level", "S₀ · white level" if kind == "white" else "S₁ · 1/f level", choices,
                            lambda v: _sci(v, "V²/Hz" if kind == "white" else "V²"), disabled=not unlocked)
        with c3:
            C.toggle(scope, "asd", "Show as spectral amplitude √S", disabled=not unlocked)
        with c4:
            C.reset_button(scope, defaults)
    at = [10.0, 100.0, 1000.0]
    vals = [float(model(np.array([v]))[0]) for v in at]
    if kind == "white":
        law, numbers = r"[[S]] = [[S0]]", rf"S = {_tex_sci(level)}\,\text{{V}}^2/\text{{Hz}} \text{{ at every }} f"
    else:
        law = r"[[S]] = \frac{[[S1]]}{[[f]]}"
        numbers = r",\ ".join(rf"S({v:g}\,\text{{Hz}}) = {_tex_sci(s)}" for v, s in zip(at, vals))
    asd_1k = math.sqrt(vals[2])
    equation.strip(
        scope, scene, law=law, numbers=numbers,
        result=rf"X_V\big|_{{1\,\text{{kHz}}}} = {asd_1k * 1e6:.3g}\,\mu\text{{V}}/\sqrt{{\text{{Hz}}}}",
        selectable=["S", "S0" if kind == "white" else "S1", "f", "X"],
        caption=("Units: V²/Hz is a POWER per hertz. Its square root, the spectral amplitude, is what datasheets "
                 "quote (V/√Hz)."),
        stacked=True,
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — estimated from the generated noise vs the model (fixed log axes)")
        c1, c2 = st.columns([3, 2])
        with c1:
            fig = plots.figure("frequency f (Hz)", "√S (V/√Hz)" if asd else "S (V²/Hz)", (0, 3.7),
                               (-4.6, -1.4) if asd else (-9, -3), height=290)
            fig.update_xaxes(type="log", range=[0, 3.7])
            fig.update_yaxes(type="log", range=[-4.6, -1.4] if asd else [-9, -3])
            m = f > 0
            yS = np.sqrt(S[m]) if asd else S[m]
            plots.line(fig, f[m], yS, "estimate (Welch)", color=plots.COLORS["muted"], width=1, x_log=True)
            ff = np.logspace(0, 3.7, 200)
            ym = np.sqrt(model(ff)) if asd else model(ff)
            fig.add_scatter(x=ff, y=ym, mode="lines", line=dict(color=plots.COLORS["ink"], width=3), hoverinfo="skip")
            plots.show(fig, key="nz_psd_plot")
            st.caption("Grey: what the noise really contains (estimated). Black: the model. Log axes: 1/f noise is a "
                       "straight line falling one decade per decade.")
        with c2:
            tt = nz.time_axis(800, nz.FS)
            fig = plots.figure("time (ms)", "noise (V)", (0, 80), (-1.2, 1.2), height=290)
            plots.line(fig, tt * 1e3, x[:800], "n(t)", color=plots.COLORS["plus"], width=1.2)
            plots.show(fig, key="nz_psd_time")
            st.caption("White noise looks uniformly jagged; 1/f noise wanders slowly — most of its power is at low f.")
    L.deeper(scope, lesson, scene)


# ------------------------------------------------------------------------------- 4 · band


def _band(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    kind = C.value(scope, "kind")
    if st.session_state.get(C.wkey(scope, "level")) not in (S0_CHOICES if kind == "white" else S1_CHOICES):
        st.session_state[C.wkey(scope, "level")] = 1e-5 if kind == "white" else 1e-4
    unlocked = L.top(scope, lesson, scene)
    level, f1, f2 = C.value(scope, "level"), C.value(scope, "f1"), C.value(scope, "f2")
    if f2 <= f1:  # the learner crossed the edges: use the band between them (never empty)
        f1, f2 = (f2, f1) if f2 < f1 else (f1, f1 * 2)
    x, f, S = _noise_record(kind, level)
    model = _model(kind, level)
    p_model = _band_model_power(kind, level, f1, f2)
    p_est = nz.band_power(f, S, f1, f2)
    p_time = nz.variance(nz.bandpass(x, nz.FS, f1, f2))
    p_flat = float(model(np.array([f1]))[0]) * (f2 - f1)
    p_lecture = 2 * math.pi * p_flat
    vrms = math.sqrt(p_model)
    res = L.resolved(scope, scene)
    svg = F.psd_view(model, band=(f1, f2), selected=res.highlight, s_lo=1e-9, s_hi=1e-3,
                     label="white" if kind == "white" else "1/f",
                     s0_label=(f"S₀ = {_sci(level, 'V²/Hz')}" if kind == "white" else f"S₁ = {_sci(level, 'V²')}"),
                     area_label=f"σ² = {_sci(p_model, 'V²')}")
    L.main_row(scope, scene, svg)
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2, 2.2, 2, 2])
        with c1:
            C.segmented(scope, "kind", "Noise shape", ["white", "pink"],
                        fmt=lambda k: "white" if k == "white" else "1/f", disabled=not unlocked)
        with c2:
            C.select_slider(scope, "level", "level", S0_CHOICES if kind == "white" else S1_CHOICES,
                            lambda v: _sci(v, "V²/Hz" if kind == "white" else "V²"), disabled=not unlocked)
        with c3:
            C.select_slider(scope, "f1", "f₁ · lower edge", F_EDGES[:-1], lambda v: f"{v:g} Hz", disabled=not unlocked)
        with c4:
            C.select_slider(scope, "f2", "f₂ · upper edge", F_EDGES[1:], lambda v: f"{v:g} Hz", disabled=not unlocked)
        C.reset_button(scope, defaults)
    if kind == "white":
        numbers = rf"= {_tex_sci(level)}\,\tfrac{{\text{{V}}^2}}{{\text{{Hz}}}}\times({f2:g} - {f1:g})\,\text{{Hz}}"
    else:
        numbers = rf"= {_tex_sci(level)}\,\text{{V}}^2\times\ln\frac{{{f2:g}}}{{{f1:g}}}"
    equation.strip(
        scope, scene,
        law=r"[[sigma2]] = \int_{[[f1]]}^{[[f2]]} [[S]]\,[[df]]",
        law_beginner=(r"[[sigma2]] = \underbrace{\int_{[[f1]]}^{[[f2]]} [[S]]\,[[df]]}_{\text{area under the PSD in the band}}"
                      + (r" \overset{\text{white}}{=} [[S0]]\,([[f2]] - [[f1]])" if kind == "white" else "")),
        numbers=numbers,
        result=(rf"\begin{{aligned}}&\sigma^2 = {_tex_sci(p_model)}\,\text{{V}}^2\\"
                rf"&V_\text{{rms}} = {vrms * 1e3:.3g}\,\text{{mV}}\end{{aligned}}"),
        selectable=["sigma2", "S", "df", "f1", "f2", "S0", "rms"],
        caption=(f"The lecture's form S(ω)·(ω₂ − ω₁) would give {_sci(p_lecture, 'V²')} — {2 * math.pi:.2f}× too "
                 "large (K4), and it assumes white noise."),
        stacked=True,
    )
    if kind == "pink":
        _banner(lesson, "flat_shortcut")
    with st.container(key="consequence"):
        layout.kicker("Consequence — four ways to get the band power, and the band-limited noise itself")
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        c1.metric("Area under the model", _sci(p_model, "V²"))
        c2.metric("Area under the estimate", _sci(p_est, "V²"), help="Welch PSD of the generated noise, integrated.")
        c3.metric("Variance of the filtered noise", _sci(p_time, "V²"),
                  help="Keep only f₁…f₂ of the time signal and measure its variance directly.")
        c4.metric("Rectangle S(f₁)·Δf", _sci(p_flat, "V²"),
                  help="Height at f₁ times the width. Exact for white noise; far too big for 1/f.")
        if kind != "white":
            st.caption(f"For 1/f noise that rectangle is {p_flat / p_model:.1f}× too big. "
                       "It is the flat-spectrum shortcut, not the band power.")
        xb = nz.bandpass(x, nz.FS, f1, f2)
        tt = nz.time_axis(2000, nz.FS)
        fig = plots.figure("time (ms)", "band-limited noise (V)", (0, 200), (-1.0, 1.0), height=240)
        plots.line(fig, tt * 1e3, xb[:2000], "noise in [f₁, f₂]", color=plots.COLORS["volt"], width=1.2)
        for yv in (vrms, -vrms):
            fig.add_hline(y=yv, line=dict(color=plots.COLORS["ink"], dash="dash"))
        plots.show(fig, key="nz_band_time")
        st.caption(f"Dashed: ± V_rms = ±{vrms * 1e3:.3g} mV from the area. The filtered noise really wiggles that much.")
    L.deeper(scope, lesson, scene, derive=_derive(scope, ["band_power"]))


# ------------------------------------------------------------------------------- 5 · sides


def _sides(lesson, scene) -> None:
    scope, defaults = _setup(scene)
    unlocked = L.top(scope, lesson, scene)
    kind, f1, f2 = C.value(scope, "kind"), C.value(scope, "f1"), C.value(scope, "f2")
    if f2 <= f1:
        f1, f2 = min(f1, f2), max(f1, f2) + 50
    S0, fmax = 1e-5, 1000.0
    model = _model(kind, S0 if kind == "white" else 1e-3)
    ff = np.linspace(0, fmax, 4001)
    S = model(np.maximum(ff, 0.5))
    fb = np.linspace(f1, f2, 2001)
    one = float(np.trapezoid(model(fb), fb))
    f_two, S_two = nz.two_sided(ff, S)
    m2 = ((f_two >= f1) & (f_two <= f2)) | ((f_two <= -f1) & (f_two >= -f2))
    two_all = float(np.trapezoid(np.where(m2, S_two, 0), f_two))
    two_pos = two_all / 2
    res = L.resolved(scope, scene)
    L.main_row(scope, scene, F.sides_view(fmax, kind=kind, selected=res.highlight, band=(f1, f2)))
    with st.container(key="tray"):
        L.tray_header(not unlocked)
        c1, c2, c3, c4 = st.columns([2.2, 2.6, 2.6, 1])
        with c1:
            C.segmented(scope, "kind", "Noise shape", ["white", "pink"],
                        fmt=lambda k: "white" if k == "white" else "1/f", disabled=not unlocked)
        with c2:
            C.slider(scope, "f1", "f₁", 0.0, 900.0, 50.0, "%.0f Hz", disabled=not unlocked)
        with c3:
            C.slider(scope, "f2", "f₂", 100.0, 1000.0, 50.0, "%.0f Hz", disabled=not unlocked)
        with c4:
            C.reset_button(scope, defaults)
    equation.strip(
        scope, scene,
        law=r"[[sigma2]] = \int_0^{\infty} [[S]]\,df = \int_{-\infty}^{\infty} [[Spp]]\,df,\qquad [[Spp]] = \tfrac12\,[[S]]",
        numbers=rf"\text{{one-sided: }} {_tex_sci(one)},\quad \text{{two-sided: }} {_tex_sci(two_all)}",
        result=r"\text{same } \sigma^2" if abs(one - two_all) <= 1e-3 * one else r"\text{differ!}",
        selectable=["sigma2", "S", "Spp"],
        caption=(f"Trap: the two-sided density integrated over f ≥ 0 only gives {_sci(two_pos, 'V²')} — exactly half. "
                 "Values in V² for the band f₁…f₂ shown in the picture."),
        stacked=True,
    )
    with st.container(key="consequence"):
        layout.kicker("Consequence — the three integrals side by side")
        c1, c2 = st.columns(2)
        c1.metric("One-sided S over f₁…f₂", _sci(one, "V²"))
        c2.metric("Two-sided S'' over ±(f₁…f₂)", _sci(two_all, "V²"))
        # No metric delta: Streamlit draws an arrow, which reads as "this value changed"
        # rather than "this reading is the mistake".
        with st.container(key="box-fail-factor2"):
            st.markdown(
                f"**Misconception, not a second formula.** Integrating the two-sided density "
                f"$S''$ over $f_1\\ldots f_2$ only (forgetting the negative frequencies) gives "
                f"**{_sci(two_pos, 'V²')}** — exactly half. That is the factor-of-2 trap."
            )
        st.markdown("Both conventions describe **the same noise**. Lab instruments and datasheets are one-sided; "
                    "the two-sided form appears in theory. Convert with $S = 2S''$ for $f \\ge 0$.")
        with st.container(key="box-note-lockin"):
            st.markdown("**Next: lock-in detection.** It measures a signal in a very narrow band around a known "
                        "frequency — exactly the band-power idea above. Its lesson follows once the lecture-3 "
                        "material is available; the demodulator building blocks are already in place.")
    L.deeper(scope, lesson, scene, derive=_derive(scope, ["psd_sides", "band_power"]))
