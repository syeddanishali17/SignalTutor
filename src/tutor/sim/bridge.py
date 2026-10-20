"""Wheatstone bridge models (lecture Lecture 1 notes, p. 2 and -02 p2).

Geometry and naming (fixed across every mode so the learner sees exactly which
resistors change)::

            V0 (supply, called V_b in the L01 notes)
          ┌──────┴──────┐
          R1            R2          left branch carries I2, right branch I1
          │             │
     V2 ──●             ●── V1      output: V_out = V2 − V1 (L02 convention)
          │             │
          R4            R3
          └──────┬──────┘
                GND

* R1..R4 follow the L01 full-bridge drawing (R1 top-left, R2 top-right,
  R3 bottom-right, R4 bottom-left).
* V1, V2, I1, I2 follow the L02 quarter-bridge derivation.
* Quarter bridge: the active gauge is R1 = R + ΔR. With this placement the
  lecture derivation ``V2 = I2·R`` holds. The L02 drawing puts R + ΔR in the
  lower-left arm instead; that flips the sign (known issue K9).
* Full bridge: R1 and R3 get +ΔR, R2 and R4 get −ΔR (diagonally opposite arms
  see the same strain), so V2 − V1 = −(ΔR/R)·V0 exactly. The lecture writes
  the magnitude, V_out = (ΔR/R)·V_b.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from tutor.sim.circuits import InvalidCircuit

Mode = Literal["balanced", "quarter", "full"]
MODES: tuple[Mode, ...] = ("balanced", "quarter", "full")


@dataclass(frozen=True)
class Arms:
    R1: float  # top-left
    R2: float  # top-right
    R3: float  # bottom-right
    R4: float  # bottom-left

    def as_dict(self) -> dict[str, float]:
        return {"R1": self.R1, "R2": self.R2, "R3": self.R3, "R4": self.R4}


@dataclass(frozen=True)
class BridgeResult:
    V0: float
    arms: Arms
    R_meter: float
    V1: float  # right midpoint, relative to ground
    V2: float  # left midpoint, relative to ground
    I1: float  # current in the right branch (through R2)
    I2: float  # current in the left branch (through R1)
    I_meter: float  # current from V2 to V1 through the meter (0 for an ideal meter)

    @property
    def Vout(self) -> float:
        """Bridge output V2 − V1."""
        return self.V2 - self.V1

    @property
    def V_cm(self) -> float:
        """Common-mode level of the two outputs (about V0/2)."""
        return 0.5 * (self.V1 + self.V2)


def gauge_flags(mode: Mode) -> dict[str, int]:
    """Strain sign of each arm: +1 / −1 for an active gauge, 0 for a fixed resistor."""
    if mode == "balanced":
        return {"R1": 0, "R2": 0, "R3": 0, "R4": 0}
    if mode == "quarter":
        return {"R1": +1, "R2": 0, "R3": 0, "R4": 0}
    if mode == "full":
        return {"R1": +1, "R2": -1, "R3": +1, "R4": -1}
    raise ValueError(f"Unknown bridge mode {mode!r}")


def arms_for(mode: Mode, R: float, dR_rel: float, thermal_rel: float = 0.0) -> Arms:
    """Arm resistances for a mode.

    ``dR_rel`` is ΔR/R from strain. ``thermal_rel`` is α·ΔT: the fractional
    resistance change a *gauge* gets from warming up. Fixed completion
    resistors are assumed to be off the membrane and not to drift.
    """
    if not (R > 0) or not math.isfinite(R):
        raise InvalidCircuit("The nominal resistance R must be positive.")
    flags = gauge_flags(mode)
    values = {}
    for name, sign in flags.items():
        if sign == 0:
            values[name] = R
        else:
            values[name] = R * (1 + sign * dR_rel) * (1 + thermal_rel)
    for name, v in values.items():
        if not (v > 0):
            raise InvalidCircuit(
                f"{name} would be {v:.3g} Ω. ΔR/R = {dR_rel:+.3g} is too large: a gauge's "
                "resistance cannot drop to zero or below. Real strain gauges only change by "
                "a fraction of a percent."
            )
    return Arms(**values)


def solve(V0: float, arms: Arms, R_meter: float = math.inf) -> BridgeResult:
    """Node voltages of the bridge, optionally loaded by a meter of resistance ``R_meter``
    connected between the two midpoints."""
    for name, r in arms.as_dict().items():
        if not (r > 0) or not math.isfinite(r):
            raise InvalidCircuit(f"{name} must be a positive resistance (got {r}).")
    if not (R_meter > 0):
        raise InvalidCircuit("The meter resistance must be positive.")
    g1, g2, g3, g4 = (1.0 / arms.R1, 1.0 / arms.R2, 1.0 / arms.R3, 1.0 / arms.R4)
    gm = 0.0 if math.isinf(R_meter) else 1.0 / R_meter
    # KCL at V2:  (V0 − V2) g1 = V2 g4 + (V2 − V1) gm
    # KCL at V1:  (V0 − V1) g2 + (V2 − V1) gm = V1 g3
    a = g1 + g4 + gm
    c = g2 + g3 + gm
    det = a * c - gm * gm
    V2 = V0 * (g1 * c + gm * g2) / det
    V1 = V0 * (g2 * a + gm * g1) / det
    return BridgeResult(
        V0=V0,
        arms=arms,
        R_meter=R_meter,
        V1=V1,
        V2=V2,
        I1=(V0 - V1) * g2,
        I2=(V0 - V2) * g1,
        I_meter=(V2 - V1) * gm,
    )


def simulate(
    mode: Mode,
    V0: float,
    R: float,
    dR_rel: float,
    thermal_rel: float = 0.0,
    R_meter: float = math.inf,
) -> BridgeResult:
    return solve(V0, arms_for(mode, R, dR_rel, thermal_rel), R_meter)


# --- closed forms from the lecture ---------------------------------------------


def quarter_exact(V0: float, dR_rel: float) -> float:
    """Exact quarter-bridge output, V2 − V1 = V0·(1/(2 + ΔR/R) − 1/2)."""
    return V0 * (1.0 / (2.0 + dR_rel) - 0.5)


def quarter_approx(V0: float, dR_rel: float) -> float:
    """Small-change approximation, V2 − V1 ≈ −(1/4)·(ΔR/R)·V0 for ΔR/R ≪ 1."""
    return -0.25 * dR_rel * V0


def full_output(V0: float, dR_rel: float) -> float:
    """Full bridge, V2 − V1 = −(ΔR/R)·V0 (exact; magnitude (ΔR/R)·V_b as in the notes)."""
    return -dR_rel * V0


def quarter_approx_rel_error(dR_rel: float) -> float:
    """(approx − exact)/exact = (ΔR/R)/2 exactly (for ΔR ≠ 0)."""
    return 0.5 * dR_rel


def dR_rel_from_strain(G: float, strain: float) -> float:
    """Gauge factor definition G = (ΔR/R)/ε  ⇒  ΔR/R = G·ε."""
    return G * strain


def balance_condition(arms: Arms, rel_tol: float = 1e-12) -> bool:
    """Bridge is balanced (V2 = V1) when R1/R4 = R2/R3."""
    return math.isclose(arms.R1 * arms.R3, arms.R2 * arms.R4, rel_tol=rel_tol)
