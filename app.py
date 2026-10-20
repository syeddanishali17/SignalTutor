"""Signal Tutor — router (spec 13: st.Page + st.navigation).

    streamlit run app.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="Signal Tutor", page_icon="📐", layout="wide",
                   initial_sidebar_state="collapsed")

from tutor.ui import state, theme  # noqa: E402
from tutor.ui.components import layout  # noqa: E402
from tutor.ui.pages import (  # noqa: E402
    amplifiers,
    capacitive,
    dev_gallery,
    glossary,
    home,
    noise,
    oral_page,
    playground,
    practice_page,
    progress,
    sources,
    wheatstone,
)

st.session_state["_run_counter"] = st.session_state.get("_run_counter", 0) + 1
theme.inject()
layout.reset_box_counter()

try:
    state.bundle()
except Exception as exc:  # content errors must be visible, not a blank page
    st.error(f"Content failed to load — run `python scripts/validate_content.py`.\n\n{exc}")
    st.stop()

DEV = os.environ.get("TUTOR_DEV") == "1"
if DEV and st.query_params.get("mode") in state.MODE_LABELS:  # deterministic screenshots
    st.session_state["mode"] = st.query_params["mode"]

pages = {
    "": [st.Page(home.render, title="Today", icon=":material/today:", url_path="home", default=True)],
    "Learn": [
        st.Page(playground.render, title="Foundation Playground", icon=":material/science:", url_path="playground"),
        st.Page(wheatstone.render, title="Wheatstone Bridge Lab", icon=":material/electric_meter:", url_path="wheatstone"),
        st.Page(amplifiers.render, title="Amplifier Lab", icon=":material/settings_input_component:",
                url_path="amplifiers"),
        st.Page(capacitive.render, title="Capacitive Sensor Lab", icon=":material/compress:",
                url_path="capacitive"),
        st.Page(noise.render, title="Noise Lab", icon=":material/graphic_eq:", url_path="noise"),
    ],
    "Practice": [
        st.Page(practice_page.render, title="Problems & review", icon=":material/calculate:", url_path="practice"),
        st.Page(oral_page.render, title="Oral & whiteboard", icon=":material/record_voice_over:", url_path="oral"),
    ],
    "Reference": [
        st.Page(progress.render, title="Progress", icon=":material/insights:", url_path="progress"),
        st.Page(glossary.render, title="Glossary & concept map", icon=":material/menu_book:", url_path="glossary"),
        st.Page(sources.render, title="Sources & known issues", icon=":material/fact_check:", url_path="sources"),
        st.Page(dev_gallery.render, title="Dev gallery", icon=":material/widgets:", url_path="dev_gallery",
                visibility="visible" if DEV else "hidden"),
    ],
}

st.session_state["_pages"] = {p.url_path: p for group in pages.values() for p in group}
st.navigation(pages, position="top").run()
layout.footer()  # after the page body: never overlaps the teaching area
