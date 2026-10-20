"""Capacitive-sensor figures (lecture 1, p. 3–6), drawn in the shared visual grammar.

One physical picture serves every capacitive scene: a membrane on two springs above a
fixed plate, the gap ``d − x`` drawn as a real dimension, charges on the plates, the
bias source and an ammeter in the loop. Options switch on pressure arrows, forces
(pull-in) and the microphone oscillation. Everything comes from the values passed in,
which the page takes from ONE simulation result.

Element ids for the inspector: membrane, fixed, gap, x, d, springs, pressure, charges,
field, source, meter, I, Fs, Fe.
"""

from __future__ import annotations

from typing import Callable, Iterable

from tutor.sim.units import format_si
from tutor.ui.svg.core import (
    BAD,
    CURRENT,
    INK,
    MINUS,
    MUTED,
    PLUS,
    VOLT,
    WIRE,
    Canvas,
    arrow,
    dot,
    flow,
    text,
    value_tag,
    wire,
)

GAP_PX = 150.0  # rest gap d drawn this tall
Y_FIXED = 326.0  # top edge of the fixed plate
PLATE_H = 9.0
X_L, X_R = 196.0, 564.0  # membrane extent
XF_L, XF_R = 240.0, 520.0  # fixed plate extent


def _sel(selected: Iterable[str] | str | None) -> set[str]:
    if selected is None:
        return set()
    if isinstance(selected, str):
        return {selected}
    return set(selected)


def _spring(x: float, y_top: float, y_bot: float, coils: int = 6, w: float = 9.0) -> str:
    """Vertical zig-zag spring between two heights (straight lead-ins at both ends)."""
    lead = 8.0
    span = (y_bot - y_top) - 2 * lead
    pts = [(x, y_top), (x, y_top + lead)]
    n = coils * 2
    for i in range(1, n):
        pts.append((x + (w if i % 2 else -w), y_top + lead + span * i / n))
    pts += [(x, y_bot - lead), (x, y_bot)]
    d = " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
    return f'<polyline points="{d}" fill="none" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'


def _dimension(c: Canvas, x: float, y1: float, y2: float, label: str, value: str, color: str = INK,
               side: str = "start") -> None:
    """A real dimension line with arrowheads at both ends and extension ticks."""
    if y2 - y1 < 14:  # too small for two arrowheads: draw a tick bracket instead
        c.add(f'<path d="M{x - 6},{y1} h12 M{x},{y1} V{y2} M{x - 6},{y2} h12" stroke="{color}" stroke-width="2" fill="none"/>')
    else:
        ym = (y1 + y2) / 2
        c.add(arrow(x, ym, x, y1 + 1, color, 2, 7))
        c.add(arrow(x, ym, x, y2 - 1, color, 2, 7))
        c.add(f'<path d="M{x - 7},{y1} h14 M{x - 7},{y2} h14" stroke="{color}" stroke-width="1.4"/>')
    ym = (y1 + y2) / 2
    dx = 10 if side == "start" else -10
    c.add(text(x + dx, ym - 2, label, "lbl", side, f'style="fill:{color}"'))
    if value:
        value_tag(c, x + dx, ym + 20, value, side, color=color)


