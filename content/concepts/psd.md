Noise has no single frequency, so a spectrum of lines does not describe it. Instead: **power per unit bandwidth**.

$$S_V(f) \quad\text{in}\quad \frac{\text{V}^2}{\text{Hz}}$$

(written form: units of $[\text{quantity}]^2/\text{Hz}$, for a displacement noise $\text{m}^2/\text{Hz}$.)

* **White noise**: $S(f) = S_0$, the same at every frequency (like white light: all colours equally).
* **1/f noise** ("flicker", "pink"): $S(f) = S_1/f$. Strong at low frequencies, every **decade** carries the same power.

**Amplitude spectral density** (spectral amplitude): $\sqrt{S(f)}$ in $\text{V}/\sqrt{\text{Hz}}$. The form datasheets usually quote.

**Notation trap (K8):** one written form gives $S_x(f) = S_x(\omega) = S_x(2\pi f)$. Read it as *one per-hertz density, written as a function of $f$ or of $\omega$* — not two different densities. When you integrate over $\omega$ you need a factor $\frac{1}{2\pi}$.
