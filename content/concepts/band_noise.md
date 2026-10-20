A measurement only "sees" the frequencies it lets through, $[f_1, f_2]$. The noise power that gets in is the area under the PSD there:

$$\sigma^2_{[f_1, f_2]} = \int_{f_1}^{f_2} S(f)\,df \qquad\text{(V}^2\text{)}, \qquad V_\text{rms} = \sqrt{\sigma^2}$$

* **White** noise: a rectangle, $\sigma^2 = S_0\,(f_2 - f_1)$. Halve the bandwidth → half the power, $1/\sqrt2$ of the RMS.
* **1/f** noise: $\sigma^2 = S_1 \ln\dfrac{f_2}{f_1}$. Each decade adds the same amount.
* The whole variance: $\sigma^2 = \int_0^\infty S(f)\,df$.

**Common traps (K4, K5).** One written form gives the band power as $S_V(\omega)\cdot(\omega_2 - \omega_1)$:

1. that shortcut is valid **only for white noise**;
2. with a per-hertz $S$, integrating over $\omega$ needs $\frac{1}{2\pi}$. $\int S\,df = \frac{1}{2\pi}\int S\,d\omega$. Without it the result is $2\pi$ too large.
