A wiggly signal in time can be taken apart into sine waves of different frequencies (Fourier's idea; the FFT does it numerically).

* **Time domain**: voltage against time — what an oscilloscope shows.
* **Frequency domain**: strength against frequency — the **spectrum**. Each sine component becomes one line at its frequency, as tall as its amplitude.

Same information, two views. The spectrum makes some things obvious: a 50 Hz hum is one sharp line; the harmonics $2\omega$, $3\omega$ of a distorted microphone are extra lines; **noise** has no single frequency — it is spread over all of them as a low "floor".

That spread-out power is described by the **power spectral density** (next idea).
