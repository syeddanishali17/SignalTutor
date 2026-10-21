"""Control tray primitives (spec 16.6 control_tray): symbol, value, unit, meaning, reset.

Each control lives in a keyed container ``ctl_<scope>_<id>`` so the selection
can outline it (tutor.ui.theme.highlight_controls).
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def ctl_key(scope: str, cid: str) -> str:
    return f"ctl_{scope}_{cid}"


def wkey(scope: str, cid: str) -> str:
    return f"w_{scope}_{cid}"


def ensure_defaults(scope: str, defaults: dict[str, Any]) -> None:
    saved = st.session_state.setdefault("_circuit_values", {})
    for cid, v in defaults.items():
        # Widget keys disappear when a scene is hidden; keep a session-owned copy.
        key = wkey(scope, cid)
        st.session_state[key] = st.session_state.get(key, saved.get(key, v))
        saved[key] = st.session_state[key]


def _remember(scope: str, cid: str) -> None:
    key = wkey(scope, cid)
    st.session_state.setdefault("_circuit_values", {})[key] = st.session_state[key]


def reset(scope: str, defaults: dict[str, Any], extra: dict[str, Any] | None = None) -> None:
    """Return the whole interaction to one canonical state (spec 16.15 #8)."""
    for cid, v in defaults.items():
        st.session_state[wkey(scope, cid)] = v
        _remember(scope, cid)
    for k, v in (extra or {}).items():
        st.session_state[k] = v


def slider(scope: str, cid: str, label: str, lo: float, hi: float, step: float, fmt: str,
           help: str | None = None, disabled: bool = False) -> float:
    with st.container(key=ctl_key(scope, cid)):
        return st.slider(label, min_value=lo, max_value=hi, step=step, format=fmt, value=value(scope, cid),
                         key=wkey(scope, cid), help=help, disabled=disabled,
                         on_change=_remember, args=(scope, cid))


def select_slider(scope: str, cid: str, label: str, options: list, fmt=str, help: str | None = None,
                  disabled: bool = False):
    with st.container(key=ctl_key(scope, cid)):
        return st.select_slider(label, options=options, value=value(scope, cid), format_func=fmt, key=wkey(scope, cid), help=help,
                                disabled=disabled, on_change=_remember, args=(scope, cid))


def toggle(scope: str, cid: str, label: str, help: str | None = None, disabled: bool = False) -> bool:
    with st.container(key=ctl_key(scope, cid)):
        return st.toggle(label, value=value(scope, cid), key=wkey(scope, cid), help=help, disabled=disabled,
                         on_change=_remember, args=(scope, cid))


def segmented(scope: str, cid: str, label: str, options: list, fmt=str, help: str | None = None,
              disabled: bool = False):
    with st.container(key=ctl_key(scope, cid)):
        val = st.segmented_control(label, options, default=value(scope, cid), format_func=fmt, key=wkey(scope, cid), help=help,
                                   disabled=disabled, required=True, on_change=_remember, args=(scope, cid))
    return val


def reset_button(scope: str, defaults: dict[str, Any], extra: dict[str, Any] | None = None,
                 label: str = "Reset") -> None:
    st.button(label, key=f"reset_{scope}", icon=":material/restart_alt:", on_click=reset, args=(scope, defaults, extra),
              help="Return every control in this scene to its starting value.")


def value(scope: str, cid: str) -> Any:
    return st.session_state.get(wkey(scope, cid))
