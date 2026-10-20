"""Capacitive pressure sensor (lecture 1, p. 3–6): membrane → gap → C(x) → current.

Model and notation follow the lecture:

* membrane on two springs ``k``: force balance ``F = 2k·x = p·A`` → ``x = p·A/(2k)``
* parallel plates, gap ``d − x``: ``C(x) = εA/(d − x) = C₀/(1 − x/d)``, ``C₀ = εA/d``
* charge ``Q = V·C``, current ``I = dQ/dt = C·dV/dt + V·dC/dt``
* barometer (slow pressure, AC bias ``V₀ cos ωt``): ``I ≈ C·dV/dt = −V₀ ω C sin ωt``
* microphone (fast pressure, DC bias ``V_b``): ``I ≈ V_b·dC/dt = V_b·(dC/dx)·(dx/dt)``
* pull-in (supplemental physics; lecture marks ``x = d/3`` as the point of instability
  at constant voltage): spring ``2k·x`` against the plate attraction ``εA V²/(2(d − x)²)``

All functions are pure; arrays are numpy. The default geometry is an illustrative MEMS
membrane (1 mm², 2 µm gap, 2 × 2.5 kN/m springs): C₀ ≈ 4.4 pF, 1 kPa moves it by d/10, and
pull-in happens at ≈ 36.6 V.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

EPS0 = 8.8541878128e-12  # F/m


class InvalidState(ValueError):
    """A physically impossible request (plates touching, negative gap, …)."""


@dataclass(frozen=True)
class Geometry:
    A: float = 1e-6  # plate area, m² (1 mm²)
    d: float = 2e-6  # rest gap, m (2 µm)
    k: float = 2500.0  # stiffness of EACH of the two springs, N/m (lecture: F = 2k·x)
    eps_r: float = 1.0

    @property
    def eps(self) -> float:
        return EPS0 * self.eps_r

    @property
    def C0(self) -> float:
        return self.eps * self.A / self.d

    @property
    def k_eff(self) -> float:
        return 2.0 * self.k


DEFAULT = Geometry()


# --- statics -------------------------------------------------------------------------


def capacitance(eps: float, A: float, gap: float) -> float:
    """Parallel-plate capacitance εA/gap (fringe fields neglected)."""
    if gap <= 0:
        raise InvalidState("The plates touch: the gap must be larger than zero.")
    return eps * A / gap


def charge(C: float, V: float) -> float:
    return C * V


def displacement(p: float, g: Geometry = DEFAULT) -> float:
    """Lecture H_p-x: F = 2k·x = p·A  →  x = p·A/(2k)."""
    return p * g.A / g.k_eff


def h_px(g: Geometry = DEFAULT) -> float:
    """Transfer function pressure → displacement, A/(2k), in m/Pa."""
    return g.A / g.k_eff


def c_of_x(x, g: Geometry = DEFAULT):
    """C(x) = C₀/(1 − x/d). Works on scalars and arrays."""
    u = np.asarray(x, dtype=float) / g.d
    if np.any(u >= 1.0):
        raise InvalidState("x reached the gap d: the plates touch and C(x) has no finite value.")
    out = g.C0 / (1.0 - u)
    return float(out) if np.ndim(out) == 0 else out


def dc_dx(x, g: Geometry = DEFAULT):
    """dC/dx = εA/(d − x)² = C₀·d/(d − x)² (canonical form; the lecture form misses εA, K2)."""
    x = np.asarray(x, dtype=float)
    if np.any(x >= g.d):
        raise InvalidState("x reached the gap d.")
    out = g.C0 * g.d / (g.d - x) ** 2
    return float(out) if np.ndim(out) == 0 else out


# --- current: I = C dV/dt + V dC/dt -----------------------------------------------------


@dataclass(frozen=True)
class CurrentResult:
    t: np.ndarray
    v: np.ndarray  # bias voltage V(t)
    x: np.ndarray  # membrane displacement x(t)
    c: np.ndarray  # capacitance C(t)
    term_cdv: np.ndarray  # C·dV/dt
    term_vdc: np.ndarray  # V·dC/dt
    total: np.ndarray  # dQ/dt

    @property
    def share_vdc(self) -> float:
        """RMS of the V·dC/dt term relative to the total RMS (0 … 1)."""
        tot = float(np.sqrt(np.mean(self.total**2))) or 1e-30
        return float(np.sqrt(np.mean(self.term_vdc**2))) / tot


def current_terms(t: np.ndarray, v: np.ndarray, x: np.ndarray, g: Geometry = DEFAULT) -> CurrentResult:
    """Both terms of the product rule from sampled V(t) and x(t) (numerical derivatives)."""
    c = c_of_x(x, g)
    dv = np.gradient(v, t)
    dc = np.gradient(c, t)
    term_cdv = c * dv
    term_vdc = v * dc
    q = c * v
    return CurrentResult(t, v, x, c, term_cdv, term_vdc, np.gradient(q, t))


def barometer(V0: float, f: float, x_static: float, g: Geometry = DEFAULT, x_drift: float = 0.0,
              periods: float = 3.0, n: int = 1200) -> CurrentResult:
    """Case 1: slow pressure (x ≈ const), AC bias V₀ cos ωt. ``x_drift`` lets the membrane creep
    by that amount over the window, to show the V·dC/dt term is negligible."""
    t = np.linspace(0.0, periods / f, n)
    v = V0 * np.cos(2 * np.pi * f * t)
    x = x_static + x_drift * t / t[-1]
    return current_terms(t, v, x, g)


def barometer_amplitude(V0: float, f: float, x: float, g: Geometry = DEFAULT) -> float:
    """|I| = V₀ ω C(x) (from I = −V₀ ω C sin ωt)."""
    return V0 * 2 * np.pi * f * c_of_x(x, g)


def microphone(Vb: float, f: float, x0: float, g: Geometry = DEFAULT, x_static: float = 0.0,
               periods: float = 3.0, n: int = 1200) -> CurrentResult:
    """Case 2: fast pressure → x(t) = x_static + x₀ cos ωt (real part of x₀e^{iωt}), DC bias V_b."""
    if x_static + abs(x0) >= g.d:
        raise InvalidState("The membrane swing reaches the fixed plate (x ≥ d).")
    t = np.linspace(0.0, periods / f, n)
    x = x_static + x0 * np.cos(2 * np.pi * f * t)
    v = np.full_like(t, Vb)
    return current_terms(t, v, x, g)


def microphone_exact(t: np.ndarray, Vb: float, f: float, x0: float, g: Geometry = DEFAULT) -> np.ndarray:
    """Analytic I = V_b·C₀d/(d − x)²·dx/dt for x = x₀ cos ωt (reference for tests)."""
    w = 2 * np.pi * f
    x = x0 * np.cos(w * t)
    return Vb * g.C0 * g.d / (g.d - x) ** 2 * (-x0 * w * np.sin(w * t))


def microphone_linear_amplitude(Vb: float, f: float, x0: float, g: Geometry = DEFAULT) -> float:
    """Small-signal amplitude V_b·(dC/dx at x = 0)·ω·x₀ = V_b C₀ ω x₀/d."""
    return Vb * g.C0 / g.d * 2 * np.pi * f * x0


# --- small-signal approximation and harmonics ---------------------------------------------


def geometric_partial(u, order: int):
    """1 + u + u² + … + u^order: the Taylor series of 1/(1 − u) cut after ``order``."""
    u = np.asarray(u, dtype=float)
    out = sum(u**k for k in range(order + 1))
    return float(out) if np.ndim(out) == 0 else out


def geometric_exact(u):
    u = np.asarray(u, dtype=float)
    out = 1.0 / (1.0 - u)
    return float(out) if np.ndim(out) == 0 else out


def relative_error(u, order: int):
    """(exact − approximation)/exact = u^(order+1): the size of the first dropped term."""
    return 1.0 - geometric_partial(u, order) / geometric_exact(u)


def mic_partial(u, order: int):
    """Lecture p. 6: x/(1 − x/d)² ≈ x + 2x²/d + 3x³/d² + …, written in u = x/d as
    (x/d)/(1 − x/d)² ≈ Σ n·uⁿ, n = 1 … order."""
    u = np.asarray(u, dtype=float)
    out = sum(n * u**n for n in range(1, order + 1))
    return float(out) if np.ndim(out) == 0 else out


def harmonics(signal: np.ndarray, t: np.ndarray, f0: float, n_harm: int = 4) -> np.ndarray:
    """Amplitudes of the 1st … n-th harmonic of ``signal`` (sampled over whole periods of f0)."""
    T = t[-1] - t[0]
    periods = T * f0
    m = int(round(periods))
    if m < 1:
        raise ValueError("need at least one full period")
    # use exactly m periods (drop the duplicated end sample)
    n = len(t) - 1
    y = signal[:n] - np.mean(signal[:n])
    spec = np.fft.rfft(y) / n * 2.0
    return np.array([abs(spec[k * m]) if k * m < len(spec) else 0.0 for k in range(1, n_harm + 1)])


def thd(amps: np.ndarray) -> float:
    """Total harmonic distortion: √(A₂² + A₃² + …)/A₁ (supplemental metric)."""
    if amps[0] == 0:
        return 0.0
    return float(np.sqrt(np.sum(amps[1:] ** 2)) / amps[0])


# --- pull-in (supplemental force balance; d/3 from the lecture) ----------------------------


def spring_force(x, g: Geometry = DEFAULT):
    return g.k_eff * np.asarray(x, dtype=float)


def electrostatic_force(V: float, x, g: Geometry = DEFAULT):
    """Attraction between the plates at constant voltage: εA V²/(2(d − x)²)."""
    x = np.asarray(x, dtype=float)
    return g.eps * g.A * V**2 / (2.0 * (g.d - x) ** 2)


def pullin_voltage(g: Geometry = DEFAULT) -> float:
    """V_PI = √(8·k_eff·d³/(27·εA)); the equilibrium is lost at x = d/3."""
    return math.sqrt(8.0 * g.k_eff * g.d**3 / (27.0 * g.eps * g.A))


def pullin_x(g: Geometry = DEFAULT) -> float:
    return g.d / 3.0


@dataclass(frozen=True)
class Equilibrium:
    x: float
    stable: bool


def equilibria(V: float, g: Geometry = DEFAULT) -> list[Equilibrium]:
    """Positions 0 ≤ x < d where spring and electrostatic forces balance.

    k_eff·x·(d − x)² = εA V²/2  is a cubic. Below pull-in there are two roots in [0, d):
    the lower one is stable (spring stiffness wins), the upper one unstable. At V_PI they
    merge at x = d/3; above V_PI there is none — the membrane snaps onto the fixed plate.
    """
    k, d, c = g.k_eff, g.d, g.eps * g.A * V**2 / 2.0
    # k x³ − 2k d x² + k d² x − c = 0
    roots = np.roots([k, -2 * k * d, k * d * d, -c])
    out: list[Equilibrium] = []
    for r in roots:
        if abs(r.imag) > 1e-4 * d:  # a double root (exactly at pull-in) comes out slightly complex
            continue
        x = float(r.real)
        if -1e-15 <= x < d * (1 - 1e-9):
            x = max(x, 0.0)
            slope_el = g.eps * g.A * V**2 / (d - x) ** 3  # dF_el/dx
            out.append(Equilibrium(x, k > slope_el * (1 + 1e-9)))
    out.sort(key=lambda e: e.x)
    # merge numerically coincident roots (exactly at pull-in)
    merged: list[Equilibrium] = []
    for e in out:
        if merged and abs(e.x - merged[-1].x) < 1e-3 * d:
            merged[-1] = Equilibrium((e.x + merged[-1].x) / 2, False)
        else:
            merged.append(e)
    return merged


def stable_position(V: float, g: Geometry = DEFAULT) -> float | None:
    """The stable equilibrium the membrane settles in, or None (pulled in)."""
    for e in equilibria(V, g):
        if e.stable:
            return e.x
    return None
