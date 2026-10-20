"""SVG primitives with a fixed visual grammar (spec 16.4).

Pure string builders (no Streamlit), so figures can be tested, shown in the dev
gallery, and reused for printouts. Every drawn part can carry an element id;
selected ids get a highlighter halo plus a dashed outline, which survives
grayscale printing.

Semantic encoding
-----------------
* wires: dark ink, 2.2 px
* current: blue moving dashes + static arrowheads (direction visible without motion)
* potentials / voltages: amber labels, brackets with signed values
* strain gauge, stretched (+ΔR): crimson, arrow up-right ending in a circled +
* strain gauge, compressed (−ΔR): teal, arrow down-left ending in a circled −
* component NAME (R₁, bold) and VALUE (R + ΔR, in its own tag) are never merged
* selection: yellow highlighter halo + dashed outline + bold label
"""

from __future__ import annotations

import html
import math
import re
from dataclasses import dataclass, field

INK = "#1d2430"
WIRE = "#2b3340"
MUTED = "#6b7280"
FAINT = "#d9d4c7"
PAPER = "#fbfaf7"
CURRENT = "#1d5fa8"
VOLT = "#b4540a"
PLUS = "#be123c"
MINUS = "#0f766e"
HILITE = "#ffe066"
HILITE_EDGE = "#8a6d00"
OK = "#15803d"
BAD = "#b91c1c"

STYLE = f"""
<style>
.mst text {{ font-family: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif; fill: {INK}; }}
.mst .lbl {{ font-size: 17px; font-weight: 700; }}
.mst .val {{ font-size: 14px; font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; }}
.mst .sym {{ font-size: 16px; font-family: "Cambria Math", Cambria, "Times New Roman", serif; font-style: italic; }}
.mst .small {{ font-size: 13px; fill: {MUTED}; }}
.mst .tag {{ font-size: 12px; font-weight: 700; letter-spacing: .03em; }}
.mst .volt {{ fill: {VOLT}; }}
.mst .cur {{ fill: {CURRENT}; }}
.mst .plus {{ fill: {PLUS}; }}
.mst .minus {{ fill: {MINUS}; }}
.mst .sel-lbl {{ font-weight: 800; }}
.mst .wire {{ stroke: {WIRE}; stroke-width: 2.2; fill: none; stroke-linecap: round; stroke-linejoin: round; }}
.mst .wire.dim {{ stroke: {FAINT}; }}
.mst .flow {{ stroke: {CURRENT}; fill: none; stroke-linecap: round; stroke-dasharray: 2 10; animation: mst-dash 1s linear infinite; }}
@keyframes mst-dash {{ to {{ stroke-dashoffset: -24; }} }}
.mst .bob {{ animation: mst-bob 2.4s ease-in-out infinite; }}
.mst .bob-rev {{ animation: mst-bob 2.4s ease-in-out infinite reverse; }}
@keyframes mst-bob {{ 0%, 100% {{ transform: translateY(-9px); }} 50% {{ transform: translateY(9px); }} }}
@media (prefers-reduced-motion: reduce) {{ .mst * {{ animation: none !important; }} }}
.mst .halo {{ fill: {HILITE}; fill-opacity: .8; stroke: {HILITE_EDGE}; stroke-width: 1.5; stroke-dasharray: 5 3; }}
</style>
"""


@dataclass
class Canvas:
    width: int
    height: int
    title: str
    desc: str = ""
    parts: list[str] = field(default_factory=list)
    under: list[str] = field(default_factory=list)  # halos, drawn below everything
    uid: str = "f"

    def add(self, s: str) -> None:
        self.parts.append(s)

    def halo(self, x: float, y: float, w: float, h: float, r: float = 8) -> None:
        self.under.append(f'<rect class="halo" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}"/>')

    def render(self) -> str:
        t = html.escape(self.title)
        d = html.escape(self.desc or self.title)
        return (
            f'<svg class="mst" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.width} {self.height}" '
            f'width="100%" role="img" aria-labelledby="{self.uid}-t {self.uid}-d" '
            f'style="max-width:{self.width * 1.35:.0f}px;display:block;margin:0 auto;height:auto">'
            f'<title id="{self.uid}-t">{t}</title><desc id="{self.uid}-d">{d}</desc>'
            f'{STYLE}<rect x="0" y="0" width="{self.width}" height="{self.height}" fill="#ffffff"/>'
            f"{''.join(self.under)}{''.join(self.parts)}</svg>"
        )


