"""Glossary and concept map (spec 5): every term, its prerequisites and the path to it."""

from __future__ import annotations

import streamlit as st

from tutor.engine.mastery import SKILLS, is_mastered
from tutor.ui import state
from tutor.ui.components import layout
from tutor.ui.components.equation import formula_card
from tutor.ui.components.inspector import concept_card
from tutor.ui.svg.concept_map import concept_map
from tutor.ui.svg.core import as_img

TRACK_NAME = {"math": "Math toolkit", "physics": "Physics toolkit", "electrical": "Electrical foundations",
              "course_l01": "Lecture 1", "course_l02": "Lecture 2", "course_l03": "Lecture 3"}
ORDER = ["not_started", "shaky", "solid", "exam_ready"]


def render() -> None:
    layout.page_header("Reference", "Glossary & concept map",
                       "Every term is one click away, together with what it builds on. Nothing hides behind hover.")
    bundle = state.bundle()
    g = state.graph()
    mastery = state.mastery_cached()
    order = g.topological_order()

    c1, c2 = st.columns([2, 3])
    with c1:
        q = st.text_input("Search", placeholder="e.g. common mode, gauge factor, ground", key="gloss_q").strip().lower()
    hits = [c for c in order if not q or q in bundle.concepts[c].title.lower() or q in bundle.concepts[c].one_liner.lower()
            or q in (bundle.concepts[c].short or "").lower()]
    if not hits:
        st.info("No match.")
        return
    st.session_state.setdefault("gloss_sel", "wheatstone_bridge")
    if st.session_state["gloss_sel"] not in hits:
        st.session_state["gloss_sel"] = hits[0]
    with c2:
        cid = st.selectbox("Concept", hits, key="gloss_sel",
                           format_func=lambda c: f"{bundle.concepts[c].title}  ·  {TRACK_NAME[bundle.concepts[c].track]}")
    c = bundle.concepts[cid]

    states = {k: max(v.values(), key=ORDER.index) for k, v in mastery.items()}
    with st.container(key="visual"):
        h1, h2 = st.columns([4, 1.4], vertical_alignment="center")
        with h1:
            layout.kicker("Concept map — foundations at the top; the selected concept and its path are dark")
        with h2:
            full = st.toggle("Show the whole map", key="gloss_full")
        st.html(as_img(concept_map(g, cid, states, full=full), max_width=1150))

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"## {c.title}")
        concept_card(c, compact=True)
        if c.explanation:
            st.divider()
            st.markdown(c.explanation)
        for m in c.misconceptions[1:]:
            st.markdown(f"**Another common mistake:** *“{m.text}”* — {m.correction}")
        fs = [f for f in bundle.formulas.values() if f.concept == cid]
        if fs:
            layout.kicker("Formulas")
            for f in fs:
                formula_card(f)
    with right:
        with st.container(key="inspector"):
            layout.kicker("Your status")
            sk = mastery.get(cid, {s: "not_started" for s in SKILLS})
            st.markdown(" ".join(layout.badge_html(sk[s], s) for s in SKILLS), unsafe_allow_html=True)
            st.caption(f"Content status: {c.status} · source: {', '.join(c.source_refs) or '—'}")
            mastered = {k for k, v in mastery.items() if is_mastered(v)}
            layout.kicker("Builds on")
            if c.prerequisites:
                for p in c.prerequisites:
                    mark = "✓" if p in mastered else "○"
                    st.button(f"{mark} {bundle.concepts[p].title}", key=f"pre_{p}", on_click=_go, args=(p,),
                              type="tertiary")
            else:
                st.caption("Nothing — a starting point.")
            deps = g.dependents.get(cid, [])
            if deps:
                layout.kicker("Needed by")
                for d in deps:
                    st.button(bundle.concepts[d].title, key=f"dep_{d}", on_click=_go, args=(d,), type="tertiary")
            layout.kicker("Path to here (a good learning order)")
            path = g.path_to(cid)
            st.markdown("\n".join(f"{i}. {'✓ ' if p in mastered else ''}{bundle.concepts[p].title}"
                                  for i, p in enumerate(path, 1)))


def _go(cid: str) -> None:
    st.session_state["gloss_q"] = ""
    st.session_state["gloss_sel"] = cid
