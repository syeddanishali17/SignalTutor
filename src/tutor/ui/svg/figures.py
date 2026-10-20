"""Figures for the Foundation Playground and the Wheatstone lab.

Every figure is a pure function of simulation state + selection, so the
diagram, the equation strip, the readouts and the plots are always computed
from the same numbers (spec 16.5 / 19).
"""

from __future__ import annotations

import math
from typing import Callable, Iterable

from tutor.sim.bridge import BridgeResult, gauge_flags
from tutor.sim.units import format_si
from tutor.ui.svg.core import (
    BAD,
    CURRENT,
    FAINT,
    INK,
    MINUS,
    MUTED,
    OK,
    PLUS,
    VOLT,
    WIRE,
    Canvas,
    arrow,
    battery,
    bracket,
    dot,
    ammeter,
    flow,
    gauge_badge,
    gauge_legend,
    ground,
    resistor,
    terminal,
    value_tag,
    text,
    voltmeter,
    wire,
)


def _sel(selected: Iterable[str] | str | None) -> set[str]:
    if selected is None:
        return set()
    if isinstance(selected, str):
        return {selected}
    return set(selected)


def _v(v: float, sig: int = 3) -> str:
    return format_si(v, "V", sig=sig)


def _ohm(r: float) -> str:
    return format_si(r, "ohm", sig=3)


# =============================================================================
# Scene A — voltage is a difference (potential ladder)
# =============================================================================


def potential_ladder(potentials: dict[str, float], reference: str, selected=None, v_min: float = -2.0,
                     v_max: float = 14.0, meter: tuple[str, str] = ("A", "B")) -> str:
    """Nodes drawn at heights proportional to their (absolute) potential.

    Labels and axis ticks are relative to ``reference``. The voltmeter bracket
    spans two nodes and shows their difference, which never depends on the reference.
    """
    sel = _sel(selected)
    c = Canvas(600, 390, "Potential ladder", "Nodes drawn at the height of their potential; a voltmeter compares two of them.", uid="lad")
    top, bot = 40, 350

    def y(v: float) -> float:
        return bot - (v - v_min) / (v_max - v_min) * (bot - top)

    ref_v = potentials[reference]
    # axis with ticks every 2 V, labelled relative to the reference
    ax = 90
    c.add(f'<line x1="{ax}" y1="{top}" x2="{ax}" y2="{bot}" stroke="{MUTED}" stroke-width="1.5"/>')
    c.add(text(ax - 6, top - 16, "potential relative to the reference", "small", "start"))
    start = math.ceil((v_min - ref_v) / 2) * 2
    v = start
    while v + ref_v <= v_max + 1e-9:
        yy = y(v + ref_v)
        c.add(f'<line x1="{ax - 5}" y1="{yy:.1f}" x2="{ax}" y2="{yy:.1f}" stroke="{MUTED}"/>')
        c.add(text(ax - 9, yy + 4, f"{v:+.0f} V" if v else "0 V", "val", "end"))
        c.add(f'<line x1="{ax}" y1="{yy:.1f}" x2="{575}" y2="{yy:.1f}" stroke="{FAINT}" stroke-width="0.8"/>')
        v += 2
    # reference line
    yr = y(ref_v)
    if "ref" in sel:
        c.halo(ax + 2, yr - 12, 480, 24, 4)
    c.add(f'<line x1="{ax}" y1="{yr:.1f}" x2="575" y2="{yr:.1f}" stroke="{INK}" stroke-width="1.6" stroke-dasharray="7 5"/>')
    # tag on the side away from the reference node's own label
    if reference == "C":
        c.add(text(ax + 8, yr - 6, f"reference: node {reference} = 0 V", "tag", "start"))
    else:
        c.add(text(575, yr - 6, f"reference: node {reference} = 0 V", "tag", "end"))

    xs = {"A": 210, "B": 320, "C": 520}
    for name, pot in potentials.items():
        x = xs.get(name, 300)
        yy = y(pot)
        if name in sel:
            c.halo(x - 48, yy - 34, 96, 58)
        c.add(f'<line x1="{x - 38}" y1="{yy:.1f}" x2="{x + 38}" y2="{yy:.1f}" stroke="{VOLT}" stroke-width="4" stroke-linecap="round"/>')
        c.add(dot(x, yy, 6, INK))
        rel = pot - ref_v
        c.add(text(x, yy - 12, f"{name}", "lbl sel-lbl" if name in sel else "lbl"))
        c.add(text(x, yy + 22, ("0 V (ref)" if name == reference else f"{rel:+.1f} V"), "val volt"))

    # voltmeter bracket to the right of both nodes: it always spans TWO points
    a, b = meter
    ya, yb = y(potentials[a]), y(potentials[b])
    xm = max(xs[a], xs[b]) + 62
    vab = potentials[a] - potentials[b]
    if "meter" in sel:
        c.halo(xm - 10, min(ya, yb) - 10, 104, max(abs(ya - yb), 30) + 20, 4)
    c.add(f'<line x1="{xs[a] + 40}" y1="{ya:.1f}" x2="{xm:.1f}" y2="{ya:.1f}" stroke="{VOLT}" stroke-width="1.4" stroke-dasharray="3 3"/>')
    c.add(f'<line x1="{xs[b] + 40}" y1="{yb:.1f}" x2="{xm:.1f}" y2="{yb:.1f}" stroke="{VOLT}" stroke-width="1.4" stroke-dasharray="3 3"/>')
    bracket(c, xm, min(ya, yb), max(ya, yb), f"V_{a}{b}", f"{vab:+.1f} V", side="right")
    return c.render()


