$x \ll 1$ reads "$x$ is **much smaller than** 1". The symbol $\approx$ reads "approximately equal". For a small $x$:

$$2 + x \approx 2 \qquad\qquad \frac{1}{2+x} \approx \frac{1}{2} - \frac{x}{4}$$

**Check it with numbers.** $x = 0.001$: $\dfrac{1}{2.001} = 0.4997501\ldots$ and $\dfrac12 - \dfrac{0.001}{4} = 0.49975$. They agree to seven digits.

**Why we do it.** The exact formula is messy; the approximate one shows the physics — the output is proportional to the change.

**The price.** An approximation has an error, and good practice is to know how big. For the quarter bridge the relative error is $\tfrac{1}{2}\,\Delta R/R$: for a metal gauge ($\Delta R/R \approx 10^{-3}$) that is 0.05 % — negligible; for $\Delta R/R = 0.2$ it is 10 % — not negligible.
