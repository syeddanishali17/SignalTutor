"""Concept dependency graph as a layered drawing, top (foundations) to bottom.

Readable at laptop width: nodes are large, and by default only the selected
concept's neighbourhood is drawn (everything it builds on + what needs it).
"""

from __future__ import annotations

from tutor.engine.concept_graph import ConceptGraph
from tutor.ui.svg.core import HILITE, INK, MUTED, Canvas, text

TRACK_TAG = {"math": "M", "physics": "P", "electrical": "E", "course_l01": "L1", "course_l02": "L2", "course_l03": "L3"}
TRACK_FILL = {"math": "#eef2f7", "physics": "#f1f5ec", "electrical": "#fdf3e7", "course_l01": "#f7eef4",
              "course_l02": "#f3effa", "course_l03": "#eef7f6"}
STATE_DASH = {"not_started": "3 4", "shaky": "8 4", "solid": "", "exam_ready": ""}


def subgraph(g: ConceptGraph, focus: str | None, full: bool) -> set[str]:
    if full or not focus or focus not in g.concepts:
        return set(g.concepts)
    down: set[str] = set()
    stack = [focus]
    while stack:
        n = stack.pop()
        for d in g.dependents.get(n, []):
            if d not in down:
                down.add(d)
                stack.append(d)
    return g.ancestors(focus) | {focus} | down


def levels(g: ConceptGraph, nodes: set[str]) -> dict[str, int]:
    lvl: dict[str, int] = {}
    for cid in g.topological_order(nodes):
        pres = [p for p in g.prereqs[cid] if p in lvl]
        lvl[cid] = 1 + max((lvl[p] for p in pres), default=-1)
    return lvl


def concept_map(g: ConceptGraph, selected: str | None = None, states: dict[str, str] | None = None,
                full: bool = False) -> str:
    states = states or {}
    nodes = subgraph(g, selected, full)
    lvl = levels(g, nodes)
    n_lv = max(lvl.values()) + 1
    rows: dict[int, list[str]] = {i: [] for i in range(n_lv)}
    for cid, l in lvl.items():
        rows[l].append(cid)
    col: dict[str, float] = {}
    for l in range(n_lv):
        def bary(c: str) -> float:
            ps = [col[p] for p in g.prereqs[c] if p in col]
            return sum(ps) / len(ps) if ps else 0.0
        rows[l].sort(key=lambda c: (bary(c), c))
        for i, c in enumerate(rows[l]):
            col[c] = i - (len(rows[l]) - 1) / 2
    max_cols = max(len(v) for v in rows.values())
    bw, bh, gx, gy = 196, 46, 26, 34
    W = max(max_cols * (bw + gx) + 40, 760)
    H = n_lv * (bh + gy) + 80
    c = Canvas(int(W), int(H), "Concept map",
               "Foundations at the top; arrows point down to the concepts that need them.", uid="cmap")
    pos: dict[str, tuple[float, float]] = {}
    for cid, l in lvl.items():
        x = W / 2 + col[cid] * (bw + gx) - bw / 2
        y = 56 + l * (bh + gy)
        pos[cid] = (x, y)
    ancestors = g.ancestors(selected) if selected in g.concepts else set()
    for cid in nodes:
        for p in g.prereqs[cid]:
            if p not in pos:
                continue
            x1, y1 = pos[p][0] + bw / 2, pos[p][1] + bh
            x2, y2 = pos[cid][0] + bw / 2, pos[cid][1]
            on = (cid == selected or cid in ancestors) and p in ancestors | {selected}
            colr = INK if on else "#cbc4b4"
            w = 2.6 if on else 1.4
            my = (y1 + y2) / 2
            c.add(f'<path d="M{x1:.1f},{y1:.1f} C{x1:.1f},{my:.1f} {x2:.1f},{my:.1f} {x2:.1f},{y2 - 5:.1f}" '
                  f'fill="none" stroke="{colr}" stroke-width="{w}"/>')
            c.add(f'<polygon points="{x2:.1f},{y2:.1f} {x2 - 5:.1f},{y2 - 9:.1f} {x2 + 5:.1f},{y2 - 9:.1f}" fill="{colr}"/>')
    for cid, (x, y) in pos.items():
        concept = g.concepts[cid]
        st_ = states.get(cid, "not_started")
        is_sel = cid == selected
        in_path = cid in ancestors or is_sel
        if is_sel:
            c.halo(x - 7, y - 7, bw + 14, bh + 14, 10)
        dash = STATE_DASH[st_]
        sw = 3.4 if st_ == "exam_ready" else 2.2 if st_ == "solid" else 1.6
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        fill = TRACK_FILL.get(concept.track, "#ffffff")
        c.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw}" height="{bh}" rx="9" fill="{fill}" '
              f'stroke="{INK if in_path or not selected else "#9b9486"}" stroke-width="{sw}"{dash_attr}/>')
        tag = TRACK_TAG.get(concept.track, "?")
        c.add(f'<rect x="{x + 6:.1f}" y="{y + 11:.1f}" width="28" height="24" rx="5" '
              f'fill="{HILITE if is_sel else "#ffffff"}" stroke="#d6d0c3"/>')
        c.add(text(x + 20, y + 28, tag, "tag", "middle", f'style="fill:{INK}"'))
        label = concept.short or concept.title
        if len(label) > 20:
            label = label[:19] + "…"
        c.add(text(x + 42, y + bh / 2 + 6, label, "lbl" if is_sel else "", "start",
                   f'style="font-size:15px;fill:{INK if in_path or not selected else MUTED}"'))
    c.add(text(20, 16, "Tags: M math · P physics · E electrical · L1/L2 lecture topics", "small", "start"))
    c.add(text(20, 33, "Border: dotted = not started · dashed = shaky · solid = solid · thick = exam-ready",
               "small", "start"))
    return c.render()
