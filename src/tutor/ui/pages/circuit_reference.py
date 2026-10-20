"""Handbook copy and equations. No learner state or content-loader extensions.

Notation follows the simulators, especially bridge.py and amplifiers.py.
Standard ideal-circuit results are independently stated, not source transcriptions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    title: str
    meaning: str
    equations: tuple[str, ...] = ()
    where: str = ""
    figure: str = ""
    note: str = ""
    example: tuple[str, str, str, str] | None = None


@dataclass(frozen=True)
class Section:
    anchor: str
    title: str
    entries: tuple[Entry, ...]


SECTIONS = (
    Section("electrical-quantities", "Electrical quantities", (
        Entry("Charge", "Charge is a property of matter. A net charge can be positive or negative; charge is conserved.",
              (r"Q=Nq_e",), "$Q$: charge (C, coulomb); $N$: signed number of elementary charges; "
              "$q_e=1.602176634\\times10^{-19}\\,\\mathrm{C}$: elementary-charge magnitude. An electron carries $-q_e$."),
        Entry("Current", "Current is the rate at which charge crosses a chosen surface. Conventional current follows "
              "positive charge; electrons in a metal drift in the opposite direction. A steady DC current needs a closed path.",
              (r"I_{\rm avg}=\frac{\Delta Q}{\Delta t}", r"I=\frac{dQ}{dt},\qquad 1\,\mathrm{A}=1\,\mathrm{C/s}"),
              "$I$: current (A, ampere); $\\Delta Q$: transferred charge (C); $\\Delta t$: time interval (s). "
              "$dQ/dt$ is the instantaneous rate.", "loop"),
        Entry("Voltage", "Voltage is always a difference between two points. Specify both measurement nodes and their order.",
              (r"V_{AB}=V_A-V_B",), "$V_A,V_B$: node potentials relative to the same reference (V, volt); "
              "$V_{AB}$: potential of A relative to B (V). Swapping meter leads reverses the sign.", "voltage",
              example=(r"V_A=6\,\mathrm{V},\ V_B=2\,\mathrm{V}", r"V_{AB}=V_A-V_B",
                       r"V_{AB}=(6-2)\,\mathrm{V}", r"V_{AB}=4\,\mathrm{V}")),
        Entry("Resistance and conductance", "Resistance describes opposition to current. Conductance describes how readily "
              "current flows. An ohmic resistor has a constant resistance under the stated operating conditions.",
              (r"R=\frac{V}{I},\qquad G_{\rm cond}=\frac{1}{R}",),
              "$R$: resistance ($\\Omega$, ohm); $V$: voltage across the resistor (V); $I$: current (A); "
              "$G_{\\rm cond}$: conductance (S, siemens). This subscript distinguishes it from gauge factor $G$ below."),
    )),
    Section("ohms-law", "Ohm's law", (
        Entry("The three forms", "For an ohmic resistor, doubling the voltage doubles current; doubling resistance halves "
              "current at fixed voltage. Use the passive sign convention: current enters the terminal labelled positive.",
              (r"V=IR,\qquad I=\frac{V}{R},\qquad R=\frac{V}{I}",),
              "$V$: resistor voltage (V); $I$: current (A); $R$: resistance ($\\Omega$). The quotient $V/I$ requires $I\\ne0$.",
              example=(r"V=6\,\mathrm{V},\ R=2\,\mathrm{k}\Omega", r"I=V/R",
                       r"I=6\,\mathrm{V}/(2000\,\Omega)", r"I=3\,\mathrm{mA}")),
    )),
    Section("power-energy", "Power & energy", (
        Entry("Power dissipated; energy transferred", "Power is the rate of energy transfer. A passive resistor converts "
              "electrical energy into heat. Energy accumulates over time.",
              (r"P=VI=I^2R=\frac{V^2}{R}", r"E=Pt\quad\text{(constant power)}", r"E=\int_{t_1}^{t_2}P(t)\,dt"),
              "$P$: power (W, watt = J/s); $E$: energy (J, joule); $t$: duration (s). The resistance forms apply to a resistor; "
              "the integral handles changing power. Positive $VI$ means absorbed power under the passive convention.",
              example=(r"I=3\,\mathrm{mA},\ R=2\,\mathrm{k}\Omega,\ t=10\,\mathrm{s}", r"P=I^2R,\ E=Pt",
                       r"P=(0.003)^2(2000)\,\mathrm{W}", r"P=18\,\mathrm{mW},\quad E=0.18\,\mathrm{J}")),
    )),
    Section("series-parallel", "Series & parallel circuits", (
        Entry("Series resistors", "The same current flows through elements in a single unbranched path. Their voltage drops add.",
              (r"R_{\rm eq}=R_1+R_2+\cdots+R_n", r"V_k=IR_k"),
              "$R_{\\rm eq}$: equivalent resistance; $R_k$: resistance of element $k$ (all $\\Omega$); $V_k$: its drop (V); "
              "$I$: common current (A); $n$: number of resistors.", "series",
              example=(r"R_1=1\,\mathrm{k}\Omega,\ R_2=2\,\mathrm{k}\Omega,\ V_S=6\,\mathrm{V}",
                       r"R_{\rm eq}=R_1+R_2,\ I=V_S/R_{\rm eq}", r"I=6/3000\,\mathrm{A}",
                       r"R_{\rm eq}=3\,\mathrm{k}\Omega,\ I=2\,\mathrm{mA},\ V_1=2\,\mathrm{V},\ V_2=4\,\mathrm{V}")),
        Entry("Parallel resistors", "Branches connected across the same two nodes have the same voltage. Branch currents add. "
              "For positive finite branch resistances, the equivalent is smaller than the smallest branch resistance.",
              (r"\frac{1}{R_{\rm eq}}=\sum_{k=1}^{n}\frac{1}{R_k}",
               r"R_{\rm eq}=\frac{R_1R_2}{R_1+R_2}\quad\text{(two branches)}"),
              "$R_k$: branch resistance ($\\Omega$); $R_{\\rm eq}$: resistance seen across the two common nodes ($\\Omega$).",
              "parallel", example=(r"R_1=1\,\mathrm{k}\Omega,\ R_2=2\,\mathrm{k}\Omega",
                                    r"R_{\rm eq}=R_1R_2/(R_1+R_2)", r"R_{\rm eq}=1000(2000)/3000\,\Omega",
                                    r"R_{\rm eq}\approx667\,\Omega")),
    )),
    Section("dividers", "Voltage & current dividers", (
        Entry("Voltage divider", "With no load drawing current from the midpoint, the same current passes through both "
              "resistors. Ohm's law converts that current into the voltage across the lower resistor.",
              (r"I=\frac{V_{\rm in}}{R_1+R_2}", r"V_{\rm out}=IR_2=V_{\rm in}\frac{R_2}{R_1+R_2}"),
              "$V_{\\rm in}$: supply (V); $R_1$: upper resistor; $R_2$: lower resistor (both $\\Omega$); "
              "$V_{\\rm out}$: midpoint relative to ground (V); $I$: series current (A).", "divider",
              "A load changes the lower resistance to $R_2\\parallel R_L$. Recalculate the divider when loading matters.",
              (r"V_{\rm in}=9\,\mathrm{V},\ R_1=1\,\mathrm{k}\Omega,\ R_2=2\,\mathrm{k}\Omega",
               r"V_{\rm out}=V_{\rm in}R_2/(R_1+R_2)", r"V_{\rm out}=9(2/3)\,\mathrm{V}", r"V_{\rm out}=6\,\mathrm{V}")),
        Entry("Current divider", "For two parallel resistors, the smaller resistance takes the larger share of total current. "
              "The other branch's resistance appears in the numerator.",
              (r"I_1=I_{\rm total}\frac{R_2}{R_1+R_2}", r"I_2=I_{\rm total}\frac{R_1}{R_1+R_2}"),
              "$I_1,I_2$: branch currents (A); $I_{\\rm total}=I_1+I_2$: current entering the split (A); "
              "$R_1,R_2$: positive branch resistances ($\\Omega$).",
              example=(r"I_{\rm total}=6\,\mathrm{mA},\ R_1=1\,\mathrm{k}\Omega,\ R_2=2\,\mathrm{k}\Omega",
                       r"I_1=I_{\rm total}R_2/(R_1+R_2)", r"I_1=6(2/3)\,\mathrm{mA}",
                       r"I_1=4\,\mathrm{mA},\quad I_2=2\,\mathrm{mA}")),
    )),
    Section("kirchhoff", "Kirchhoff laws: KCL & KVL", (
        Entry("Kirchhoff's Current Law (KCL)", "Current entering a node equals current leaving it. Assign entering currents "
              "positive and leaving currents negative, or use the reverse convention consistently.",
              (r"\sum_k I_k=0", r"I_{\rm in}=I_1+I_2"),
              "$I_k$: signed branch current at a node (A). The drawing names the incoming current $I_{\\rm in}$ and outgoing currents $I_1,I_2$.",
              "kcl", example=(r"I_{\rm in}=6\,\mathrm{mA},\ I_1=4\,\mathrm{mA}", r"I_2=I_{\rm in}-I_1",
                              r"I_2=(6-4)\,\mathrm{mA}", r"I_2=2\,\mathrm{mA}")),
        Entry("Kirchhoff's Voltage Law (KVL)", "The algebraic sum of voltage rises and drops around a closed lumped-circuit "
              "loop is zero. Going from − to + across a source is a rise; moving along current through a resistor is a drop.",
              (r"\sum_k V_k=0", r"V_S-V_{R1}-V_{R2}=0"),
              "$V_k$: signed voltage change (V); $V_S$: supply rise; $V_{R1},V_{R2}$: positive resistor-drop magnitudes (V).",
              note="The series-circuit drawing above is also a KVL loop: 6 V − 2 V − 4 V = 0. "
                   "Time-varying magnetic flux requires the induced-emf term; do not apply the simple electrostatic loop rule blindly."),
    )),
    Section("reference-open-short", "Ground, open & short circuits", (
        Entry("Ground and voltage reference", "Ground is the chosen zero-volt reference, not necessarily Earth. Changing "
              "reference changes node labels but does not change physical voltage differences.",
              (r"V_{\rm ground}=0\,\mathrm{V}", r"(V_A-V_C)-(V_B-V_C)=V_A-V_B"),
              "$V_C$: potential of the newly chosen reference (V); $V_A,V_B$: original node potentials (V)."),
        Entry("Open circuit", "An ideal open breaks the conducting path. It can support a nonzero voltage while carrying no current.",
              (r"R\to\infty\quad\Longrightarrow\quad I\to0\quad\text{for finite }V",),
              "$R$: path resistance ($\\Omega$); $I$: path current (A); $V$: applied voltage (V).", "open"),
        Entry("Short circuit", "An ideal short connects two nodes with zero resistance, so their voltage difference is zero. "
              "Current is set by the rest of the circuit. Real sources, wires and protection limit current; real shorts can overheat.",
              (r"R\to0,\qquad V_{\rm short}=0\quad\text{(ideal wire)}",),
              "$V_{\\rm short}$: voltage across the wire (V). An ideal nonzero voltage source directly shorted has no finite ideal-circuit solution."),
    )),
    Section("sources", "Sources & equivalent circuits", (
        Entry("Ideal voltage and current sources", "A voltage source maintains its voltage while the load determines current. "
              "A current source maintains its current while the load determines voltage. Real sources have finite operating limits.",
              (r"V=V_S\quad\text{(ideal voltage source)}", r"I=I_S\quad\text{(ideal current source)}"),
              "$V_S$: specified source voltage (V); $I_S$: specified source current (A). Source arrows specify positive current direction.", "sources"),
        Entry("Source resistance and loading", "A practical source can often be approximated by a voltage source in series "
              "with a source resistance. A finite load lowers its terminal voltage.",
              (r"V_L=V_{\rm th}\frac{R_L}{R_{\rm th}+R_L}",),
              "$V_L$: loaded terminal voltage (V); $V_{\\rm th}$: open-circuit voltage (V); $R_{\\rm th}$: source resistance; "
              "$R_L$: load resistance (both $\\Omega$).", "loading",
              example=(r"V_{\rm th}=5\,\mathrm{V},\ R_{\rm th}=1\,\mathrm{k}\Omega,\ R_L=9\,\mathrm{k}\Omega",
                       r"V_L=V_{\rm th}R_L/(R_{\rm th}+R_L)", r"V_L=5(9/10)\,\mathrm{V}", r"V_L=4.5\,\mathrm{V}")),
        Entry("Thévenin equivalent · Next step", "At a chosen pair of terminals, a linear resistive network can be represented "
              "by its open-circuit voltage in series with its equivalent resistance. A divider is one useful original network.",
              (r"V_{\rm th}=V_S\frac{R_2}{R_1+R_2},\qquad R_{\rm th}=R_1\parallel R_2",),
              "For the unloaded divider above: $V_S$ is its supply (V), $R_1,R_2$ are its resistors ($\\Omega$), "
              "and $\\parallel$ means parallel combination. Look into its midpoint/ground terminals with the ideal voltage source shorted.",
              note="Turn off independent voltage sources by shorting and independent current sources by opening. "
                   "Keep dependent sources active and use a test source if necessary. Reactive networks use impedance equivalents."),
        Entry("Norton equivalent · Next step", "The same linear one-port can be represented by a current source in parallel "
              "with a resistance. The chosen source direction must give the same terminal polarity as the Thévenin source.",
              (r"R_N=R_{\rm th},\qquad I_N=\frac{V_{\rm th}}{R_{\rm th}}",),
              "$I_N$: short-circuit current (A); $R_N$: parallel resistance ($\\Omega$). The conversion requires a finite nonzero $R_{\\rm th}$.", "norton"),
    )),
    Section("capacitors", "Capacitors", (
        Entry("Charge, voltage and current", "A capacitor stores separated charge. When voltage or capacitance changes, "
              "the stored charge changes and current flows.",
              (r"Q=CV,\qquad C=\frac{Q}{V}", r"I=\frac{dQ}{dt}",
               r"I=C\frac{dV}{dt}\quad\text{(constant }C\text{)}",
               r"I=\frac{d(CV)}{dt}=C\frac{dV}{dt}+V\frac{dC}{dt}"),
              "$Q$: charge on the positive-reference plate (C); $C$: capacitance (F, farad = C/V); $V$: voltage across the capacitor (V); "
              "$I$: current into that plate (A); $t$: time (s). The first term changes voltage; the second changes capacitance."),
        Entry("Parallel-plate capacitance", "Increasing plate area increases capacitance. Increasing the separation decreases "
              "it. This simple model neglects edge fields and assumes a uniform dielectric.",
              (r"C=\frac{\varepsilon_{\rm diel} A}{d}",),
              "$\\varepsilon_{\\rm diel}$: dielectric permittivity (F/m), distinguished from strain $\\varepsilon$; "
              "$A$: facing area (m²); $d$: separation (m); $C$: capacitance (F).", "capacitor",
              example=(r"\varepsilon_{\rm diel}=8.854\times10^{-12}\,\mathrm{F/m}",
                       r"C=\varepsilon_{\rm diel}A/d", r"C=(8.854\times10^{-12})(10^{-6})/(2\times10^{-6})\,\mathrm{F}",
                       r"A=1\,\mathrm{mm^2},\ d=2\,\mu\mathrm{m}\quad\Rightarrow\quad C\approx4.427\,\mathrm{pF}")),
        Entry("Capacitors in parallel and series", "Parallel capacitors share a voltage and their charges add. "
              "A simple series chain with initially uncharged floating junctions carries equal charge magnitudes.",
              (r"C_{\rm eq}=\sum_k C_k\quad\text{(parallel)}", r"\frac{1}{C_{\rm eq}}=\sum_k\frac{1}{C_k}\quad\text{(series)}"),
              "$C_k$: individual capacitances (F); $C_{\\rm eq}$: equivalent capacitance (F).", "capacitors",
              "*The equal-charge statement assumes no initial net charge on the isolated intermediate nodes.",
              (r"C_1=C_2=100\,\mathrm{nF}", r"C_{\parallel}=C_1+C_2,\ C_{\rm series}=C_1C_2/(C_1+C_2)",
               r"C_{\rm series}=100(100)/(100+100)\,\mathrm{nF}", r"C_{\parallel}=200\,\mathrm{nF},\quad C_{\rm series}=50\,\mathrm{nF}")),
    )),
    Section("rc-rl", "RC circuits, inductors & RL circuits", (
        Entry("RC time constant", "A resistor limits how quickly a capacitor can charge. After one time constant, a zero-start "
              "charging capacitor reaches about 63.2% of the supply; discharge leaves about 36.8% of the initial voltage.",
              (r"\tau=RC", r"V_C(t)=V_S\left(1-e^{-t/\tau}\right)\quad\text{(charge from zero)}",
               r"V_C(t)=V_0e^{-t/\tau}\quad\text{(discharge toward zero)}"),
              "$\\tau$: time constant (s); $R$: total resistance seen by the capacitor ($\\Omega$); $C$: capacitance (F); "
              "$V_S$: constant charging supply; $V_0$: initial discharge voltage; $V_C$: capacitor voltage (all V); $t\\ge0$: time after switching (s).",
              "rc", example=(r"R=10\,\mathrm{k}\Omega,\ C=100\,\mathrm{nF},\ V_S=5\,\mathrm{V}",
                             r"\tau=RC,\quad V_C(\tau)=V_S(1-e^{-1})", r"\tau=10^4(10^{-7})\,\mathrm{s}",
                             r"\tau=1\,\mathrm{ms},\quad V_C(\tau)\approx3.16\,\mathrm{V}")),
        Entry("Inductor fundamentals", "An inductor stores magnetic energy. It opposes sudden current changes, just as a "
              "capacitor opposes sudden voltage changes. Finite voltage cannot instantaneously change ideal-inductor current.",
              (r"V=L\frac{dI}{dt},\qquad E_L=\frac12 LI^2",),
              "$L$: inductance (H, henry = V·s/A); $V$: voltage with current entering the positive terminal (V); "
              "$I$: current (A); $E_L$: stored energy (J).", "inductor"),
        Entry("RL time constant", "In a simple series RL circuit driven by a DC step from zero current, current approaches "
              "its final value exponentially. On discharge through a resistance it decays exponentially.",
              (r"\tau=\frac{L}{R}", r"I(t)=\frac{V_S}{R}(1-e^{-t/\tau})", r"I_{\rm decay}(t)=I_0e^{-t/\tau}"),
              "$R$: total resistance in the current path ($\\Omega$); $L$: inductance (H); $I_0$: initial discharge current (A); "
              "$V_S$: step voltage (V); $t$: time (s).",
              example=(r"L=10\,\mathrm{mH},\ R=100\,\Omega,\ V_S=5\,\mathrm{V}", r"\tau=L/R,\ I_\infty=V_S/R",
                       r"\tau=0.01/100\,\mathrm{s}", r"\tau=100\,\mu\mathrm{s},\quad I_\infty=50\,\mathrm{mA}")),
    )),
    Section("ac-rms-phase", "AC signals, RMS & phase", (
        Entry("Sine-wave fundamentals", "A sinusoid repeats every period. Phase specifies where in the cycle it starts.",
              (r"v(t)=V_{\rm pk}\sin(\omega t+\phi)", r"\omega=2\pi f,\qquad T=\frac{1}{f}"),
              "$v(t)$: instantaneous voltage (V); $V_{\\rm pk}$: peak amplitude (V); $f$: frequency (Hz); "
              "$\\omega$: angular frequency (rad/s); $T$: period (s); $\\phi$: phase (rad).", "sine"),
        Entry("Peak, peak-to-peak and RMS", "RMS is the square root of mean square over a cycle. It gives the DC-equivalent "
              "heating effect in a resistor. The peak-to-RMS shortcuts here apply to a zero-offset sinusoid.",
              (r"V_{\rm pp}=2V_{\rm pk}", r"V_{\rm rms}=\frac{V_{\rm pk}}{\sqrt2},\qquad I_{\rm rms}=\frac{I_{\rm pk}}{\sqrt2}",
               r"V_{\rm rms}=\sqrt{\frac1T\int_0^T v^2(t)\,dt}"),
              "$V_{\\rm pp}$: maximum minus minimum voltage (V); $V_{\\rm rms}$: RMS voltage (V); "
              "$I_{\\rm pk},I_{\\rm rms}$: peak/RMS current (A); $T$: period (s). Use the integral for other waveforms or DC offsets.",
              example=(r"V_{\rm pk}=2\,\mathrm{V}", r"V_{\rm rms}=V_{\rm pk}/\sqrt2", r"V_{\rm rms}=2/\sqrt2\,\mathrm{V}",
                       r"V_{\rm pp}=4\,\mathrm{V},\quad V_{\rm rms}\approx1.414\,\mathrm{V}")),
        Entry("Phase: in phase, leading and lagging", "Compare signals at the same frequency. Equal phase means their peaks "
              "coincide. A positive phase shift in the sine convention below makes a peak arrive earlier: the signal leads.",
              (r"v_1=V_{\rm pk}\sin(\omega t),\quad v_2=V_{\rm pk}\sin(\omega t+\phi)",
               r"\Delta t=\frac{\phi}{\omega}\quad\text{(lead for }\phi>0\text{)}"),
              "$\\phi$: phase of $v_2$ relative to $v_1$ (rad, modulo $2\\pi$); $\\Delta t$: corresponding lead (s). "
              "A negative phase shift is a lag. Here a quarter cycle is $\\pi/2$ rad = 90°.", "phase"),
        Entry("Complex numbers and phasors · Next step", "A phasor packages a sinusoid's amplitude and phase into one complex "
              "number for steady-state calculations at a single frequency. It is not the instantaneous waveform.",
              (r"j^2=-1,\qquad e^{j\phi}=\cos\phi+j\sin\phi", r"\underline V=V_{\rm rms}e^{j\phi}"),
              "$j$: imaginary unit; $\\underline V$: RMS voltage phasor (V); $\\phi$: phase (rad). "
              "Use a consistent sine or cosine reference for every phasor; this handbook uses the sine reference above."),
    )),
    Section("impedance", "Impedance & AC Ohm's law", (
        Entry("Resistance generalized to AC", "Impedance describes both amplitude ratio and phase shift. Capacitors become "
              "easier for AC to pass as frequency rises; inductors become harder.",
              (r"Z_R=R", r"Z_C=\frac{1}{j\omega C},\qquad |Z_C|=\frac{1}{\omega C}",
               r"Z_L=j\omega L,\qquad |Z_L|=\omega L"),
              "$Z$: impedance ($\\Omega$); $R$: resistance ($\\Omega$); $C$: capacitance (F); $L$: inductance (H); "
              "$\\omega=2\\pi f$: angular frequency (rad/s). $|Z|$ is magnitude. At ideal DC a capacitor is open and an inductor is short in steady state.",
              example=(r"f=1\,\mathrm{kHz},\ C=100\,\mathrm{nF}", r"|Z_C|=1/(2\pi fC)",
                       r"|Z_C|=1/[2\pi(1000)(10^{-7})]\,\Omega", r"|Z_C|\approx1.59\,\mathrm{k}\Omega")),
        Entry("AC Ohm's law · phasor form", "Divide phasor voltage by impedance to obtain phasor current. Series impedances "
              "add; parallel admittances (reciprocals of impedance) add.",
              (r"\underline V=\underline I Z,\qquad \underline I=\frac{\underline V}{Z}",),
              "$\\underline V$: RMS voltage phasor (V); $\\underline I$: RMS current phasor (A); $Z$: complex impedance ($\\Omega$). "
              "This is a sinusoidal steady-state relation, not a replacement for transient differential equations."),
    )),
    Section("filters", "Filters & transfer functions", (
        Entry("RC low-pass filter", "Take output across the capacitor. Low frequencies pass with little attenuation; high "
              "frequencies are attenuated. The formula assumes an ideal voltage source and no output load.",
              (r"H_{\rm LP}(j\omega)=\frac{1}{1+j\omega RC}", r"f_c=\frac{1}{2\pi RC}"),
              "$H$: output/input voltage ratio (dimensionless); $f_c$: cutoff frequency (Hz); $R$: series resistance ($\\Omega$); "
              "$C$: shunt capacitance (F). At $f_c$, $|H|=1/\\sqrt2$, about −3.01 dB.", "lowpass"),
        Entry("RC high-pass filter", "Take output across the resistor. DC is blocked; high frequencies approach unity gain. "
              "Use the same ideal-source and unloaded-output assumptions.",
              (r"H_{\rm HP}(j\omega)=\frac{j\omega RC}{1+j\omega RC}", r"f_c=\frac{1}{2\pi RC}"),
              "$R$: shunt resistance ($\\Omega$); $C$: series capacitance (F); $\\omega$: angular frequency (rad/s).", "highpass"),
        Entry("Magnitude response", "Both first-order RC filters have the same cutoff for the same R and C. The solid and "
              "dashed traces remain distinct in grayscale.",
              (r"|H_{\rm LP}|=\frac{1}{\sqrt{1+(f/f_c)^2}}", r"|H_{\rm HP}|=\frac{f/f_c}{\sqrt{1+(f/f_c)^2}}"),
              "$f$: signal frequency (Hz); $f_c$: cutoff (Hz).", "filters",
              example=(r"R=10\,\mathrm{k}\Omega,\ C=100\,\mathrm{nF}", r"f_c=1/(2\pi RC)",
                       r"f_c=1/[2\pi(10^4)(10^{-7})]\,\mathrm{Hz}", r"f_c\approx159\,\mathrm{Hz}")),
        Entry("Transfer functions · Next step", "A transfer function is output divided by input as a function of frequency "
              "or complex frequency. It describes a linear time-invariant system, with zero initial conditions in the Laplace form.",
              (r"H(s)=\frac{Y(s)}{X(s)},\qquad H(j\omega)=\frac{\underline Y}{\underline X}",),
              "$X,Y$: input/output transforms; $s$: Laplace complex frequency (s⁻¹). "
              "At sinusoidal steady state use $s=j\\omega$. Voltage/voltage transfer is dimensionless; voltage/current transfer has units $\\Omega$."),
    )),
    Section("gain-db", "Gain & decibels", (
        Entry("Voltage, current and power gain", "Gain is the ratio of output to input. A negative voltage gain means inversion "
              "under the chosen reference convention.",
              (r"A_v=\frac{V_{\rm out}}{V_{\rm in}},\quad A_i=\frac{I_{\rm out}}{I_{\rm in}},\quad G_P=\frac{P_{\rm out}}{P_{\rm in}}",),
              "$A_v,A_i,G_P$: dimensionless voltage, current and power ratios; voltages in V, currents in A and powers in W. "
              "Use matching amplitude definitions (for example RMS on both sides)."),
        Entry("Decibels", "A decibel expresses a ratio logarithmically. Use 20 log for amplitude ratios and 10 log for power "
              "ratios. Voltage gain in dB equals power gain in dB only when the compared resistances are equal.",
              (r"G_{V,\rm dB}=20\log_{10}|A_v|", r"G_{P,\rm dB}=10\log_{10}(G_P)"),
              "$G_{V,\\rm dB},G_{P,\\rm dB}$: gains in dB; $G_P>0$. Voltage magnitude ratios 2, 10 and ½ give approximately "
              "+6.02, +20 and −6.02 dB. Decibels alone do not retain an inversion sign.",
              example=(r"V_{\rm out}/V_{\rm in}=2", r"G_{V,\rm dB}=20\log_{10}2", r"G_{V,\rm dB}=20(0.30103)", r"G_{V,\rm dB}\approx6.02\,\mathrm{dB}")),
    )),
    Section("op-amps", "Op-amps & feedback", (
        Entry("Ideal op-amp rules", "The ideal model has infinite open-loop gain, infinite input resistance, zero output "
              "resistance and zero input current. Negative feedback can make its two input voltages nearly equal.",
              (r"I_+=I_-=0", r"V_+\approx V_-\quad\text{(negative feedback, linear operation)}"),
              "$V_+,V_-$: non-inverting/inverting input voltages (V); $I_+,I_-$: input currents (A). "
              "The virtual short is a voltage relation, not a wire carrying current between the inputs.", "opamp",
              "Do not use the virtual-short rule with positive feedback, an open loop, or a saturated output."),
        Entry("Saturation and finite gain", "An output cannot exceed its available supply range. Real op-amps often need "
              "headroom inside the rails. Required output swing, input common-mode limits and bandwidth must all be respected.",
              (r"V_{\rm out}=A_{\rm OL}(V_+-V_-)\quad\text{before limiting}",
               r"V_{\rm rail-}\le V_{\rm out}\le V_{\rm rail+}"),
              "$A_{\\rm OL}$: finite open-loop gain (dimensionless); $V_{\\rm rail-},V_{\\rm rail+}$: lower/upper supply rails (V). "
              "These bounds are an idealized limit, not a guarantee of rail-to-rail output."),
    )),
    Section("amplifiers", "Amplifier configurations", (
        Entry("Inverting amplifier", "The signal enters the inverting summing node through an input resistor. Negative "
              "feedback holds that node near the grounded non-inverting input.",
              (r"\frac{V_{\rm out}}{V_{\rm in}}=-\frac{R_f}{R_{\rm in}}",),
              "$R_f$: feedback resistance; $R_{\\rm in}$: input resistance (both $\\Omega$); voltages in V. "
              "Ideal op-amp, negative feedback and unsaturated operation are assumed.", "inverting",
              example=(r"R_f=10\,\mathrm{k}\Omega,\ R_{\rm in}=2\,\mathrm{k}\Omega,\ V_{\rm in}=0.2\,\mathrm{V}",
                       r"V_{\rm out}=-(R_f/R_{\rm in})V_{\rm in}", r"V_{\rm out}=-(10/2)(0.2)\,\mathrm{V}", r"V_{\rm out}=-1\,\mathrm{V}")),
        Entry("Non-inverting amplifier", "The input drives the + pin. A divider returns a fraction of output to the − pin. "
              "Keep the lab convention: R₁ is feedback; R₂ goes to ground.",
              (r"A_v=1+\frac{R_1}{R_2}=1+\frac{R_f}{R_g}",),
              "$R_f=R_1$: output-to-− feedback resistor; $R_g=R_2$: −-to-ground resistor (all $\\Omega$). "
              "$A_v=V_{\\rm out}/V_{\\rm in}$; ideal linear negative feedback is assumed.", "noninv",
              example=(r"R_1=10\,\mathrm{k}\Omega,\ R_2=1\,\mathrm{k}\Omega,\ V_{\rm in}=0.1\,\mathrm{V}",
                       r"A_v=1+R_1/R_2", r"A_v=1+10/1=11", r"V_{\rm out}=1.1\,\mathrm{V}")),
        Entry("Voltage follower", "Return output directly to the − pin and apply the signal to the + pin. A buffer "
              "provides high input impedance and low output impedance without intentionally increasing voltage.",
              (r"V_{\rm out}\approx V_{\rm in}",), "Both voltages are relative to the same reference (V). "
              "Supply, input-range and stability limits still apply.", "follower"),
        Entry("Summing amplifier", "Several input resistors feed one virtual-ground node. Each input contributes an "
              "inverted weighted term to the output.",
              (r"V_{\rm out}=-R_f\left(\frac{V_1}{R_1}+\frac{V_2}{R_2}+\cdots\right)",),
              "$V_k$: input voltages (V); $R_k$: respective input resistors; $R_f$: feedback resistor (all $\\Omega$). "
              "The + input is grounded; ideal linear operation is assumed.", "summing"),
        Entry("Difference amplifier", "Matched resistor ratios subtract the two inputs and reject their common part. "
              "The lab connects V₁ to the − path and V₂ to the + path.",
              (r"\frac{R_2}{R_1}=\frac{R_4}{R_3}\quad\Longrightarrow\quad V_{\rm out}=\frac{R_2}{R_1}(V_2-V_1)",),
              "$R_1$: V₁ input resistor; $R_2$: feedback resistor; $R_3$: V₂ input resistor; $R_4$: + input to ground (all $\\Omega$). "
              "Voltages are in V. Ratio mismatch converts common-mode input into output error.", "difference"),
        Entry("Transimpedance amplifier (TIA)", "A current-output sensor feeds the virtual-ground node. The feedback "
              "resistor turns input current into an output voltage.",
              (r"V_{\rm out}=-R_f I_{\rm in}",),
              "$I_{\\rm in}$: current entering the summing node (A); $R_f$: feedback resistance ($\\Omega$); "
              "$V_{\\rm out}$: output (V), with the + input grounded. Assumes stable linear negative feedback.", "tia",
              "K3 concerns a source-specific barometer sign; K7 concerns its feedback capacitor. "
              "This generic DC transimpedance relation does not resolve either source issue.",
              (r"I_{\rm in}=2\,\mu\mathrm{A},\ R_f=100\,\mathrm{k}\Omega", r"V_{\rm out}=-R_fI_{\rm in}",
               r"V_{\rm out}=-(10^5)(2\times10^{-6})\,\mathrm{V}", r"V_{\rm out}=-0.2\,\mathrm{V}")),
    )),
    Section("differential-common-mode", "Differential signals, common mode & CMRR", (
        Entry("Differential and common-mode decomposition", "Differential motion changes the separation of the two input "
              "voltages. Common-mode motion shifts both together. The lab sign convention is V₂ minus V₁.",
              (r"V_d=V_2-V_1,\qquad V_{\rm cm}=\frac{V_1+V_2}{2}",
               r"V_1=V_{\rm cm}-\frac{V_d}{2},\qquad V_2=V_{\rm cm}+\frac{V_d}{2}"),
              "$V_d$: differential voltage; $V_{\\rm cm}$: common-mode voltage; $V_1,V_2$: inputs relative to ground (all V).",
              "signals", example=(r"V_1=2.49\,\mathrm{V},\ V_2=2.51\,\mathrm{V}", r"V_d=V_2-V_1,\ V_{\rm cm}=(V_1+V_2)/2",
                                   r"V_d=2.51-2.49\,\mathrm{V}", r"V_d=20\,\mathrm{mV},\quad V_{\rm cm}=2.50\,\mathrm{V}")),
        Entry("Common-mode rejection ratio (CMRR)", "High CMRR means the amplifier responds strongly to input difference "
              "and weakly to a shared disturbance. It does not remove the input common-mode operating-range limit.",
              (r"V_{\rm out}=A_dV_d+A_{\rm cm}V_{\rm cm}", r"\mathrm{CMRR}=\left|\frac{A_d}{A_{\rm cm}}\right|",
               r"\mathrm{CMRR}_{\rm dB}=20\log_{10}(\mathrm{CMRR})"),
              "$A_d,A_{\\rm cm}$: dimensionless differential/common-mode gains; CMRR is dimensionless; its logarithmic form is in dB. "
              "An ideal $A_{\\rm cm}=0$ gives infinite CMRR."),
        Entry("Instrumentation amplifier", "The first two op-amps present high input impedance and amplify differential "
              "voltage. A matched difference stage subtracts their outputs and rejects their shared common-mode component.",
              (r"A_{d,1}=1+\frac{2R_2}{R_1}", r"V_{\rm out}=A_{d,1}(V_2-V_1)\quad\text{(unity difference stage)}"),
              "$R_1$: resistor joining the first-stage inverting inputs; $R_2$: each first-stage feedback resistor (both $\\Omega$). "
              "$A_{d,1}$: first-stage differential gain. The lab's four equal second-stage resistors give unity differential gain.",
              "ina", "All three op-amps must remain in their linear input/output ranges. High CMRR also needs good resistor-ratio matching.",
              (r"R_1=1\,\mathrm{k}\Omega,\ R_2=10\,\mathrm{k}\Omega,\ V_d=5\,\mathrm{mV}",
               r"A_{d,1}=1+2R_2/R_1", r"A_{d,1}=1+2(10)/1=21", r"V_{\rm out}=21(5\,\mathrm{mV})=105\,\mathrm{mV}")),
    )),
    Section("wheatstone", "Wheatstone bridge & strain gauges", (
        Entry("Bridge as two voltage dividers", "Use the exact lab orientation: R₁ upper left, R₄ lower left; R₂ upper "
              "right, R₃ lower right. V₂ is the left midpoint, V₁ the right. The ideal meter draws no current.",
              (r"V_2=V_0\frac{R_4}{R_1+R_4},\qquad V_1=V_0\frac{R_3}{R_2+R_3}",
               r"V_{\rm out}=V_2-V_1", r"\frac{R_1}{R_4}=\frac{R_2}{R_3}\quad\text{(balance)}"),
              "$V_0$: excitation (V); $R_1\\ldots R_4$: arm resistances ($\\Omega$); midpoint/output voltages in V. "
              "Balance is an arm-ratio condition; zero excitation alone does not establish balance.", "bridge"),
        Entry("Strain gauge basics", "Strain is relative extension. A strain gauge converts it into a relative resistance change.",
              (r"\varepsilon=\frac{\Delta\ell}{\ell},\qquad G=\frac{\Delta R/R}{\varepsilon}",
               r"\frac{\Delta R}{R}=G\varepsilon"),
              "$\\ell$: original length; $\\Delta\\ell$: extension (both m); $\\varepsilon$: strain (dimensionless); "
              "$G$: gauge factor, also called GF (dimensionless); $R$: nominal resistance; $\\Delta R$: change (both $\\Omega$). "
              "500 µε means $500\\times10^{-6}$ strain.",
              example=(r"G=2,\ \varepsilon=500\,\mu\varepsilon,\ R=350\,\Omega", r"\Delta R=RG\varepsilon",
                       r"\Delta R=350(2)(500\times10^{-6})\,\Omega", r"\Delta R=0.35\,\Omega")),
        Entry("Quarter bridge: one active gauge", "With R₁ = R + ΔR and the other three arms equal to R, the left midpoint "
              "falls for positive ΔR. This is the verified registry model for the app's chosen orientation.",
              (r"x=\frac{\Delta R}{R}", r"V_{\rm out}=V_0\left(\frac{1}{2+x}-\frac12\right)",
               r"V_{\rm out}\approx-\frac{V_0x}{4}\quad(|x|\ll1)"),
              "$x$: fractional resistance change (dimensionless); $R$: nominal arm resistance ($\\Omega$); $V_0$: excitation (V).",
              note="⚠ K9 remains open: moving the gauge to the lower-left arm reverses the sign. "
                   "The registry flags this orientation assumption; it is not silently resolved here."),
        Entry("Full bridge: four active gauges", "With R₁ and R₃ stretched and R₂ and R₄ compressed by equal relative "
              "amounts, the midpoint shifts add. The output magnitude is about four times the quarter-bridge small-signal magnitude.",
              (r"R_1=R_3=R(1+x),\quad R_2=R_4=R(1-x)", r"V_{\rm out}=-V_0x,\qquad |V_{\rm out}|=|V_0G\varepsilon|"),
              "$x=G\\varepsilon$, with $|x|<1$ to keep all arm resistances positive; $V_0$: excitation (V). "
              "The registry's full-bridge magnitude is verified; the signed form follows the displayed lab orientation.",
              example=(r"V_0=5\,\mathrm{V},\ G=2,\ \varepsilon=500\times10^{-6}", r"x=G\varepsilon,\ V_{\rm out}=-V_0x",
                       r"V_{\rm out}=-5(2)(500\times10^{-6})\,\mathrm{V}", r"V_{\rm out}=-5\,\mathrm{mV}")),
    )),
    Section("measurement", "Loading, measurement & signal chains", (
        Entry("Voltmeter and ammeter connections", "A voltmeter goes across two nodes; its ideal input resistance is infinite. "
              "An ammeter goes in series; its ideal resistance is zero. A real instrument changes the circuit slightly.",
              (r"R_{\rm voltmeter}\to\infty,\qquad R_{\rm ammeter}\to0",),
              "Instrument resistances are in $\\Omega$. A real ammeter has a burden voltage. "
              "Connecting its low resistance across a source can create a short.", "measurement"),
        Entry("Input and output impedance", "High input impedance reduces loading of the previous stage. Low output "
              "impedance helps a stage maintain its output voltage when it drives the next one.",
              (r"\frac{V_{\rm loaded}}{V_{\rm open}}=\frac{Z_{\rm in}}{Z_{\rm out}+Z_{\rm in}}",),
              "$Z_{\\rm out}$: source output impedance; $Z_{\\rm in}$: receiving input impedance (both $\\Omega$). "
              "At DC use resistances. The simple voltage-transfer picture is most accurate when $|Z_{\\rm in}|\\gg|Z_{\\rm out}|$.",
              example=(r"V_{\rm open}=1\,\mathrm{V},\ R_{\rm out}=10\,\mathrm{k}\Omega,\ R_{\rm in}=1\,\mathrm{M}\Omega",
                       r"V_{\rm loaded}=V_{\rm open}R_{\rm in}/(R_{\rm out}+R_{\rm in})",
                       r"V_{\rm loaded}=1(1000/1010)\,\mathrm{V}", r"V_{\rm loaded}\approx0.990\,\mathrm{V}")),
        Entry("Basic sensor signal chain", "A transducer converts a physical stimulus into a measurable signal. Conditioning "
              "can amplify and filter it. An ADC (analog-to-digital converter) samples it for processing and communication.",
              note="The compact chain below is context, not a separate lesson or a progress requirement.", figure="chain"),
    )),
    Section("noise", "Noise, mean, variance & RMS", (
        Entry("Deterministic signal and random noise", "A deterministic signal follows a specified rule. Noise has an "
              "unpredictable realization and is described statistically. Additive noise adds to a signal; multiplicative noise changes its scale.",
              (r"y(t)=s(t)+n(t)\quad\text{(additive)}", r"y(t)=s(t)[1+n(t)]\quad\text{(multiplicative)}"),
              "$y$: output; $s$: desired signal; $n$: noise; $t$: time (s). In the additive model $s,n,y$ share units. "
              "In the multiplicative model $n$ is a dimensionless fractional fluctuation."),
        Entry("Mean, variance and RMS", "Mean locates the average level. Variance measures spread about that level. RMS "
              "includes both the mean and the fluctuations.",
              (r"\mu=\mathbb E[x]", r"\sigma^2=\mathbb E[(x-\mu)^2]", r"x_{\rm rms}=\sqrt{\mathbb E[x^2]}",
               r"x_{\rm rms}^2=\mu^2+\sigma^2,\qquad x_{\rm rms}=\sigma\ \text{if }\mu=0"),
              "$x$: random quantity; $\\mathbb E$: expectation (statistical average); $\\mu$: mean; $\\sigma$: standard deviation. "
              "For voltage, mean/RMS/standard deviation use V and variance uses V². Time averages estimate expectations under suitable sampling assumptions.",
              example=(r"\mu=3\,\mathrm{V},\ \sigma=4\,\mathrm{V}", r"x_{\rm rms}=\sqrt{\mu^2+\sigma^2}",
                       r"x_{\rm rms}=\sqrt{9+16}\,\mathrm{V}", r"x_{\rm rms}=5\,\mathrm{V},\quad\sigma^2=16\,\mathrm{V^2}")),
    )),
    Section("spectrum-psd", "Spectrum, PSD & noise bandwidth", (
        Entry("Time domain and frequency domain", "A time trace shows how a quantity changes. A spectrum shows its "
              "frequency components. A random-noise PSD describes average mean-square content per unit bandwidth, not one deterministic amplitude.",
              (r"\omega=2\pi f",), "$f$: ordinary frequency (Hz); $\\omega$: angular frequency (rad/s). "
              "Do not interchange these integration variables without their Jacobian."),
        Entry("Power spectral density (PSD)", "For voltage noise the PSD is mean-square voltage per hertz. Its square root "
              "is amplitude spectral density (ASD). These quantities have different units.",
              (r"\mathrm{ASD}(f)=\sqrt{S_x(f)}",),
              "$S_x(f)$: voltage-noise PSD (V²/Hz); ASD: amplitude spectral density (V/$\\sqrt{\\mathrm{Hz}}$). "
              "Electrical power in watts also depends on resistance; a V²/Hz density is not itself W/Hz."),
        Entry("Noise over a bandwidth", "For zero-mean stationary noise, integrate its PSD to obtain variance, then take "
              "the square root for RMS. Here S₁ is one-sided per hertz and the band has nonnegative edges.",
              (r"\sigma_{\rm band}^2=\int_{f_1}^{f_2} S_1(f)\,df", r"x_{\rm rms,band}=\sqrt{\sigma_{\rm band}^2}",
               r"\int_{f_1}^{f_2}S_1(f)\,df=\frac{1}{2\pi}\int_{\omega_1}^{\omega_2}S_1(\omega/2\pi)\,d\omega"),
              "$f_1,f_2$: band edges (Hz), $0\\le f_1<f_2$; $\\omega_i=2\\pi f_i$ (rad/s). "
              "$S_1(\\omega/2\\pi)$ still has per-Hz units, so the $1/(2\\pi)$ is necessary. "
              "A density defined per rad/s would instead incorporate that conversion.",
              note="⚠ K4 and K5 remain open in the source register. This explicit per-Hz convention avoids their normalization ambiguity."),
        Entry("White-noise shortcut", "For a flat one-sided PSD across the band, variance equals density times bandwidth. "
              "For non-flat noise use the integral. Ideal white noise extending to infinite frequency has infinite total variance.",
              (r"B=f_2-f_1,\qquad \sigma^2=S_0B", r"x_{\rm rms}=\sqrt{S_0B}"),
              "$S_0$: constant one-sided density (V²/Hz for voltage noise); $B$: bandwidth (Hz); $\\sigma^2$: variance (V²).",
              example=(r"S_0=10^{-5}\,\mathrm{V^2/Hz},\ f_1=100\,\mathrm{Hz},\ f_2=1000\,\mathrm{Hz}",
                       r"\sigma^2=S_0(f_2-f_1)", r"\sigma^2=10^{-5}(900)\,\mathrm{V^2}=0.009\,\mathrm{V^2}",
                       r"x_{\rm rms}\approx94.9\,\mathrm{mV}")),
        Entry("One-sided vs two-sided PSD", "For a real zero-mean signal, the two-sided PSD is symmetric. Moving negative "
              "frequency content onto the positive side doubles the positive-frequency density and preserves total area.",
              (r"S_1(f)=2S_2(f)\quad(f>0)",
               r"\sigma^2=\int_0^\infty S_1(f)\,df=\int_{-\infty}^{\infty}S_2(f)\,df"),
              "$S_1,S_2$: one-/two-sided PSD with the same per-Hz units; $\\sigma^2$: total variance. "
              "A DC spectral line and discrete FFT endpoint bins require separate endpoint bookkeeping.", "psd"),
    )),
    Section("mathematical-tools", "Mathematical tools", (
        Entry("Derivatives and integrals", "A derivative is instantaneous slope: change per unit time. An integral accumulates "
              "a quantity over an interval. Current is the derivative of charge, and integrating current gives transferred charge.",
              (r"\frac{dx}{dt},\qquad \Delta Q=\int_{t_1}^{t_2}I(t)\,dt",),
              "$x$: time-varying quantity; $t$: time (s); $I$: current (A); $\\Delta Q$: charge transferred between $t_1,t_2$ (C). "
              "A derivative divides units by seconds; a time integral multiplies units by seconds."),
        Entry("Product rule", "When both factors change, differentiate each while retaining the other. This is why "
              "a changing capacitor has two current terms.",
              (r"\frac{d(uv)}{dt}=u\frac{dv}{dt}+v\frac{du}{dt}",
               r"I=\frac{d(CV)}{dt}=C\frac{dV}{dt}+V\frac{dC}{dt}"),
              "$u,v$: differentiable functions of time; $C$: capacitance (F); $V$: capacitor voltage (V); $I$: current (A)."),
        Entry("Small-signal approximation · Next step", "Near an operating point, replace a smooth nonlinear relation "
              "by its tangent. The approximation is useful only while higher-order terms stay small.",
              (r"f(x)\approx f(x_0)+f'(x_0)(x-x_0)", r"\Delta C\approx\left.\frac{dC}{dx}\right|_{x_0}\Delta x"),
              "$x_0$: operating point; $f'(x_0)$: slope there; $\\Delta x=x-x_0$. In the sensor example $x$ is displacement (m), "
              "$C$ is capacitance (F), and $dC/dx$ has units F/m. This is a generic Taylor rule, not a resolution of K1/K2."),
        Entry("Ratios, fractions and proportionality", "A direct proportion preserves a constant ratio. An inverse proportion "
              "preserves a constant product. Keep all other parameters fixed when using either statement.",
              (r"y\propto x\quad\Longleftrightarrow\quad y=kx", r"y\propto\frac1x\quad\Longleftrightarrow\quad y=\frac{k}{x}"),
              "$k$: proportionality constant with units needed to match $x,y$. At fixed resistance $I\\propto V$; "
              "at fixed voltage $I\\propto1/R$. Fractions describe a ratio, not two disconnected numbers."),
    )),
    Section("units-prefixes", "SI units, prefixes & conversions", (
        Entry("Prefixes are powers of ten", "Case matters: m means milli, M means mega. A prefix multiplies a unit; "
              "convert to compatible units before substitution.",
              (r"\mathrm{k}=10^3,\quad \mathrm{M}=10^6", r"\mathrm{m}=10^{-3},\quad \mu=10^{-6}",
               r"\mathrm{n}=10^{-9},\quad \mathrm{p}=10^{-12}"),
              "Examples: kΩ, MΩ, mA, µA, mV, µV, nF and pF. The same letter may be a unit in another context: "
              "m alone is metre; m before A is the milli prefix. S (siemens) and s (second) are different units."),
        Entry("Unit conversions", "Multiply the numerical value by the prefix factor, retaining the physical quantity.",
              (r"2\,\mathrm{k}\Omega=2000\,\Omega", r"3\,\mathrm{mA}=0.003\,\mathrm{A}",
               r"100\,\mathrm{nF}=0.1\,\mu\mathrm{F}"),
              "C: coulomb; A: ampere; V: volt; Ω: ohm; S: siemens; W: watt; J: joule; F: farad; H: henry; "
              "Hz: hertz; s: second; m: metre. Strain and gain ratios are dimensionless."),
    )),
)


# Deliberately compact revision sheet: labels + equations only. K9 remains visible.
SUMMARY = (
    ("Quantities", (r"I=\frac{dQ}{dt},\quad V_{AB}=V_A-V_B,\quad G_{\rm cond}=1/R",)),
    ("Ohm / power", (r"V=IR,\quad P=VI=I^2R=V^2/R,\quad E=Pt\ (P\text{ constant})",)),
    ("Series / parallel", (r"R_s=\sum R_k,\quad \frac1{R_p}=\sum\frac1{R_k}",)),
    ("Dividers", (r"V_{\rm out}=V_{\rm in}\frac{R_2}{R_1+R_2},\quad I_1=I_T\frac{R_2}{R_1+R_2}",)),
    ("Kirchhoff", (r"\sum I_k=0,\qquad\sum V_k=0",)),
    ("Capacitors", (r"Q=CV,\quad C=\varepsilon_{\rm diel}A/d,\quad \tau_{RC}=RC",
                    r"I=C\frac{dV}{dt}+V\frac{dC}{dt}", r"C_p=\sum C_k,\quad \frac1{C_s}=\sum\frac1{C_k}",
                    r"V_{C,\rm charge}=V_S(1-e^{-t/RC}),\quad V_{C,\rm decay}=V_0e^{-t/RC}")),
    ("Inductors", (r"V=L\frac{dI}{dt},\quad E_L=\frac12LI^2,\quad \tau_{RL}=L/R",)),
    ("AC", (r"v=V_{\rm pk}\sin(\omega t+\phi),\quad\omega=2\pi f,\quad T=1/f",
            r"V_{\rm pp}=2V_{\rm pk},\quad V_{\rm rms}=V_{\rm pk}/\sqrt2\quad(\text{sine})",)),
    ("Impedance", (r"Z_R=R,\quad Z_C=\frac1{j\omega C},\quad Z_L=j\omega L,\quad\underline V=\underline I Z",)),
    ("Filters", (r"H_{\rm LP}=\frac1{1+j\omega RC},\quad H_{\rm HP}=\frac{j\omega RC}{1+j\omega RC}",
                 r"f_c=1/(2\pi RC),\quad H(s)=Y(s)/X(s)")),
    ("Gain / dB", (r"A_v=V_{\rm out}/V_{\rm in},\quad G_{V,\rm dB}=20\log_{10}|A_v|",
                   r"G_{P,\rm dB}=10\log_{10}(P_{\rm out}/P_{\rm in})")),
    ("Op-amps · ideal, linear negative feedback", (r"V_+\approx V_-,\quad I_+=I_-=0",
                   r"A_{\rm inv}=-R_f/R_{\rm in},\quad A_{\rm noninv}=1+R_1/R_2",
                   r"V_{\rm sum}=-R_f\sum_k V_k/R_k,\quad V_{\rm TIA}=-R_fI_{\rm in}",
                   r"V_{\rm diff}=(R_2/R_1)(V_2-V_1)\quad(\text{matched ratios})",
                   r"A_{d,1}=1+2R_2/R_1,\quad\mathrm{CMRR}=|A_d/A_{\rm cm}|")),
    ("Bridge · app orientation, K9 remains open", (r"V_{\rm out}=V_0\left(\frac{R_4}{R_1+R_4}-\frac{R_3}{R_2+R_3}\right)",
                   r"\frac{\Delta R}{R}=G\varepsilon=x,\quad V_{q}\approx-V_0x/4\ (|x|\ll1),\quad V_{\rm full}=-V_0x")),
    ("Measurement", (r"V_L=V_{\rm th}R_L/(R_{\rm th}+R_L),\quad I_N=V_{\rm th}/R_{\rm th}",
                     r"R_V\to\infty,\quad R_A\to0,\quad V_d=V_2-V_1,\quad V_{\rm cm}=(V_1+V_2)/2")),
    ("Noise · zero mean, one-sided PSD per Hz", (r"\sigma^2=\mathbb E[(x-\mu)^2],\quad x_{\rm rms}^2=\mu^2+\sigma^2",
                     r"\sigma^2=\int_0^\infty S_1(f)\,df,\quad S_1(f)=2S_2(f)\ (f>0)",
                     r"\sigma_{\rm band}^2=S_0B\quad(\text{flat }S_1=S_0),\quad\mathrm{ASD}=\sqrt{S_1}")),
    ("Calculus / math", (r"\frac{d(uv)}{dt}=u\frac{dv}{dt}+v\frac{du}{dt},\quad\Delta Q=\int I\,dt",
                         r"f(x)\approx f(x_0)+f'(x_0)(x-x_0)")),
)
