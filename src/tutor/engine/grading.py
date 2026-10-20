"""Parse learner answers such as ``"−1,25 mV"`` or ``"4.7kΩ"`` into SI values with a unit."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

PREFIX = {"p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3, "": 1.0, "k": 1e3, "M": 1e6, "G": 1e9}
UNITS = {"v": "V", "a": "A", "ohm": "ohm", "w": "W", "f": "F", "hz": "Hz", "s": "s"}
DIMENSIONLESS = {"%": 1e-2, "ppm": 1e-6, "ue": 1e-6}
UNIT_NAMES = {
    "V": "a voltage (V)",
    "A": "a current (A)",
    "ohm": "a resistance (Ω)",
    "W": "a power (W)",
    "F": "a capacitance (F)",
    "Hz": "a frequency (Hz)",
    "s": "a time (s)",
    "1": "a pure number (no unit)",
}

_NUMBER = re.compile(
    r"^\s*(?P<sign>[-+]?)\s*(?P<mant>(\d+([.,]\d*)?|[.,]\d+))"
    r"(\s*(?:[eE](?P<exp>[-+]?\d+)|(?:[x×*·⋅]\s*10\s*\^\s*\(?(?P<exp2>[-+]?\d+)\)?)))?"
)


@dataclass(frozen=True)
class Quantity:
    value: float  # SI base units (fractions for dimensionless)
    unit: str | None  # canonical SI symbol, "1" for %/ppm/µε, None if no unit was given
    raw: str


class ParseError(ValueError):
    pass


def _normalise(text: str) -> str:
    return (
        text.replace("−", "-")  # unicode minus
        .replace("–", "-")
        .replace("µ", "u")  # micro sign U+00B5
        .replace("μ", "u")  # greek mu U+03BC
        .replace("Ω", "ohm")
        .replace("ε", "e")
        .strip()
    )


def parse_quantity(text: str) -> Quantity:
    """Parse a number with an optional SI-prefixed unit.

    Accepts a decimal comma (``1,25``), scientific notation (``1.25e-3``,
    ``1.25×10^-3``), unicode minus, ``µ``/``μ``/``u`` for micro, ``Ω``/``ohm``.
    """
    raw = text
    s = _normalise(text)
    if not s:
        raise ParseError("Type a number, for example 1.25 mV.")
    m = _NUMBER.match(s)
    if not m:
        raise ParseError(f"Could not read a number at the start of “{raw}”.")
    mant = m.group("mant")
    if "," in mant:
        if "." in mant:
            raise ParseError("Use either a decimal point or a decimal comma, not both.")
        mant = mant.replace(",", ".")
    value = float(mant)
    exp = m.group("exp") or m.group("exp2")
    if exp:
        value *= 10.0 ** int(exp)
    if m.group("sign") == "-":
        value = -value
    rest = s[m.end() :].strip().replace(" ", "")
    if not rest:
        return Quantity(value, None, raw)
    low = rest.lower()
    if low in DIMENSIONLESS:
        return Quantity(value * DIMENSIONLESS[low], "1", raw)
    if low in ("ohms", "ohm"):
        return Quantity(value, "ohm", raw)
    # prefix (case-sensitive except K -> k) + unit (case-insensitive)
    for unit_key in sorted(UNITS, key=len, reverse=True):
        if low.endswith(unit_key):
            prefix = rest[: len(rest) - len(unit_key)]
            if prefix == "K":
                prefix = "k"
            if prefix in PREFIX:
                return Quantity(value * PREFIX[prefix], UNITS[unit_key], raw)
    if low.endswith("ohms") and rest[:-4] in PREFIX:
        return Quantity(value * PREFIX[rest[:-4]], "ohm", raw)
    raise ParseError(
        f"Unknown unit “{rest}”. Try V, mV, µV, A, mA, Ω, kΩ, % — e.g. “1.25 mV”."
    )


def close(a: float, b: float, tol_rel: float, abs_floor: float = 1e-15) -> bool:
    """Relative comparison with a tiny absolute floor for answers that are exactly 0."""
    if not (math.isfinite(a) and math.isfinite(b)):
        return False
    scale = max(abs(b), abs_floor)
    return abs(a - b) <= tol_rel * scale
