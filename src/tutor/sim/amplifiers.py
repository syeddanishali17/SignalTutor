"""Amplifier circuits from the lecture, built on the MNA solver (tutor.sim.network).

Resistor names follow the lecture drawings exactly:

* non-inverting amplifier: R1 from the output to V−, R2 from V− to ground →
  A = 1 + R1/R2
* difference amplifier: input V1 → R1 → V−, feedback R2; input V2 → R3 → V+,
  R4 from V+ to ground → A_d = R2/R1 = R4/R3 when matched
* instrumentation amplifier: stage 1 = two op-amps with R2 feedback each and
  R1 between their inverting inputs (nodes A and B); stage 2 = difference
  amplifier with four equal resistors R → A_d = 1 + 2·R2/R1

Closed-form ideal results are provided next to the simulated ones so tests can
check the solver against the lecture formulas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from tutor.sim.network import GND, Network, OpAmp, Solution, solve

A_DEFAULT = 1e5
RAIL = 15.0


def clamp(v: float, rail: float = RAIL) -> float:
    return max(-rail, min(rail, v))


# --- open loop ------------------------------------------------------------------


def open_loop(v_plus: float, v_minus: float, gain: float = A_DEFAULT, rail: float = RAIL) -> float:
    """Bare op-amp, no feedback: V_out = A·(V+ − V−), clipped at the rails."""
    return clamp(gain * (v_plus - v_minus), rail)


# --- non-inverting amplifier --------------------------------------------------------


def noninv_gain_ideal(R1: float, R2: float) -> float:
    return 1.0 + R1 / R2


def noninv_gain_finite(R1: float, R2: float, gain: float) -> float:
    """Closed-loop gain with a finite open-loop gain A: A / (1 + A·β), β = R2/(R1 + R2)."""
    beta = R2 / (R1 + R2)
    return gain / (1.0 + gain * beta)


@dataclass(frozen=True)
class NonInvResult:
    v_in: float
    v_out: float
    v_minus: float
    saturated: int

    @property
    def v_diff(self) -> float:
        """V+ − V− — tiny under negative feedback (the 'virtual short')."""
        return self.v_in - self.v_minus


def non_inverting(v_in: float, R1: float, R2: float, gain: float = A_DEFAULT, rail: float = RAIL) -> NonInvResult:
    net = (Network().v("in", v_in).r("out", "m", R1, "R1").r("m", GND, R2, "R2")
           .amp(OpAmp("U", "in", "m", "out", gain, -rail, rail)))
    s = solve(net)
    return NonInvResult(v_in, s["out"], s["m"], s.saturated["U"])


def follower(v_in: float, gain: float = A_DEFAULT, rail: float = RAIL) -> NonInvResult:
    """Voltage follower: output wired straight back to V− (R1 → 0, R2 → ∞)."""
    v_out = clamp(gain * v_in / (1.0 + gain), rail)
    sat = 0 if abs(gain * v_in / (1.0 + gain)) <= rail else (1 if v_in > 0 else -1)
    return NonInvResult(v_in, v_out, v_out, sat)


def positive_feedback_output(v_in: float, rail: float = RAIL) -> float:
    """Input on V−, output fed back to V+: any tiny difference grows until the output sits
    at a rail (opposite sign to the input). There is no stable linear operating point."""
    return -rail if v_in >= 0 else rail


# --- difference amplifier --------------------------------------------------------------


@dataclass(frozen=True)
class DiffAmpResult:
    v_out: float
    v_plus: float
    v_minus: float
    i_in1: float  # current drawn from input 1
    i_in2: float  # current drawn from input 2
    saturated: int


def difference_amp(v1: float, v2: float, R1: float, R2: float, R3: float, R4: float,
                   gain: float = A_DEFAULT, rail: float = RAIL) -> DiffAmpResult:
    net = (Network().v("in1", v1, "in1").v("in2", v2, "in2")
           .r("in1", "m", R1, "R1").r("m", "out", R2, "R2")
           .r("in2", "p", R3, "R3").r("p", GND, R4, "R4")
           .amp(OpAmp("U", "p", "m", "out", gain, -rail, rail)))
    s = solve(net)
    return DiffAmpResult(s["out"], s["p"], s["m"], s.source_current["in1"], s.source_current["in2"], s.saturated["U"])


def diffamp_ideal(v1: float, v2: float, R1: float, R2: float, R3: float, R4: float) -> float:
    """Ideal op-amp (virtual short), any resistor values:
    V_out = V2·R4/(R3+R4)·(1 + R2/R1) − V1·R2/R1."""
    return v2 * R4 / (R3 + R4) * (1.0 + R2 / R1) - v1 * R2 / R1


def diffamp_gains(R1: float, R2: float, R3: float, R4: float) -> tuple[float, float]:
    """(A_d, A_cm) of the ideal difference amplifier.

    With v1 = Vcm − Vd/2, v2 = Vcm + Vd/2:
      A_cm = R4/(R3+R4)·(1 + R2/R1) − R2/R1   (0 when R4/R3 = R2/R1)
      A_d  = ½·[R4/(R3+R4)·(1 + R2/R1) + R2/R1]
    """
    a = R4 / (R3 + R4) * (1.0 + R2 / R1)
    b = R2 / R1
    return 0.5 * (a + b), a - b


def cmrr_db(a_d: float, a_cm: float) -> float:
    """Common-mode rejection ratio in decibels (supplemental): 20·log10(|A_d/A_cm|)."""
    if a_cm == 0:
        return math.inf
    return 20.0 * math.log10(abs(a_d / a_cm))


# --- instrumentation amplifier -----------------------------------------------------------


@dataclass(frozen=True)
class InaResult:
    v_in1: float
    v_in2: float
    v_A: float  # inverting input of the top op-amp (top of R1)
    v_B: float  # inverting input of the bottom op-amp (bottom of R1)
    v_o1: float  # stage-1 outputs (the lecture reuses V1, V2 for these, see K10)
    v_o2: float
    v_out: float
    i_R1: float  # current from B to A through R1 (the same current flows through both R2)
    saturated: dict[str, int]


def instrumentation_amp(v_in1: float, v_in2: float, R1: float, R2: float, R: float = 10e3,
                        mismatch: float = 0.0, gain: float = A_DEFAULT, rail: float = RAIL) -> InaResult:
    """Three-op-amp instrumentation amplifier. ``mismatch`` scales the stage-2 resistor
    from V+ to ground: R·(1 + mismatch)."""
    net = (Network().v("in1", v_in1, "in1").v("in2", v_in2, "in2")
           # stage 1
           .r("o1", "A", R2, "R2a").r("A", "B", R1, "R1").r("B", "o2", R2, "R2b")
           .amp(OpAmp("U1", "in1", "A", "o1", gain, -rail, rail))
           .amp(OpAmp("U2", "in2", "B", "o2", gain, -rail, rail))
           # stage 2: difference amplifier with four (nominally) equal resistors
           .r("o1", "m", R, "Ra").r("m", "out", R, "Rf")
           .r("o2", "p", R, "Rb").r("p", GND, R * (1.0 + mismatch), "Rg")
           .amp(OpAmp("U3", "p", "m", "out", gain, -rail, rail)))
    s = solve(net)
    return InaResult(v_in1, v_in2, s["A"], s["B"], s["o1"], s["o2"], s["out"],
                     (s["B"] - s["A"]) / R1, s.saturated)


def ina_gain_ideal(R1: float, R2: float) -> float:
    return 1.0 + 2.0 * R2 / R1


def ina_r1_for_gain(target: float, R2: float) -> float:
    """R1 that gives a stage-1 gain ``target`` with feedback resistors R2."""
    return 2.0 * R2 / (target - 1.0)


# --- signals ---------------------------------------------------------------------------------


def time_axis(duration: float = 0.1, n: int = 500) -> np.ndarray:
    return np.linspace(0.0, duration, n)


def bridge_like_inputs(t: np.ndarray, v_cm_dc: float, v_d: float, v_int: float, f_sig: float = 10.0,
                       f_int: float = 50.0) -> tuple[np.ndarray, np.ndarray]:
    """Two input wires: shared DC level + shared mains pickup (common mode) and a
    small signal that pushes them apart (differential). Returns (V1, V2) with
    V2 − V1 = v_d·sin(2π f_sig t)."""
    vd = v_d * np.sin(2 * np.pi * f_sig * t)
    vcm = v_cm_dc + v_int * np.sin(2 * np.pi * f_int * t)
    return vcm - vd / 2, vcm + vd / 2