def capacitor(*, x_rel: float, C: float | None = None, V: float | None = None, I: float | None = None,
              p_rel: float | None = None, p_label: str = "", source: str = "dc", selected=None,
              osc_rel: float = 0.0, forces: tuple[float, float] | None = None, pulled_in: bool = False,
              snap_from_rel: float | None = None, i_strength: float = 0.0, q_rel: float | None = None,
              gap_value: str = "", x_value: str = "", meter_label: str = "", title: str = "Capacitive pressure sensor",
              show_circuit: bool = True, show_d: bool = True, show_x: bool = True,
              area_rel: float | None = None, note: str = "", note_color: str = INK) -> str:
    """The membrane capacitor.

    ``x_rel`` = x/d (membrane deflection toward the fixed plate), ``p_rel`` 0…1 pressure
    arrow scale, ``source`` "dc" / "ac" / "none", ``osc_rel`` microphone swing x₀/d
    (animated), ``forces`` (spring, electrostatic) scaled 0…1, ``q_rel`` 0…1 charge amount.
    """
    sel = _sel(selected)
    c = Canvas(780, 420, title,
               "A membrane on two springs above a fixed plate. Pressure pushes it down; the gap d − x shrinks and "
               "the capacitance grows.", uid="cap")
    xr = min(max(x_rel, 0.0), 0.995)
    y_rest = Y_FIXED - GAP_PX  # membrane underside at rest
    y_m = Y_FIXED - GAP_PX * (1 - xr) if not pulled_in else Y_FIXED - 2.0
    xm = (X_L + X_R) / 2

    # ---- base and fixed plate ----------------------------------------------------------
    c.add(f'<rect x="{X_L - 6}" y="{Y_FIXED + PLATE_H + 4}" width="{X_R - X_L + 12}" height="18" fill="#efebe2" '
          f'stroke="{MUTED}" stroke-width="1.2"/>')
    for k in range(int((X_R - X_L + 12) / 14)):
        x0 = X_L - 6 + k * 14
        c.add(f'<line x1="{x0}" y1="{Y_FIXED + PLATE_H + 22}" x2="{x0 + 12}" y2="{Y_FIXED + PLATE_H + 4}" '
              f'stroke="#c9c2b2" stroke-width="1"/>')
    if "fixed" in sel:
        c.halo(XF_L - 8, Y_FIXED - 8, XF_R - XF_L + 16, PLATE_H + 16)
    c.add(f'<rect x="{XF_L}" y="{Y_FIXED}" width="{XF_R - XF_L}" height="{PLATE_H}" fill="#9aa3b2" stroke="{INK}" '
          f'stroke-width="1.6"/>')
    c.add(text((XF_L + XF_R) / 2, Y_FIXED + PLATE_H + 40, "fixed plate (on the chip)", "small", "middle"))

    # ---- springs (static ends on the base, moving ends on the membrane) -----------------
    if "springs" in sel:
        for xs in (X_L + 16, X_R - 16):
            c.halo(xs - 18, y_m - 4, 36, Y_FIXED + PLATE_H + 8 - y_m)
    # ---- moving group: membrane, its charges, pressure arrows ---------------------------
    grp: list[str] = []
    if not pulled_in:
        for xs in (X_L + 16, X_R - 16):
            c.add(_spring(xs, y_m, Y_FIXED + PLATE_H + 4))
    if "membrane" in sel:
        c.halo(X_L - 8, y_m - PLATE_H - 8, X_R - X_L + 16, PLATE_H + 16)
    grp.append(f'<rect x="{X_L}" y="{y_m - PLATE_H}" width="{X_R - X_L}" height="{PLATE_H}" fill="#cfd6e2" '
               f'stroke="{INK}" stroke-width="1.8" rx="2"/>')
    # charges
    if q_rel is not None and abs(q_rel) > 0.02 and not pulled_in:
        if "charges" in sel:
            c.halo(XF_L, y_m + 2, XF_R - XF_L, 22)
            c.halo(XF_L, Y_FIXED - 24, XF_R - XF_L, 22)
        n = max(1, min(13, round(abs(q_rel) * 13)))
        top_sign, bot_sign = ("+", "−") if q_rel > 0 else ("−", "+")
        top_col, bot_col = (PLUS, MINUS) if q_rel > 0 else (MINUS, PLUS)
        for i in range(n):
            xx = XF_L + 14 + (XF_R - XF_L - 28) * (i + 0.5) / n
            grp.append(text(xx, y_m + 15, top_sign, "tag", "middle", f'style="fill:{top_col};font-size:15px"'))
            c.add(text(xx, Y_FIXED - 5, bot_sign, "tag", "middle", f'style="fill:{bot_col};font-size:15px"'))
    # field lines in the gap
    if V and abs(V) > 0 and not pulled_in and (Y_FIXED - y_m) > 30:
        if "field" in sel:
            c.halo(XF_L + 10, y_m + 18, XF_R - XF_L - 20, Y_FIXED - y_m - 40)
        for k in range(6):
            xx = XF_L + 30 + k * (XF_R - XF_L - 60) / 5
            c.add(f'<line x1="{xx:.1f}" y1="{y_m + 20:.1f}" x2="{xx:.1f}" y2="{Y_FIXED - 22:.1f}" stroke="{VOLT}" '
                  f'stroke-width="1.2" stroke-dasharray="3 4" opacity=".7"/>')
    # pressure arrows
    if p_rel is not None and p_rel > 0.005:
        if "pressure" in sel:
            c.halo(X_L + 30, y_m - PLATE_H - 70, X_R - X_L - 60, 64)
        L = 18 + 40 * min(p_rel, 1.0)
        for k in range(6):
            xx = X_L + 60 + k * (X_R - X_L - 120) / 5
            grp.append(arrow(xx, y_m - PLATE_H - 6 - L, xx, y_m - PLATE_H - 4, CURRENT, 2.4, 9))
        grp.append(text(xm, y_m - PLATE_H - 16 - L, "p" + (f" = {p_label}" if p_label else ""), "lbl", "middle",
                        f'style="fill:{CURRENT}"'))
    # microphone oscillation (amplitude in px from the same state as the plots)
    amp_px = GAP_PX * osc_rel
    if amp_px > 0.4 and not pulled_in:
        c.add(f'<style>@keyframes cap-osc {{ 0%,100% {{ transform: translateY({-amp_px:.1f}px) }} '
              f'50% {{ transform: translateY({amp_px:.1f}px) }} }} .cap-osc {{ animation: cap-osc 1.2s ease-in-out infinite }} '
              f'@media (prefers-reduced-motion: reduce) {{ .cap-osc {{ animation: none }} }}</style>')
        c.add(f'<g class="cap-osc">{"".join(grp)}</g>')
        c.add(f'<line x1="{X_L}" y1="{y_m - amp_px:.1f}" x2="{X_L - 22}" y2="{y_m - amp_px:.1f}" stroke="{MUTED}" '
              f'stroke-dasharray="3 3"/><line x1="{X_L}" y1="{y_m + amp_px:.1f}" x2="{X_L - 22}" y2="{y_m + amp_px:.1f}" '
              f'stroke="{MUTED}" stroke-dasharray="3 3"/>')
        c.add(text(X_L - 26, y_m - amp_px - 6, "±x₀", "tag", "end", f'style="fill:{MUTED}"'))
    elif pulled_in and snap_from_rel is not None:
        dy = GAP_PX * (1 - snap_from_rel) - 2.0
        c.add(f'<style>@keyframes cap-snap {{ 0% {{ transform: translateY({-dy:.1f}px) }} 70% {{ transform: translateY(0px) }} '
              f'100% {{ transform: translateY(0px) }} }} .cap-snap {{ animation: cap-snap 0.9s cubic-bezier(.6,0,1,1) 1 both }} '
              f'@media (prefers-reduced-motion: reduce) {{ .cap-snap {{ animation: none }} }}</style>')
        c.add(f'<g class="cap-snap">{"".join(grp)}</g>')
    else:
        c.add("".join(grp))
    c.add(text(X_L - 8, y_m + 16, "membrane", "small", "end"))

    # ---- dimensions: rest line, x, gap d − x, d ---------------------------------------------
    c.add(f'<line x1="{X_L - 10}" y1="{y_rest}" x2="{X_R + 120}" y2="{y_rest}" stroke="{MUTED}" stroke-width="1.2" '
          f'stroke-dasharray="6 5"/>')
    c.add(text(X_R + 40, y_rest - 7, "rest (x = 0)", "small", "start"))
    if not pulled_in:
        gx = X_R + 34
        if "gap" in sel:
            c.halo(gx - 14, y_m - 4, 110, Y_FIXED - y_m + 8)
        _dimension(c, gx, y_m, Y_FIXED, "d − x", gap_value, PLUS if "gap" in sel else INK)
        if xr > 0.004 and show_x:
            xx = X_R + 12
            if "x" in sel:
                c.halo(xx - 10, y_rest - 6, 20, y_m - y_rest + 12)
            if y_m - y_rest >= 14:
                c.add(arrow(xx, y_rest, xx, y_m - 1, CURRENT, 2.2, 8))
            else:
                c.add(f'<path d="M{xx - 5},{y_rest} h10 M{xx},{y_rest} V{y_m} M{xx - 5},{y_m} h10" stroke="{CURRENT}" '
                      f'stroke-width="2" fill="none"/>')
            c.add(text(xx - 6, (y_rest + y_m) / 2 + 5, "x", "lbl", "end", f'style="fill:{CURRENT}"'))
            if x_value:
                value_tag(c, xx - 6, (y_rest + y_m) / 2 + 26, x_value, "end", color=CURRENT)
    if show_d:
        dx_ = X_R + 160
        if "d" in sel:
            c.halo(dx_ - 12, y_rest - 6, 50, Y_FIXED - y_rest + 12)
        c.add(f'<line x1="{XF_R}" y1="{Y_FIXED}" x2="{dx_ + 8}" y2="{Y_FIXED}" stroke="{MUTED}" stroke-width="1" '
              f'stroke-dasharray="2 4"/>')
        _dimension(c, dx_, y_rest, Y_FIXED, "d", "", MUTED)

    # ---- forces (pull-in) -----------------------------------------------------------------
    if forces is not None and not pulled_in:
        fs, fe = forces
        top = y_m - PLATE_H
        if fs > 0.01:
            if "Fs" in sel:
                c.halo(xm - 74, top - 8 - 90 * fs - 6, 36, 90 * fs + 14)
            c.add(arrow(xm - 56, top - 4, xm - 56, top - 4 - 90 * min(fs, 1.2), MINUS, 4, 12))
            c.add(text(xm - 64, top - 14 - 90 * min(fs, 1.2), "F_spring", "lbl", "end", f'style="fill:{MINUS}"'))
        if fe > 0.01:
            if "Fe" in sel:
                c.halo(xm + 38, top - 8 - 90 * min(fe, 1.2) - 6, 36, 90 * min(fe, 1.2) + 14)
            c.add(arrow(xm + 56, top - 4 - 90 * min(fe, 1.2), xm + 56, top - 4, PLUS, 4, 12))
            c.add(text(xm + 66, top - 14 - 90 * min(fe, 1.2) + 4, "F_el", "lbl", "start", f'style="fill:{PLUS}"'))
    if pulled_in:
        c.add(text(xm, Y_FIXED - 40, "pulled in — the plates touch", "lbl", "middle", f'style="fill:{BAD}"'))
    if note:
        c.add(text(xm, 26, note, "lbl", "middle", f'style="fill:{note_color}"'))
    # top view of the plate area (side views cannot show area)
    if area_rel is not None:
        side = 24 + 46 * max(0.05, min(area_rel, 1.0)) ** 0.5
        cx_, cy_ = 700.0, 70.0
        if "membrane" in sel or "A" in sel:
            c.halo(cx_ - side / 2 - 8, cy_ - side / 2 - 8, side + 16, side + 30)
        c.add(f'<rect x="{cx_ - side / 2:.1f}" y="{cy_ - side / 2:.1f}" width="{side:.1f}" height="{side:.1f}" '
              f'fill="#cfd6e2" stroke="{INK}" stroke-width="1.6"/>')
        c.add(text(cx_, cy_ + 4, "A", "lbl"))
        c.add(text(cx_, cy_ + side / 2 + 16, "area, top view", "small"))

    # ---- circuit: bias source, ammeter, current ---------------------------------------------
    if show_circuit and source != "none":
        xs = 104.0
        y_top_w, y_bot_w = 60.0, Y_FIXED + PLATE_H / 2
        lead_y = y_m - PLATE_H / 2
        path_top = [(X_L, lead_y), (172, lead_y), (172, y_top_w), (xs, y_top_w), (xs, 128)]
        c.add(wire(path_top))
        c.add(dot(X_L, lead_y, 3.5))
        c.add(wire([(xs, 172), (xs, 230)]))
        c.add(wire([(xs, 280), (xs, y_bot_w), (XF_L, y_bot_w)]))
        c.add(dot(XF_L, y_bot_w, 3.5))
        # ammeter
        if "meter" in sel:
            c.halo(xs - 30, 120, 60, 60)
        c.add(f'<circle cx="{xs}" cy="150" r="22" fill="#fff" stroke="{INK}" stroke-width="2.2"/>')
        c.add(text(xs, 156, "A", "lbl"))
        if meter_label:
            value_tag(c, xs, 114, meter_label, "middle", color=CURRENT)
        # source
        if "source" in sel:
            c.halo(xs - 30, 226, 60, 58)
        if source == "ac":
            c.add(f'<circle cx="{xs}" cy="255" r="24" fill="#fff" stroke="{INK}" stroke-width="2.2"/>')
            c.add(f'<path d="M{xs - 13},255 q6.5,-13 13,0 t13,0" fill="none" stroke="{INK}" stroke-width="2.2"/>')
            c.add(text(xs - 32, 248, "V₀ cos ωt", "tag", "end", f'style="fill:{VOLT}"'))
            c.add(text(xs - 32, 266, "AC bias", "small", "end"))
        else:
            c.add(f'<line x1="{xs - 22}" y1="248" x2="{xs + 22}" y2="248" stroke="{INK}" stroke-width="3"/>')
            c.add(f'<line x1="{xs - 11}" y1="261" x2="{xs + 11}" y2="261" stroke="{INK}" stroke-width="6"/>')
            c.add(wire([(xs, 230), (xs, 248)]))
            c.add(wire([(xs, 261), (xs, 280)]))
            c.add(text(xs - 30, 252, "V_b", "tag", "end", f'style="fill:{VOLT}"'))
            c.add(text(xs - 30, 268, "DC bias", "small", "end"))
        if source == "ac":
            c.add(wire([(xs, 230), (xs, 231)]))
        if i_strength > 0:
            c.add(flow([(xs, 128), (xs, y_top_w), (172, y_top_w), (172, lead_y), (X_L - 2, lead_y)], i_strength, eid="I"))
            c.add(flow([(XF_L - 2, y_bot_w), (xs, y_bot_w), (xs, 282)], i_strength, eid="I2"))
        if "I" in sel:
            c.halo(xs - 14, y_top_w - 14, 172 - xs + 28, 28)
            c.halo(xs - 14, y_bot_w - 14, XF_L - xs + 28, 28)
    return c.render()


