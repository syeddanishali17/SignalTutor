Lecture p. 5 expands the nonlinear factor in a geometric series:

$$\frac{1}{1 - \frac{x}{d}} \cong 1 + \frac{x}{d} + \frac{x^2}{d^2} + \frac{x^3}{d^3} + \dots$$

If $x \ll d$, keep only $1 + \frac{x}{d}$:

$$V_\text{out} \cong V_{ft}\left(1 + \frac{x}{d}\right)$$

* $V_{ft}$ — the **feed-through** voltage: the output that is there even with no pressure (lecture: $V_{ft} = R V_0 \omega\,C_0\sin\omega t$, up to the sign issue K3).
* The useful **signal** is the small extra part $V_{ft}\,\dfrac{x}{d}$.

"Small signal" means the **deflection** is small compared with the gap ($x/d \ll 1$) — not that the voltage is small. Push the membrane to $x/d = 0.3$ and the dropped $x^2/d^2$ term is already $9\,\%$ of the output.
