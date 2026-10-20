The bias voltage that reads the sensor also **pulls** the plates together:

$$\underbrace{2k\,x}_{F_\text{spring}} \quad\text{vs.}\quad \underbrace{\frac{\varepsilon A\,V^2}{2\,(d - x)^2}}_{F_\text{el}\ \text{(constant } V\text{)}}$$

* For small $V$ the curves cross twice: a **stable** point (low $x$) and an **unstable** one (higher $x$).
* Raising $V$ moves them toward each other. They meet at

$$x = \frac{d}{3} \qquad\text{at}\qquad V_\text{PI} = \sqrt{\frac{8\,k_\text{eff}\,d^3}{27\,\varepsilon A}}$$

* Above $V_\text{PI}$ there is no balance at all: the membrane collapses (*pull-in*, *snap-in*).

The lecture marks $d/3$ as the **point of instability for constant $V$** (p. 5) — the $V_\text{out}(x)$ curve is only usable up to there.

**Why exactly $d/3$** (supplemental): at the touching point both the forces *and* their slopes are equal. Dividing the two conditions gives $d - x = 2x$, so $x = d/3$.

**Feedback avoids it.** Keep $x$ (or the charge) under control with a feedback loop that supplies a counter-force or adjusts the bias, and the membrane can stay anywhere — even beyond $d/3$. With constant **charge** instead of constant voltage, the attraction no longer depends on $x$ and there is no pull-in (supplemental).
