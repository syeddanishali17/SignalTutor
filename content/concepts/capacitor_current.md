Charge on the capacitor: $Q = V\,C$. Current is its rate of change; the **product rule** gives two terms:

$$I(t) = \frac{d}{dt}\big[V(t)\,C(t)\big] = C(t)\,\frac{dV}{dt} + V(t)\,\frac{dC}{dt}$$

**Case 1 — barometer** (quasi-static: $p$ changes very slowly). Then $\frac{dC}{dt} \approx 0$, and with a constant voltage *nothing* would flow. So apply an **AC bias** $\hat V_b = V_0\,e^{i\omega t}$. 

$$I(t) \approx C\,\frac{dV}{dt} = \text{Re}\left[V_0\,i\omega C\,e^{i\omega t}\right] = -V_0\,\omega\,C\,\sin\omega t$$

The current's **amplitude** $V_0\omega C$ is proportional to $C$, it carries the pressure. Best measured with a **lock-in amplifier** (we know the frequency; a later topic).

**Case 2 — microphone** (fast pressure, $\hat x(t) = x_0 e^{i\omega t}$). Use a **DC bias** $V_b$: then $\frac{dV}{dt} = 0$ and

$$I(t) \approx V_b\,\frac{dC}{dt} = V_b\,\frac{dC}{dx}\,\frac{dx}{dt}$$

(chain rule). With $\frac{dC}{dx} = \frac{C_0\,d}{(d-x)^2}$. $\hat I = V_b\,C_0\,\frac{d}{(d-x)^2}\,i\omega\,\hat x$. One written form gives $\frac{1}{(d-x)^2}$. Wrong units (known issue K1).