def as_img(svg: str, max_width: int | None = None) -> str:
    """Wrap an SVG document as ``<img src="data:image/svg+xml;base64,…">``.

    Streamlit sanitises ``st.html`` with DOMPurify's HTML-only profile, which
    strips inline ``<svg>``. As an image the SVG keeps its own stylesheet and
    CSS animations, is isolated from page CSS, and gets a real alt text.
    """
    import base64

    m_t = re.search(r"<title[^>]*>(.*?)</title>", svg, re.S)
    m_d = re.search(r"<desc[^>]*>(.*?)</desc>", svg, re.S)
    alt = ": ".join(x.group(1) for x in (m_t, m_d) if x)
    m_w = re.search(r'viewBox="0 0 (\d+(?:\.\d+)?) ', svg)
    mw = max_width or (int(float(m_w.group(1)) * 1.35) if m_w else 900)
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    # A media query inside a data-URL SVG is not reliably refreshed by every
    # browser when the device preference changes. Let the parent document
    # choose an explicitly static image as well (including for Safari).
    still = svg.replace("</svg>", '<style>.mst * { animation: none !important; }</style></svg>')
    still_data = base64.b64encode(still.encode("utf-8")).decode("ascii")
    sizing = f"width:100%;max-width:{mw}px;height:auto;display:block;margin:0 auto"
    # DOMPurify strips data-URL srcset on <source>. Both <img> sources are
    # supported, and display:none also removes the inactive image from the
    # accessibility tree. The media query now belongs to the parent document.
    return (
        '<style>.mst-motion-static {display:none!important;}'
        '@media (prefers-reduced-motion:reduce) {'
        '.mst-motion-animated {display:none!important;}'
        '.mst-motion-static {display:block!important;}}</style>'
        f'<img class="mst-motion-animated" src="data:image/svg+xml;base64,{data}" alt="{alt}" style="{sizing}"/>'
        f'<img class="mst-motion-static" src="data:image/svg+xml;base64,{still_data}" alt="{alt}" style="{sizing}"/>'
    )


# --- text ---------------------------------------------------------------------------

_SUB = re.compile(r"_(\{[^}]*\}|[A-Za-z0-9₀-₉]+|[+\-−])")  # V_2, V_{out}, V_+, V_−


def rich(text: str) -> str:
    """Escape text and turn ``V_2`` / ``V_{out}`` into SVG subscripts."""
    out, pos = [], 0
    lowered = False
    for m in _SUB.finditer(text):
        before = html.escape(text[pos : m.start()])
        if lowered:
            out.append(f'<tspan dy="-5">{before}</tspan>')
        else:
            out.append(before)
        sub = m.group(1).strip("{}")
        # explicit small offset: predictable, never collides with a value line below
        out.append(f'<tspan dy="5" font-size="74%">{html.escape(sub)}</tspan>')
        lowered = True
        pos = m.end()
    rest = html.escape(text[pos:])
    out.append(f'<tspan dy="-5">{rest}</tspan>' if lowered and rest else rest)
    return "".join(out)


def text(x: float, y: float, s: str, cls: str = "lbl", anchor: str = "middle", extra: str = "") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}" {extra}>{rich(s)}</text>'


# --- wires, nodes, terminals -------------------------------------------------------


def wire(points: list[tuple[float, float]], dim: bool = False, eid: str = "") -> str:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    idattr = f' id="{eid}"' if eid else ""
    return f'<polyline{idattr} class="wire{" dim" if dim else ""}" points="{pts}"/>'


def dot(x: float, y: float, r: float = 4.2, color: str = WIRE) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{color}"/>'


def terminal(x: float, y: float) -> str:
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{PAPER}" stroke="{WIRE}" stroke-width="2"/>'


# --- parts -----------------------------------------------------------------------------


def _is_symbolic(value: str) -> bool:
    """True for algebraic values like 'R + ΔR' (vs numbers like '350.35 Ω')."""
    stripped = value.replace("Ω", "").replace("µ", "")
    return "Δ" in value or any(ch.isalpha() for ch in stripped.split(" ")[0])


