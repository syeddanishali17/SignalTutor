Split the inputs into difference and common part (common-mode lesson). A real amplifier responds to both:

$$V_\text{out} = A_d\,V_d + A_{cm}\,V_{cm}$$

The **common-mode rejection ratio** compares the two gains:

$$\text{CMRR} = \frac{A_d}{A_{cm}}, \qquad \text{CMRR}_\text{dB} = 20\log_{10}\frac{A_d}{A_{cm}}$$

**Example.** $A_d = 100$, and a 1 % resistor mismatch gives $A_{cm} \approx 0.01$ → CMRR = $10^4$ = 80 dB. A 2.5 V common mode then still leaks about 25 mV to the output — comparable to the signal you wanted.

(The decibel form is *supplemental*: it is how datasheets quote it.)
