**Picture it.** Two resistors in a row across a supply. The junction between them — the **output node** — sits somewhere between the top and the bottom voltage. Where exactly depends on how the two resistors share the voltage.

**Derive it in two lines.**

$$I = \frac{V_\text{in}}{\underbrace{R_1 + R_2}_{\text{total resistance}}} \qquad\Rightarrow\qquad V_\text{out} = I\,R_2 = V_\text{in}\,\frac{R_2}{R_1+R_2}$$

Read the fraction as **"the share of the supply that drops across the bottom resistor"**: its own resistance (numerator) over the total (denominator).

**Checks that always work**

* $R_1 = R_2$ ⇒ $V_\text{out} = V_\text{in}/2$.
* $R_2 \gg R_1$ ⇒ $V_\text{out} \to V_\text{in}$; $R_2 \ll R_1$ ⇒ $V_\text{out} \to 0$.
* Only the **ratio** matters: 1 kΩ / 1 kΩ and 10 kΩ / 10 kΩ give the same output.

**Why it matters here.** Each side of a Wheatstone bridge *is* a voltage divider. Understand the divider and the bridge is just two of them, side by side.