def value_tag(c: Canvas, x: float, y: float, value: str, anchor: str = "start", color: str = INK,
              border: str = "#d9d4c7") -> None:
    """A component's VALUE in its own rounded tag, visually separate from its NAME.

    Symbolic values (R + ΔR) use a maths-style italic serif; numbers use mono.
    """
    sym = _is_symbolic(value)
    per = 7.8 if sym else 8.6
    w = len(value) * per + 14
    x0 = x if anchor == "start" else x - w if anchor == "end" else x - w / 2
    c.add(f'<rect x="{x0:.1f}" y="{y - 16:.1f}" width="{w:.1f}" height="23" rx="6" fill="#f7f4ec" stroke="{border}"/>')
    cls = "sym" if sym else "val"
    c.add(f'<text x="{x0 + 7:.1f}" y="{y:.1f}" class="{cls}" text-anchor="start" style="fill:{color}">'
          f"{rich(value)}</text>")


def gauge_badge(c: Canvas, x: float, y: float, strain: int) -> None:
    """Small circled + / − at the arrow head: resistance goes UP (+) or DOWN (−)."""
    color = PLUS if strain > 0 else MINUS
    c.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{color}"/>')
    c.add(f'<text x="{x:.1f}" y="{y + 5:.1f}" text-anchor="middle" style="fill:#ffffff;font-size:15px;font-weight:800">'
          f'{"+" if strain > 0 else "−"}</text>')


def resistor(
    c: Canvas,
    cx: float,
    cy: float,
    *,
    vertical: bool = True,
    label: str = "",
    value: str = "",
    eid: str = "",
    strain: int = 0,
    selected: bool = False,
    label_side: str = "left",
    length: float = 64,
    thick: float = 24,
    warm: bool = False,
) -> None:
    """IEC resistor (rectangle).

    ``label`` is the component NAME (R₁); ``value`` its resistance (R + ΔR or
    350.35 Ω), drawn in a separate tag. ``strain`` +1/−1 marks a strain gauge:
    a diagonal arrow through the body (as in the lecture drawings) ending in a
    circled + (stretched → resistance goes up) or − (compressed → goes down).
    """
    w, h = (thick, length) if vertical else (length, thick)
    x0, y0 = cx - w / 2, cy - h / 2
    color = PLUS if strain > 0 else MINUS if strain < 0 else WIRE
    if selected:
        pad = 10
        lw = 116 if label_side in ("left", "right") else 0
        hx = x0 - pad - (lw if label_side == "left" else 0)
        c.halo(hx, y0 - pad, w + 2 * pad + lw, h + 2 * pad)
    fill = "#fff4f4" if strain > 0 else "#effaf8" if strain < 0 else "#ffffff"
    sw = 3.2 if selected else 2.2
    idattr = f' id="{eid}"' if eid else ""
    c.add(f'<rect{idattr} x="{x0:.1f}" y="{y0:.1f}" width="{w}" height="{h}" rx="2" fill="{fill}" '
          f'stroke="{color}" stroke-width="{sw}"/>')
    if strain:
        L = 30
        ax, ay = cx - L / 2, cy + L / 2
        bx, by = cx + L / 2, cy - L / 2
        if strain < 0:
            ax, ay, bx, by = bx, by, ax, ay
        c.add(_arrow_line(ax, ay, bx, by, color, 2.2))
        gauge_badge(c, bx + (7 if strain > 0 else -7), by + (-7 if strain > 0 else 7), strain)
    if warm:
        c.add(text(cx + (w / 2 + 6 if label_side == "left" else -w / 2 - 6), cy + h / 2 + 4,
                   "warm", "tag", "start" if label_side == "left" else "end", f'style="fill:{VOLT}"'))
    if label:
        lcls = "lbl sel-lbl" if selected else "lbl"
        vcol = PLUS if strain > 0 else MINUS if strain < 0 else INK
        if vertical:
            sx = x0 - 12 if label_side == "left" else x0 + w + 12
            anchor = "end" if label_side == "left" else "start"
            c.add(text(sx, cy - 8, label, lcls, anchor))
            if value:
                value_tag(c, sx, cy + 20, value, anchor, color=vcol)
        else:
            c.add(text(cx, y0 - 12, label, lcls))
            if value:
                value_tag(c, cx, y0 + h + 24, value, "middle", color=vcol)