# =============================================================================
# Scene B — closed loop with one resistor
# =============================================================================


def ohm_loop(V: float, R: float, I: float, I_max: float, closed: bool = True, selected=None,
             meters: bool = False) -> str:
    """One battery, one resistor, one loop.

    ``meters=True`` puts three ammeters at different places in the loop: they
    always read the same value (nothing is used up), and all drop to 0 the
    moment the loop is opened anywhere.
    """
    sel = _sel(selected)
    H = 380 if meters else 330
    c = Canvas(580, H, "Battery and resistor loop",
               "A battery drives current around a closed loop through one resistor.", uid="ohm")
    xl, xr, yt, yb = 90, 400, 70, 280
    cy = (yt + yb) / 2
    if "loop" in sel:
        c.halo(xl - 14, yt - 14, xr - xl + 28, yb - yt + 28)
    if "nodeTop" in sel:
        c.halo(xl - 10, yt - 12, xr - xl + 20, 24, 6)
        c.halo(xl - 10, yt - 12, 20, cy - yt + 6, 6)
        c.halo(xr - 10, yt - 12, 20, cy - 32 - yt + 12, 6)
    # wires (with an optional open switch on the top wire)
    sx = 250
    c.add(wire([(xl, cy - 5), (xl, yt), (sx - 30, yt)]))
    if closed:
        c.add(wire([(sx - 30, yt), (xr, yt), (xr, cy - 32)]))
    else:
        c.add(wire([(sx + 10, yt), (xr, yt), (xr, cy - 32)]))
        c.add(f'<line x1="{sx - 30}" y1="{yt}" x2="{sx + 6}" y2="{yt - 24}" stroke="{WIRE}" stroke-width="2.4" '
              f'stroke-linecap="round"/>')
        c.add(dot(sx - 30, yt, 3.5))
        c.add(dot(sx + 10, yt, 3.5))
        c.add(text(sx - 10, yt - 32, "switch open", "tag", "middle", f'style="fill:{BAD}"'))
    c.add(wire([(xr, cy + 32), (xr, yb), (xl, yb), (xl, cy + 5)]))
    strength = min(1.0, abs(I) / I_max) if I_max > 0 else 0
    if closed:
        c.add(flow([(xl, cy - 8), (xl, yt), (xr, yt), (xr, yb), (xl, yb), (xl, cy + 8)], strength, eid="I"))
    battery(c, xl, cy, label="V", value=_v(V), eid="V", selected="V" in sel)
    resistor(c, xr, cy, label="R", value=_ohm(R), eid="R", selected="R" in sel, label_side="right")
    if meters:
        reading = format_si(I, "A") if closed else "0 A"
        if "I" in sel:
            for mx, my in ((170, yt), (330, yb), (170, yb)):
                c.halo(mx - 22, my - 22, 44, 44, 22)
        for name, (mx, my) in (("A_1", (170, yt)), ("A_2", (330, yb)), ("A_3", (170, yb))):
            ammeter(c, mx, my, reading, label="A")
            c.add(text(mx + 22, my - 12, name, "tag", "start", f'style="fill:{CURRENT}"'))
        c.add(text(255, H - 14, "Three ammeters, three places in the loop — always the same reading.", "small"))
    else:
        lbl = f"I = {format_si(I, 'A')}" if closed else "I = 0 A (no closed path)"
        if "I" in sel:
            c.halo(150, yt + 12, 210, 44)
        c.add(text(255, yt + 34, lbl, "lbl cur sel-lbl" if "I" in sel else "lbl cur"))
        c.add(text(255, yb + 34, "same current everywhere in the loop", "small"))
    return c.render()


