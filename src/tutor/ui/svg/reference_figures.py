"""Independent handbook sketches, using Signal Tutor's existing SVG grammar.

No simulation state or learner storage. Curves are drawn from their equations;
motion is a supplementary reading cue and can be paused by the shared viewer.
"""

from __future__ import annotations

import math

from tutor.ui.svg import amp_figures as A, figures as F
from tutor.ui.svg.core import (
    CURRENT, FAINT, INK, MINUS, MUTED, VOLT, Canvas, arrow, battery,
    dot, flow, ground, resistor, terminal, text, wire,
)


def passive(kind: str) -> str:
    titles = {"series": "Series circuit / KVL", "parallel": "Parallel circuit / current divider",
              "open": "Open and short circuits", "sources": "Ideal voltage and current sources",
              "loading": "Source resistance and loading / Thévenin equivalent",
              "norton": "Norton equivalent", "capacitor": "Parallel-plate capacitor",
              "capacitors": "Capacitors in parallel and series", "inductor": "Inductor",
              "measurement": "Ammeter in series; voltmeter across the resistor",
              "lowpass": "RC low-pass filter", "highpass": "RC high-pass filter"}
    c = Canvas(640, 320, titles[kind], uid="ref-" + kind)
    if kind in ("series", "parallel", "measurement"):
        c.add(wire([(80, 155), (80, 55), (510, 55), (510, 265), (80, 265), (80, 165)]))
        battery(c, 80, 160, label="V_S")
        ground(c, 370, 265)
        if kind == "series":
            # Replace the right-hand wire with two components, rather than
            # drawing a continuous short underneath the resistor symbols.
            c.parts[0] = wire([(80, 155), (80, 55), (510, 55), (510, 70)]) + wire(
                [(510, 134), (510, 186)]) + wire([(510, 250), (510, 265), (80, 265), (80, 165)])
            resistor(c, 510, 102, label="R_1", value="1 kΩ")
            resistor(c, 510, 218, label="R_2", value="2 kΩ")
            c.add(flow([(150, 55), (430, 55)], .45))
            c.add(text(290, 39, "I = 2 mA for V_S = 6 V", "val cur"))
        elif kind == "parallel":
            c.parts[0] = wire([(80, 155), (80, 55), (510, 55), (510, 128)]) + wire(
                [(510, 192), (510, 265), (80, 265), (80, 165)])
            c.add(wire([(320, 55), (320, 128)]))
            c.add(wire([(320, 192), (320, 265)]))
            resistor(c, 320, 160, label="R_1", value="1 kΩ")
            resistor(c, 510, 160, label="R_2", value="2 kΩ")
            for x, label, strength in ((320, "I_1", .6), (510, "I_2", .3)):
                c.add(flow([(x, 65), (x, 112)], strength))
                c.add(text(x + 25, 95, label, "cur", "start"))
                c.add(dot(x, 55)); c.add(dot(x, 265))
        else:
            c.parts[0] = wire([(80, 155), (80, 55), (510, 55), (510, 128)]) + wire(
                [(510, 192), (510, 265), (80, 265), (80, 165)])
            # Ammeter breaks the top wire; voltmeter is a separate branch.
            c.add('<circle cx="280" cy="55" r="20" fill="white" stroke="' + CURRENT + '" stroke-width="2.2"/>')
            c.add(text(280, 61, "A", "lbl cur"))
            resistor(c, 510, 160, label="R")
            c.add(wire([(510, 100), (590, 100), (590, 140)]))
            c.add(wire([(590, 180), (590, 220), (510, 220)]))
            c.add('<circle cx="590" cy="160" r="20" fill="white" stroke="' + INK + '" stroke-width="2.2"/>')
            c.add(text(590, 166, "V")); c.add(dot(510, 100)); c.add(dot(510, 220))
    elif kind == "open":
        for y, label in ((90, "Open: no conducting path"), (230, "Short: conducting wire, V = 0")):
            c.add(terminal(80, y)); c.add(terminal(560, y))
            c.add(text(320, y - 35, label, "lbl"))
            if y == 90:
                c.add(wire([(80, y), (280, y)])); c.add(wire([(350, y), (560, y)]))
                c.add(arrow(280, y, 333, y - 27, INK)); c.add(dot(350, y))
            else:
                c.add(wire([(80, y), (560, y)])); c.add(flow([(100, y), (540, y)], .4))
    elif kind in ("sources", "norton"):
        sources = ((250, True),) if kind == "norton" else ((170, False), (460, True))
        for x, current in sources:
            c.add(wire([(x, 50), (x, 105)])); c.add(wire([(x, 175), (x, 235)]))
            c.add(terminal(x, 50)); c.add(terminal(x, 235))
            c.add(f'<circle cx="{x}" cy="140" r="35" fill="white" stroke="{INK}" stroke-width="2.2"/>')
            if current:
                c.add(arrow(x, 160, x, 120, CURRENT)); c.add(text(x, 280, "I_N" if kind == "norton" else "I_S"))
            else:
                c.add(text(x, 130, "+")); c.add(text(x, 161, "−")); c.add(text(x, 280, "V_S"))
        if kind == "norton":
            c.add(wire([(250, 50), (490, 50), (490, 108)]))
            c.add(wire([(490, 172), (490, 235), (250, 235)]))
            resistor(c, 490, 140, label="R_N")
            c.add(terminal(490, 50)); c.add(terminal(490, 235))
            c.add(text(370, 306, "Equivalent seen at the two right-hand terminals", "small"))
    elif kind == "loading":
        c.add(wire([(90, 155), (90, 60), (258, 60)]))
        c.add(wire([(322, 60), (510, 60), (510, 128)]))
        c.add(wire([(510, 192), (510, 260), (90, 260), (90, 165)]))
        battery(c, 90, 160, label="V_th")
        resistor(c, 290, 60, vertical=False, label="R_th")
        resistor(c, 510, 160, label="R_L")
        c.add(dot(510, 60)); c.add(text(560, 82, "V_L", "lbl volt")); ground(c, 360, 260)
        c.add(text(280, 306, "A linear source network → V_th in series with R_th", "small"))
    elif kind in ("capacitor", "capacitors", "inductor", "lowpass", "highpass"):
        if kind == "capacitor":
            for y in (110, 210):
                c.add(f'<line x1="180" y1="{y}" x2="460" y2="{y}" stroke="{INK}" stroke-width="6"/>')
            c.add(wire([(320, 45), (320, 110)])); c.add(wire([(320, 210), (320, 275)]))
            c.add(text(320, 148, "+ + + +", "lbl volt")); c.add(text(320, 191, "− − − −", "lbl"))
            c.add(arrow(505, 113, 505, 207, MUTED)); c.add(text(530, 166, "d"))
            c.add(text(320, 310, "Plate area A; dielectric permittivity ε", "small"))
        elif kind == "capacitors":
            for x in (140, 280):
                c.add(wire([(x, 65), (x, 143)])); _cap(c, x, 160)
                c.add(wire([(x, 177), (x, 255)]))
            c.add(wire([(140, 65), (280, 65)])); c.add(wire([(140, 255), (280, 255)]))
            for y in (105, 215):
                _cap(c, 490, y)
            c.add(wire([(490, 50), (490, 88)])); c.add(wire([(490, 122), (490, 198)]))
            c.add(wire([(490, 232), (490, 270)]))
            c.add(text(210, 302, "Parallel: same V", "lbl")); c.add(text(490, 302, "Series: same |Q|*", "lbl"))
        elif kind == "inductor":
            c.add(wire([(90, 150), (220, 150)])); c.add(wire([(420, 150), (550, 150)]))
            c.add(f'<path d="M220,150 ' + ' '.join('a25,25 0 0 1 50,0' for _ in range(4)) +
                  f'" fill="none" stroke="{INK}" stroke-width="2.2"/>')
            c.add(text(320, 110, "L (H)")); c.add(arrow(130, 190, 220, 190, CURRENT))
            c.add(text(175, 220, "I", "cur")); c.add(text(320, 270, "+ V −  (current enters +)", "small"))
        else:
            c.add(terminal(80, 90)); c.add(wire([(80, 90), (245, 90)]))
            c.add(wire([(315, 90), (480, 90)])); c.add(dot(430, 90))
            if kind == "lowpass":
                resistor(c, 280, 90, vertical=False, label="R")
                c.add(wire([(430, 90), (430, 163)])); _cap(c, 430, 180)
                c.add(wire([(430, 197), (430, 255)])); c.add(text(480, 185, "C"))
            else:
                _cap(c, 280, 90, horizontal=True); c.add(text(280, 48, "C"))
                c.add(wire([(430, 90), (430, 148)])); resistor(c, 430, 180, label="R")
                c.add(wire([(430, 212), (430, 255)]))
            ground(c, 430, 255); c.add(text(95, 135, "V_in", "lbl volt"))
            c.add(text(520, 96, "V_out", "lbl volt")); c.add(terminal(480, 90))
    return c.render()