def gauge_legend(c: Canvas, y: float, x: float = 20) -> None:
    """Explains the resistor icons in one line (no unexplained symbols, spec 3)."""
    def mini(x0: float, strain: int) -> None:
        color = PLUS if strain > 0 else MINUS if strain < 0 else WIRE
        fill = "#fff4f4" if strain > 0 else "#effaf8" if strain < 0 else "#ffffff"
        c.add(f'<rect x="{x0:.1f}" y="{y - 13:.1f}" width="30" height="13" rx="2" fill="{fill}" '
              f'stroke="{color}" stroke-width="2"/>')
        if strain > 0:
            c.add(_arrow_line(x0 + 4, y + 2, x0 + 26, y - 15, color, 1.8, 6))
        elif strain < 0:
            c.add(_arrow_line(x0 + 26, y - 15, x0 + 4, y + 2, color, 1.8, 6))
    c.add(f'<line x1="{x}" y1="{y - 24}" x2="{c.width - x}" y2="{y - 24}" stroke="#e4dfd3"/>')
    c.add(text(x, y, "How to read:", "tag", "start"))
    mini(x + 96, 0)
    c.add(text(x + 132, y, "fixed resistor", "small", "start", f'style="fill:{INK}"'))
    mini(x + 240, +1)
    c.add(text(x + 276, y, "gauge stretched: R goes UP (+ΔR)", "small", "start", f'style="fill:{PLUS}"'))
    mini(x + 490, -1)
    c.add(text(x + 526, y, "compressed: DOWN (−ΔR)", "small", "start", f'style="fill:{MINUS}"'))


def ammeter(c: Canvas, x: float, y: float, reading: str, label: str = "A") -> None:
    """Ammeter glyph (circle with A) and its reading in a tag below."""
    c.add(f'<circle cx="{x}" cy="{y}" r="15" fill="#ffffff" stroke="{CURRENT}" stroke-width="2.4"/>')
    c.add(text(x, y + 6, label, "lbl", "middle", f'style="fill:{CURRENT}"'))
    value_tag(c, x, y + 40, reading, "middle", color=CURRENT, border="#bcd3ee")


def _arrow_line(x1: float, y1: float, x2: float, y2: float, color: str, sw: float = 2.0, head: float = 8) -> str:
    ang = math.atan2(y2 - y1, x2 - x1)
    hx1 = x2 - head * math.cos(ang - 0.45)
    hy1 = y2 - head * math.sin(ang - 0.45)
    hx2 = x2 - head * math.cos(ang + 0.45)
    hy2 = y2 - head * math.sin(ang + 0.45)
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>'
        f'<polygon points="{x2:.1f},{y2:.1f} {hx1:.1f},{hy1:.1f} {hx2:.1f},{hy2:.1f}" fill="{color}"/>'
    )


def arrow(x1: float, y1: float, x2: float, y2: float, color: str = INK, sw: float = 2.0, head: float = 9) -> str:
    return _arrow_line(x1, y1, x2, y2, color, sw, head)


def battery(c: Canvas, cx: float, cy: float, *, label: str = "", value: str = "", eid: str = "",
            selected: bool = False, gap: float = 10) -> None:
    """Vertical DC source: long plate (+) on top, short plate (−) below."""
    if selected:
        c.halo(cx - 32, cy - 26, 64 + 96, 52)
    idattr = f' id="{eid}"' if eid else ""
    c.add(f'<g{idattr}>'
          f'<line x1="{cx - 22}" y1="{cy - gap / 2}" x2="{cx + 22}" y2="{cy - gap / 2}" stroke="{INK}" stroke-width="3"/>'
          f'<line x1="{cx - 11}" y1="{cy + gap / 2}" x2="{cx + 11}" y2="{cy + gap / 2}" stroke="{INK}" stroke-width="6"/>'
          f"</g>")
    c.add(text(cx - 30, cy - gap / 2 - 4, "+", "lbl", "middle"))
    c.add(text(cx - 30, cy + gap / 2 + 14, "−", "lbl", "middle"))
    if label:
        c.add(text(cx + 32, cy - 4, label, "lbl sel-lbl" if selected else "lbl", "start"))
    if value:
        value_tag(c, cx + 32, cy + 22, value, "start", color=VOLT)


def ground(c: Canvas, x: float, y: float, *, selected: bool = False, label: str = "0 V") -> None:
    if selected:
        c.halo(x - 26, y - 6, 52, 40)
    c.add(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 10}" stroke="{WIRE}" stroke-width="2.2"/>')
    for i, half in enumerate((16, 10, 4)):
        yy = y + 10 + i * 6
        c.add(f'<line x1="{x - half}" y1="{yy}" x2="{x + half}" y2="{yy}" stroke="{WIRE}" stroke-width="2.2"/>')
    if label:
        c.add(text(x + 22, y + 26, label, "small", "start"))


