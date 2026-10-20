Any pair of voltages can be split into a **shared part** and a **difference**:

$$V_{cm} = \frac{V_1 + V_2}{2}, \qquad V_d = V_2 - V_1, \qquad V_1 = V_{cm} - \frac{V_d}{2}, \quad V_2 = V_{cm} + \frac{V_d}{2}$$

* **Common mode**: both inputs move **together** — same direction, same amount.
* **Differential**: the inputs move **in opposite directions**.

In a bridge the common mode is large ($\approx V_0/2$, e.g. 2.5 V) and harmless. Mains pickup (50 Hz) also tends to arrive as common mode, because it couples into both wires alike. A good differential amplifier must amplify $V_d$ and **reject** $V_{cm}$ — its *common-mode rejection*.
