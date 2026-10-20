The microphone current contains $\dfrac{x}{(1 - x/d)^2}$. A series expansion of it around $x = 0$. 

$$\frac{x}{\left(1 - \frac{x}{d}\right)^2} \approx \underbrace{0 + x}_{\text{linear response, } x \ll d} + \underbrace{2\,\frac{x^2}{d} + 3\,\frac{x^3}{d^2} + \dots}_{\text{nonlinear response}}$$

**Why new frequencies appear.** With $\hat x = x_0 e^{i\omega t}$. 

$$\hat x^2 = x_0^2\,e^{i2\omega t}, \qquad \hat x^3 = x_0^3\,e^{i3\omega t}$$

The squared term oscillates **twice** as fast, the cubed term **three** times as fast. (With real cosines: $\cos^2\omega t = \tfrac12 + \tfrac12\cos 2\omega t$.)

* The $2\omega$ part grows like $x_0^2$, the $3\omega$ part like $x_0^3$: double the loudness and the second harmonic grows four-fold.
* It is **deterministic**, not noise: it comes from the curved $C(x)$.

**THD** (total harmonic distortion, supplemental): $\sqrt{A_2^2 + A_3^2 + \dots}\,/\,A_1$.
