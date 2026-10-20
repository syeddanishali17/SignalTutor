**Picture it.** A thin, zig-zag metal track (or a doped strip of silicon) glued to — or built into — the part that bends. When the part stretches, the track gets longer and thinner, so its resistance goes up. Compressed, it goes down.

**What it is.**

$$G = \frac{\Delta R / R}{\varepsilon} \qquad\Longleftrightarrow\qquad \frac{\Delta R}{R} = G\,\varepsilon$$

* Metal foil: $G \approx 2$, mostly geometry (longer and thinner).
* Silicon piezoresistor: $G$ of order 100 — the material's resistivity itself changes.

**Worked example.** $G = 2$, $\varepsilon = 500\,\mu\varepsilon$ ⇒ $\Delta R/R = 2 \times 500\times10^{-6} = 10^{-3}$. On a 350 Ω gauge that is $\Delta R = 0.35\,\Omega$. Far too small to read reliably with an ohmmeter. That is why the gauge goes into a **Wheatstone bridge**.

**In the transfer chain** : pressure $\xrightarrow{\ \xi\ }$ strain $\xrightarrow{\ G\ }$ $\Delta R/R$ $\xrightarrow{\text{bridge}}$ voltage, with $H_{\varepsilon\text{-}V} = G\,V_b$ once the full bridge is included.
