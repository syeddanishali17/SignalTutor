"""Equation strip and formula cards (spec 16.2, 16.5, 16.6 equation_strip).

Visual rules (apply to every module):

* Equations are always typeset LaTeX (KaTeX), never slash-notation text.
* The strip shows: governing law → the same law with today's numbers → result.
* Terms are written as ``[[term_id]]`` tokens. A token's LaTeX may itself contain
  tokens, so a composite term (``R_1 + R_4``) and its pieces can each be boxed.
* The boxed term(s) come from the same selection that outlines the parts in the
  SVG and the matching controls (tutor.ui.components.inspector.resolve).
* Beginner mode can show an annotated version of the law (``\\underbrace``
  labels that name numerator and denominator).
"""

from __future__ import annotations

import html
import re

import streamlit as st

from tutor.engine.formula_view import view
from tutor.models.content import Formula, Scene
from tutor.sim.units import format_si
from tutor.ui import state
from tutor.ui.components import inspector

_TOKEN = re.compile(r"\[\[(\w+)\]\]")
BOX = r"\fcolorbox{#8a6d00}{#ffe066}{$\displaystyle {tex}$}"


def q(value: float, unit: str, sig: int = 3, force_prefix: str | None = None) -> str:
    """A quantity as LaTeX with an upright unit, e.g. ``-1.25\\,\\text{mV}``."""
    s = format_si(value, unit, sig=sig, force_prefix=force_prefix).replace("−", "-")
    num, _, u = s.partition(" ")
    if not u:
        return num
    if u.startswith("µ"):
        u = u[1:]
        pre = r"\mu"
    else:
        pre = ""
    u = u.replace("Ω", r"\Omega")
    if u.endswith(r"\Omega"):
        return rf"{num}\,{pre}\text{{{u[:-6]}}}\Omega"
    return rf"{num}\,{pre}\text{{{u}}}"


def mark(template: str, scene: Scene | None, boxed: set[str]) -> str:
    """Expand ``[[id]]`` tokens recursively; box the selected ones."""
    bundle = state.bundle()
    terms = {t.id: t for t in scene.terms} if scene else {}

    def tex_of(tid: str, depth: int = 0) -> str:
        t = terms.get(tid)
        if t is None:
            return tid
        raw = t.latex or bundle.symbols[t.symbol].latex
        inner = _TOKEN.sub(lambda m: sub(m, depth + 1), raw) if depth < 4 else raw
        return inner

    def sub(m: re.Match[str], depth: int = 0) -> str:
        tid = m.group(1)
        tex = tex_of(tid, depth)
        if tid in boxed:
            return BOX.replace("{tex}", tex)
        return "{" + tex + "}"

    return _TOKEN.sub(sub, template)


def strip(scope: str, scene: Scene | None, law: str, numbers: str, result: str, *,
          law_beginner: str | None = None, selectable: list[str] | None = None,
          caption: str | None = None, stacked: bool = False) -> None:
    """Render law → numbers → result.

    ``selectable`` lists term ids offered as clickable symbols (LaTeX buttons).
    ``stacked`` puts the law on its own line (long formulas never get clipped).
    """
    sel = inspector.selected(scope)
    res = inspector.resolve(scene, sel) if scene else inspector.Resolved()
    mode = state.mode()
    shown_law = law_beginner if (law_beginner and mode == "beginner") else law
    with st.container(key="eqstrip"):
        st.markdown('<p class="mst-kicker">Equation strip — the same numbers as the picture</p>',
                    unsafe_allow_html=True)
        if stacked or (law_beginner and mode == "beginner"):
            st.latex(mark(shown_law, scene, res.boxed))
            c2, a2, c3 = st.columns([7, 0.5, 3.4], vertical_alignment="center")
        else:
            c1, a1, c2, a2, c3 = st.columns([5, 0.5, 5, 0.5, 3.4], vertical_alignment="center")
            with c1:
                st.latex(mark(shown_law, scene, res.boxed))
            with a1:
                st.markdown('<div class="mst-eqarrow">→</div>', unsafe_allow_html=True)
        with c2:
            st.latex(numbers)
        with a2:
            st.markdown('<div class="mst-eqarrow">→</div>', unsafe_allow_html=True)
        with c3:
            st.latex(result)
        if selectable and scene and mode != "exam":
            with st.container(horizontal=True, gap="small", key="eqterms"):
                st.markdown('<span class="mst-muted" style="padding-top:9px;display:inline-block">'
                            'Click a symbol:</span>', unsafe_allow_html=True)
                for tid in selectable:
                    on = tid in res.boxed or tid == sel
                    st.button(f"${inspector.term_latex(scene, tid)}$", key=f"eqsel_{scope}_{tid}",
                              type="primary" if on else "secondary",
                              on_click=inspector.select, args=(scope, None if tid == sel else tid))
        if caption:
            st.caption(caption)


def formula_card(f: Formula, show_meaning: bool = True) -> None:
    """Formula with status badge, needs-review flag and meaning card (spec 4.4, 11)."""
    v = view(f, state.mode())
    chip = {"verified": "verified", "supplemental": "supplemental", "needs_review": "needs_review"}.get(f.status, "supplemental")
    st.markdown(
        f'<span class="mst-chip {chip}">{html.escape(f.status.replace("_", " "))}</span>'
        f'<b>{html.escape(f.title)}</b> <span class="mst-muted">· {html.escape(f.source)}</span>',
        unsafe_allow_html=True,
    )
    st.latex(v.latex)
    if v.flag:
        with st.container(key=f"box-flag-{f.id}"):
            st.markdown("⚠ " + v.flag.lstrip("⚠ "))
    if v.lecture_latex:
        st.caption("As written:")
        st.latex(v.lecture_latex)
    if show_meaning and (f.meaning or f.assumptions or f.comes_from) and state.mode() != "exam":
        with st.expander("Meaning card — every symbol, its unit, what happens when it goes up"):
            if f.meaning:
                rows = "\n".join(
                    f"| ${m.symbol}$ | {m.meaning} | {m.unit} | {m.when_it_goes_up or ''} |" for m in f.meaning
                )
                st.markdown("| symbol | meaning | unit | when it goes up |\n|---|---|---|---|\n" + rows)
            if f.comes_from:
                st.markdown(f"**Where it comes from:** {f.comes_from}")
            if f.assumptions:
                st.markdown("**Assumptions:** " + "; ".join(f.assumptions))
            st.caption(v.badge)
