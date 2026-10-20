Cut the region under a curve into thin vertical strips of width $df$. Each strip has area $S(f)\cdot df$ (height × width). Add them all up:

$$\int_{f_1}^{f_2} S(f)\,df \;=\; \text{area under } S \text{ from } f_1 \text{ to } f_2$$

* **Units multiply**: if $S$ is in $\text{V}^2/\text{Hz}$ and $df$ in Hz, the area is in $\text{V}^2$.
* For a **flat** curve the area is a rectangle: height × width, $S_0\,(f_2 - f_1)$.
* For anything else you cannot use height × width — you must really add the strips (that is the trap of known issue K4).
* $\int_0^\infty$ means "all the way up": the total area.
