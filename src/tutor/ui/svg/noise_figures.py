"""Noise figures in the shared visual grammar.

* ``chain``    — clean signal ⊕/⊗ noise → measured output, with live sparklines drawn
  from the SAME arrays as the plots (ids: signal, noise, op, out, mean, sigma)
* ``psd_view`` — a PSD on log–log (or mirrored linear, two-sided) axes with the band
  [f₁, f₂] shaded (ids: curve, band, f1, f2, S0, units, half)
* ``spectrum`` — a signal as a sum of sines: one stem per component (ids: p1, p2, p3, floor)
"""

from __future__ import annotations

import math
from typing import Callable, Iterable

import numpy as np

from tutor.sim.units import format_si
from tutor.ui.svg.core import CURRENT, INK, MINUS, MUTED, PLUS, VOLT, Canvas, arrow, text, value_tag

LIGHT = "#ece7dc"


def _sel(selected: Iterable[str] | str | None) -> set[str]:
    if selected is None:
        return set()
    if isinstance(selected, str):
        return {selected}
    return set(selected)


def _poly(xs: np.ndarray, ys: np.ndarray, color: str, width: float = 2.0, extra: str = "") -> str:
    pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(xs, ys))
    return (f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linejoin="round" {extra}/>')


def _spark(c: Canvas, x0: float, y0: float, w: float, h: float, data: np.ndarray, lo: float, hi: float,
           color: str, n: int = 260) -> tuple[float, float]:
    """Draw a sparkline of ``data`` in the box; returns the (y of lo, scale) mapping."""
    d = np.asarray(data, dtype=float)
    if len(d) > n:
        idx = np.linspace(0, len(d) - 1, n).astype(int)
        d = d[idx]
    xs = np.linspace(x0 + 8, x0 + w - 8, len(d))
    span = (hi - lo) or 1.0
    ys = y0 + h - 10 - (np.clip(d, lo, hi) - lo) / span * (h - 20)
    c.add(_poly(xs, ys, color, 1.6))
    return y0 + h - 10, (h - 20) / span


def _box(c: Canvas, x: float, y: float, w: float, h: float, title: str, selected: bool) -> None:
    if selected:
        c.halo(x - 6, y - 6, w + 12, h + 12, 12)
    c.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ffffff" stroke="{INK}" stroke-width="1.6"/>')
    c.add(text(x + 10, y - 8, title, "tag", "start"))


def chain(clean: np.ndarray, noise: np.ndarray, out: np.ndarray, *, mode: str = "additive", selected=None,
          show_sigma: bool = False, noise_label: str = "noise", out_range: tuple[float, float] = (-0.2, 1.6),
          noise_range: tuple[float, float] | None = None) -> str:
    sel = _sel(selected)
    c = Canvas(780, 320, "Measurement with noise",
               "A clean sensor signal and random noise combine into the measured output.", uid="nz")
    # clean signal
    _box(c, 20, 36, 250, 110, "clean signal (what we want)", "signal" in sel)
    _spark(c, 20, 36, 250, 110, clean, *out_range, INK)
    # noise
    nr = noise_range or (float(-4 * np.std(noise) - 1e-12), float(4 * np.std(noise) + 1e-12))
    _box(c, 20, 186, 250, 110, noise_label, "noise" in sel)
    _spark(c, 20, 186, 250, 110, noise, *nr, PLUS)
    # operator
    ox, oy = 330.0, 166.0
    if "op" in sel:
        c.halo(ox - 34, oy - 34, 68, 68, 34)
    c.add(f'<circle cx="{ox}" cy="{oy}" r="24" fill="#fff" stroke="{INK}" stroke-width="2.2"/>')
    sym = "+" if mode == "additive" else "×"
    c.add(text(ox, oy + 9, sym, "lbl", "middle", 'style="font-size:28px"'))
    c.add(text(ox, oy + 50, "additive" if mode == "additive" else "multiplicative", "small"))
    c.add(arrow(270, 91, ox - 18, oy - 16, MUTED, 2, 9))
    c.add(arrow(270, 241, ox - 18, oy + 16, MUTED, 2, 9))
    c.add(arrow(ox + 24, oy, 392, oy, MUTED, 2, 9))
    # output
    _box(c, 400, 56, 360, 220, "measured output", "out" in sel)
    base, scale = _spark(c, 400, 56, 360, 220, out, *out_range, CURRENT)
    if show_sigma:
        m = float(np.mean(out))
        s = float(np.std(out))
        lo, hi = out_range
        for val, eid, col, dash in ((m, "mean", INK, "6 4"), (m + s, "sigma", VOLT, "4 4"), (m - s, "sigma", VOLT, "4 4")):
            if lo <= val <= hi:
                y = base - (val - lo) * scale
                if eid in sel:
                    c.halo(404, y - 7, 352, 14, 6)
                c.add(f'<line x1="408" y1="{y:.1f}" x2="752" y2="{y:.1f}" stroke="{col}" stroke-width="2" '
                      f'stroke-dasharray="{dash}"/>')
        c.add(text(756, base - (m - lo) * scale - 6, "mean", "tag", "end", f'style="fill:{INK}"'))
        if lo <= m + s <= hi:
            c.add(text(756, base - (m + s - lo) * scale - 6, "+σ", "tag", "end", f'style="fill:{VOLT}"'))
    return c.render()


# ----------------------------------------------------------------------------------- PSD


SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _hz(f: float) -> str:
    return f"{f / 1e3:g} kHz" if f >= 1e3 else f"{f:g} Hz"


def _pow10(v: float) -> str:
    return "10" + str(int(round(math.log10(v)))).translate(SUP)


def _decades(lo: float, hi: float) -> list[float]:
    return [10.0**k for k in range(math.floor(math.log10(lo)), math.ceil(math.log10(hi)) + 1)]


def psd_view(model: Callable[[np.ndarray], np.ndarray], *, f_lo: float = 1.0, f_hi: float = 5000.0,
             s_lo: float = 1e-8, s_hi: float = 1e-3, band: tuple[float, float] | None = None, selected=None,
             estimate: tuple[np.ndarray, np.ndarray] | None = None, label: str = "S(f)", s0_label: str = "",
             area_label: str = "", unit: str = "V²/Hz") -> str:
    """One-sided PSD on log–log axes; the band [f1, f2] is shaded under the curve."""
    sel = _sel(selected)
    c = Canvas(780, 380, "Power spectral density",
               "Noise power per hertz against frequency, on logarithmic axes. The shaded band's area is the "
               "noise power in that band.", uid="psd")
    X0, X1, Y0, Y1 = 96.0, 744.0, 34.0, 318.0
    lf0, lf1 = math.log10(f_lo), math.log10(f_hi)
    ls0, ls1 = math.log10(s_lo), math.log10(s_hi)

    def X(f):
        return X0 + (np.log10(f) - lf0) / (lf1 - lf0) * (X1 - X0)

    def Y(s):
        return Y1 - (np.log10(np.clip(s, s_lo, s_hi)) - ls0) / (ls1 - ls0) * (Y1 - Y0)

    c.add(f'<rect x="{X0}" y="{Y0}" width="{X1 - X0}" height="{Y1 - Y0}" fill="#ffffff" stroke="#b9b2a2"/>')
    for fd in _decades(f_lo, f_hi):
        if f_lo <= fd <= f_hi:
            x = float(X(fd))
            c.add(f'<line x1="{x:.1f}" y1="{Y0}" x2="{x:.1f}" y2="{Y1}" stroke="{LIGHT}"/>')
            c.add(text(x, Y1 + 18, _hz(fd), "small"))
    for sd in _decades(s_lo, s_hi):
        if s_lo <= sd <= s_hi:
            y = float(Y(sd))
            c.add(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{LIGHT}"/>')
            c.add(text(X0 - 6, y + 4, _pow10(sd), "small", "end"))
    if "units" in sel:
        c.halo(4, 130, 44, 130)
    c.add(f'<text x="22" y="{(Y0 + Y1) / 2}" transform="rotate(-90 22 {(Y0 + Y1) / 2})" text-anchor="middle" '
          f'class="small">S(f) in {unit}</text>')
    c.add(text((X0 + X1) / 2, Y1 + 40, "frequency f (log scale)", "small"))

    ff = np.logspace(lf0, lf1, 300)
    SS = model(ff)
    # shaded band
    if band:
        f1, f2 = band
        fb = np.logspace(math.log10(f1), math.log10(f2), 120)
        sb = model(fb)
        if "band" in sel:
            c.halo(float(X(f1)) - 6, Y0 + 2, float(X(f2) - X(f1)) + 12, Y1 - Y0 - 4, 6)
        pts = [(float(X(f1)), Y1)] + [(float(X(a)), float(Y(b))) for a, b in zip(fb, sb)] + [(float(X(f2)), Y1)]
        d = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        c.add(f'<polygon points="{d}" fill="{VOLT}" fill-opacity=".28" stroke="{VOLT}" stroke-width="1.4"/>')
        for fv, eid, name in ((f1, "f1", "f₁"), (f2, "f2", "f₂")):
            x = float(X(fv))
            if eid in sel:
                c.halo(x - 22, Y1 - 4, 44, 50)
            c.add(f'<line x1="{x:.1f}" y1="{Y0}" x2="{x:.1f}" y2="{Y1}" stroke="{VOLT}" stroke-width="2" '
                  f'stroke-dasharray="5 4"/>')
            c.add(text(x, Y0 - 8, f"{name} = {format_si(fv, 'Hz', 3)}", "tag", "middle", f'style="fill:{VOLT}"'))
        if area_label:
            xm = float(X(math.sqrt(f1 * f2)))
            value_tag(c, xm, Y1 - 18, area_label, "middle", color=VOLT)
    # estimate (thin, behind the model)
    if estimate is not None:
        fe, se = estimate
        m = (fe >= f_lo) & (fe <= f_hi) & (se > 0)
        if np.any(m):
            c.add(_poly(X(fe[m]), Y(se[m]), "#9aa3b2", 1.0, 'opacity=".8"'))
    if "curve" in sel:
        c.add(_poly(X(ff), Y(SS), "#ffe066", 11, 'opacity=".9"'))
    c.add(_poly(X(ff), Y(SS), INK, 3.0))
    c.add(text(X1 - 8, float(Y(SS[-1])) - 10, label, "lbl", "end"))
    if s0_label:
        y = float(Y(SS[len(SS) // 5]))
        if "S0" in sel:
            c.halo(X0 + 4, y - 30, 120, 26)
        c.add(text(X0 + 10, y - 10, s0_label, "tag", "start"))
    return c.render()


def sides_view(f_max: float, *, kind: str = "white", selected=None, band: tuple[float, float] | None = None) -> str:
    """One-sided S (f ≥ 0) above, two-sided S/2 (−f … f) below, on the same linear axes."""
    sel = _sel(selected)
    c = Canvas(780, 420, "One-sided and two-sided PSD",
               "The same noise drawn two ways: all power at positive frequencies, or half the height spread over "
               "positive and negative frequencies.", uid="sides")
    X0, X1 = 70.0, 750.0
    xm = (X0 + X1) / 2

    def X(f):
        return xm + f / f_max * (X1 - xm)

    def shape(f):
        f = np.maximum(np.abs(f), f_max / 400)
        return np.ones_like(f) if kind == "white" else (f_max / 20) / f

    smax = 1.15 * (1.0 if kind == "white" else float(shape(np.array([f_max / 400]))[0]) / 4)
    rows = (("one-sided  S(f)", 40.0, 180.0, 1.0, "one", 0.0), ("two-sided  S''(f) = S(|f|)/2", 230.0, 370.0, 0.5,
                                                                 "two", -f_max))
    for title, top, bot, factor, eid, fstart in rows:
        if eid in sel:
            c.halo(X0 - 8, top - 8, X1 - X0 + 16, bot - top + 16)
        c.add(f'<line x1="{X0}" y1="{bot}" x2="{X1}" y2="{bot}" stroke="{INK}" stroke-width="1.4"/>')
        c.add(f'<line x1="{xm}" y1="{top}" x2="{xm}" y2="{bot + 4}" stroke="{INK}" stroke-width="1.4"/>')
        c.add(text(X0, top + 2, title, "tag", "start"))
        fs = np.linspace(fstart, f_max, 400)
        h = np.minimum(shape(fs) * factor / smax, 1.0) * (bot - top - 16)
        ys = bot - h
        pts = [(float(X(fs[0])), bot)] + [(float(X(a)), float(b)) for a, b in zip(fs, ys)] + [(float(X(fs[-1])), bot)]
        d = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        col = CURRENT if eid == "one" else MINUS
        c.add(f'<polygon points="{d}" fill="{col}" fill-opacity=".20" stroke="{col}" stroke-width="2"/>')
        if band:
            f1, f2 = band
            for sgn in ((1,) if eid == "one" else (1, -1)):
                a, b = sorted((sgn * f1, sgn * f2))
                fb = np.linspace(a, b, 120)
                hb = np.minimum(shape(fb) * factor / smax, 1.0) * (bot - top - 16)
                pb = [(float(X(a)), bot)] + [(float(X(u)), float(bot - v)) for u, v in zip(fb, hb)] + [(float(X(b)), bot)]
                db = " ".join(f"{p:.1f},{q:.1f}" for p, q in pb)
                c.add(f'<polygon points="{db}" fill="{VOLT}" fill-opacity=".35" stroke="{VOLT}" stroke-width="1.2"/>')
        for fv in (-f_max, 0.0, f_max):
            if eid == "one" and fv < 0:
                continue
            c.add(text(float(X(fv)), bot + 16, f"{format_si(fv, 'Hz', 2) if fv else '0'}", "small"))
    if "half" in sel:
        c.halo(xm + 20, 236, 220, 30)
    c.add(text(xm + 30, 256, "half the height, twice the width", "tag", "start", f'style="fill:{MINUS}"'))
    c.add(text(xm + 30, 60, "all the power at f ≥ 0", "tag", "start", f'style="fill:{CURRENT}"'))
    return c.render()


# ----------------------------------------------------------------------------------- spectrum


def spectrum(components: list[tuple[float, float]], *, f_max: float = 500.0, a_max: float = 1.2, selected=None,
             floor: float = 0.0) -> str:
    """Stems at each component frequency, height = amplitude (V). ids p1, p2, p3 and floor."""
    sel = _sel(selected)
    c = Canvas(780, 330, "A signal as a sum of sines",
               "Each sine wave in the signal becomes one line in the spectrum, at its frequency, as tall as its "
               "amplitude.", uid="sp")
    X0, X1, Y0, Y1 = 80.0, 740.0, 40.0, 270.0
    c.add(f'<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="{INK}" stroke-width="1.6"/>')
    c.add(f'<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="{INK}" stroke-width="1.6"/>')
    for k in range(0, int(f_max) + 1, 100):
        x = X0 + k / f_max * (X1 - X0)
        c.add(f'<line x1="{x:.1f}" y1="{Y1}" x2="{x:.1f}" y2="{Y1 + 6}" stroke="{INK}"/>')
        c.add(text(x, Y1 + 22, f"{k} Hz", "small"))
    c.add(text((X0 + X1) / 2, Y1 + 46, "frequency", "small"))
    c.add(f'<text x="26" y="{(Y0 + Y1) / 2}" transform="rotate(-90 26 {(Y0 + Y1) / 2})" text-anchor="middle" '
          f'class="small">amplitude (V)</text>')
    if floor > 0:
        yf = Y1 - min(floor / a_max, 1.0) * (Y1 - Y0)
        if "floor" in sel:
            c.halo(X0 + 2, yf - 8, X1 - X0 - 4, Y1 - yf + 8, 4)
        c.add(f'<rect x="{X0 + 1}" y="{yf:.1f}" width="{X1 - X0 - 2}" height="{Y1 - yf:.1f}" fill="{PLUS}" '
              f'fill-opacity=".12"/>')
        c.add(text(X1 - 6, yf - 6, "noise floor (spread over all f)", "tag", "end", f'style="fill:{PLUS}"'))
    colors = (INK, CURRENT, VOLT)
    for i, (f, a) in enumerate(components, start=1):
        if a <= 0:
            continue
        x = X0 + f / f_max * (X1 - X0)
        y = Y1 - min(a / a_max, 1.0) * (Y1 - Y0)
        eid = f"p{i}"
        if eid in sel:
            c.halo(x - 26, y - 34, 52, Y1 - y + 38, 8)
        col = colors[(i - 1) % 3]
        c.add(f'<line x1="{x:.1f}" y1="{Y1}" x2="{x:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="5" '
              f'stroke-linecap="round"/>')
        c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{col}"/>')
        # Keep the frequency label inside the viewBox. A centred label on a tall
        # stem, or on a line near the right edge, was clipping (the 120 Hz line).
        label = f"{f:g} Hz · {format_si(a, 'V', 2)}"
        half = 3.7 * len(label)
        ly = y - 16
        anchor, lx = "middle", x
        if ly < 22:
            ly, anchor, lx = y + 16, "start", min(x + 10, X1 - 8)
        if anchor == "middle" and x - half < X0 + 6:
            anchor, lx = "start", x + 8
        elif x + half > X1 - 6:
            anchor, lx = "end", x - 8
        c.add(text(lx, ly, label, "tag", anchor, f'style="fill:{col}"'))
    return c.render()


FIGURES: dict[str, Callable[[list[str]], str]] = {
    "psd_band": lambda hl: psd_view(lambda f: 1e-5 + 0 * f, band=(100.0, 1000.0), selected=hl, label="white",
                                    s0_label="S₀"),
    "psd_sides": lambda hl: sides_view(1000.0, selected=hl, band=(100.0, 400.0)),
}
