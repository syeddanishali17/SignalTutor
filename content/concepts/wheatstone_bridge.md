**Problem:** a strain gauge changes by 0.1 %. Measured directly, that is a tiny change on top of a big value.

**Idea:** build *two* voltage dividers from the same supply $V_0$ and measure the **difference** between their midpoints.

* Left divider ($R_1$ over $R_4$) sets $V_2$; right divider ($R_2$ over $R_3$) sets $V_1$.
* Equal ratios ⇒ $V_2 = V_1$ ⇒ output **0 V** (balanced). The large $V_0/2$ cancels out of the difference.
* Change one resistor ⇒ one midpoint moves ⇒ a small output that is (almost) proportional to $\Delta R/R$.

So the bridge turns "a 0.1 % change of a big number" into "a few mV away from zero" — much easier to amplify.

**Balance condition:** $\dfrac{R_1}{R_4} = \dfrac{R_2}{R_3}$.

The textbook "diamond" drawing is the same circuit rotated by 45°.
