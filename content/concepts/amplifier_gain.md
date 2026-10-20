$$A = \frac{V_\text{out}}{V_\text{in}}$$

A bridge gives a few millivolts; an analog-to-digital converter wants volts. An amplifier with gain $A = 100$ turns 2 mV into 0.2 V.

* The gain is a pure number (volts divided by volts).
* The extra energy comes from the amplifier's **power supply**, e.g. $\pm 15\,\text{V}$. The output can never leave the range set by the supply — the **rails**. Asked for more, the output simply sticks at the rail: it **saturates** (clips).
