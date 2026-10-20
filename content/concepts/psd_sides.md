Mathematics likes negative frequencies ($e^{i\omega t}$ and $e^{-i\omega t}$ together make a cosine); the lab only has positive ones. So there are two conventions:

$$\sigma_x^2 = \int_0^\infty S_x(f)\,df \quad\text{(one-sided, practical)} \qquad \sigma_x^2 = \int_{-\infty}^{\infty} S''_x(f)\,df \quad\text{(two-sided)}$$

$$S''(\omega) = \tfrac12\,S(\omega)$$

Half the height, twice the width: **the area — the variance — is the same.**

**The factor-2 trap.** Mixing the conventions doubles or halves the answer:

* a two-sided density integrated only over $f \ge 0$ gives **half** the variance;
* a one-sided density integrated over $-\infty \dots \infty$ gives **twice** it.

Always state which convention a PSD uses (datasheets and lab instruments: one-sided).
