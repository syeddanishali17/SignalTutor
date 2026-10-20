import pytest
import sympy as sp

from tutor.engine import dims
from tutor.engine.expr import ExprError, equivalent, parse, to_sympy


def test_parser_precedence_and_unary_minus():
    x = sp.Symbol("x", positive=True)
    assert to_sympy("-x^2") == -(x**2)
    assert to_sympy("2^3^2") == 512  # right-associative
    assert to_sympy("1/(2+x)-1/2") == 1 / (2 + x) - sp.Rational(1, 2)
    assert to_sympy("x**2") == x**2


def test_parser_rejects_code_and_unknown_functions():
    for bad in ("__import__('os')", "x.real", "open(1)", "lambda: 1", "x;y", ""):
        with pytest.raises(ExprError):
            parse(bad)


def test_equivalent():
    assert equivalent("V0/(2 + dR/R)", "V0*R/(2*R + dR)")
    assert not equivalent("V0/(2*R)", "V0/(2*R + dR)")


def test_unit_dimensions():
    assert dims.unit_dim("V") * dims.unit_dim("F") == dims.unit_dim("C")
    assert dims.unit_dim("ohm") * dims.unit_dim("F") == dims.unit_dim("s")
    assert dims.unit_dim("V^2/Hz") == dims.unit_dim("V^2*s")
    assert dims.unit_dim("1").dimensionless


def test_K1_lecture_form_fails_and_canonical_passes():
    syms = {"Vb": "V", "C0": "F", "d": "m", "x": "m", "omega": "1/s"}
    ok_lecture, msg = dims.check("Vb*C0*1/(d - x)^2*imath*omega*x", syms, "A")
    ok_canon, _ = dims.check("Vb*C0*d/(d - x)^2*imath*omega*x", syms, "A")
    assert not ok_lecture and "expected" in msg
    assert ok_canon


def test_K2_lecture_form_fails():
    ok, _ = dims.check("d/(d - x)^2", {"d": "m", "x": "m"}, "F/m")
    assert not ok


def test_adding_mismatched_dimensions_is_an_error():
    ok, msg = dims.check("V0 + R", {"V0": "V", "R": "ohm"}, "V")
    assert not ok and "add" in msg


def test_sin_needs_dimensionless_argument():
    ok, _ = dims.check("sin(omega)", {"omega": "1/s"}, "1")
    assert not ok
    ok, _ = dims.check("sin(omega*t)", {"omega": "1/s", "t": "s"}, "1")
    assert ok
