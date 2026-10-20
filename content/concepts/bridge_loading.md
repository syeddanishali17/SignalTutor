The bridge derivation starts with an assumption written as $I = 0$ next to the output: the **voltmeter draws no current**, so each branch keeps its own current.

A real meter or amplifier has a finite **input resistance** $R_\text{in}$. Connected between the midpoints, it lets current flow from one divider to the other and **pulls the two midpoints towards each other** — the reading shrinks.

For a bridge of four equal resistors $R$, seen from the meter the bridge behaves like the open-circuit output in series with $R$, so

$$V_\text{read} \approx V_\text{open}\,\frac{R_\text{in}}{R_\text{in} + R}$$

$R_\text{in} = 10\,R$ loses about 9 %; $R_\text{in} = 1000\,R$ loses 0.1 %.

This is the same problem a difference amplifier raises — its input impedance is set by ordinary resistors, "less than ∞" — and why the **instrumentation amplifier** feeds the bridge straight into op-amp inputs.
