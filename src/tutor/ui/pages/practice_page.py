"""Problems & review: today's Leitner queue (spec 8.6) and all problems by topic (spec 8.1)."""

from __future__ import annotations

import html
import random

import streamlit as st

from tutor.ui import state
from tutor.ui.components import layout
from tutor.ui.components.oral import oral_dock, whiteboard_drill
from tutor.ui.components.practice import problem_card

TABS = ["Today's review", "By topic"]


def render() -> None:
    layout.page_header("Practice", "Problems & review",
                       "Auto-graded with units. Only your first attempt on each instance counts towards mastery.")
    st.session_state.setdefault("practice_tab", TABS[0])
    tab = st.segmented_control("View", TABS, key="practice_tab", required=True)
    if tab == TABS[0]:
        _review()
    else:
        _by_topic()


def _review() -> None:
    svc = state.service()
    bundle = state.bundle()
    if "review_snapshot" not in st.session_state:
        st.session_state["review_snapshot"] = [(i.item_type, i.item_id) for i in svc.due()]
        st.session_state["review_pos"] = 0
    items = st.session_state["review_snapshot"]
    pos = st.session_state.get("review_pos", 0)
    if not items:
        st.markdown('<p class="mst-muted">Nothing due today. Work through a lesson or the topic list; '
                    'everything you answer enters the spaced review queue.</p>', unsafe_allow_html=True)
        if st.button("Check again"):
            st.session_state.pop("review_snapshot", None)
            st.rerun()
        return
    if pos >= len(items):
        st.success(f"Review done — {len(items)} items. See you tomorrow.", icon=":material/celebration:")
        if st.button("Reload the queue"):
            st.session_state.pop("review_snapshot", None)
            st.rerun()
        return
    st.progress(pos / len(items), text=f"Item {pos + 1} of {len(items)}")
    item_type, item_id = items[pos]
    scope = f"rev{pos}"
    if item_type == "problem" and item_id in bundle.problems:
        problem_card(bundle.problems[item_id], scope=scope)
    elif item_type == "oral" and item_id in bundle.oral:
        oral_dock(bundle.oral[item_id], scope=scope)
    elif item_type == "whiteboard" and item_id in bundle.whiteboard:
        whiteboard_drill(bundle.whiteboard[item_id], scope=scope)
    elif item_type == "concept" and item_id in bundle.concepts:
        _concept_item(item_id, scope)
    elif item_type == "derivation" and item_id in bundle.derivations:
        d = bundle.derivations[item_id]
        st.markdown(f"**Derivation:** {html.escape(d.title)} — derive it on paper, then use the lab's *Derive* tab "
                    "in Faded style to check yourself.")
    else:
        # e.g. an explain-aloud checklist from a lesson scene
        lesson_id, _, scene_id = item_id.partition("/")
        lesson = bundle.lessons.get(lesson_id)
        scene = next((s for s in lesson.scenes if s.id == scene_id), None) if lesson else None
        if scene:
            st.markdown('<p class="mst-kicker">Explain aloud</p>', unsafe_allow_html=True)
            with st.container(key=f"box-note-ex-{scope}"):
                st.markdown(f"**{scene.explain.prompt}**")
            with st.expander("Points to cover"):
                for p in scene.explain.points:
                    st.markdown(f"- {p}")
            _self_check(scope, lambda ok: svc.review_concept(scene.concepts[0], ok))
        else:
            st.caption(f"Unknown review item {item_type}/{item_id} — skipping.")
    st.button("Next item ▶", type="secondary", on_click=_next, key=f"next_{pos}")


def _next() -> None:
    st.session_state["review_pos"] = st.session_state.get("review_pos", 0) + 1


def _concept_item(cid: str, scope: str) -> None:
    """Concept due for review: an auto-graded problem if one exists, else self-checked recall."""
    bundle = state.bundle()
    pids = [p.id for p in bundle.problems.values() if p.concept == cid]
    c = bundle.concepts[cid]
    if pids:
        key = f"{scope}__pick"
        st.session_state.setdefault(key, random.choice(pids))
        st.caption(f"Concept review: {c.title}")
        problem_card(bundle.problems[st.session_state[key]], scope=scope)
        return
    st.markdown(f'<p class="mst-kicker">Recall · {html.escape(c.title)}</p>', unsafe_allow_html=True)
    with st.container(key=f"box-note-rc-{scope}"):
        st.markdown(f"**In one or two sentences: what is “{c.title}” and why does it matter here?**")
    if st.toggle("Reveal", key=f"{scope}__rev"):
        st.markdown(c.one_liner)
        if c.explanation:
            with st.expander("Full explanation"):
                st.markdown(c.explanation)
        _self_check(scope, lambda ok: state.service().review_concept(cid, ok))


def _self_check(scope: str, record) -> None:
    done = st.session_state.get(f"{scope}__done")
    if done is not None:
        st.caption("Recorded." if done else "Recorded — it comes back tomorrow.")
        return
    c1, c2 = st.columns(2)
    if c1.button("I had it", key=f"{scope}__ok", use_container_width=True):
        record(True)
        st.session_state[f"{scope}__done"] = True
        st.rerun()
    if c2.button("Not yet", key=f"{scope}__no", use_container_width=True):
        record(False)
        st.session_state[f"{scope}__done"] = False
        st.rerun()


def _by_topic() -> None:
    bundle = state.bundle()
    order = state.graph().topological_order({p.concept for p in bundle.problems.values()})
    cid = st.selectbox("Topic", order, format_func=lambda c: bundle.concepts[c].title, key="topic_pick")
    st.markdown(bundle.concepts[cid].one_liner)
    for p in sorted((p for p in bundle.problems.values() if p.concept == cid), key=lambda p: p.level):
        problem_card(p, scope="topic")
