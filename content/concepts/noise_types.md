Lecture 2: *noise is any random fluctuation that adds uncertainty to a measurement.*

**Additive noise** — the measured output is the signal **plus** a random part:

$$V_\text{meas}(t) = V(t) + n(t)$$

The wiggles have the same size whether the signal is small or large (resistor thermal noise, amplifier noise).

**Multiplicative noise** — the random part **scales** the signal:

$$V_\text{meas}(t) = V(t)\,\big(1 + n(t)\big)$$

Large signal, large wiggles (e.g. a fluctuating supply or gain).

Noise is **random**: you cannot predict the next value, only describe it statistically — by its variance, and by *how its power is distributed over frequency* (the PSD). Interference (50 Hz pickup) is different: it is a known, deterministic disturbance.
