"""Noise, power spectral density and band-limited noise.

One coherent signal generator feeds every noise scene: a clean measurement plus
white or 1/f noise, added (additive) or multiplied in (multiplicative).

Conventions (stated explicitly because the notation mixes them, K4/K5/K8):

* ``S`` is a **one-sided** PSD **per hertz**, defined for f ≥ 0, unit V²/Hz.
* variance  σ² = ∫₀^∞ S(f) df  (the band [f₁, f₂]: ∫_{f₁}^{f₂} S(f) df)
* two-sided S''(f) = S(|f|)/2 on −∞ … ∞ integrates to the same σ²
* white noise S(f) = S₀: band power S₀ (f₂ − f₁);  1/f noise S(f) = S₁/f: S₁ ln(f₂/f₁)
* amplitude spectral density √S in V/√Hz

Also: generic sine generator and lock-in demodulator primitives (infrastructure for the
lock-in lesson, which waits for its lecture source).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import signal as sps

FS = 10_000.0  # Hz, sample rate of the generator
N = 2**15  # samples (3.28 s)


# --- generators -------------------------------------------------------------------------------


def time_axis(n: int = N, fs: float = FS) -> np.ndarray:
    return np.arange(n) / fs


def white(n: int, fs: float, S0: float, seed: int = 1) -> np.ndarray:
    """Gaussian white noise with one-sided PSD S0 (V²/Hz) up to fs/2: σ² = S0·fs/2."""
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, np.sqrt(S0 * fs / 2.0), n)


def shaped(n: int, fs: float, psd, seed: int = 1, f_min: float = 0.5) -> np.ndarray:
    """Noise with an arbitrary one-sided PSD ``psd(f)`` (V²/Hz): white noise of unit PSD,
    filtered in the frequency domain by √psd. Below ``f_min`` the PSD is held at psd(f_min)."""
    base = white(n, fs, 1.0, seed)
    spec = np.fft.rfft(base)
    f = np.fft.rfftfreq(n, 1.0 / fs)
    gain = np.sqrt(psd(np.maximum(f, f_min)))
    gain[0] = 0.0  # no DC offset
    return np.fft.irfft(spec * gain, n)


def pink(n: int, fs: float, S1: float, seed: int = 1, f_min: float = 0.5) -> np.ndarray:
    """1/f noise: one-sided PSD S1/f (S1 in V²)."""
    return shaped(n, fs, lambda f: S1 / f, seed, f_min)


def sine(t: np.ndarray, amplitude: float, f: float, phase: float = 0.0) -> np.ndarray:
    return amplitude * np.sin(2 * np.pi * f * t + phase)


def clean_measurement(t: np.ndarray) -> np.ndarray:
    """The written sketch of a sensor output: a smooth S-shaped rise (V)."""
    T = t[-1] if len(t) else 1.0
    return 0.3 + 0.7 / (1.0 + np.exp(-(t / T - 0.5) * 9.0))


def compose(clean: np.ndarray, noise: np.ndarray, mode: str = "additive") -> np.ndarray:
    """Additive: clean + noise. Multiplicative: clean·(1 + noise) — the noise scales with the signal.
    For multiplicative noise, ``noise`` is relative (dimensionless)."""
    if mode == "additive":
        return clean + noise
    if mode == "multiplicative":
        return clean * (1.0 + noise)
    raise ValueError(f"unknown noise mode {mode!r}")


# --- statistics -------------------------------------------------------------------------------


def variance(x: np.ndarray) -> float:
    return float(np.var(x))


def rms(x: np.ndarray) -> float:
    """Root mean square √(mean x²). For zero-mean noise RMS = standard deviation σ."""
    return float(np.sqrt(np.mean(np.asarray(x) ** 2)))


# --- spectra ------------------------------------------------------------------------------------


def welch_psd(x: np.ndarray, fs: float = FS, nperseg: int = 2048) -> tuple[np.ndarray, np.ndarray]:
    """One-sided PSD estimate (V²/Hz) by Welch's method (Hann window, 50 % overlap)."""
    f, S = sps.welch(x, fs=fs, nperseg=nperseg, window="hann", detrend="constant", scaling="density",
                     return_onesided=True)
    return f, S


def amplitude_spectrum(x: np.ndarray, fs: float = FS) -> tuple[np.ndarray, np.ndarray]:
    """Peak amplitude of each sine component (V) — the 'sum of sines' picture."""
    n = len(x)
    w = np.hanning(n)
    spec = np.fft.rfft(x * w)
    f = np.fft.rfftfreq(n, 1.0 / fs)
    return f, 2.0 * np.abs(spec) / np.sum(w)


def band_power(f: np.ndarray, S: np.ndarray, f1: float, f2: float) -> float:
    """∫_{f1}^{f2} S(f) df by the trapezoid rule on a fine interpolation of (f, S)."""
    if f2 <= f1:
        return 0.0
    ff = np.linspace(f1, f2, 2001)
    return float(np.trapezoid(np.interp(ff, f, S), ff))


def white_band_power(S0: float, f1: float, f2: float) -> float:
    return S0 * (f2 - f1)


def pink_band_power(S1: float, f1: float, f2: float) -> float:
    return S1 * np.log(f2 / f1)


def lecture_band_power_omega(S0: float, f1: float, f2: float) -> float:
    """The written form S·(ω₂ − ω₁) with a per-Hz S: 2π too large (K4)."""
    return S0 * 2 * np.pi * (f2 - f1)


def two_sided(f: np.ndarray, S: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Mirror a one-sided PSD to −f … +f with half the height: S''(f) = S(|f|)/2."""
    ff = np.concatenate([-f[:0:-1], f])
    SS = np.concatenate([S[:0:-1], S]) / 2.0
    return ff, SS


def bandpass(x: np.ndarray, fs: float, f1: float, f2: float) -> np.ndarray:
    """Ideal band-pass (FFT mask) — what a measurement restricted to [f1, f2] would see."""
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / fs)
    spec[(f < f1) | (f > f2)] = 0.0
    return np.fft.irfft(spec, len(x))


# --- lock-in primitives (infrastructure; no lesson until that material exists) -----------


@dataclass(frozen=True)
class Demodulated:
    X: float  # in-phase component (V)
    Y: float  # quadrature component (V)

    @property
    def R(self) -> float:
        return float(np.hypot(self.X, self.Y))

    @property
    def phase(self) -> float:
        return float(np.arctan2(self.Y, self.X))


def demodulate(x: np.ndarray, t: np.ndarray, f_ref: float) -> Demodulated:
    """Multiply by the reference cos/sin and average (ideal low-pass over the whole record).

    For x = A·cos(2π f_ref t + φ) and X = 2⟨x·cos⟩, Y = −2⟨x·sin⟩:  X = A cos φ, Y = A sin φ,
    so R = √(X² + Y²) = A and atan2(Y, X) = φ (exact for a whole number of periods).
    """
    c = np.cos(2 * np.pi * f_ref * t)
    s = np.sin(2 * np.pi * f_ref * t)
    return Demodulated(float(2 * np.mean(x * c)), float(-2 * np.mean(x * s)))
