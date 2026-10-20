"""Amplifier models vs the lecture's closed forms (spec 15 reference values)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tutor.sim import amplifiers as amp
from tutor.sim import bridge
from tutor.sim.network import GND, Network, OpAmp, solve


def test_mna_divider_and_source_current_sign():
    s = solve(Network().v("in", 10.0).r("in", "mid", 1e3).r("mid", GND, 1e3))
    assert s["mid"] == pytest.approx(5.0)
    assert s.source_current["in"] == pytest.approx(10.0 / 2e3)  # delivered INTO the circuit: positive


def test_mna_matches_bridge_solver_with_meter():
    arms = bridge.Arms(R1=1001.0, R2=1000.0, R3=1000.0, R4=1000.0)
    ref = bridge.solve(5.0, arms, R_meter=10e3)
    net = (Network().v("top", 5.0).r("top", "v2", arms.R1).r("v2", GND, arms.R4)
           .r("top", "v1", arms.R2).r("v1", GND, arms.R3).r("v2", "v1", 10e3))
    s = solve(net)
    assert s["v2"] == pytest.approx(ref.V2, rel=1e-12)
    assert s["v1"] == pytest.approx(ref.V1, rel=1e-12)


def test_open_loop_saturates():
    assert amp.open_loop(1e-6, 0.0) == pytest.approx(0.1)
    assert amp.open_loop(1e-3, 0.0) == pytest.approx(15.0)
    assert amp.open_loop(0.0, 1e-3) == pytest.approx(-15.0)


def test_non_inverting_gain_and_virtual_short():
    r = amp.non_inverting(0.1, R1=9e3, R2=1e3)
    assert r.v_out == pytest.approx(1.0, rel=1e-3)  # 1 + R1/R2 = 10
    assert abs(r.v_diff) < 1e-4  # V+ − V− ≈ V_out/A
    assert r.v_out == pytest.approx(0.1 * amp.noninv_gain_finite(9e3, 1e3, amp.A_DEFAULT), rel=1e-9)
    assert amp.noninv_gain_ideal(9e3, 1e3) == 10.0


def test_non_inverting_saturates_on_common_mode():
    r = amp.non_inverting(2.5, R1=100e3, R2=1e3)  # gain 101 on a 2.5 V node
    assert r.v_out == pytest.approx(15.0)
    assert r.saturated == 1
    assert abs(r.v_diff) > 1.0  # virtual short is gone in saturation


def test_follower_and_positive_feedback():
    assert amp.follower(1.0).v_out == pytest.approx(1.0, rel=1e-4)
    assert amp.positive_feedback_output(0.001) == -15.0
    assert amp.positive_feedback_output(-0.001) == 15.0


def test_difference_amp_matched():
    r = amp.difference_amp(2.499, 2.501, R1=1e3, R2=100e3, R3=1e3, R4=100e3)
    # finite open-loop gain: relative error ≈ noise gain / A = 101 / 1e5 ≈ 0.1 %
    assert r.v_out == pytest.approx(100 * 0.002, rel=3e-3)
    assert amp.diffamp_ideal(2.499, 2.501, 1e3, 100e3, 1e3, 100e3) == pytest.approx(0.2, rel=1e-9)
    ad, acm = amp.diffamp_gains(1e3, 100e3, 1e3, 100e3)
    assert ad == pytest.approx(100.0)
    assert acm == pytest.approx(0.0, abs=1e-12)


def test_difference_amp_mismatch_leaks_common_mode():
    ad, acm = amp.diffamp_gains(1e3, 100e3, 1e3, 101e3)  # R4 1 % high
    assert acm != 0
    v = amp.difference_amp(2.5, 2.5, 1e3, 100e3, 1e3, 101e3).v_out
    assert v == pytest.approx(acm * 2.5, rel=3e-3)  # finite-gain error ≈ 0.1 %
    assert amp.diffamp_ideal(2.5, 2.5, 1e3, 100e3, 1e3, 101e3) == pytest.approx(acm * 2.5)


def test_difference_amp_draws_input_current():
    r = amp.difference_amp(2.5, 2.5, 1e3, 1e3, 1e3, 1e3)
    # input 2 sees R3 + R4 to ground: 2 kΩ
    assert r.i_in2 == pytest.approx(2.5 / 2e3, rel=1e-6)


def test_ina_reference_gain_21():
    assert amp.ina_gain_ideal(1e3, 10e3) == 21.0
    r = amp.instrumentation_amp(2.5 - 0.001, 2.5 + 0.001, R1=1e3, R2=10e3)
    assert r.v_out == pytest.approx(21 * 0.002, rel=1e-3)


def test_ina_pure_common_mode_gives_zero():
    r = amp.instrumentation_amp(2.5, 2.5, R1=1e3, R2=10e3)
    assert abs(r.v_out) < 1e-6
    assert r.v_o1 == pytest.approx(2.5, rel=1e-4) and r.v_o2 == pytest.approx(2.5, rel=1e-4)  # stage 1: Acm = 1
    assert abs(r.i_R1) < 1e-9  # no current through R1 (or the R2s)


def test_ina_lecture_differential_case():
    # lecture: top input at 0, bottom at V -> V_o1 = -(R2/R1) V, V_o2 = (1 + R2/R1) V
    V, R1, R2 = 0.01, 1e3, 10e3
    r = amp.instrumentation_amp(0.0, V, R1=R1, R2=R2)
    assert r.v_o1 == pytest.approx(-R2 / R1 * V, rel=1e-3)
    assert r.v_o2 == pytest.approx((1 + R2 / R1) * V, rel=1e-3)
    assert r.i_R1 == pytest.approx(V / R1, rel=1e-3)


def test_ina_r1_for_gain_roundtrip():
    R1 = amp.ina_r1_for_gain(101, 10e3)
    assert amp.ina_gain_ideal(R1, 10e3) == pytest.approx(101)


def test_bridge_inputs_split():
    t = amp.time_axis()
    v1, v2 = amp.bridge_like_inputs(t, 2.5, 0.002, 0.5)
    assert (v2 - v1).max() == pytest.approx(0.002, rel=1e-3)
    assert ((v1 + v2) / 2).mean() == pytest.approx(2.5, abs=0.05)


@given(r2r1=st.floats(0.5, 200))
def test_ina_gain_monotonic_in_ratio(r2r1):
    g1 = amp.ina_gain_ideal(1e3, r2r1 * 1e3)
    g2 = amp.ina_gain_ideal(1e3, r2r1 * 1.1 * 1e3)
    assert g2 > g1


@given(vcm=st.floats(-5, 5), vd=st.floats(-0.01, 0.01))
def test_ina_matches_ideal_formula(vcm, vd):
    r = amp.instrumentation_amp(vcm - vd / 2, vcm + vd / 2, R1=2e3, R2=10e3)
    assert r.v_out == pytest.approx(amp.ina_gain_ideal(2e3, 10e3) * vd, abs=2e-4)