# =============================================================================
# Scenes C, D, F — voltage divider
# =============================================================================


def divider(Vin: float, R1: float, R2: float, Vout: float, I: float, *, I_max: float = 5e-3,
            selected=None, reference: str = "bottom", R_load: float | None = None,
            symbolic: bool = False, show_levels: bool = True, show_flow: bool = True) -> str:
    """Divider with brackets for both drops, a level scale, and a movable ground symbol."""
    sel = _sel(selected)
    c = Canvas(640, 400, "Voltage divider", "Two resistors in series across a supply; the output is their junction.", uid="div")
    xb, xr, yt, yb, ym = 80, 330, 60, 340, 200
    xo = 505 if R_load is not None else 470  # output terminal
    if "branch" in sel:
        c.halo(xr - 30, yt + 10, 60, yb - yt - 20)
    if "wire" in sel:
        c.halo(xb - 6, yt - 10, xr - xb + 12, 20, 4)
    c.add(wire([(xb, 195), (xb, yt), (xr, yt), (xr, 100)]))
    c.add(wire([(xr, 160), (xr, 240)]))
    c.add(wire([(xr, 300), (xr, yb), (xb, yb), (xb, 205)]))
    c.add(wire([(xr, ym), (xo, ym)]))
    if R_load is not None:
        xl = 450
        c.add(wire([(xl, ym), (xl, 245)]))
        c.add(wire([(xl, 305), (xl, yb), (xr, yb)]))
        c.add(dot(xl, ym))
    if show_flow:
        c.add(flow([(xb, 190), (xb, yt), (xr, yt), (xr, yb), (xb, yb), (xb, 210)],
                   min(1.0, abs(I) / I_max) if I_max else 0, eid="I"))
    battery(c, xb, 200, label="V_in", value="" if symbolic else _v(Vin), eid="Vin", selected=bool({"Vin", "src"} & sel))
    resistor(c, xr, 130, label="R_1", value="" if symbolic else _ohm(R1), eid="R1", selected="R1" in sel, label_side="right")
    resistor(c, xr, 270, label="R_2", value="" if symbolic else _ohm(R2), eid="R2", selected="R2" in sel, label_side="right")
    if R_load is not None:
        resistor(c, 450, 275, label="R_load", value=_ohm(R_load), label_side="right", length=56)
    c.add(dot(xr, ym))
    if "out" in sel:
        c.halo(xr + 10, ym - 26, xo - xr + 30, 50)
    c.add(terminal(xo, ym))
    c.add(text(xo, ym - 14, "V_out", "lbl sel-lbl" if "out" in sel else "lbl"))
    # potentials relative to the chosen reference
    absolute = {"top": Vin, "mid": Vout, "bottom": 0.0}
    ref = absolute[reference]
    rel = {k: v - ref for k, v in absolute.items()}
    if not symbolic:
        value_tag(c, xo, ym + 30, _v(rel["mid"]), "middle", color=VOLT)
    # brackets for the two drops (left of the resistors)
    bx = 268
    bracket(c, bx, yt + 4, ym - 4, "V_R1", "" if symbolic else _v(Vin - Vout), side="left", selected="VR1" in sel)
    bracket(c, bx, ym + 4, yb - 4, "V_R2", "" if symbolic else _v(Vout), side="left", selected="VR2" in sel)
    # ground symbol at the chosen reference node
    gpos = {"bottom": (200, yb), "mid": (385, ym), "top": (200, yt)}[reference]
    if reference == "top":
        # hang the symbol above the top wire so it does not cross the circuit
        _ground_up(c, gpos[0], yt, selected="gnd" in sel)
    else:
        # at the output node the terminal already reads "0 V": no second label
        ground(c, gpos[0], gpos[1], selected="gnd" in sel, label="" if reference == "mid" else "0 V")
    # level scale
    if show_levels and not symbolic:
        _levels(c, 585, yt, yb, Vin, {"top": rel["top"], "mid": rel["mid"], "bottom": rel["bottom"]},
                {"top": "top", "mid": "out", "bottom": "bottom"}, sel)
    return c.render()


def _ground_up(c: Canvas, x: float, y: float, selected: bool = False) -> None:
    if selected:
        c.halo(x - 26, y - 40, 52, 40)
    c.add(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y - 10}" stroke="{WIRE}" stroke-width="2.2"/>')
    for i, half in enumerate((16, 10, 4)):
        yy = y - 10 - i * 6
        c.add(f'<line x1="{x - half}" y1="{yy}" x2="{x + half}" y2="{yy}" stroke="{WIRE}" stroke-width="2.2"/>')
    c.add(text(x + 22, y - 22, "0 V", "small", "start"))


