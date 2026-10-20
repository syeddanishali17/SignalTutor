"""Amplifier figures (op-amp, feedback, non-inverting, difference, instrumentation).

Same grammar as tutor.ui.svg.figures: component NAME in bold, VALUE in a tag,
selection = highlighter halo, current = moving dashes, semantics never by colour
alone. Every function returns a full SVG document.
"""

from __future__ import annotations

from typing import Callable, Iterable

from tutor.sim.units import format_si
from tutor.ui.svg.core import (
    BAD,
    CURRENT,
    INK,
    MUTED,
    OK,
    PLUS,
    VOLT,
    Canvas,
    dot,
    flow,
    ground,
    resistor,
    terminal,
    text,
    value_tag,
    wire,
)


def _sel(selected: Iterable[str] | str | None) -> set[str]:
    if selected is None:
        return set()
    if isinstance(selected, str):
        return {selected}
    return set(selected)


def _v(v: float | None, sig: int = 3) -> str:
    return "" if v is None else format_si(v, "V", sig=sig)


def _ohm(r: float | None) -> str:
    return "" if r is None else format_si(r, "ohm", sig=3)


# ----------------------------------------------------------------------------- primitives


def opamp(c: Canvas, x0: float, yc: float, *, w: float = 120, h: float = 110, top: str = "+",
          eid: str = "U", label: str = "", selected: bool = False, sat: int = 0, rails: bool = True,
          rail_label: str = "±V_s") -> dict[str, tuple[float, float]]:
    """Op-amp triangle pointing right. ``top`` is the sign of the upper input ("+" or "−").

    Returns pin coordinates: ``top``, ``bot``, ``out``.
    """
    pins = {"top": (x0, yc - h / 4), "bot": (x0, yc + h / 4), "out": (x0 + w, yc)}
    if selected:
        c.halo(x0 - 12, yc - h / 2 - 12, w + 24, h + 24, 10)
    c.add(f'<polygon id="{eid}" points="{x0},{yc - h / 2} {x0},{yc + h / 2} {x0 + w},{yc}" fill="#ffffff" '
          f'stroke="{INK}" stroke-width="{3 if selected else 2.4}" stroke-linejoin="round"/>')
    bot_sign = "−" if top == "+" else "+"
    for (px, py), sign in ((pins["top"], top), (pins["bot"], bot_sign)):
        c.add(text(px + 16, py + 6, sign, "lbl", "middle", 'style="font-size:20px"'))
    if rails:
        xr = x0 + w * 0.42
        ytop = yc - h / 2 + h * 0.21
        ybot = yc + h / 2 - h * 0.21
        c.add(f'<line x1="{xr}" y1="{ytop}" x2="{xr}" y2="{ytop - 22}" stroke="{MUTED}" stroke-width="1.8"/>')
        c.add(f'<line x1="{xr}" y1="{ybot}" x2="{xr}" y2="{ybot + 22}" stroke="{MUTED}" stroke-width="1.8"/>')
        c.add(text(xr + 4, ytop - 26, "+V_s", "small", "start"))
        c.add(text(xr + 4, ybot + 36, "−V_s", "small", "start"))
    if label:
        c.add(text(x0 + w * 0.35, yc + 5, label, "tag", "middle", f'style="fill:{MUTED}"'))
    if sat:
        c.add(text(x0 + w + 10, yc - 34, "clipped at " + ("+" if sat > 0 else "−") + "rail", "tag", "start",
                   f'style="fill:{BAD}"'))
    return pins


def _node_label(c: Canvas, x: float, y: float, name: str, val: str, anchor: str = "start",
                selected: bool = False, dy: float = -10) -> None:
    if selected:
        w = 96
        c.halo(x - (w if anchor == "end" else 6), y + dy - 22, w + 6, 52)
    c.add(text(x, y + dy, name, "lbl sel-lbl" if selected else "lbl", anchor))
    if val:
        value_tag(c, x, y + dy + 26, val, anchor, color=VOLT)


# ----------------------------------------------------------------------------- 1 interference


