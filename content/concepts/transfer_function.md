Every transducer turns an input $X$ into an output $Y$. When the output is proportional to the input, one number describes the stage:

$$H = \frac{Y}{X} \qquad\Rightarrow\qquad Y = H\,X$$

**Chains multiply.** The piezoresistive sensor: $H_{p\text{-}V} = H_{p\text{-}\varepsilon}\cdot H_{\varepsilon\text{-}V} = \xi\,G\,V_b$. Each stage scales what the previous stage delivered.

**Sensitivity** is the slope $\dfrac{\Delta V}{\Delta p}$ . For a linear sensor it is the same everywhere; in the **nonlinear regime** it changes along the curve.

**When there is no transfer function.** The capacitive sensor's $C(x) = \dfrac{C_0}{1 - x/d}$ is curved *from the start*: equal steps in $x$ give *unequal* steps in $C$. There is no single number $H$ any more — the notes: *"no more H!"*. Only for small $x$ (small-signal approximation) can we use the slope at one operating point.