def _levels(c: Canvas, x: float, yt: float, yb: float, span: float, rel: dict[str, float],
            names: dict[str, str], sel: set[str]) -> None:
    """Vertical potential scale: each node as a tick at its height (labels relative to the reference)."""
    lo = min(rel.values())
    hi = max(rel.values())
    if hi - lo < 1e-12:
        hi = lo + 1

    def y(v: float) -> float:
        return yb - (v - lo) / (hi - lo) * (yb - yt)

    c.add(f'<line x1="{x}" y1="{yt}" x2="{x}" y2="{yb}" stroke="{MUTED}" stroke-width="6" stroke-linecap="round" opacity=".25"/>')
    c.add(text(x, yt - 22, "potential", "small"))
    for key, v in rel.items():
        yy = y(v)
        is_sel = key in sel or names[key] in sel
        c.add(f'<line x1="{x - 12}" y1="{yy:.1f}" x2="{x + 12}" y2="{yy:.1f}" stroke="{VOLT}" stroke-width="{4 if is_sel else 3}"/>')
        c.add(text(x - 16, yy + 4, names[key], "small", "end"))
        c.add(text(x + 16, yy + 4, f"{v:+.2f} V" if abs(v) > 1e-9 else "0 V", "val volt", "start"))


# =============================================================================
# Scene E — junction (KCL)
# =============================================================================


def kcl_junction(I_in: float, I1: float, I2: float, I_max: float, selected=None) -> str:
    sel = _sel(selected)
    c = Canvas(560, 330, "Junction", "Current into a node equals current out of it.", uid="kcl")
    nx, ny = 250, 165
    if "node" in sel:
        c.halo(nx - 22, ny - 22, 44, 44, 22)
    c.add(wire([(50, ny), (nx, ny)]))
    c.add(wire([(nx, ny), (nx, 60), (500, 60)]))
    c.add(wire([(nx, ny), (nx, 270), (500, 270)]))
    c.add(dot(nx, ny, 7, INK))

    def branch(path, I, name, label, lx, ly):
        s = min(1.0, abs(I) / I_max) if I_max else 0
        pts = path if I >= 0 else list(reversed(path))
        c.add(flow(pts, s, eid=name))
        if name in sel:
            c.halo(lx - 10, ly - 22, 200, 34)
        txt = f"{label} = {format_si(I, 'A')}"
        if I < 0:
            txt += "  (flows IN)"
        c.add(text(lx, ly, txt, "lbl cur sel-lbl" if name in sel else "lbl cur", "start"))

    branch([(55, ny), (nx - 8, ny)], I_in, "Iin", "I_in", 60, ny - 14)
    branch([(nx, ny - 8), (nx, 60), (495, 60)], I1, "I1", "I_1", 330, 48)
    branch([(nx, ny + 8), (nx, 270), (495, 270)], I2, "I2", "I_2", 330, 300)
    ok = abs(I_in - I1 - I2) < 1e-12
    c.add(text(nx + 20, ny + 6, "Σ in = Σ out" + (" ✓" if ok else ""), "tag", "start", f'fill="{OK if ok else BAD}"'))
    return c.render()


# =============================================================================
# Wheatstone bridge
# =============================================================================


