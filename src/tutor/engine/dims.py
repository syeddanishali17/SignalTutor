"""Dimension checking without third-party unit libraries.

A dimension is a vector of rational exponents over the SI base dimensions
(mass, length, time, current, temperature). Units in content files are written
as expressions over the unit names below, e.g. ``"V^2/Hz"`` or ``"F/m"``.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from tutor.engine.expr import BinOp, Call, ExprError, Name, Neg, Node, Num, const_value, parse

BASE = ("M", "L", "T", "I", "Th")


@dataclass(frozen=True)
class Dim:
    exps: tuple[Fraction, ...] = (Fraction(0),) * 5

    @staticmethod
    def of(**kw: float | Fraction) -> "Dim":
        return Dim(tuple(Fraction(kw.get(b, 0)) for b in BASE))

    def __mul__(self, other: "Dim") -> "Dim":
        return Dim(tuple(a + b for a, b in zip(self.exps, other.exps)))

    def __truediv__(self, other: "Dim") -> "Dim":
        return Dim(tuple(a - b for a, b in zip(self.exps, other.exps)))

    def __pow__(self, p: Fraction) -> "Dim":
        return Dim(tuple(a * p for a in self.exps))

    @property
    def dimensionless(self) -> bool:
        return all(e == 0 for e in self.exps)

    def __str__(self) -> str:
        if self.dimensionless:
            return "1"
        parts = []
        for name, e in zip(("kg", "m", "s", "A", "K"), self.exps):
            if e == 0:
                continue
            parts.append(name if e == 1 else f"{name}^{e}")
        return "·".join(parts)


ONE = Dim()

UNITS: dict[str, Dim] = {
    "1": ONE,
    "rad": ONE,
    "kg": Dim.of(M=1),
    "m": Dim.of(L=1),
    "s": Dim.of(T=1),
    "A": Dim.of(I=1),
    "K": Dim.of(Th=1),
    "Hz": Dim.of(T=-1),
    "N": Dim.of(M=1, L=1, T=-2),
    "Pa": Dim.of(M=1, L=-1, T=-2),
    "J": Dim.of(M=1, L=2, T=-2),
    "W": Dim.of(M=1, L=2, T=-3),
    "C": Dim.of(T=1, I=1),
    "V": Dim.of(M=1, L=2, T=-3, I=-1),
    "ohm": Dim.of(M=1, L=2, T=-3, I=-2),
    "F": Dim.of(M=-1, L=-2, T=4, I=2),
}


class DimensionError(ValueError):
    """Raised when an expression is dimensionally inconsistent."""


def unit_dim(unit: str) -> Dim:
    """Dimension of a unit expression such as ``"V^2/Hz"``. ``"1"`` is dimensionless."""
    unit = unit.strip()
    if unit in ("", "1"):
        return ONE
    return _eval(parse(unit), lambda n: _unit_lookup(n))


def _unit_lookup(name: str) -> Dim:
    if name not in UNITS:
        raise ExprError(f"Unknown unit {name!r}. Known: {', '.join(sorted(UNITS))}")
    return UNITS[name]


def expr_dim(expr: str | Node, symbol_units: dict[str, str]) -> Dim:
    """Dimension of ``expr`` given a unit for every symbol in it."""
    node = parse(expr) if isinstance(expr, str) else expr
    dims = {k: unit_dim(v) for k, v in symbol_units.items()}

    def lookup(name: str) -> Dim:
        if name in ("pi", "imath"):
            return ONE
        if name not in dims:
            raise ExprError(f"Symbol {name!r} has no unit declared")
        return dims[name]

    return _eval(node, lookup)


def check(expr: str, symbol_units: dict[str, str], result_unit: str) -> tuple[bool, str]:
    """Return ``(ok, message)`` for a dimension check of ``expr`` against ``result_unit``."""
    try:
        got = expr_dim(expr, symbol_units)
    except DimensionError as exc:
        return False, str(exc)
    want = unit_dim(result_unit)
    if got == want:
        return True, f"dimensions match ({want})"
    return False, f"expression has dimension {got}, expected {want} ({result_unit})"


def _eval(node: Node, lookup) -> Dim:
    if isinstance(node, Num):
        return ONE
    if isinstance(node, Name):
        return lookup(node.name)
    if isinstance(node, Neg):
        return _eval(node.arg, lookup)
    if isinstance(node, Call):
        args = [_eval(a, lookup) for a in node.args]
        if node.func in ("sin", "cos", "exp", "log"):
            if not args[0].dimensionless:
                raise DimensionError(f"{node.func}() needs a dimensionless argument, got {args[0]}")
            return ONE
        if node.func == "sqrt":
            return args[0] ** Fraction(1, 2)
        return args[0]  # abs, re
    if isinstance(node, BinOp):
        if node.op == "^":
            base = _eval(node.left, lookup)
            exp_dim = _eval(node.right, lookup)
            if not exp_dim.dimensionless:
                raise DimensionError(f"Exponent must be dimensionless, got {exp_dim}")
            if base.dimensionless:
                return ONE
            p = const_value(node.right)
            if p is None:
                raise DimensionError("A dimensional base needs a numeric exponent")
            return base**p
        a, b = _eval(node.left, lookup), _eval(node.right, lookup)
        if node.op == "*":
            return a * b
        if node.op == "/":
            return a / b
        if a != b:
            raise DimensionError(f"Cannot add/subtract {a} and {b}")
        return a
    raise ExprError(f"Unknown node {node!r}")