def _cap(c: Canvas, x: float, y: float, horizontal: bool = False) -> None:
    if horizontal:
        c.add(wire([(x - 35, y), (x - 8, y)])); c.add(wire([(x + 8, y), (x + 35, y)]))
        for dx in (-8, 8):
            c.add(f'<line x1="{x+dx}" y1="{y-24}" x2="{x+dx}" y2="{y+24}" stroke="{INK}" stroke-width="3"/>')
    else:
        for dy in (-8, 8):
            c.add(f'<line x1="{x-25}" y1="{y+dy}" x2="{x+25}" y2="{y+dy}" stroke="{INK}" stroke-width="3"/>')
        c.add(wire([(x, y - 17), (x, y - 8)])); c.add(wire([(x, y + 8), (x, y + 17)]))


def inverting(kind: str = "inverting") -> str:
    c = Canvas(700, 350, {"inverting": "Inverting amplifier", "summing": "Summing amplifier",
                          "tia": "Transimpedance amplifier", "follower": "Voltage follower",
                          "opamp": "Ideal op-amp"}[kind], uid="ref-" + kind)
    pins = A.opamp(c, 340, 190, top="−", rails=True)
    xt, yt = pins["top"]; xb, yb = pins["bot"]; xo, yo = pins["out"]
    c.add(wire([(xo, yo), (620, yo)])); c.add(text(640, yo + 6, "V_out", "lbl volt"))
    if kind == "opamp":
        for y, label in ((yt, "V_−"), (yb, "V_+")):
            c.add(wire([(180, y), (340, y)])); c.add(text(130, y + 5, label))
    elif kind == "follower":
        c.add(wire([(560, yo), (560, 70), (280, 70), (280, yt), (xt, yt)]))
        c.add(dot(560, yo)); c.add(wire([(100, yb), (xb, yb)])); c.add(text(130, yb - 18, "V_in", "lbl volt"))
    else:
        c.add(wire([(290, yt), (xt, yt)])); c.add(dot(290, yt))
        c.add(wire([(290, yt), (290, 70), (398, 70)]))
        resistor(c, 430, 70, vertical=False, label="R_f")
        c.add(wire([(462, 70), (560, 70), (560, yo)])); c.add(dot(560, yo))
        c.add(wire([(xb, yb), (290, yb), (290, 275)])); ground(c, 290, 275)
        if kind == "tia":
            c.add(wire([(90, yt), (290, yt)])); c.add(flow([(100, yt), (260, yt)], .5))
            c.add(text(155, yt - 23, "I_in", "lbl cur"))
        else:
            ys = [yt] if kind == "inverting" else [yt - 40, yt + 40]
            for i, y in enumerate(ys):
                c.add(wire([(70, y), (148, y)])); c.add(wire([(212, y), (260, y), (260, yt), (290, yt)]))
                resistor(c, 180, y, vertical=False, label="R_in" if len(ys) == 1 else f"R_{i+1}")
                c.add(text(55, y + 6, "V_in" if len(ys) == 1 else f"V_{i+1}", "lbl", "end"))
    return c.render()


