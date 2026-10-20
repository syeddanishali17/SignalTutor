* **Signal** — the part that carries the information (here: the bridge's millivolt difference).
* **Interference** — a disturbance from an identifiable source: mains cables at **50 Hz**, motors, radio.
* **Noise** — random fluctuations (thermal, …); it gets its own lessons later.

**How mains gets in.** A mains cable is surrounded by an alternating electric field. Any wire near it picks up a little 50 Hz voltage — like an antenna. Two wires running **side by side** pick up almost the **same** amount, so the pickup appears as **common mode**:

$$V_1 = V_{cm} - \tfrac{V_d}{2} + v_\text{pickup},\qquad V_2 = V_{cm} + \tfrac{V_d}{2} + v_\text{pickup} \quad\Rightarrow\quad V_2 - V_1 = V_d$$

The pickup cancels in the difference. An amplifier that amplifies the **difference** only — and rejects what both wires share — removes it.
