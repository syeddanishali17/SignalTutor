"""Reference values from spec section 15, plus property tests."""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tutor.sim import bridge
from tutor.sim.circuits import InvalidCircuit


def test_quarter_bridge_reference_value_exact_and_approx():
    # R = 1 kΩ, ΔR = 1 Ω, V0 = 5 V
    res = bridge.solve(5.0, bridge.Arms(R1=1001.0, R2=1000.0, R3=1000.0, R4=1000.0))
    assert res.Vout == pytest.approx(5 / 2.001 - 2.5, rel=1e-12)
    assert res.Vout == pytest.approx(-1.2494e-3, abs=1e-7)
    assert bridge.quarter_exact(5.0, 1e-3) == pytest.approx(res.Vout, rel=1e-12)
    assert bridge.quarter_approx(5.0, 1e-3) == pytest.approx(-1.25e-3, rel=1e-12)


def test_full_bridge_reference_value():
    # G = 2, ε = 500 µε, Vb = 5 V  ->  5.0 mV
    x = bridge.dR_rel_from_strain(2.0, 500e-6)
    res = bridge.simulate("full", 5.0, 350.0, x)
    assert abs(res.Vout) == pytest.approx(5.0e-3, rel=1e-12)
    assert res.Vout == pytest.approx(bridge.full_output(5.0, x), rel=1e-12)


def test_quarter_is_quarter_of_full_for_small_change():
    x = 1e-4
    q = bridge.simulate("quarter", 5.0, 1e3, x).Vout
    f = bridge.simulate("full", 5.0, 1e3, x).Vout
    assert f / q == pytest.approx(4.0, rel=1e-3)


def test_lecture_node_formulas():
    V0, R, dR = 5.0, 1000.0, 7.0
    res = bridge.simulate("quarter", V0, R, dR / R)
    assert res.I1 == pytest.approx(V0 / (2 * R))
    assert res.I2 == pytest.approx(V0 / (2 * R + dR))
    assert res.V1 == pytest.approx(V0 / 2)
    assert res.V2 == pytest.approx(V0 / (2 + dR / R))


def test_approximation_error_is_half_of_dR_over_R():
    for x in (1e-3, 0.02, 0.1, 0.4):
        approx, exact = bridge.quarter_approx(5, x), bridge.quarter_exact(5, x)
        assert (approx - exact) / exact == pytest.approx(x / 2, rel=1e-9)
        assert bridge.quarter_approx_rel_error(x) == pytest.approx(x / 2)


def test_temperature_cancels_in_full_bridge_but_not_quarter():
    full = bridge.simulate("full", 5.0, 1e3, 0.0, thermal_rel=0.02)
    quarter = bridge.simulate("quarter", 5.0, 1e3, 0.0, thermal_rel=0.02)
    assert abs(full.Vout) < 1e-15
    assert quarter.Vout == pytest.approx(bridge.quarter_exact(5.0, 0.02), rel=1e-12)


def test_loading_follows_thevenin_estimate():
    ideal = bridge.simulate("quarter", 5.0, 1e3, 1e-3)
    loaded = bridge.simulate("quarter", 5.0, 1e3, 1e-3, R_meter=10e3)
    assert loaded.Vout / ideal.Vout == pytest.approx(10 / 11, rel=2e-3)
    assert loaded.I_meter == pytest.approx(loaded.Vout / 10e3)


def test_balance_condition_with_unequal_resistors():
    arms = bridge.Arms(R1=2e3, R2=4e3, R3=2e3, R4=1e3)  # R1/R4 = 2 = R2/R3
    assert bridge.balance_condition(arms)
    assert abs(bridge.solve(5.0, arms).Vout) < 1e-12


def test_invalid_ranges_raise_learner_message():
    with pytest.raises(InvalidCircuit, match="too large"):
        bridge.arms_for("full", 1e3, 1.2)
    with pytest.raises(InvalidCircuit):
        bridge.arms_for("quarter", -5, 0.0)


@given(V0=st.floats(0.1, 20), R=st.floats(10, 1e6), mode=st.sampled_from(bridge.MODES))
def test_output_zero_without_change(V0, R, mode):
    assert abs(bridge.simulate(mode, V0, R, 0.0).Vout) <= 1e-12 * V0


@given(x=st.floats(-0.5, 0.5), V0=st.floats(0.1, 20))
def test_full_bridge_exactly_linear(x, V0):
    res = bridge.simulate("full", V0, 1e3, x)
    # V2 − V1 subtracts two ≈ V0/2 node voltages: float cancellation is ~1e-16·V0 absolute
    assert res.Vout == pytest.approx(-x * V0, rel=1e-9, abs=1e-13 * V0)


@given(x=st.floats(1e-6, 0.5), V0=st.floats(0.1, 20), R=st.floats(10, 1e6))
def test_kcl_holds_at_both_midpoints(x, V0, R):
    res = bridge.simulate("quarter", V0, R, x, R_meter=5 * R)
    a = res.arms
    assert (V0 - res.V2) / a.R1 == pytest.approx(res.V2 / a.R4 + res.I_meter, rel=1e-9)
    assert (V0 - res.V1) / a.R2 + res.I_meter == pytest.approx(res.V1 / a.R3, rel=1e-9)


@given(x=st.floats(1e-6, 0.3))
def test_quarter_output_sign_and_monotonic(x):
    assert bridge.quarter_exact(5, x) < 0
    assert bridge.quarter_exact(5, x * 1.5) < bridge.quarter_exact(5, x)


def test_common_mode_is_half_supply_when_balanced():
    res = bridge.simulate("balanced", 5.0, 350.0, 0.0)
    assert res.V1 == pytest.approx(2.5) and res.V2 == pytest.approx(2.5)
    assert res.V_cm == pytest.approx(2.5)
    assert math.isinf(res.R_meter)