def interference(v1: float, v2: float, v_pickup: float, selected=None, show: str = "common") -> str:
    """Bridge → two long wires → amplifier. A mains cable couples the same 50 Hz into both wires.

    ``show``: "common" animates both wire markers together, "diff" animates them apart.
    """
    sel = _sel(selected)
    c = Canvas(780, 380, "Mains pickup on two wires",
               "A mains cable couples the same 50 Hz voltage into both wires; the bridge signal pushes them apart.",
               uid="intf")
    # bridge box
    if "bridge" in sel:
        c.halo(28, 98, 150, 164)
    c.add(f'<rect x="40" y="110" width="126" height="140" rx="10" fill="#fdf3e7" stroke="{INK}" stroke-width="2"/>')
    c.add(text(103, 172, "bridge", "lbl"))
    c.add(text(103, 192, "V₀ = 5 V", "small"))
    y2, y1 = 150, 222
    for y, name, nid in ((y2, "V_2", "w2"), (y1, "V_1", "w1")):
        if nid in sel:
            c.halo(166, y - 12, 480, 24, 6)
        c.add(wire([(166, y), (640, y)]))
        c.add(dot(166, y))
        c.add(text(176, y - 12, name, "lbl", "start"))
    # amplifier box
    if "amp" in sel:
        c.halo(628, 110, 136, 140)
    c.add(f'<rect x="640" y="122" width="112" height="116" rx="10" fill="#ffffff" stroke="{INK}" stroke-width="2" '
          f'stroke-dasharray="6 4"/>')
    c.add(text(696, 178, "amplifier", "lbl"))
    c.add(text(696, 198, "?", "lbl", "middle", 'style="font-size:22px"'))
    # mains cable + capacitive coupling
    if "mains" in sel:
        c.halo(200, 26, 430, 50)
    path = "M210,52 " + " ".join(f"Q{220 + 40 * k},{40 if k % 2 == 0 else 64} {230 + 40 * k},52" for k in range(10))
    c.add(f'<path d="{path}" fill="none" stroke="{VOLT}" stroke-width="3"/>')
    c.add(text(415, 32, "mains cable · 230 V, 50 Hz", "tag", "middle", f'style="fill:{VOLT}"'))
    for x in (250, 420, 560):
        c.add(f'<line x1="{x}" y1="66" x2="{x}" y2="{y2 - 8}" stroke="{VOLT}" stroke-width="1.6" stroke-dasharray="4 4"/>')
        c.add(f'<line x1="{x + 8}" y1="66" x2="{x + 8}" y2="{y1 - 8}" stroke="{VOLT}" stroke-width="1.6" stroke-dasharray="4 4"/>')
    c.add(text(560, 104, "same pickup on both wires", "small", "start"))
    # animated level markers (together = common mode, apart = differential)
    for y, cls in ((y2, "bob"), (y1, "bob" if show == "common" else "bob-rev")):
        c.add(f'<g class="{cls}"><polygon points="606,{y - 22} 598,{y - 34} 614,{y - 34}" fill="{CURRENT}"/>'
              f'<line x1="606" y1="{y - 22}" x2="606" y2="{y - 12}" stroke="{CURRENT}" stroke-width="2"/></g>')
    c.add(text(606, 262, "both move together" if show == "common" else "moving apart", "tag", "middle",
               f'style="fill:{CURRENT}"'))
    # readouts
    value_tag(c, 300, y2 + 30, f"V₂ = {_v(v2, 4)}", "start", color=VOLT)
    value_tag(c, 300, y1 + 30, f"V₁ = {_v(v1, 4)}", "start", color=VOLT)
    if "diff" in sel:
        c.halo(446, y2 - 4, 104, y1 - y2 + 8)
    c.add(f'<path d="M460,{y2} h-8 V{y1} h8" fill="none" stroke="{PLUS}" stroke-width="2"/>')
    c.add(text(466, (y1 + y2) / 2 - 2, "V₂ − V₁", "lbl", "start", f'style="fill:{PLUS}"'))
    c.add(text(466, (y1 + y2) / 2 + 16, format_si(v2 - v1, "V", 3), "val", "start", f'style="fill:{PLUS}"'))
    c.add(text(390, 330, f"pickup right now: {format_si(v_pickup, 'V', 3)} on each wire", "small"))
    return c.render()


