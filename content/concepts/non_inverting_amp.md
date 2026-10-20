**Circuit** (lecture naming): input to $V_+$; $R_1$ from the output to $V_-$; $R_2$ from $V_-$ to ground.

**Derivation in three lines** (virtual short + no input current):

1. $V_- = V_+ = V_\text{in}$
2. Current through $R_2$: $I = V_\text{in}/R_2$. No current enters $V_-$, so the **same** $I$ flows through $R_1$ (KCL).
3. $V_\text{out} = V_- + I\,R_1 = V_\text{in} + V_\text{in}\dfrac{R_1}{R_2} = V_\text{in}\left(1 + \dfrac{R_1}{R_2}\right)$

**As approach 1 for the bridge** it fails: it measures one node **against ground**, so the large common mode ($\approx V_0/2$) and all pickup are amplified with the signal — "no common-mode rejection; any noise picked up by the system gets amplified".
