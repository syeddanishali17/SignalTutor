"""Reference values for the noise generator, PSD estimation and band integration (lecture 2, p. 7–8)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from tutor.sim import noise as nz

FS, N = nz.FS, nz.N


def test_white_variance_matches_psd():
    S0 = 1e-5  # V²/Hz
    x = nz.white(N, FS, S0, seed=3)
    # σ² = ∫₀^{fs/2} S0 df = S0·fs/2 = 0.05 V²
    assert nz.variance(x) == pytest.approx(S0 * FS / 2, rel=0.03)
    assert nz.rms(x) == pytest.approx(math.sqrt(S0 * FS / 2), rel=0.02)


def test_welch_recovers_white_level_and_parseval():
    S0 = 2e-6
    x = nz.white(N, FS, S0, seed=4)
    f, S = nz.welch_psd(x)
    inner = (f > 50) & (f < 4500)
    assert np.mean(S[inner]) == pytest.approx(S0, rel=0.05)
    # Parseval: the area under the one-sided PSD is the variance
    assert nz.band_power(f, S, 0.0, FS / 2) == pytest.approx(nz.variance(x), rel=0.03)


def test_band_power_white_shortcut():
    S0 = 1e-5
    x = nz.white(N, FS, S0, seed=5)
    f, S = nz.welch_psd(x)
    assert nz.band_power(f, S, 100, 1100) == pytest.approx(nz.white_band_power(S0, 100, 1100), rel=0.06)
    # the band-limited signal itself carries exactly that variance
    xb = nz.bandpass(x, FS, 100, 1100)
    assert nz.variance(xb) == pytest.approx(S0 * 1000, rel=0.08)


def test_lecture_omega_form_is_2pi_too_large():
    S0 = 1e-5
    assert nz.lecture_band_power_omega(S0, 100, 1100) / nz.white_band_power(S0, 100, 1100) == pytest.approx(
        2 * math.pi)


def test_pink_noise_slope_and_band_power():
    S1 = 1e-3  # V²: S(f) = S1/f
    x = nz.pink(N, FS, S1, seed=6)
    f, S = nz.welch_psd(x, nperseg=4096)
    sel = (f > 20) & (f < 2000)
    slope = np.polyfit(np.log10(f[sel]), np.log10(S[sel]), 1)[0]
    assert slope == pytest.approx(-1.0, abs=0.08)
    assert np.median(S[sel] * f[sel]) == pytest.approx(S1, rel=0.15)
    # band power ≈ S1·ln(f2/f1): every decade carries the same power
    assert nz.band_power(f, S, 10, 100) == pytest.approx(nz.pink_band_power(S1, 10, 100), rel=0.15)
    assert nz.pink_band_power(S1, 10, 100) == pytest.approx(nz.pink_band_power(S1, 100, 1000))


def test_one_and_two_sided_integrate_to_the_same_variance():
    S0 = 1e-5
    f = np.linspace(0, 5000, 5001)
    S = np.full_like(f, S0)
    f2, S2 = nz.two_sided(f, S)
    assert np.all(S2 == pytest.approx(S0 / 2))
    one = np.trapezoid(S, f)
    two = np.trapezoid(S2, f2)
    assert two == pytest.approx(one, rel=1e-9)
    # the classic mistake: two-sided height over the positive axis only → factor 2 too small
    assert np.trapezoid(S2[f2 >= 0], f2[f2 >= 0]) == pytest.approx(one / 2, rel=1e-6)


def test_additive_vs_multiplicative():
    t = nz.time_axis(1000, 1000.0)
    clean = nz.clean_measurement(t)
    n = np.full_like(t, 0.1)
    assert np.allclose(nz.compose(clean, n, "additive") - clean, 0.1)
    assert np.allclose(nz.compose(clean, n, "multiplicative") - clean, 0.1 * clean)
    with pytest.raises(ValueError):
        nz.compose(clean, n, "both")


def test_amplitude_spectrum_reads_sine_amplitudes():
    t = nz.time_axis(10_000, 10_000.0)
    x = nz.sine(t, 0.5, 50.0) + nz.sine(t, 0.2, 120.0)
    f, A = nz.amplitude_spectrum(x, 10_000.0)
    assert A[np.argmin(abs(f - 50))] == pytest.approx(0.5, rel=0.02)
    assert A[np.argmin(abs(f - 120))] == pytest.approx(0.2, rel=0.02)


def test_lockin_demodulator_recovers_amplitude_and_phase():
    t = nz.time_axis(20_000, 10_000.0)  # 2 s = whole periods of 1 kHz
    x = 0.3 * np.cos(2 * np.pi * 1000 * t + 0.7) + nz.white(len(t), 10_000.0, 1e-6, seed=9)
    d = nz.demodulate(x, t, 1000.0)
    assert d.R == pytest.approx(0.3, rel=0.02)
    assert d.phase == pytest.approx(0.7, abs=0.03)