# ----------------------------------------------------------------------------- 2 open loop


def opamp_open(v_plus: float, v_minus: float, v_out: float, rail: float, selected=None) -> str:
    sel = _sel(selected)
    c = Canvas(680, 360, "Op-amp without feedback",
               "The op-amp multiplies the difference of its inputs by a huge gain; the output stops at the rails.",
               uid="ol")
    sat = 1 if v_out >= rail - 1e-9 else -1 if v_out <= -rail + 1e-9 else 0
    pins = opamp(c, 260, 180, top="+", selected="U" in sel, sat=sat, label="A_d")
    (xt, yt), (xb, yb), (xo, yo) = pins["top"], pins["bot"], pins["out"]
    for (x, y), nid, name, val in (((xt, yt), "Vp", "V_+", v_plus), ((xb, yb), "Vm", "V_−", v_minus)):
        c.add(wire([(90, y), (x, y)]))
        c.add(terminal(90, y))
        _node_label(c, 98, y, name, _v(val, 4), "start", selected=nid in sel, dy=-10)
    if "diff" in sel:
        c.halo(158, yt - 10, 92, yb - yt + 20)
    c.add(f'<path d="M178,{yt} h-8 V{yb} h8" fill="none" stroke="{PLUS}" stroke-width="2"/>')
    c.add(text(184, (yt + yb) / 2 + 5, format_si(v_plus - v_minus, "V", 3), "val", "start", f'style="fill:{PLUS}"'))
    c.add(wire([(xo, yo), (500, yo)]))
    c.add(terminal(500, yo))
    _node_label(c, 470, yo, "V_out", _v(v_out, 3), "start", selected="out" in sel, dy=-14)
    # rail gauge
    gx, gt, gb = 620, 50, 310
    if "rail" in sel:
        c.halo(gx - 30, gt - 20, 60, gb - gt + 40)
    c.add(f'<line x1="{gx}" y1="{gt}" x2="{gx}" y2="{gb}" stroke="#d6d0c3" stroke-width="8" stroke-linecap="round"/>')
    for v, lab in ((rail, "+V_s"), (0, "0"), (-rail, "−V_s")):
        y = gt + (rail - v) / (2 * rail) * (gb - gt)
        c.add(f'<line x1="{gx - 10}" y1="{y}" x2="{gx + 10}" y2="{y}" stroke="{MUTED}"/>')
        c.add(text(gx - 14, y + 4, lab, "small", "end"))
    y = gt + (rail - max(-rail, min(rail, v_out))) / (2 * rail) * (gb - gt)
    c.add(f'<polygon points="{gx + 12},{y} {gx + 24},{y - 7} {gx + 24},{y + 7}" fill="{BAD if sat else VOLT}"/>')
    c.add(text(gx, gb + 26, "output range", "small"))
    return c.render()


# ----------------------------------------------------------------------------- 3/4 non-inverting