def bridge(res: BridgeResult | None, mode: str, *, layout: str = "dividers", selected=None,
           show_currents: bool = True, thermal: bool = False, symbolic: bool = False,
           show_scale: bool = True, i_max: float | None = None, legend: bool = False) -> str:
    """Bridge figure in two layouts that share element ids:

    * ``dividers`` — two vertical dividers side by side (spec 16.10: start here)
    * ``diamond``  — the textbook drawing, same circuit rotated
    """
    sel = _sel(selected)
    flags = gauge_flags(mode)  # type: ignore[arg-type]
    c = Canvas(700, 470, "Wheatstone bridge",
               "Two voltage dividers fed by the same supply; a meter reads the difference of their midpoints.", uid="br")

    def rval(name: str) -> str:
        if symbolic or res is None:
            s = flags[name]
            return "R + ΔR" if s > 0 else "R − ΔR" if s < 0 else "R"
        # 5 significant figures: a 0.1 % gauge change (350 → 350.35 Ω) must be visible
        return format_si(res.arms.as_dict()[name], "ohm", sig=5)

    ideal = res is None or math.isinf(res.R_meter)
    imax = i_max or (res.V0 / (2 * res.arms.R1) if res else 1.0)

    if layout == "diamond":
        geo = _bridge_diamond(c, res, flags, sel, rval, show_currents, thermal, symbolic, imax, ideal)
    else:
        geo = _bridge_dividers(c, res, flags, sel, rval, show_currents, thermal, symbolic, imax, ideal)

    # midpoint labels
    (x2, y2), (x1, y1) = geo["V2"], geo["V1"]
    for name, (x, y), anchor, dx in (("V2", (x2, y2), "end", -14), ("V1", (x1, y1), "start", 14)):
        if name in sel:
            c.halo(x + (dx - 86 if anchor == "end" else dx - 6), y - 26, 92, 54)
        val = "" if (symbolic or res is None) else _v(getattr(res, name), 4)
        c.add(text(x + dx, y - 8, name[0] + "_" + name[1], "lbl sel-lbl" if name in sel else "lbl", anchor))
        if val:
            value_tag(c, x + dx, y + 20, val, anchor, color=VOLT)

    # meter between the midpoints
    mx, my = geo["meter"]
    if symbolic or res is None:
        reading = "V₂ − V₁"
    else:
        reading = "V₂ − V₁ = " + format_si(res.Vout, "V", sig=4)
    voltmeter(c, mx, my, reading, selected="meter" in sel)
    if ideal:
        c.add(text(mx, my - 32, "I = 0 (ideal meter)", "small"))
    else:
        c.add(text(mx, my - 32, f"meter R_in = {_ohm(res.R_meter)}", "tag", "middle", f'fill="{BAD}"'))  # type: ignore[union-attr]

    if res is not None and not symbolic and show_scale:
        _bridge_scale(c, 640, 70, 370, res, sel)
    if res is not None and not symbolic and abs(res.Vout) < 1e-12:
        c.add(text(mx, my + 64, "balanced", "tag", "middle", f'style="fill:{OK}"'))
    if any(flags.values()) or legend:
        gauge_legend(c, 458)
    return c.render()


def _bridge_dividers(c, res, flags, sel, rval, show_currents, thermal, symbolic, imax, ideal):
    xs, xl, xr = 70, 260, 470
    yt, yb, ym = 60, 370, 215
    # wires
    c.add(wire([(xs, ym - 5), (xs, yt), (xr, yt), (xr, 100)]))
    c.add(wire([(xl, yt), (xl, 100)]))
    c.add(wire([(xl, 170), (xl, 260)]))
    c.add(wire([(xr, 170), (xr, 260)]))
    c.add(wire([(xl, 330), (xl, yb)]))
    c.add(wire([(xr, 330), (xr, yb), (xs, yb), (xs, ym + 5)]))
    mx = (xl + xr) / 2
    c.add(wire([(xl, ym), (mx - 22, ym)]))
    c.add(wire([(mx + 22, ym), (xr, ym)]))
    c.add(dot(xl, ym))
    c.add(dot(xr, ym))
    c.add(dot(xl, yt))
    c.add(dot(xl, yb))
    if show_currents and res is not None:
        c.add(flow([(xl, yt + 6), (xl, yb - 6)], min(1.0, res.I2 / imax), eid="I2"))
        c.add(flow([(xr, yt + 6), (xr, yb - 6)], min(1.0, res.I1 / imax), eid="I1"))
        if not ideal and abs(res.I_meter) > 0:
            path = [(xl + 8, ym), (mx - 26, ym)] if res.I_meter > 0 else [(xr - 8, ym), (mx + 26, ym)]
            c.add(flow(path, 0.6, arrows=True))
    for name, (x, y) in {"I2": (xl - 24, 398), "I1": (xr + 24, 398)}.items():
        if name in sel:
            c.halo((xl if name == "I2" else xr) - 18, yt + 6, 36, yb - yt - 12)
        if show_currents:
            lab = "I_2" if name == "I2" else "I_1"
            val = "" if (symbolic or res is None) else " = " + format_si(getattr(res, name), "A")
            c.add(text(x, y, lab + val, "val cur", "end" if name == "I2" else "start"))
    battery(c, xs, ym, label="V_0", value="" if (symbolic or res is None) else _v(res.V0), eid="V0", selected="V0" in sel)
    ground(c, (xl + xr) / 2, yb, label="0 V")
    pos = {"R1": (xl, 135, "left"), "R4": (xl, 295, "left"), "R2": (xr, 135, "right"), "R3": (xr, 295, "right")}
    for name, (x, y, side) in pos.items():
        resistor(c, x, y, label=name[0] + "_" + name[1], value=rval(name), eid=name, strain=flags[name],
                 selected=name in sel, label_side=side, warm=thermal and flags[name] != 0)
    return {"V2": (xl, ym), "V1": (xr, ym), "meter": (mx, ym)}


