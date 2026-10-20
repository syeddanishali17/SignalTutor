**Why** (approach 3): the bridge needs an amplifier with

* **high input impedance** — the bridge must not be loaded,
* **high CMR** — reject the $\approx V_0/2$ level and the mains pickup,
* **simple gain adjustment** — one resistor.

**Circuit.** Stage 1: each input goes straight into an op-amp's $+$ input (so no input current at all). Each op-amp has a feedback resistor $R_2$; one resistor $R_1$ connects their inverting inputs (nodes $A$ and $B$). Stage 2: a difference amplifier with four equal resistors $R$.

**Common mode** ($V_A = V_B = V_{cm}$ by the virtual shorts): no voltage across $R_1$ → no current in $R_1$ → no current in either $R_2$ → both stage-1 outputs equal $V_{cm}$. Stage 1 passes common mode with **gain 1**; stage 2 subtracts the two equal outputs → **0**.

**Differential**: the same current $I$ flows through $R_2$, $R_1$, $R_2$ (no current can leave into the op-amp inputs, KCL). With $V_A = 0$ and $V_B = V$. 

$$I = \frac{V}{R_1},\quad V_{o2} = V\left(1 + \frac{R_2}{R_1}\right),\quad V_{o1} = -\frac{R_2}{R_1}\,V \quad\Rightarrow\quad V_{o2} - V_{o1} = \left(1 + \frac{2R_2}{R_1}\right) V$$

Change **only $R_1$** to change the gain; the CMR comes from stage 2's matched resistors and does not depend on the gain.

*Notation:* some notes reuse $V_1, V_2$ for the stage-1 outputs; this app calls them $V_{o1}, V_{o2}$ (K10).
