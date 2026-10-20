**The symbol.** A triangle pointing to the right. Two inputs on the left: the **non-inverting input** $V_+$ (marked $+$) and the **inverting input** $V_-$ (marked $-$). One output at the tip. Two supply connections (the **rails**, e.g. $+15\,\text{V}$ and $-15\,\text{V}$) are often left out of the drawing.

**What it does:**

$$V_\text{out} = A_d\,(V_+ - V_-) + A_{cm}\,V_{cm}$$

**The five ideal properties**

1. infinite gain for a differential signal, $A_d \to \infty$ (real: $10^5$ to $10^6$)
2. zero common-mode gain, $A_{cm} = 0$
3. infinite input impedance — the inputs draw **no current**
4. zero output impedance — the output voltage does not sag under load
5. infinite bandwidth (supplemental: real op-amps get slower at high frequency)

**Used alone** ("open loop") the gain is so huge that any difference above a few tens of µV drives the output into a **rail**. The trick that makes op-amps useful is **negative feedback** — next.
