Sensor signals are tiny and resistances are large, so engineers glue **powers of ten** onto units:

| prefix | symbol | factor |
|---|---|---|
| pico | p | $10^{-12}$ |
| nano | n | $10^{-9}$ |
| micro | µ | $10^{-6}$ |
| milli | m | $10^{-3}$ |
| kilo | k | $10^{3}$ |
| mega | M | $10^{6}$ |

**Recipe that never fails:** convert every input to base units (V, A, Ω), compute, then choose a prefix for the answer so the number sits between 1 and 1000.

Example: $5\,\text{V}$ across $2.2\,\text{k}\Omega$ → $5 / 2200 = 0.00227\,\text{A} = 2.27\,\text{mA}$.

Strain is so small that it gets its own "unit": **microstrain**, $1\,\mu\varepsilon = 10^{-6}$ (a pure number).
