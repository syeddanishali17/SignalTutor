Take many samples $x_1, x_2, \dots, x_N$ of a noisy voltage.

* **Mean**: $\bar x = \dfrac{1}{N}\sum x_i$ — where the wiggles are centred.
* **Variance**: $\sigma^2 = \dfrac{1}{N}\sum (x_i - \bar x)^2$ — the average **squared** distance from the mean. Unit: $\text{V}^2$.
* **Standard deviation**: $\sigma = \sqrt{\sigma^2}$ — back in volts; about 68 % of Gaussian noise samples lie within $\pm\sigma$.
* **RMS** (root mean square): $\sqrt{\overline{x^2}}$ — square, average, take the root. For zero-mean noise **RMS = σ**.

Why squares? Positive and negative wiggles would cancel in a plain average; squaring makes every wiggle count, and squared voltage is proportional to **power** — which is what a PSD describes.
