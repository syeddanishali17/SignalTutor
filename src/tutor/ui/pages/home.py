"""Today: exam countdown, today's review, the learning path with honest mastery states."""

from __future__ import annotations

from datetime import date

import streamlit as st

from tutor.engine.mastery import SKILLS, is_mastered
from tutor.ui import state
from tutor.ui.components import layout

EXAM_DATES = (date(2027, 1, 29), date(2027, 2, 12))
FREEZE = date(2027, 1, 5)

# the learning path: (concept, page, scene)
PATH = [
    ("charge_current", "playground", "loop"),
    ("voltage", "playground", "voltage_difference"),
    ("ohms_law", "playground", "current_resistance"),
    ("voltage_divider", "playground", "divider"),
    ("ground_reference", "playground", "ground"),
    ("kcl", "playground", "junction"),
    ("gauge_factor", "wheatstone", "sensor"),
    ("wheatstone_bridge", "wheatstone", "build"),
    ("wheatstone_quarter", "wheatstone", "quarter"),
    ("wheatstone_full", "wheatstone", "full"),
    ("temperature_compensation", "wheatstone", "temperature"),
    ("bridge_loading", "wheatstone", "loading"),
]
AMP_PATH = [
    ("interference", "amplifiers", "problem"),
    ("op_amp", "amplifiers", "opamp"),
    ("negative_feedback", "amplifiers", "feedback"),
    ("non_inverting_amp", "amplifiers", "noninv"),
    ("difference_amp", "amplifiers", "diffamp"),
    ("instrumentation_amp", "amplifiers", "ina"),
]
CAP_PATH = [
    ("spring_hooke", "capacitive", "membrane"),
    ("capacitance", "capacitive", "capacitance"),
    ("capacitive_sensor", "capacitive", "cx"),
    ("capacitor_current", "capacitive", "current"),
    ("harmonic_distortion", "capacitive", "smallsignal"),
    ("pull_in", "capacitive", "pullin"),
]
NOISE_PATH = [
    ("noise_types", "noise", "noise"),
    ("variance_rms", "noise", "stats"),
    ("spectrum", "noise", "spectrum"),
    ("psd", "noise", "psd"),
    ("band_noise", "noise", "band"),
    ("psd_sides", "noise", "sides"),
]


SCENE_KEY = {"playground": "pg_scene", "wheatstone": "wb_scene", "amplifiers": "amp_scene",
             "capacitive": "cap_scene", "noise": "noise_scene"}


def render() -> None:
    today = date.today()
    layout.page_header("Modern Sensor Technologies", "Today",
                       "Oral exam: about 20 minutes at the whiteboard, two topics. Practise explaining, drawing and deriving.")
    bundle = state.bundle()
    svc = state.service()
    mastery = state.mastery_cached()

    c1, c2, c3 = st.columns(3)
    first = EXAM_DATES[0]
    c1.metric("Days to the first exam date", (first - today).days, help="29.01.2027 — second date 12.02.2027.")
    c2.metric("Days to feature freeze", max(0, (FREEZE - today).days), help="From 5 Jan 2027: practice only, no new features.")
    items, minutes = svc.due_summary(today)
    c3.metric("Today's review", f"{len(items)} items", help=f"About {minutes} minutes.")

    st.markdown("### Today's review")
    if not items:
        st.markdown("Nothing due. Material enters the queue the first time you answer a problem, an oral question "
                    "or a whiteboard prompt — and comes back after 1, 3, 7, 14 and 30 days.")
    else:
        lines = [f"- **{it.item_type}** · {_item_title(it.item_type, it.item_id)} *(box {it.box})*" for it in items[:8]]
        st.markdown("\n".join(lines) + (f"\n- … and {len(items) - 8} more" if len(items) > 8 else ""))
        if st.button(f"Start review · about {minutes} min", type="primary", icon=":material/play_arrow:"):
            st.session_state["practice_tab"] = "Today's review"
            st.session_state.pop("review_snapshot", None)
            st.switch_page(_page("practice"))

    mastered = {k for k, v in mastery.items() if is_mastered(v)}
    for title, path in (("Path 1 — from 'what is current?' to the Wheatstone bridge", PATH),
                        ("Path 2 — amplifiers: from the op-amp to the instrumentation amplifier", AMP_PATH),
                        ("Path 3 — the capacitive sensor: from a membrane to pull-in", CAP_PATH),
                        ("Path 4 — noise: from random wiggles to the PSD and the factor 2", NOISE_PATH)):
        st.markdown(f"### {title}")
        st.caption("States follow fixed rules (see Progress), not percentages. Weak prerequisites are named.")
        for i, (cid, page, scene) in enumerate(path, 1):
            if cid not in bundle.concepts:
                continue
            c = bundle.concepts[cid]
            states = mastery.get(cid, {s: "not_started" for s in SKILLS})
            left, right = st.columns([6, 1.2], vertical_alignment="center")
            with left:
                st.markdown(f"**{i}. {c.title}** — {c.one_liner}")
                badges = " ".join(layout.badge_html(states[s], s) for s in SKILLS)
                missing = state.graph().unmastered_prerequisites(cid, mastered)
                extra = (f" <span class='mst-muted'>· needs first: "
                         f"{', '.join(bundle.concepts[m].short or bundle.concepts[m].title for m in missing)}</span>"
                         if missing else "")
                st.markdown(badges + extra, unsafe_allow_html=True)
            with right:
                if st.button("Open", key=f"open_{cid}", use_container_width=True):
                    st.session_state[SCENE_KEY[page]] = scene
                    st.switch_page(_page(page))

    st.markdown("### How to use this")
    st.markdown(
        "1. **Learn** a scene: predict first, then move the controls and watch the picture.  \n"
        "2. Click any **part** or **symbol** — the part, its control and its symbol light up together.  \n"
        "3. **Check** with auto-graded problems — wrong answers name the likely misconception.  \n"
        "4. **Explain it** out loud, tick what you covered, answer the examiner's follow-up.  \n"
        "5. **Whiteboard**: draw and derive on paper, then compare with the reference.  \n"
        "6. Come back for **Today's review**."
    )
    with st.expander("About this tutor"):
        st.markdown(
            "A personal, visual study tool for the oral exam in Modern Sensor Technologies. Lecture-derived material "
            "is marked with its source; anything added beyond the lecture is labelled *supplemental*; doubtful "
            "lecture formulas are flagged *needs review* instead of being silently corrected (see Sources)."
        )
        layout.signature_inline()


def _item_title(item_type: str, item_id: str) -> str:
    b = state.bundle()
    if item_type == "concept" and item_id in b.concepts:
        return b.concepts[item_id].title
    if item_type == "problem" and item_id in b.problems:
        return b.concepts[b.problems[item_id].concept].title + " (problem)"
    if item_type == "oral" and item_id in b.oral:
        return b.oral[item_id].question
    if item_type == "whiteboard" and item_id in b.whiteboard:
        return b.whiteboard[item_id].prompt
    if item_type == "derivation" and item_id in b.derivations:
        return b.derivations[item_id].title
    return item_id


def _page(name: str):
    return st.session_state["_pages"][name]