def _bridge_diamond(c, res, flags, sel, rval, show_currents, thermal, symbolic, imax, ideal):
    T, B, L, Rn = (340, 70), (340, 360), (190, 215), (490, 215)
    xs = 60
    c.add(wire([T, (T[0], 40), (xs, 40), (xs, 210)]))
    c.add(wire([(xs, 220), (xs, 395), (B[0], 395), B]))
    for a, b in ((T, L), (T, Rn), (L, B), (Rn, B)):
        c.add(wire([a, b]))
    c.add(wire([L, (340 - 22, 215)]))
    c.add(wire([(340 + 22, 215), Rn]))
    for p in (T, B, L, Rn):
        c.add(dot(*p))
    if show_currents and res is not None:
        c.add(flow([T, L, B], min(1.0, res.I2 / imax), eid="I2"))
        c.add(flow([T, Rn, B], min(1.0, res.I1 / imax), eid="I1"))
    for name, xy in {"I2": (150, 140), "I1": (530, 140)}.items():
        if name in sel:
            c.halo(xy[0] - 40, xy[1] - 20, 80, 30)
        if show_currents:
            c.add(text(xy[0], xy[1], "I_2" if name == "I2" else "I_1", "lbl cur sel-lbl" if name in sel else "lbl cur"))
    battery(c, xs, 215, label="V_0", value="" if (symbolic or res is None) else _v(res.V0), eid="V0", selected="V0" in sel)
    ground(c, 200, 395, label="0 V")
    arms = {"R1": (T, L, "left"), "R2": (T, Rn, "right"), "R3": (Rn, B, "right"), "R4": (L, B, "left")}
    for name, (a, b, side) in arms.items():
        cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) - 90
        _rot_resistor(c, cx, cy, ang, name, rval(name), flags[name], name in sel, side, thermal and flags[name] != 0)
    return {"V2": L, "V1": Rn, "meter": (340, 215)}


def _rot_resistor(c: Canvas, cx, cy, ang, name, value, strain, selected, side, warm):
    color = PLUS if strain > 0 else MINUS if strain < 0 else WIRE
    fill = "#fff4f4" if strain > 0 else "#effaf8" if strain < 0 else "#ffffff"
    if selected:
        c.under.append(f'<rect class="halo" x="{cx - 24}" y="{cy - 44}" width="48" height="88" rx="8" '
                       f'transform="rotate({ang:.1f} {cx} {cy})"/>')
    c.add(f'<rect id="{name}" x="{cx - 12}" y="{cy - 32}" width="24" height="64" rx="2" fill="{fill}" stroke="{color}" '
          f'stroke-width="{3.2 if selected else 2.2}" transform="rotate({ang:.1f} {cx} {cy})"/>')
    if strain:
        L = 30
        ax, ay, bx, by = cx - L / 2, cy + L / 2, cx + L / 2, cy - L / 2
        if strain < 0:
            ax, ay, bx, by = bx, by, ax, ay
        c.add(arrow(ax, ay, bx, by, color, 2.2, 8))
        gauge_badge(c, bx + (7 if strain > 0 else -7), by + (-7 if strain > 0 else 7), strain)
    # label outside the diamond: push away from the diamond centre, perpendicular to the arm
    ox, oy = cx - 340, cy - 215
    L = math.hypot(ox, oy) or 1.0
    lx, ly = cx + ox / L * 52, cy + oy / L * 52
    anchor = "end" if side == "left" else "start"
    c.add(text(lx, ly - 8, name[0] + "_" + name[1], "lbl sel-lbl" if selected else "lbl", anchor))
    vcol = PLUS if strain > 0 else MINUS if strain < 0 else INK
    value_tag(c, lx, ly + 18, value, anchor, color=vcol)
    if warm:
        c.add(text(lx, ly + 40, "warm", "tag", anchor, f'style="fill:{VOLT}"'))


