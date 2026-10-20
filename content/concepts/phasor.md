Engineers write oscillations as $\hat V(t) = V_0\,e^{i\omega t}$ because derivatives become simple:

$$\frac{d}{dt}\,e^{i\omega t} = i\omega\,e^{i\omega t}$$

— "differentiate" becomes "multiply by $i\omega$".

**What it means.** $e^{i\omega t} = \cos\omega t + i\sin\omega t$ is a point going round a circle of radius 1, $\omega = 2\pi f$ radians per second. Its horizontal shadow (the **real part**) is $\cos\omega t$ — that is the signal you measure. Multiplying by $i$ turns the arrow by $90^\circ$.

**Barometer (lecture p. 4–5):** $\hat V_b = V_0 e^{i\omega t}$ gives $\hat I = V_0\,i\omega C\,e^{i\omega t}$; the real current is

$$I(t) = \text{Re}\!\left[\hat I(t)\right] = \text{Re}\!\left[i\,V_0\omega C(\cos\omega t + i\sin\omega t)\right] = -V_0\,\omega C\sin\omega t.$$
