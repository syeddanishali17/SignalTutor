import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tutor.sim import circuits
from tutor.sim.units import format_si


def test_ohm():
    assert circuits.ohm_current(9.0, 4.7e3) == pytest.approx(1.9149e-3, rel=1e-4)
    with pytest.raises(circuits.InvalidCircuit, match="short circuit"):
        circuits.ohm_current(5.0, 0.0)


def test_divider_unloaded_and_loaded():
    d = circuits.divider(10.0, 1e3, 1e3)
    assert d.Vout == pytest.approx(5.0)
    assert d.V_R1 + d.V_R2 == pytest.approx(10.0)
    loaded = circuits.divider(10.0, 1e3, 1e3, R_load=1e3)
    assert loaded.Vout == pytest.approx(10.0 * 500 / 1500)
    assert loaded.I == pytest.approx(loaded.I_load + loaded.Vout / 1e3)


@given(Vin=st.floats(0.1, 50), R1=st.floats(1, 1e6), R2=st.floats(1, 1e6))
def test_divider_bounds_and_series_current(Vin, R1, R2):
    d = circuits.divider(Vin, R1, R2)
    assert 0 <= d.Vout <= Vin
    assert d.V_R1 == pytest.approx(d.I * R1, rel=1e-9)
    assert d.V_R2 == pytest.approx(d.I * R2, rel=1e-9)


def test_kcl_sign_means_direction():
    assert circuits.kcl_remaining([5e-3], [2e-3]) == pytest.approx(3e-3)
    assert circuits.kcl_remaining([5e-3], [7e-3]) == pytest.approx(-2e-3)


@given(a=st.floats(-20, 20), b=st.floats(-20, 20), c=st.floats(-20, 20), ref=st.sampled_from(["A", "B", "C"]))
def test_relabelling_keeps_differences(a, b, c, ref):
    pots = {"A": a, "B": b, "C": c}
    rel = circuits.relabel_potentials(pots, ref)
    assert rel[ref] == 0
    assert rel["A"] - rel["B"] == pytest.approx(a - b, abs=1e-9)


@pytest.mark.parametrize(
    "value, unit, expected",
    [
        (-1.2494e-3, "V", "−1.25 mV"),
        (5e-3, "V", "5.00 mV"),
        (4700, "ohm", "4.70 kΩ"),
        (0.0, "V", "0 V"),
        (2.5, "V", "2.50 V"),
        (999.96e-6, "A", "1.00 mA"),
        (math.inf, "ohm", "∞ Ω"),
    ],
)
def test_format_si(value, unit, expected):
    assert format_si(value, unit) == expected


def test_format_si_forced_prefix():
    assert format_si(2e-4, "V", force_prefix="m") == "0.200 mV"
