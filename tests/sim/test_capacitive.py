"""Reference values for the capacitive sensor model (lecture 1, p. 3–6)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from tutor.sim import capacitive as cap

G = cap.DEFAULT  # 1 mm², 2 µm, 2 × 2500 N/m


def test_geometry_reference_values():
    assert G.C0 == pytest.approx(8.8541878128e-12 * 1e-6 / 2e-6)  # 4.427 pF
    assert G.C0 == pytest.approx(4.427e-12, rel=1e-3)
    assert G.k_eff == 5000.0


def test_displacement_lecture_force_balance():
    # F = 2k x = p A  →  1 kPa · 1 mm² / 5000 N/m = 0.2 µm = d/10
    assert cap.displacement(1e3) == pytest.approx(2e-7)
    assert cap.h_px() == pytest.approx(1e-6 / 5000)


def test_c_of_x_and_slope():
    assert cap.c_of_x(0.0) == pytest.approx(G.C0)
    assert cap.c_of_x(G.d / 2) == pytest.approx(2 * G.C0)  # half the gap → double C
    assert cap.dc_dx(0.0) == pytest.approx(G.C0 / G.d)
    # dC/dx equals the numerical slope of C(x)
    x, h = 0.6e-6, 1e-12
    num = (cap.c_of_x(x + h) - cap.c_of_x(x - h)) / (2 * h)
    assert cap.dc_dx(x) == pytest.approx(num, rel=1e-6)
    # canonical form εA/(d − x)²
    assert cap.dc_dx(x) == pytest.approx(G.eps * G.A / (G.d - x) ** 2)


def test_touching_plates_is_invalid():
    with pytest.raises(cap.InvalidState):
        cap.c_of_x(G.d)
    with pytest.raises(cap.InvalidState):
        cap.capacitance(G.eps, G.A, 0.0)


def test_charge_qcv():
    assert cap.charge(4e-12, 2.0) == pytest.approx(8e-12)


def test_barometer_current_matches_lecture_form():
    V0, f = 1.0, 10e3
    r = cap.barometer(V0, f, x_static=0.0, n=4001)
    w = 2 * math.pi * f
    expected = -V0 * w * G.C0 * np.sin(w * r.t)  # lecture p. 5: I = −V₀ω C sin ωt
    inner = slice(5, -5)  # np.gradient is one-sided at the ends
    assert np.allclose(r.total[inner], expected[inner], atol=1e-3 * V0 * w * G.C0)
    assert np.max(np.abs(r.term_vdc)) < 1e-9 * np.max(np.abs(r.total))  # x const → V dC/dt = 0
    assert cap.barometer_amplitude(V0, f, 0.0) == pytest.approx(2.7815e-7, rel=1e-3)


def test_microphone_current_matches_analytic_and_small_signal():
    Vb, f, x0 = 2.0, 1e3, 0.02 * G.d
    r = cap.microphone(Vb, f, x0, n=6001)
    exact = cap.microphone_exact(r.t, Vb, f, x0)
    inner = slice(5, -5)
    amp = np.max(np.abs(exact))
    assert np.allclose(r.total[inner], exact[inner], atol=2e-3 * amp)
    assert np.allclose(r.term_cdv, 0.0)  # DC bias → C dV/dt = 0
    # small x0: amplitude ≈ V_b C₀ ω x₀ / d
    assert amp == pytest.approx(cap.microphone_linear_amplitude(Vb, f, x0), rel=0.05)


def test_product_rule_terms_sum_to_dq_dt():
    t = np.linspace(0, 1e-3, 5001)
    v = 1.0 + 0.5 * np.sin(2 * np.pi * 3e3 * t)
    x = 0.3e-6 * np.cos(2 * np.pi * 1e3 * t)
    r = cap.current_terms(t, v, x)
    inner = slice(5, -5)
    assert np.allclose(r.total[inner], (r.term_cdv + r.term_vdc)[inner], rtol=1e-3,
                       atol=1e-4 * np.max(np.abs(r.total)))


def test_geometric_series_and_error():
    assert cap.geometric_partial(0.1, 1) == pytest.approx(1.1)
    assert cap.geometric_exact(0.1) == pytest.approx(1 / 0.9)
    # relative error of the order-n cut is exactly u^(n+1)
    for u in (0.05, 0.2, 0.5):
        for n in (1, 2, 3):
            assert cap.relative_error(u, n) == pytest.approx(u ** (n + 1))


def test_mic_taylor_lecture_coefficients():
    # x/(1 − x/d)² ≈ x + 2x²/d + 3x³/d²   (lecture p. 6), in u = x/d
    u = 0.01
    assert cap.mic_partial(u, 3) == pytest.approx(u + 2 * u**2 + 3 * u**3)
    assert cap.mic_partial(u, 30) == pytest.approx(u / (1 - u) ** 2, rel=1e-12)


def test_harmonics_grow_with_amplitude():
    f = 1e3
    small = cap.microphone(2.0, f, 0.01 * G.d, periods=4, n=8001)
    big = cap.microphone(2.0, f, 0.3 * G.d, periods=4, n=8001)
    a_s = cap.harmonics(small.total, small.t, f)
    a_b = cap.harmonics(big.total, big.t, f)
    # second harmonic relative to the fundamental ≈ u₀ for small swings
    assert a_s[1] / a_s[0] == pytest.approx(0.01, rel=0.05)
    assert a_b[1] / a_b[0] > 0.2 and a_b[2] / a_b[0] > 0.03
    assert cap.thd(a_b) > cap.thd(a_s)


def test_pullin_reference_values():
    assert cap.pullin_x() == pytest.approx(G.d / 3)
    assert cap.pullin_voltage() == pytest.approx(36.587, rel=1e-3)
    # just below: two equilibria, lower stable below d/3, upper unstable above d/3
    eqs = cap.equilibria(0.98 * cap.pullin_voltage())
    assert len(eqs) == 2
    assert eqs[0].stable and eqs[0].x < G.d / 3
    assert not eqs[1].stable and eqs[1].x > G.d / 3
    # at pull-in they merge at d/3; above it, none
    at = cap.equilibria(cap.pullin_voltage())
    assert len(at) == 1 and at[0].x == pytest.approx(G.d / 3, rel=1e-3)
    assert cap.equilibria(1.02 * cap.pullin_voltage()) == []
    assert cap.stable_position(1.02 * cap.pullin_voltage()) is None


def test_force_balance_at_equilibrium():
    V = 25.0
    x = cap.stable_position(V)
    assert x is not None
    assert cap.spring_force(x) == pytest.approx(cap.electrostatic_force(V, x), rel=1e-6)
    assert cap.stable_position(0.0) == 0.0
