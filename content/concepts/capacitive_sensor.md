**The chain :** pressure $p$ → membrane → displacement $x(p)$ → capacitive transducer → current $I(x)$ → transimpedance amplifier → $V_\text{out}$.

**Step 1 — membrane:** $x = \dfrac{A}{2k}\,p$ (two springs). Linear.

**Step 2 — capacitor:** the gap is $d - x$, so

$$C(x) = \frac{\varepsilon A}{d - x} = \underbrace{\frac{\varepsilon A}{d}}_{C_0}\cdot\frac{1}{1 - x/d}$$

$C_0$ is the capacitance at rest. Read the fraction: as $x$ approaches $d$, the denominator $1 - x/d$ approaches 0 and $C$ shoots up.

**No constant transfer function.** Equal steps in $x$ give *growing* steps in $C$. The slope

$$\frac{\partial C}{\partial x} = \frac{\varepsilon A}{(d-x)^2} = \frac{C_0\,d}{(d-x)^2}$$

changes with $x$. (One written form gives $\frac{d}{(d-x)^2}$, missing the factor $\varepsilon A$, known issue K2.)

**Small signals:** for $x \ll d$, $C \approx C_0\,(1 + x/d)$, the tangent line. That is the only sense in which a capacitive sensor is "linear".
