Only $R_1$ is a strain gauge, $R_1 = R + \Delta R$; the other three are fixed $R$.

Each branch is a divider (the ideal voltmeter draws no current):

$$I_1 = \frac{V_0}{2R},\quad I_2 = \frac{V_0}{2R+\Delta R},\quad V_1 = I_1 R = \frac{V_0}{2},\quad V_2 = I_2 R = \frac{V_0}{2 + \Delta R/R}$$

$$V_2 - V_1 = V_0\left(\frac{1}{2+\Delta R/R} - \frac12\right) \approx -\frac14\,\frac{\Delta R}{R}\,V_0 \quad\text{for } \frac{\Delta R}{R}\ll 1$$

* The **exact** result is slightly nonlinear; the approximation overestimates its size by a relative $\tfrac12\,\Delta R/R$.
* The **sign** depends on which arm holds the gauge and which node you call +. (The L02 drawing and derivation disagree on the arm — see known issue K9.)