def product_rule(V: float, C: float, dV: float, dC: float, *, selected=None) -> str:
    """Q = V·C as the area of a rectangle; a small change adds a V·ΔC strip and a C·ΔV strip
    (spec M6: the product rule as the area of a changing rectangle)."""
    sel = _sel(selected)
    c = Canvas(440, 300, "Why there are two terms",
               "Charge is the area of a rectangle with sides C and V. Changing either side adds a strip.", uid="pr")
    x0, y0 = 70.0, 250.0
    W, H = 240.0, 150.0  # C → width, V → height (normalised)
    dw = max(6.0, min(60.0, abs(dC) * W)) if dC else 0.0
    dh = max(6.0, min(50.0, abs(dV) * H)) if dV else 0.0
    c.add(f'<rect x="{x0}" y="{y0 - H}" width="{W}" height="{H}" fill="#eef2f8" stroke="{INK}" stroke-width="2"/>')
    c.add(text(x0 + W / 2, y0 - H / 2 + 6, "Q = V · C", "lbl"))
    if dw:
        if "VdC" in sel:
            c.halo(x0 + W - 4, y0 - H - 4, dw + 8, H + 8)
        c.add(f'<rect x="{x0 + W}" y="{y0 - H}" width="{dw}" height="{H}" fill="{PLUS}" fill-opacity=".22" '
              f'stroke="{PLUS}" stroke-width="2"/>')
        c.add(text(x0 + W + dw + 6, y0 - H / 2 + 6, "V · ΔC", "lbl", "start", f'style="fill:{PLUS}"'))
    if dh:
        if "CdV" in sel:
            c.halo(x0 - 4, y0 - H - dh - 4, W + 8, dh + 8)
        c.add(f'<rect x="{x0}" y="{y0 - H - dh}" width="{W}" height="{dh}" fill="{CURRENT}" fill-opacity=".22" '
              f'stroke="{CURRENT}" stroke-width="2"/>')
        c.add(text(x0 + W / 2, y0 - H - dh - 8, "C · ΔV", "lbl", "middle", f'style="fill:{CURRENT}"'))
    if dw and dh:
        c.add(f'<rect x="{x0 + W}" y="{y0 - H - dh}" width="{dw}" height="{dh}" fill="#d9d4c7" stroke="{MUTED}"/>')
    c.add(text(x0 + W / 2, y0 + 22, "C (width)", "small"))
    c.add(text(x0 - 10, y0 - H / 2, "V", "small", "end"))
    c.add(text(x0 - 10, y0 - H / 2 + 16, "(height)", "small", "end"))
    c.add(f'<line x1="{x0}" y1="{y0}" x2="{x0 + W}" y2="{y0}" stroke="{WIRE}" stroke-width="0"/>')
    return c.render()


FIGURES: dict[str, Callable[[list[str]], str]] = {
    "capacitor": lambda hl: capacitor(x_rel=0.25, V=1.0, q_rel=0.5, source="dc", selected=hl, p_rel=0.5),
    "capacitor_ac": lambda hl: capacitor(x_rel=0.1, V=1.0, q_rel=0.5, source="ac", selected=hl),
    "capacitor_forces": lambda hl: capacitor(x_rel=0.25, V=1.0, q_rel=0.6, source="dc", selected=hl,
                                             forces=(0.6, 0.6)),
}


def amp_label(i: float) -> str:
    return format_si(i, "A", 3)
