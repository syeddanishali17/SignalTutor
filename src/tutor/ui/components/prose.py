"""Render learner prose so an equation is not glued to the sentence after it.

A paragraph that is only an equation, or that opens with a full equation and
then an explanation, is drawn as display mathematics followed by the prose.
"""

from __future__ import annotations

import re

import streamlit as st

from tutor.engine.typography import inline_spans

_IMPORTANT = re.compile(r"frac|\\int|\\sum|\\sqrt|=")


def blocks(text: str) -> list[tuple[str, str]]:
    """``('math', latex)`` or ``('md', markdown)`` pieces, in order."""
    out: list[tuple[str, str]] = []
    for para in re.split(r"\n\s*\n", text.strip()):
        if not para.strip():
            continue
        spans = inline_spans(para)
        if spans:
            start, end = spans[0]
            body = para[start + 1: end]
            before = para[:start].strip()
            after = para[end + 1:].lstrip()
            if not before and _IMPORTANT.search(body) and (not after or after[0] in ".!?"):
                if after[:1] in ".!?":
                    after = after[1:].lstrip()
                out.append(("math", body))
                if after:
                    out.append(("md", after))
                continue
        out.append(("md", para.strip()))
    return out


def show(text: str) -> None:
    """Markdown, with a leading full equation lifted onto its own line."""
    for kind, payload in blocks(text):
        if kind == "math":
            st.latex(payload)
        else:
            st.markdown(payload)
