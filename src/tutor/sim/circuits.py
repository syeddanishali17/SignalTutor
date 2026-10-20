"""Foundation circuits: Ohm's law, series path, voltage divider, KCL, reference nodes.

All functions take and return SI base units (V, A, Ω).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class InvalidCircuit(ValueError):
    """A physically meaningless parameter set, with a learner-facing explanation."""


def _require_positive(name: str, value: float) -> None:
    if not (value > 0) or not math.isfinite(value):
        raise InvalidCircuit(
            f"{name} must be a positive, finite resistance. A resistor of {value} Ω "
            "does not exist: 0 Ω is a plain wire (a short circuit) and negative "
            "resistance would mean the part supplies energy."
        )


def ohm_current(V: float, R: float) -> float:
    """Current through a resistor ``R`` with voltage ``V`` across it: I = V / R."""
    _require_positive("R", R)
    return V / R


def series_resistance(*rs: float) -> float:
    """Resistors in series add: the current has to pass through each one in turn."""
    for i, r in enumerate(rs, 1):
        _require_positive(f"R{i}", r)
    return float(sum(rs))


def parallel_resistance(*rs: float) -> float:
    for i, r in enumerate(rs, 1):
        _require_positive(f"R{i}", r)
    return 1.0 / sum(1.0 / r for r in rs)


@dataclass(frozen=True)
class DividerResult:
    Vin: float
    R1: float  # top resistor (between Vin and the output node)
    R2: float  # bottom resistor (between the output node and ground)
    R_load: float  # load from the output node to ground (inf = no load)
    Vout: float  # output node voltage, relative to ground
    I: float  # current through R1
    I_load: float
    V_R1: float  # voltage drop across R1
    V_R2: float  # voltage drop across R2 (= Vout)

    @property
    def ratio(self) -> float:
        return self.Vout / self.Vin if self.Vin else float("nan")


def divider(Vin: float, R1: float, R2: float, R_load: float = math.inf) -> DividerResult:
    """Unloaded or loaded voltage divider. ``Vout = Vin * R2 / (R1 + R2)`` when unloaded."""
    _require_positive("R1", R1)
    _require_positive("R2", R2)
    if R_load != math.inf:
        _require_positive("R_load", R_load)
        R_bottom = parallel_resistance(R2, R_load)
    else:
        R_bottom = R2
    I = Vin / (R1 + R_bottom)
    Vout = I * R_bottom
    I_load = 0.0 if R_load == math.inf else Vout / R_load
    return DividerResult(Vin, R1, R2, R_load, Vout, I, I_load, Vin - Vout, Vout)


def kcl_remaining(currents_in: list[float], currents_out_known: list[float]) -> float:
    """Kirchhoff's current law at one node: total in = total out.

    Returns the one unknown outgoing current. A negative result means that
    current actually flows *into* the node (the arrow was drawn the wrong way).
    """
    return sum(currents_in) - sum(currents_out_known)


def relabel_potentials(potentials: dict[str, float], reference: str) -> dict[str, float]:
    """Express node potentials relative to a chosen reference node (which becomes 0 V).

    Voltage *differences* between any two nodes are unchanged by this.
    """
    if reference not in potentials:
        raise KeyError(f"Unknown reference node {reference!r}")
    ref = potentials[reference]
    return {node: v - ref for node, v in potentials.items()}
