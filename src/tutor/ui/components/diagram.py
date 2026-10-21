"""Shared diagram display; motion never carries information by itself."""

from __future__ import annotations

import streamlit as st

from tutor.ui.svg.core import as_img


def motion_svg(svg: str, enabled: bool) -> str:
    if enabled:
        return svg
    return svg.replace("</svg>", '<style>.mst * { animation: none !important; }</style></svg>')


def show(svg: str, *, animate: bool = True, max_width: int | None = None) -> None:
    st.html(as_img(motion_svg(svg, animate), max_width=max_width))