def noninv(v_in: float | None, v_out: float | None, v_minus: float | None, R1: float | None, R2: float | None, *,
           selected=None, feedback: str = "negative", source: str = "input", sat: int = 0,
           i_max: float = 1e-3, symbolic: bool = False) -> str:
    """Non-inverting amplifier (lecture naming). ``feedback="positive"`` swaps the input signs.

    ``source="bridge"`` draws one bridge node as the input with the other node left unused
    (the lecture's approach 1 for the bridge).
    """
    sel = _sel(selected)
    c = Canvas(740, 450, "Non-inverting amplifier",
               "Input on the + input; R1 from the output to the − input and R2 to ground feed part of the output back.",
               uid="ni")
    top_sign = "+" if feedback == "negative" else "−"
    pins = opamp(c, 300, 170, top=top_sign, selected="U" in sel, sat=sat)
    (xt, yt), (xb, yb), (xo, yo) = pins["top"], pins["bot"], pins["out"]
    xn, ym = 500, 312
    # input side
    if source == "bridge":
        if "bridge" in sel:
            c.halo(20, yt - 46, 132, 150)
        c.add(f'<rect x="32" y="{yt - 34}" width="108" height="126" rx="10" fill="#fdf3e7" stroke="{INK}" stroke-width="2"/>')
        c.add(text(86, yt + 30, "bridge", "lbl"))
        c.add(wire([(140, yt), (xt, yt)]))
        c.add(dot(140, yt))
        c.add(text(150, yt - 10, "V_2", "lbl", "start"))
        c.add(f'<line x1="140" y1="{yt + 70}" x2="230" y2="{yt + 70}" stroke="{MUTED}" stroke-width="2" stroke-dasharray="5 5"/>')
        c.add(text(32, yt + 114, "V_1 — not connected!", "tag", "start", f'style="fill:{BAD}"'))
        if v_in is not None and not symbolic:
            value_tag(c, 150, yt + 30, _v(v_in, 4), "start", color=VOLT)
    else:
        c.add(terminal(100, yt))
        c.add(wire([(100, yt), (xt, yt)]))
        _node_label(c, 108, yt, "V_in", "" if symbolic else _v(v_in, 3), "start", selected="Vin" in sel)
    # output and divider
    c.add(wire([(xo, yo), (xn, yo), (640, yo)]))
    c.add(dot(xn, yo))
    c.add(terminal(640, yo))
    _node_label(c, 600, yo, "V_out", "" if symbolic else _v(v_out, 3), "start", selected="out" in sel, dy=-16)
    c.add(wire([(xn, yo), (xn, 216)]))
    c.add(wire([(xn, 280), (xn, 344)]))
    c.add(wire([(xn, 408), (xn, 420)]))
    if v_out is not None and not symbolic and feedback == "negative" and abs(v_out) > 0:
        s = min(1.0, abs(v_out / (R1 + R2)) / i_max) if R1 and R2 else 0
        pts = [(xn, yo + 4), (xn, 418)] if v_out > 0 else [(xn, 418), (xn, yo + 4)]
        c.add(flow(pts, s, eid="I"))
    resistor(c, xn, 248, label="R_1", value="" if symbolic else _ohm(R1), eid="R1", selected="R1" in sel,
             label_side="right")
    resistor(c, xn, 376, label="R_2", value="" if symbolic else _ohm(R2), eid="R2", selected="R2" in sel,
             label_side="right")
    ground(c, xn, 420, label="")
    # feedback path back to the lower input
    fb_color = INK if feedback == "negative" else BAD
    if "fb" in sel:
        c.halo(254, yb - 12, xn - 254 + 12, 24, 6)
        c.halo(254, yb - 12, 24, ym - yb + 24, 6)
        c.halo(254, ym - 12, xn - 254 + 12, 24, 6)
    c.add(f'<polyline points="{xn},{ym} 266,{ym} 266,{yb} {xb},{yb}" fill="none" stroke="{fb_color}" '
          f'stroke-width="2.4" stroke-linejoin="round"/>')
    c.add(dot(xn, ym))
    c.add(text(383, ym + 24, "feedback" + (" → − input (negative)" if feedback == "negative" else " → + input (POSITIVE!)"),
               "tag", "middle", f'style="fill:{fb_color}"'))
    if "Vm" in sel:
        c.halo(268, yb + 10, 96, 62)
    lbl = "V_−" if feedback == "negative" else "V_+"
    c.add(text(278, yb + 32, lbl, "lbl", "start"))
    if v_minus is not None and not symbolic:
        value_tag(c, 278, yb + 58, _v(v_minus, 4), "start", color=VOLT)
    return c.render()


# ----------------------------------------------------------------------------- 5 difference amplifier