def _bridge_scale(c: Canvas, x: float, yt: float, yb: float, res: BridgeResult, sel: set[str]) -> None:
    """Two scales: full 0..V0 (both midpoints look identical) and a zoom around V0/2."""
    V0 = res.V0

    def y_full(v: float) -> float:
        return yb - v / V0 * (yb - yt)

    xa, xz = x - 34, x + 18
    c.add(text(xa, yt - 26, "0 … V₀", "small"))
    c.add(f'<line x1="{xa}" y1="{yt}" x2="{xa}" y2="{yb}" stroke="{MUTED}" stroke-width="6" opacity=".25" stroke-linecap="round"/>')
    for v, lab in ((V0, "V₀"), (V0 / 2, "V₀/2"), (0, "0")):
        c.add(f'<line x1="{xa - 6}" y1="{y_full(v):.1f}" x2="{xa + 6}" y2="{y_full(v):.1f}" stroke="{MUTED}"/>')
        c.add(text(xa - 10, y_full(v) + 4, lab, "small", "end"))
    for name, v, col in (("V2", res.V2, PLUS), ("V1", res.V1, CURRENT)):
        yy = y_full(v)
        c.add(f'<polygon points="{xa + 8},{yy:.1f} {xa + 18},{yy - 5:.1f} {xa + 18},{yy + 5:.1f}" fill="{col}"/>')
    # zoom bar
    span = max(abs(res.Vout) * 1.6, 1e-3)
    mid = V0 / 2

    def y_zoom(v: float) -> float:
        return (yt + yb) / 2 - (v - mid) / span * (yb - yt) / 2

    c.add(text(xz, yt - 26, "zoom", "small"))
    c.add(f'<line x1="{xz}" y1="{yt}" x2="{xz}" y2="{yb}" stroke="{VOLT}" stroke-width="6" opacity=".18" stroke-linecap="round"/>')
    c.add(f'<line x1="{xz - 8}" y1="{y_zoom(mid):.1f}" x2="{xz + 8}" y2="{y_zoom(mid):.1f}" stroke="{MUTED}" stroke-dasharray="2 2"/>')
    c.add(text(xz + 4, yb + 18, "±" + format_si(span, "V", sig=2), "small"))
    for name, v, col, side in (("V2", res.V2, PLUS, -1), ("V1", res.V1, CURRENT, 1)):
        yy = max(yt, min(yb, y_zoom(v)))
        bold = name in sel
        c.add(f'<line x1="{xz - 10}" y1="{yy:.1f}" x2="{xz + 10}" y2="{yy:.1f}" stroke="{col}" stroke-width="{4 if bold else 3}"/>')
        c.add(text(xz + (14 if side > 0 else -14), yy + 4, "V₁" if name == "V1" else "V₂", "tag",
                   "start" if side > 0 else "end", f'fill="{col}"'))


# =============================================================================
# Lab step 0 — pressure membrane with four strain gauges
# =============================================================================


