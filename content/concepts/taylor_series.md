A curved function can be built from simple powers. The one this course needs is the **geometric series**:

$$\frac{1}{1-u} = 1 + u + u^2 + u^3 + \dots \qquad (|u| < 1)$$

With $u = x/d$:

$$C(x) = \frac{C_0}{1 - x/d} = C_0\left(1 + \frac{x}{d} + \frac{x^2}{d^2} + \frac{x^3}{d^3} + \dots\right)$$

* **First order** keeps $1 + u$: a straight line — the tangent at $x = 0$.
* **Second order** adds $u^2$: the first bend.
* The relative error of stopping after $u^n$ is exactly $u^{n+1}$: at $u = 0.1$ the first-order error is $1\,\%$, at $u = 0.3$ already $9\,\%$.

The approximation is good **only while $u \ll 1$** — always state that condition.