def diffamp(v1: float | None, v2: float | None, v_out: float | None, R: tuple[float, float, float, float] | None, *,
            selected=None, i1: float | None = None, i2: float | None = None, sat: int = 0, symbolic: bool = False,
            i_max: float = 2e-3) -> str:
    sel = _sel(selected)
    c = Canvas(760, 430, "Difference amplifier",
               "V1 through R1 to the − input with feedback R2; V2 through R3 to the + input with R4 to ground.",
               uid="da")
    R1, R2, R3, R4 = R if R else (None, None, None, None)
    pins = opamp(c, 400, 200, top="−", selected="U" in sel, sat=sat)
    (xt, yt), (xb, yb), (xo, yo) = pins["top"], pins["bot"], pins["out"]
    ytop_in, ybot_in = 150, 260
    xm = 340
    # top path: V1 -> R1 -> V- ; feedback R2
    c.add(terminal(70, ytop_in))
    c.add(wire([(70, ytop_in), (170, ytop_in)]))
    c.add(wire([(250, ytop_in), (xm, ytop_in), (370, ytop_in), (370, yt), (xt, yt)]))
    c.add(dot(xm, ytop_in))
    c.add(wire([(xm, ytop_in), (xm, 80), (420, 80)]))
    c.add(wire([(500, 80), (590, 80), (590, yo)]))
    c.add(wire([(xo, yo), (590, yo), (660, yo)]))
    c.add(dot(590, yo))
    c.add(terminal(660, yo))
    # bottom path: V2 -> R3 -> V+ ; R4 to ground
    c.add(terminal(70, ybot_in))
    c.add(wire([(70, ybot_in), (170, ybot_in)]))
    c.add(wire([(250, ybot_in), (xm, ybot_in), (370, ybot_in), (370, yb), (xb, yb)]))
    c.add(dot(xm, ybot_in))
    c.add(wire([(xm, ybot_in), (xm, 300)]))
    c.add(wire([(xm, 364), (xm, 380)]))
    ground(c, xm, 380, label="")
    if not symbolic:
        for (val, y, nid) in ((i1, ytop_in, "i1"), (i2, ybot_in, "i2")):
            if val is not None and abs(val) > 1e-12:
                pts = [(74, y), (166, y)] if val > 0 else [(166, y), (74, y)]
                c.add(flow(pts, min(1.0, abs(val) / i_max), eid=nid))
    resistor(c, 210, ytop_in, vertical=False, label="R_1", value="" if symbolic else _ohm(R1), eid="R1",
             selected="R1" in sel, length=80)
    resistor(c, 460, 80, vertical=False, label="R_2", value="" if symbolic else _ohm(R2), eid="R2",
             selected="R2" in sel, length=80)
    resistor(c, 210, ybot_in, vertical=False, label="R_3", value="" if symbolic else _ohm(R3), eid="R3",
             selected="R3" in sel, length=80)
    resistor(c, xm, 332, label="R_4", value="" if symbolic else _ohm(R4), eid="R4", selected="R4" in sel,
             label_side="right")
    _node_label(c, 78, ytop_in, "V_1", "" if symbolic else _v(v1, 4), "start", selected="in1" in sel, dy=-14)
    _node_label(c, 78, ybot_in, "V_2", "" if symbolic else _v(v2, 4), "start", selected="in2" in sel, dy=-14)
    _node_label(c, 600, yo, "V_out", "" if symbolic else _v(v_out, 3), "start", selected="out" in sel, dy=-16)
    if "Vm" in sel:
        c.halo(xm - 16, ytop_in - 16, 32, 32, 16)
    if "Vp" in sel:
        c.halo(xm - 16, ybot_in - 16, 32, 32, 16)
    c.add(text(xm + 6, ytop_in + 22, "V_−", "tag", "start"))
    c.add(text(xm + 6, ybot_in - 10, "V_+", "tag", "start"))
    if not symbolic and i1 is not None and i2 is not None:
        c.add(text(390, 410, f"drawn from the source: i₁ = {format_si(i1, 'A')}, i₂ = {format_si(i2, 'A')}",
                   "small", "start"))
    return c.render()


# ----------------------------------------------------------------------------- 6 instrumentation amplifier


