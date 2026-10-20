**Circuit** (lecture naming): $V_1 \to R_1 \to V_-$, feedback $R_2$ from the output to $V_-$; $V_2 \to R_3 \to V_+$, $R_4$ from $V_+$ to ground.

**Result** (virtual short, no input current):

$$V_\text{out} = V_2\,\frac{R_4}{R_3 + R_4}\left(1 + \frac{R_2}{R_1}\right) - V_1\,\frac{R_2}{R_1}
\;\;\xrightarrow{\;R_2/R_1 = R_4/R_3\;}\;\; \frac{R_2}{R_1}\,(V_2 - V_1)$$

With the match, the common mode cancels: $A_{cm} = 0$. **Two problems** (lecture 2):

1. **CMR is coupled to the gain.** Any mismatch between $R_2/R_1$ and $R_4/R_3$ lets common mode through, and changing the gain means changing two resistors in step.
2. **Input impedance is finite.** The inputs draw current through $R_1$ and through $R_3 + R_4$ — that loads the Wheatstone bridge and unbalances it.

The **instrumentation amplifier** fixes both.
