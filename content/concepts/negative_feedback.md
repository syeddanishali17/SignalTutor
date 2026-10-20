**Picture it as a loop that corrects itself.** Connect the output back to the $-$ input. If the output is too high, $V_-$ rises above $V_+$, the difference $V_+ - V_-$ turns negative, and the huge gain pulls the output down. Too low → pushed up. The output settles where

$$V_+ - V_- = \frac{V_\text{out}}{A_d} \approx 0 \qquad (A_d \text{ huge})$$

With a divider in the feedback path (only a fraction $\beta$ of the output returns), the closed-loop gain becomes

$$\frac{V_\text{out}}{V_\text{in}} = \frac{A_d}{1 + A_d\,\beta} \;\xrightarrow{A_d \to \infty}\; \frac{1}{\beta}$$

— set by **resistors**, not by the fragile op-amp gain. That is the whole point.

**Positive feedback** (output back to the $+$ input) does the opposite: every error grows until the output hits a rail.