def ina(res=None, R1: float | None = None, R2: float | None = None, R: float | None = None, *, selected=None,
        view: str = "both", probe: str | None = None, symbolic: bool = False, i_max: float = 1e-3,
        mismatch: float = 0.0) -> str:
    """Three-op-amp instrumentation amplifier with stage boxes.

    ``res`` is a tutor.sim.amplifiers.InaResult (or None for symbolic drawings).
    ``view``: "common" / "diff" animate the input level markers together / apart.
    ``probe``: "in" / "stage1" / "out" draws an oscilloscope probe at those nodes.
    """
    sel = _sel(selected)
    c = Canvas(900, 540, "Instrumentation amplifier",
               "Stage 1: two op-amps with R2 feedback and one R1 between their inverting inputs. "
               "Stage 2: a difference amplifier with four equal resistors.", uid="ina")
    # stage boxes
    for (x, y, w, h, title, sub, sid) in ((140, 34, 330, 486, "Stage 1", "A_d = 1 + 2R₂/R₁ · A_cm = 1", "stage1"),
                                          (490, 150, 390, 300, "Stage 2", "A_d = 1 · A_cm = 0", "stage2")):
        if sid in sel:
            c.halo(x - 6, y - 6, w + 12, h + 12, 14)
        c.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="none" stroke="#b9b2a2" '
              f'stroke-width="1.6" stroke-dasharray="7 5"/>')
        tx, anc = (x + 12, "start") if sid == "stage1" else (x + w - 12, "end")
        c.add(text(tx, y + h - 26, title, "tag", anc))
        c.add(text(tx, y + h - 9, sub, "small", anc))
    u1 = opamp(c, 250, 120, top="+", eid="U1", selected="U1" in sel,
               sat=(res.saturated.get("U1", 0) if res else 0), rails=False)
    u2 = opamp(c, 250, 420, top="−", eid="U2", selected="U2" in sel,
               sat=(res.saturated.get("U2", 0) if res else 0), rails=False)
    xa = 205
    yA, yB = 220, 320
    # inputs
    yin1, yin2 = u1["top"][1], u2["bot"][1]
    for y, nid in ((yin1, "in1"), (yin2, "in2")):
        c.add(terminal(70, y))
        c.add(wire([(70, y), (250, y)]))
    # level markers on the inputs (common: together, diff: apart)
    if view in ("common", "diff"):
        for y, cls in ((yin1, "bob"), (yin2, "bob" if view == "common" else "bob-rev")):
            c.add(f'<g class="{cls}"><polygon points="40,{y - 4} 30,{y - 16} 50,{y - 16}" fill="{CURRENT}"/></g>')
    # node A / B and R1
    c.add(wire([(xa, yA), (xa, u1["bot"][1]), (250, u1["bot"][1])]))
    c.add(wire([(xa, yB), (xa, u2["top"][1]), (250, u2["top"][1])]))
    c.add(wire([(xa, yA), (xa, 238)]))
    c.add(wire([(xa, 302), (xa, yB)]))
    resistor(c, xa, 270, label="R_1", value="" if symbolic else _ohm(R1), eid="R1", selected="R1" in sel)
    # R2 feedback resistors
    xo1, yo1 = u1["out"]
    xo2, yo2 = u2["out"]
    xr = 420
    c.add(wire([(xa, yA), (275, yA)]))
    c.add(wire([(355, yA), (xr, yA), (xr, yo1)]))
    c.add(wire([(xa, yB), (275, yB)]))
    c.add(wire([(355, yB), (xr, yB), (xr, yo2)]))
    c.add(wire([(xo1, yo1), (xr, yo1)]))
    c.add(wire([(xo2, yo2), (xr, yo2)]))
    for (x, y) in ((xa, yA), (xa, yB), (xr, yo1), (xr, yo2)):
        c.add(dot(x, y))
    # the one current through R2 - R1 - R2
    if res is not None and not symbolic and abs(res.i_R1) > 1e-12:
        s = min(1.0, abs(res.i_R1) / i_max)
        path = [(xr, yo2 + 4), (xr, yB), (xa, yB), (xa, yA), (xr, yA), (xr, yo1 - 4)]
        c.add(flow(path if res.i_R1 > 0 else list(reversed(path)), s, eid="Ipath"))
    if "Ipath" in sel:
        c.halo(xa - 14, yA - 14, xr - xa + 28, yB - yA + 28, 10)
    resistor(c, 315, yA, vertical=False, label="R_2", value="" if symbolic else _ohm(R2), eid="R2a",
             selected=bool({"R2a", "R2"} & sel), length=80)
    resistor(c, 315, yB, vertical=False, label="R_2", value="" if symbolic else _ohm(R2), eid="R2b",
             selected=bool({"R2b", "R2"} & sel), length=80)
    # node labels
    _node_label(c, xa - 12, yA, "V_A", "" if (symbolic or res is None) else _v(res.v_A, 4), "end",
                selected="VA" in sel, dy=-6)
    _node_label(c, xa - 12, yB, "V_B", "" if (symbolic or res is None) else _v(res.v_B, 4), "end",
                selected="VB" in sel, dy=18)
    _node_label(c, 78, yin1, "V_in1", "" if (symbolic or res is None) else _v(res.v_in1, 4), "start",
                selected="in1" in sel, dy=-14)
    _node_label(c, 78, yin2, "V_in2", "" if (symbolic or res is None) else _v(res.v_in2, 4), "start",
                selected="in2" in sel, dy=-14)
    # stage 2
    xs, xm2 = 470, 600
    y_m, y_p = 250, 352
    u3 = opamp(c, 650, 300, top="−", eid="U3", selected="U3" in sel,
               sat=(res.saturated.get("U3", 0) if res else 0), rails=False)
    c.add(wire([(xr, yo1), (xs, yo1), (xs, y_m), (500, y_m)]))
    c.add(wire([(580, y_m), (xm2, y_m), (xm2, u3["top"][1]), (650, u3["top"][1])]))
    c.add(wire([(xr, yo2), (xs, yo2), (xs, y_p), (500, y_p)]))
    c.add(wire([(580, y_p), (xm2, y_p), (xm2, u3["bot"][1]), (650, u3["bot"][1])]))
    c.add(wire([(xm2, y_m), (xm2, 200), (660, 200)]))
    c.add(wire([(740, 200), (820, 200), (820, 300)]))
    xo3, yo3 = u3["out"]
    c.add(wire([(xo3, yo3), (860, yo3)]))
    c.add(dot(820, yo3))
    c.add(terminal(860, yo3))
    c.add(wire([(xm2, y_p), (xm2, 380)]))
    c.add(wire([(xm2, 436), (xm2, 446)]))
    ground(c, xm2, 446, label="")
    resistor(c, 540, y_m, vertical=False, label="R", value="" if symbolic else _ohm(R), eid="Ra",
             selected="Ra" in sel, length=80)
    resistor(c, 700, 200, vertical=False, label="R", value="" if symbolic else _ohm(R), eid="Rf",
             selected="Rf" in sel, length=80)
    resistor(c, 540, y_p, vertical=False, label="R", value="" if symbolic else _ohm(R), eid="Rb",
             selected="Rb" in sel, length=80)
    gval = "" if (symbolic or R is None) else _ohm(R * (1 + mismatch))
    resistor(c, xm2, 408, label="R", value=gval, eid="Rg", selected="Rg" in sel, label_side="right", length=56)
    _node_label(c, xs + 8, yo1, "V_o1", "" if (symbolic or res is None) else _v(res.v_o1, 4), "start",
                selected="o1" in sel, dy=-12)
    _node_label(c, xs + 8, yo2, "V_o2", "" if (symbolic or res is None) else _v(res.v_o2, 4), "start",
                selected="o2" in sel, dy=44)
    _node_label(c, 880, yo3, "V_out", "" if (symbolic or res is None) else _v(res.v_out, 4), "end",
                selected="out" in sel, dy=30)
    # oscilloscope probe marker
    if probe:
        spots = {"in": [(150, yin1), (150, yin2)], "stage1": [(xs, yo1), (xs, yo2)], "out": [(845, yo3)]}[probe]
        for (px, py) in spots:
            c.add(f'<circle cx="{px}" cy="{py}" r="11" fill="none" stroke="{OK}" stroke-width="3"/>')
            c.add(text(px - 15, py + 22, "probe", "tag", "end", f'style="fill:{OK}"'))
    return c.render()


# ----------------------------------------------------------------------------- registry (symbolic, for derivations)

FIGURES: dict[str, Callable[[list[str]], str]] = {
    "noninv": lambda hl: noninv(None, None, None, None, None, selected=hl, symbolic=True),
    "diffamp": lambda hl: diffamp(None, None, None, None, selected=hl, symbolic=True),
    "ina": lambda hl: ina(None, selected=hl, symbolic=True),
}

