"""A small modified-nodal-analysis (MNA) solver for resistive circuits with op-amps.

Elements
--------
* resistors between two nodes,
* ideal voltage sources from a node to ground (``"0"``),
* op-amps: a voltage-controlled source ``V_out = A·(V+ − V−)`` from the output to
  ground, with ideal (infinite) input resistance and zero output resistance.

Saturation: an op-amp whose solution exceeds its supply rails is replaced by a
fixed source at that rail and the circuit is solved again (repeated until stable).
This is the textbook "ideal op-amp with finite gain and rails" model — enough to
show virtual short, saturation, loading and common-mode leakage without SPICE.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

GND = "0"


@dataclass(frozen=True)
class OpAmp:
    name: str
    plus: str
    minus: str
    out: str
    gain: float = 1e5
    rail_lo: float = -15.0
    rail_hi: float = 15.0


@dataclass
class Network:
    resistors: list[tuple[str, str, float, str]] = field(default_factory=list)  # (a, b, R, name)
    sources: list[tuple[str, float, str]] = field(default_factory=list)  # (node, V, name)
    opamps: list[OpAmp] = field(default_factory=list)

    def r(self, a: str, b: str, value: float, name: str = "") -> "Network":
        if not (value > 0) or not math.isfinite(value):
            raise ValueError(f"Resistor {name or (a, b)} must be positive and finite, got {value}")
        self.resistors.append((a, b, float(value), name))
        return self

    def v(self, node: str, value: float, name: str = "") -> "Network":
        self.sources.append((node, float(value), name or node))
        return self

    def amp(self, oa: OpAmp) -> "Network":
        self.opamps.append(oa)
        return self


@dataclass(frozen=True)
class Solution:
    v: dict[str, float]  # node voltages (ground = 0)
    source_current: dict[str, float]  # current delivered BY each source into the circuit
    saturated: dict[str, int]  # op-amp name -> -1 (low rail), 0 (linear), +1 (high rail)

    def __getitem__(self, node: str) -> float:
        return 0.0 if node == GND else self.v[node]

    def current(self, a: str, b: str, R: float) -> float:
        """Current from a to b through a resistor R."""
        return (self[a] - self[b]) / R


def solve(net: Network, max_iter: int = 12) -> Solution:
    nodes = sorted({n for a, b, _, _ in net.resistors for n in (a, b)}
                   | {n for n, _, _ in net.sources}
                   | {n for oa in net.opamps for n in (oa.plus, oa.minus, oa.out)} - {GND})
    nodes = [n for n in nodes if n != GND]
    idx = {n: i for i, n in enumerate(nodes)}
    state = {oa.name: 0 for oa in net.opamps}
    for _ in range(max_iter):
        sol = _solve_linear(net, nodes, idx, state)
        changed = False
        for oa in net.opamps:
            vo = sol.v[oa.out]
            drive = oa.gain * (sol[oa.plus] - sol[oa.minus])
            cur = state[oa.name]
            if cur == 0 and vo > oa.rail_hi:
                state[oa.name] = +1
                changed = True
            elif cur == 0 and vo < oa.rail_lo:
                state[oa.name] = -1
                changed = True
            elif cur == +1 and drive < oa.rail_hi:
                state[oa.name] = 0
                changed = True
            elif cur == -1 and drive > oa.rail_lo:
                state[oa.name] = 0
                changed = True
        if not changed:
            return sol
    return sol


def _solve_linear(net: Network, nodes: list[str], idx: dict[str, int], state: dict[str, int]) -> Solution:
    n = len(nodes)
    m = len(net.sources) + len(net.opamps)
    A = np.zeros((n + m, n + m))
    z = np.zeros(n + m)

    def stamp_g(a: str, b: str, g: float) -> None:
        ia, ib = idx.get(a), idx.get(b)
        if ia is not None:
            A[ia, ia] += g
        if ib is not None:
            A[ib, ib] += g
        if ia is not None and ib is not None:
            A[ia, ib] -= g
            A[ib, ia] -= g

    for a, b, R, _ in net.resistors:
        stamp_g(a, b, 1.0 / R)
    k = n
    for node, value, _ in net.sources:
        i = idx[node]
        A[i, k] += 1.0  # source current enters the node
        A[k, i] = 1.0
        z[k] = value
        k += 1
    for oa in net.opamps:
        io = idx[oa.out]
        A[io, k] += 1.0
        s = state[oa.name]
        A[k, io] = 1.0
        if s == 0:  # V_out − A (V+ − V−) = 0
            if oa.plus != GND:
                A[k, idx[oa.plus]] -= oa.gain
            if oa.minus != GND:
                A[k, idx[oa.minus]] += oa.gain
        else:
            z[k] = oa.rail_hi if s > 0 else oa.rail_lo
        k += 1
    x = np.linalg.solve(A, z)
    v = {name: float(x[i]) for name, i in idx.items()}
    # the MNA unknown is the current flowing from the node INTO the source; report what the source delivers
    src = {name: -float(x[n + j]) for j, (_, _, name) in enumerate(net.sources)}
    return Solution(v, src, dict(state))
