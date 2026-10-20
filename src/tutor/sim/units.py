"""SI prefix formatting for readouts (pure functions, no Streamlit)."""

from __future__ import annotations

import math

_PREFIXES = [
    (1e9, "G"),
    (1e6, "M"),
    (1e3, "k"),
    (1.0, ""),
    (1e-3, "m"),
    (1e-6, "µ"),
    (1e-9, "n"),
    (1e-12, "p"),
]

UNIT_SYMBOLS = {"ohm": "Ω", "1": ""}


def _round_sig(x: float, sig: int) -> float:
    if x == 0 or not math.isfinite(x):
        return x
    return round(x, sig - 1 - int(math.floor(math.log10(abs(x)))))


def format_si(value: float, unit: str = "", sig: int = 3, force_prefix: str | None = None) -> str:
    """Format ``value`` with an SI prefix, e.g. ``format_si(-1.2494e-3, "V") -> "-1.25 mV"``.

    ``force_prefix`` pins the prefix (useful to keep a readout from jumping
    between mV and µV while a slider moves).
    """
    sym = UNIT_SYMBOLS.get(unit, unit)
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if isinstance(value, float) and math.isinf(value):
        return ("∞" if value > 0 else "−∞") + (f" {sym}" if sym else "")
    if force_prefix is not None:
        factor = {p: f for f, p in _PREFIXES}[force_prefix]
        scaled, prefix = value / factor, force_prefix
    elif value == 0:
        scaled, prefix = 0.0, ""
    else:
        mag = abs(_round_sig(value, sig))
        factor, prefix = next(((f, p) for f, p in _PREFIXES if mag >= f * 0.9995), _PREFIXES[-1])
        scaled = value / factor
    rounded = _round_sig(scaled, sig)
    if rounded == 0:
        text = "0"
    else:
        digits = max(0, sig - 1 - int(math.floor(math.log10(abs(rounded)))))
        text = f"{rounded:.{digits}f}"
    text = text.replace("-", "−")
    unit_part = f"{prefix}{sym}"
    return f"{text} {unit_part}".strip()


def format_ratio_percent(x: float, sig: int = 3) -> str:
    """``0.0123 -> "1.23 %"``."""
    return format_si(x * 100, "%", sig=sig, force_prefix="")