def membrane(p_kpa: float, p_max_kpa: float, eps: float, x_rel: float, selected=None) -> str:
    """Cross-section of a clamped membrane under pressure, with gauges on the pressed surface.

    The bulge follows the clamped-plate shape w(u) ∝ (1 − 4u²)² (zero slope at the rim).
    Rim gauges are stretched (+ε → R + ΔR), centre gauges squeezed (−ε → R − ΔR); the
    equal magnitudes are the written full-bridge idealisation.
    """
    sel = _sel(selected)
    c = Canvas(700, 420, "Pressure membrane with strain gauges",
               "Pressure bends a clamped membrane; gauges near the rim stretch, gauges near the centre are squeezed.",
               uid="mem")
    xl, xr, y0 = 130, 570, 170
    span = xr - xl
    depth = 70 * max(0.0, min(1.0, p_kpa / p_max_kpa)) if p_max_kpa else 0

    def surf(u: float) -> float:  # u in [-0.5, 0.5]
        return y0 + depth * (1 - 4 * u * u) ** 2

    # clamps (hatched blocks)
    for x0 in (xl - 70, xr):
        c.add(f'<rect x="{x0}" y="{y0 - 34}" width="70" height="90" fill="#ece7dc" stroke="{WIRE}" stroke-width="2"/>')
        for k in range(0, 90, 12):
            c.add(f'<line x1="{x0}" y1="{y0 - 34 + k}" x2="{x0 + 14}" y2="{y0 - 48 + k}" stroke="#b9b2a2"/>')
    c.add(text(xl - 35, y0 + 78, "clamp", "small"))
    c.add(text(xr + 35, y0 + 78, "clamp", "small"))
    # membrane (thick curve) and its bottom surface
    pts_top = [(xl + span * (u + 0.5), surf(u)) for u in [i / 60 - 0.5 for i in range(61)]]
    pts_bot = [(x, y + 12) for x, y in pts_top]
    if "membrane" in sel:
        c.halo(xl - 6, y0 - 16, span + 12, depth + 46)
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts_top) + " L" + \
           " L".join(f"{x:.1f},{y:.1f}" for x, y in reversed(pts_bot)) + " Z"
    c.add(f'<path d="{path}" fill="#dfe7f1" stroke="{WIRE}" stroke-width="2.2"/>')
    if depth < 1:
        c.add(text(350, y0 + 40, "flat: no pressure, no strain", "small"))
    # pressure arrows
    n_arrows = 7
    if "pressure" in sel:
        c.halo(xl + 10, 20, span - 20, y0 - 40)
    alen = 18 + 46 * max(0.0, min(1.0, p_kpa / p_max_kpa)) if p_max_kpa else 0
    if p_kpa > 0:
        for i in range(n_arrows):
            u = -0.42 + i * 0.84 / (n_arrows - 1)
            x = xl + span * (u + 0.5)
            ytip = surf(u) - 32
            c.add(arrow(x, ytip - alen, x, ytip, VOLT, 2.4, 10))
        c.add(text(350, 30, f"p = {p_kpa:g} kPa", "lbl volt"))
    # gauges on the pressed (top) surface
    # positions where the clamped-plate surface strain is equal and opposite (r = 0.8 and r ≈ 0.385)
    gauges = [("R_1", -0.40, +1, "gEdge"), ("R_4", -0.1923, -1, "gCenter"),
              ("R_2", 0.1923, -1, "gCenter"), ("R_3", 0.40, +1, "gEdge")]
    for name, u, sign, gid in gauges:
        x = xl + span * (u + 0.5)
        y = surf(u) - 9
        if gid in sel:
            c.halo(x - 30, y - 30, 60, 48)
        color = PLUS if sign > 0 else MINUS
        fill = "#fff4f4" if sign > 0 else "#effaf8"
        c.add(f'<rect x="{x - 22:.1f}" y="{y - 7:.1f}" width="44" height="14" rx="2" fill="{fill}" '
              f'stroke="{color}" stroke-width="2.2"/>')
        if abs(eps) > 0:
            if sign > 0:  # stretched: arrows pointing outwards
                c.add(arrow(x - 4, y - 18, x - 26, y - 18, color, 2, 7))
                c.add(arrow(x + 4, y - 18, x + 26, y - 18, color, 2, 7))
            else:  # squeezed: arrows pointing inwards
                c.add(arrow(x - 28, y - 18, x - 7, y - 18, color, 2, 7))
                c.add(arrow(x + 28, y - 18, x + 7, y - 18, color, 2, 7))
        c.add(text(x, y + 34 + depth * 0.15, name, "lbl", "middle", f'style="fill:{color}"'))
    # the transfer chain readout
    yb = 330
    c.add(f'<line x1="30" y1="{yb - 44}" x2="670" y2="{yb - 44}" stroke="#e4dfd3"/>')
    c.add(text(30, yb - 22, "The transfer chain", "tag", "start"))
    eps_ue = eps * 1e6
    items = [("pressure", f"p = {p_kpa:g} kPa", VOLT), ("strain", f"ε = ±{abs(eps_ue):.0f} µε", INK),
             ("resistance", f"ΔR/R = ±{abs(x_rel) * 100:.3g} %", PLUS)]
    xs = [40, 270, 480]
    for (cap, val, col), x in zip(items, xs):
        c.add(text(x, yb + 4, cap, "small", "start"))
        value_tag(c, x, yb + 34, val, "start", color=col)
    c.add(arrow(200, yb + 26, 258, yb + 26, MUTED, 2, 9))
    c.add(text(229, yb + 16, "× ξ", "tag", "middle"))
    c.add(arrow(410, yb + 26, 468, yb + 26, MUTED, 2, 9))
    c.add(text(439, yb + 16, "× G", "tag", "middle"))
    c.add(text(350, 410, "rim: stretched (+)  ·  centre: squeezed (−)  ·  gauges sit where the strains are equal and opposite",
               "small"))
    return c.render()


# =============================================================================
# Registry used by derivations / whiteboard references (symbolic labels)
# =============================================================================

FIGURES: dict[str, Callable[[list[str]], str]] = {
    "bridge_quarter": lambda hl: bridge(None, "quarter", selected=hl, symbolic=True, show_currents=True),
    "bridge_full": lambda hl: bridge(None, "full", selected=hl, symbolic=True, show_currents=True),
    "bridge_quarter_diamond": lambda hl: bridge(None, "quarter", layout="diamond", selected=hl, symbolic=True),
    "divider": lambda hl: divider(5.0, 1e3, 1e3, 2.5, 2.5e-3, selected=hl, symbolic=True, show_flow=False),
}

# amplifier figures register their symbolic versions too
from tutor.ui.svg import amp_figures as _amp  # noqa: E402

FIGURES.update(_amp.FIGURES)
from tutor.ui.svg import cap_figures as _cap  # noqa: E402

FIGURES.update(_cap.FIGURES)
from tutor.ui.svg import noise_figures as _noise  # noqa: E402

FIGURES.update(_noise.FIGURES)