def flow(points: list[tuple[float, float]], strength: float, eid: str = "", arrows: bool = True,
         offset: float = 0.0) -> str:
    """Current along a path: moving dashes (speed and width ∝ strength) + static arrowheads.

    ``strength`` in [0, 1]; ≤ 0 draws nothing (no current). ``offset`` shifts the
    path sideways so it does not hide the wire.
    """
    if strength <= 1e-6:
        return ""
    s = max(0.0, min(1.0, strength))
    pts = _offset_path(points, offset) if offset else points
    dur = 0.55 / max(s, 0.08)
    # Larger moving dots and matching direction heads; keep paths, dash spacing
    # and timing unchanged so prominence does not imply a different current.
    marker_scale = 1.4
    width = marker_scale * (2.2 + 3.0 * s)
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    idattr = f' id="{eid}"' if eid else ""
    out = [f'<polyline{idattr} class="flow" points="{d}" stroke-width="{width:.2f}" style="animation-duration:{dur:.2f}s"/>']
    if arrows:
        head = marker_scale * (7 + 5 * s)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            seg = math.hypot(x2 - x1, y2 - y1)
            if seg < 40:
                continue
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ang = math.atan2(y2 - y1, x2 - x1)
            tx, ty = mx + head * math.cos(ang), my + head * math.sin(ang)
            b1 = (mx - head * 0.6 * math.cos(ang - 1.1), my - head * 0.6 * math.sin(ang - 1.1))
            b2 = (mx - head * 0.6 * math.cos(ang + 1.1), my - head * 0.6 * math.sin(ang + 1.1))
            out.append(f'<polygon points="{tx:.1f},{ty:.1f} {b1[0]:.1f},{b1[1]:.1f} {b2[0]:.1f},{b2[1]:.1f}" fill="{CURRENT}"/>')
    return "".join(out)


def _normal(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    L = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return ((a[1] - b[1]) / L, (b[0] - a[0]) / L)


def _offset_path(points: list[tuple[float, float]], d: float) -> list[tuple[float, float]]:
    """Offset a polyline sideways by ``d`` (left of the travel direction in screen coords).

    Corners use vertex + d·(n1 + n2)/(1 + n1·n2), the intersection of the two
    offset segments (exact for right angles and straight continuations).
    """
    n = len(points)
    out: list[tuple[float, float]] = []
    for i, (x, y) in enumerate(points):
        if i == 0:
            nx, ny = _normal(points[0], points[1])
            out.append((x + d * nx, y + d * ny))
        elif i == n - 1:
            nx, ny = _normal(points[-2], points[-1])
            out.append((x + d * nx, y + d * ny))
        else:
            n1, n2 = _normal(points[i - 1], points[i]), _normal(points[i], points[i + 1])
            k = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]
            k = k if k > 1e-6 else 1.0
            out.append((x + d * (n1[0] + n2[0]) / k, y + d * (n1[1] + n2[1]) / k))
    return out


def bracket(c: Canvas, x: float, y_top: float, y_bot: float, label: str, value: str, *,
            side: str = "right", color: str = VOLT, selected: bool = False, eid: str = "") -> None:
    """Vertical voltage bracket between two heights, with a signed label (spans two points)."""
    sgn = 1 if side == "right" else -1
    tick = 8 * sgn
    if selected:
        c.halo(min(x, x + 70 * sgn) - 6, y_top - 6, 80, y_bot - y_top + 12)
    idattr = f' id="{eid}"' if eid else ""
    c.add(f'<path{idattr} d="M{x:.1f},{y_top:.1f} h{tick} V{y_bot:.1f} h{-tick}" fill="none" stroke="{color}" stroke-width="2"/>')
    ym = (y_top + y_bot) / 2
    anchor = "start" if side == "right" else "end"
    c.add(text(x + tick + 6 * sgn, ym - 6, label, "lbl volt", anchor))
    c.add(text(x + tick + 6 * sgn, ym + 18, value, "val volt", anchor))


def voltmeter(c: Canvas, cx: float, cy: float, reading: str, *, selected: bool = False, label: str = "V",
              eid: str = "meter", r: float = 22) -> None:
    if selected:
        c.halo(cx - r - 10, cy - r - 10, 2 * r + 20, 2 * r + 46)
    c.add(f'<circle id="{eid}" cx="{cx}" cy="{cy}" r="{r}" fill="#ffffff" stroke="{INK}" stroke-width="{3 if selected else 2.2}"/>')
    c.add(text(cx, cy + 6, label, "lbl"))
    value_tag(c, cx, cy + r + 26, reading, "middle", color=VOLT)
