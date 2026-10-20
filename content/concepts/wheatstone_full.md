On a pressure membrane, some regions stretch ($+\varepsilon$) and others compress ($-\varepsilon$). Put a gauge in each and wire them so **diagonally opposite arms see the same sign**: $R_1, R_3 = R\,(1+\Delta R/R)$ and $R_2, R_4 = R\,(1-\Delta R/R)$.

Then each midpoint moves by $\tfrac12\,(\Delta R/R)\,V_b$, in opposite directions:

$$|V_\text{out}| = \frac{\Delta R}{R}\,V_b = G\,\varepsilon\,V_b\qquad\text{(exact, no approximation)}$$

Why it wins:

* **4× the output** of a quarter bridge with the same strain and supply.
* **Linear**: each branch still totals $2R$, so no $\Delta R/R \ll 1$ approximation is needed.
* **Temperature compensation**: all four gauges drift together, and equal drifts cancel.

Transfer function (L01): $H_{\varepsilon\text{-}V} = V_\text{out}/\varepsilon = G\,V_b$.

*Notation:* L01 calls the supply $V_b$, L02 calls it $V_0$ — same thing.