def curve(kind: str) -> str:
    titles = {"rc": "RC charging and discharging", "sine": "Sine wave: peak, RMS and period",
              "phase": "Phase: the dashed signal leads by π/2", "filters": "RC filter magnitude responses",
              "psd": "One-sided and two-sided white PSD: equal total area"}
    c = Canvas(700, 320, titles[kind], uid="ref-" + kind)
    c.add(wire([(75, 35), (75, 265), (640, 265)]))
    if kind == "psd":
        # Identical bandwidth [-B,B] vs [0,B]; twice the height over half the width.
        c.add(wire([(110, 185), (610, 185)]))
        c.add(wire([(360, 105), (610, 105)]))
        c.add(text(230, 168, "S₂ = S₀/2", "lbl")); c.add(text(490, 88, "S₁ = S₀", "lbl"))
        for x, label in ((110, "−B"), (360, "0"), (610, "B")):
            c.add(text(x, 288, label, "val"))
        c.add(text(390, 312, "frequency f (Hz)", "small")); return c.render()
    values: list[tuple[str, str, bool]] = []
    def path(fn) -> str:
        return "M" + " L".join(f"{75+565*i/200:.2f},{265-210*fn(i/200):.2f}" for i in range(201))
    if kind == "rc":
        values = [(path(lambda u: 1-math.exp(-5*u)), CURRENT, False),
                  (path(lambda u: math.exp(-5*u)), VOLT, True)]
        c.add(text(420, 48, "charging → V_S", "lbl cur")); c.add(text(445, 245, "discharging → 0", "lbl volt"))
        c.add(text(365, 310, "time t: 0 … 5τ", "small"))
        c.add(text(44, 65, "1", "val")); c.add(text(42, 270, "0", "val"))
        c.add(text(62, 22, "V_C / reference voltage", "small", "start"))
        c.add(text(188, 290, "τ", "val"))
    elif kind in ("sine", "phase"):
        values = [(path(lambda u: .5+.44*math.sin(4*math.pi*u)), CURRENT, False)]
        c.add(wire([(75, 160), (640, 160)], dim=True))
        if kind == "phase":
            values.append((path(lambda u: .5+.44*math.sin(4*math.pi*u+math.pi/2)), VOLT, True))
            c.add(text(420, 25, "solid: phase 0; dashed: +π/2", "small"))
        else:
            for y, label in ((67.6, "+V_pk"), (94.7, "+V_rms*"), (160, "0"), (252.4, "−V_pk")):
                c.add(text(66, y+4, label, "small", "end"))
            c.add(text(440, 27, "*RMS magnitude, not instantaneous voltage", "small"))
        c.add(text(355, 310, "time t: 0 … 2T", "small"))
    else:
        values = [(path(lambda u: 1/math.sqrt(1+10**(6*u-3))), CURRENT, False),
                  (path(lambda u: math.sqrt(10**(6*u-3)/(1+10**(6*u-3)))), VOLT, True)]
        c.add(text(240, 40, "solid: low-pass", "lbl cur")); c.add(text(490, 40, "dashed: high-pass", "lbl volt"))
        c.add(text(353, 290, "f_c", "val")); c.add(text(350, 312, "frequency f / f_c (log scale: 0.032 … 31.6)", "small"))
        c.add(text(40, 65, "1", "val")); c.add(text(40, 272, "0", "val")); c.add(text(82, 22, "|H|", "lbl"))
    for i, (d, color, dashed) in enumerate(values):
        c.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.6"' +
              (' stroke-dasharray="7 5"' if dashed else '') + '/>')
        if kind != "filters":
            c.add(f'<circle class="ref-trace" r="5" fill="{color}" style="offset-path:path(\'{d}\');offset-distance:50%"/>')
    c.add('<style>.ref-trace {animation: ref-travel 8s linear infinite;} '
          '@keyframes ref-travel {from {offset-distance:0%;} to {offset-distance:100%;}}'
          '@media (prefers-reduced-motion:reduce) {.mst .ref-trace {animation:none!important;}}</style>')
    return c.render()


