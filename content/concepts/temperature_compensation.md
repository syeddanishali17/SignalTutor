A gauge's resistance also changes with **temperature**:

$$R(T) = R\,(1 + \alpha\,\Delta T)$$

where $\alpha$ (Greek "alpha") is the **temperature coefficient** — the fractional change per kelvin.

* **Full bridge:** all four gauges sit on the same membrane at the same temperature. Every arm is multiplied by the same factor $(1+\alpha\Delta T)$, so each divider *ratio* — and therefore the output — is unchanged. The drift **cancels exactly**.
* **Quarter bridge:** only $R_1$ is on the membrane. Its thermal change is indistinguishable from a strain change: the bridge reports **apparent strain** $\varepsilon_\text{apparent} = \alpha\,\Delta T / G$.

**Sizes** (illustrative, *supplemental*): silicon piezoresistors drift by roughly 0.1 % per kelvin (strongly doping-dependent), so 10 K of warming already gives $\Delta R/R \approx 10^{-3}$, as large as a real strain signal.
