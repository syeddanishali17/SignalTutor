"""Selection, linking and the concept inspector (spec 16.5 / 16.6).

One selection per scene. It can be

* a **part** of the picture (``InspectItem``: R₁, a node, the meter …), or
* a **term** of the equation (``Term``: R₁ + R₄, ΔR/R …).

``resolve`` turns the selection into what lights up everywhere:
the SVG ids to highlight, the controls to outline and the equation terms to box.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import streamlit as st

from tutor.engine.mastery import is_mastered
from tutor.models.content import Concept, InspectItem, Scene, Term
from tutor.ui import state
from tutor.ui.components import prose


# --------------------------------------------------------------------------- selection state


def sel_key(scope: str) -> str:
    return f"sel__{scope}"


def _pills_key(scope: str) -> str:
    return f"pills__{scope}"


def selected(scope: str) -> str | None:
    return st.session_state.get(sel_key(scope))


def select(scope: str, item_id: str | None) -> None:
    """Callback-safe setter (use from on_click of buttons)."""
    st.session_state[sel_key(scope)] = item_id
    st.session_state.pop(_pills_key(scope), None)


def _from_pills(scope: str) -> None:
    st.session_state[sel_key(scope)] = st.session_state.get(_pills_key(scope))


@dataclass
class Resolved:
    highlight: set[str] = field(default_factory=set)
    controls: list[str] = field(default_factory=list)
    boxed: set[str] = field(default_factory=set)
    item: InspectItem | None = None
    term: Term | None = None


def resolve(scene: Scene, sel: str | None) -> Resolved:
    if not sel:
        return Resolved()
    item = next((i for i in scene.inspect if i.id == sel), None)
    if item is not None:
        hl = set(item.highlight or [item.id])
        boxed = {t.id for t in scene.terms if t.id == item.id or t.highlight == [item.id]}
        return Resolved(hl, list(item.controls), boxed, item=item)
    term = next((t for t in scene.terms if t.id == sel), None)
    if term is not None:
        return Resolved(set(term.highlight), list(term.controls), {term.id}, term=term)
    return Resolved()


def term_latex(scene: Scene, term_id: str) -> str:
    """Plain LaTeX of a term (nested [[tokens]] expanded, no boxes)."""
    bundle = state.bundle()
    terms = {t.id: t for t in scene.terms}
    t = terms[term_id]
    tex = t.latex or bundle.symbols[t.symbol].latex
    return re.sub(r"\[\[(\w+)\]\]", lambda m: term_latex(scene, m.group(1)), tex)


# --------------------------------------------------------------------------- panel


def inspector_panel(scope: str, scene: Scene, intro: str | None = None) -> Resolved:
    """Part selector + details card. Returns the resolved selection."""
    with st.container(key="inspector"):
        st.markdown('<p class="mst-kicker">Inspector — click a part or a symbol</p>', unsafe_allow_html=True)
        items = scene.inspect
        cur = selected(scope)
        if items:
            ids = [i.id for i in items]
            if cur in ids:
                st.session_state[_pills_key(scope)] = cur
            else:
                st.session_state.pop(_pills_key(scope), None)
            labels = {i.id: i.label for i in items}
            st.pills("Parts of the picture", ids, format_func=lambda i: labels[i], key=_pills_key(scope),
                     selection_mode="single", on_change=_from_pills, args=(scope,))
        res = resolve(scene, selected(scope))
        if res.item is not None:
            _part_card(res.item)
        elif res.term is not None:
            _term_card(scene, res.term)
        else:
            st.markdown(intro or "Pick a **part** above, or a **symbol** in the equation strip below. "
                        "The part, its control and its symbol light up together.")
            if state.mode() == "beginner" and scene.terms:
                st.caption("Tip: the symbols under the equation are clickable too.")
    return res


def _part_card(item: InspectItem) -> None:
    c = state.bundle().concepts[item.concept]
    st.markdown(f"#### {item.label}")
    st.markdown("**In this picture:**")
    prose.show(item.role)
    concept_card(c, compact=True)


def _term_card(scene: Scene, term: Term) -> None:
    bundle = state.bundle()
    sym = bundle.symbols[term.symbol]
    st.latex(term_latex(scene, term.id))
    prose.show(sym.meaning)
    if sym.unit:
        st.markdown(f'<p class="mst-muted">Unit: <b>{sym.unit}</b></p>', unsafe_allow_html=True)
    if sym.concept and sym.concept in bundle.concepts:
        with st.expander(f"About: {bundle.concepts[sym.concept].title}"):
            concept_card(bundle.concepts[sym.concept], compact=True)


def concept_card(c: Concept, compact: bool = False) -> None:
    """Plain words → definition → picture → unit → watch out → builds on."""
    mode = state.mode()
    if not compact:
        st.markdown(f"#### {c.title}")
    if c.plain_words and mode != "exam":
        st.markdown(f'<div class="mst-plain">In plain words: <b>{c.plain_words}</b></div>', unsafe_allow_html=True)
    st.markdown("**What it is.**")
    prose.show(c.one_liner)
    if c.analogy and mode == "beginner":
        st.markdown(f"**Picture it** *(analogy — not the physics)*: {c.analogy.text} "
                    f"*Where it breaks:* {c.analogy.breaks_when}")
    if c.units:
        st.markdown(f"**Unit:** {c.units}")
    if c.misconceptions and mode != "exam":
        m = c.misconceptions[0]
        st.markdown(f"**Watch out.** A common mistake: *“{m.text}”*")
        prose.show(m.correction)
    missing = unmastered_prereqs(c.id)
    if missing:
        names = ", ".join(state.bundle().concepts[p].short or state.bundle().concepts[p].title for p in missing)
        st.caption(f"Builds on (not yet solid for you): {names} — see the Glossary.")


def unmastered_prereqs(cid: str) -> list[str]:
    m = state.mastery_cached()
    mastered = {k for k, v in m.items() if is_mastered(v)}  # type: ignore[arg-type]
    return state.graph().unmastered_prerequisites(cid, mastered)


def term_chips(concept_ids: list[str], label: str = "New words here") -> None:
    """Click-to-open glossary popovers (never hover-only)."""
    bundle = state.bundle()
    if state.mode() == "exam":
        return
    with st.container(horizontal=True, gap="small", key="termchips"):
        st.markdown(f'<span class="mst-muted" style="padding-top:6px;display:inline-block">{label}:</span>',
                    unsafe_allow_html=True)
        for cid in concept_ids:
            c = bundle.concepts.get(cid)
            if c is None:
                continue
            with st.popover(c.short or c.title, type="tertiary"):
                concept_card(c)
                if c.explanation:
                    with st.expander("Full explanation"):
                        prose.show(c.explanation)