def figure(key: str) -> str:
    if key == "loop":
        return F.ohm_loop(6, 2000, .003, .006)
    if key == "voltage":
        return F.potential_ladder({"A": 6., "B": 2., "C": 0.}, "C")
    if key == "divider":
        return F.divider(9, 1000, 2000, 6, .003)
    if key == "kcl":
        return F.kcl_junction(.006, .004, .002, .006)
    if key == "noninv":
        return A.noninv(None, None, None, None, None, symbolic=True)
    if key == "difference":
        return A.diffamp(None, None, None, None, symbolic=True)
    if key == "ina":
        return A.ina(symbolic=True)
    if key == "signals":
        c = Canvas(700, 300, "Common-mode and differential motion",
                   "Common mode moves both inputs together; differential mode moves them in opposite directions.", uid="ref-signals")
        for x, heading, classes in ((175, "Common mode", ("bob", "bob")),
                                    (525, "Differential", ("bob", "bob-rev"))):
            c.add(text(x, 35, heading))
            for i, (y, cls) in enumerate(zip((120, 210), classes)):
                c.add(wire([(x-120, y), (x+120, y)]))
                c.add(text(x-100, y-25, "V_2" if i == 0 else "V_1", "lbl"))
                c.add(f'<g class="{cls}"><circle cx="{x}" cy="{y}" r="9" fill="{CURRENT}"/></g>')
            c.add(text(x, 285, "same shift; V_d fixed" if x == 175 else "opposite shifts; V_cm fixed", "small"))
        return c.render()
    if key == "bridge":
        return F.bridge(None, "balanced", symbolic=True, show_currents=False)
    if key in ("rc", "sine", "phase", "filters", "psd"):
        return curve(key)
    if key in ("inverting", "summing", "tia", "follower", "opamp"):
        return inverting(key)
    return passive(key)
