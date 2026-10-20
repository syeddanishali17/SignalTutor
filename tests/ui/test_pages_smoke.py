"""Headless UI smoke tests: every page and every lesson scene renders without exceptions.

Uses streamlit.testing (AppTest). Data goes to a temp dir so the learner DB is untouched.
"""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest



def _page(name: str) -> None:
    # AppTest serialises this function's source: imports must live inside it
    import importlib

    from tutor.ui import theme
    from tutor.ui.components import layout

    theme.inject()
    layout.reset_box_counter()
    importlib.import_module(f"tutor.ui.pages.{name}").render()


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("TUTOR_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("TUTOR_DEV", "1")
    # paths.py reads the env at import time; point the module at the temp dir too
    import tutor.paths as paths
    import tutor.ui.state as ui_state

    monkeypatch.setattr(paths, "DB_PATH", tmp_path / "tutor.db")
    monkeypatch.setattr(ui_state, "DB_PATH", tmp_path / "tutor.db")
    import streamlit as st

    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def _run(name: str, **query) -> AppTest:
    at = AppTest.from_function(_page, args=(name,), default_timeout=60)
    for k, v in query.items():
        at.query_params[k] = v
    at.run()
    assert not at.exception, [e.message for e in at.exception]
    return at


@pytest.mark.parametrize("name", ["home", "practice_page", "oral_page", "progress", "glossary", "sources", "dev_gallery"])
def test_page_renders(name):
    _run(name)


@pytest.mark.parametrize("scene", ["loop", "voltage_difference", "current_resistance", "divider", "ground", "junction",
                                   "read_circuit"])
def test_playground_scenes(scene):
    from tutor.models.loader import load_or_raise

    title = next(s.title for s in load_or_raise().lessons["foundation_playground"].scenes if s.id == scene)
    at = _run("playground", scene=scene, unlock="1")
    assert any(title in m.value for m in at.markdown), "deep-linked scene was not rendered"
    assert any("Equation strip" in m.value for m in at.markdown) or scene == "read_circuit"


@pytest.mark.parametrize("scene", ["sensor", "build", "quarter", "full", "temperature", "loading"])
def test_wheatstone_scenes(scene):
    from tutor.models.loader import load_or_raise

    title = next(s.title for s in load_or_raise().lessons["wheatstone_lab"].scenes if s.id == scene)
    at = _run("wheatstone", scene=scene, unlock="1", sel="left" if scene != "sensor" else "eps")
    assert any(title in m.value for m in at.markdown), "deep-linked scene was not rendered"
    assert len(at.latex) >= 3  # law, numbers, result


AMP_SEL = {"problem": "Vcm", "opamp": "diff", "feedback": "diff", "noninv": "gain", "diffamp": "Acm", "ina": "gain"}


@pytest.mark.parametrize("scene", list(AMP_SEL))
def test_amplifier_scenes(scene):
    from tutor.models.loader import load_or_raise

    title = next(s.title for s in load_or_raise().lessons["amplifier_lab"].scenes if s.id == scene)
    at = _run("amplifiers", scene=scene, unlock="1", sel=AMP_SEL[scene])
    assert any(title in m.value for m in at.markdown), "deep-linked scene was not rendered"
    assert len(at.latex) >= 3  # law, numbers, result


@pytest.mark.parametrize("scene,ctl,value", [("feedback", "fb", "positive"), ("noninv", "src", "test"),
                                             ("ina", "view", "common"), ("ina", "probe", "out"),
                                             ("diffamp", "mis", 1.0)])
def test_amplifier_variants(scene, ctl, value):
    """Alternative control states render too (positive feedback, pure common mode, …)."""
    at = AppTest.from_function(_page, args=("amplifiers",), default_timeout=60)
    at.query_params["scene"] = scene
    at.query_params["unlock"] = "1"
    at.session_state[f"w_amp_{scene}_{ctl}"] = value
    at.run()
    assert not at.exception, [e.message for e in at.exception]


CAP_SEL = {"membrane": "H", "capacitance": "gap", "cx": "u", "current": "VdC", "smallsignal": "u", "pullin": "Fe"}


@pytest.mark.parametrize("scene", list(CAP_SEL))
def test_capacitive_scenes(scene):
    from tutor.models.loader import load_or_raise

    title = next(s.title for s in load_or_raise().lessons["capacitive_lab"].scenes if s.id == scene)
    at = _run("capacitive", scene=scene, unlock="1", sel=CAP_SEL[scene])
    assert any(title in m.value for m in at.markdown), "deep-linked scene was not rendered"
    assert len(at.latex) >= 3


@pytest.mark.parametrize("scene,ctl,value", [("current", "mode", "microphone"), ("current", "dc", True),
                                             ("pullin", "V", 44.0), ("pullin", "mode", "feedback"),
                                             ("smallsignal", "a", 0.0), ("smallsignal", "a", 0.6),
                                             ("cx", "p", 9.0)])
def test_capacitive_variants(scene, ctl, value):
    at = AppTest.from_function(_page, args=("capacitive",), default_timeout=60)
    at.query_params["scene"] = scene
    at.query_params["unlock"] = "1"
    at.session_state[f"w_cap_{scene}_{ctl}"] = value
    at.run()
    assert not at.exception, [e.message for e in at.exception]


NOISE_SEL = {"noise": "op", "stats": "sigma", "spectrum": "A", "psd": "S", "band": "sigma2", "sides": "Spp"}


@pytest.mark.parametrize("scene", list(NOISE_SEL))
def test_noise_scenes(scene):
    from tutor.models.loader import load_or_raise

    title = next(s.title for s in load_or_raise().lessons["noise_lab"].scenes if s.id == scene)
    at = _run("noise", scene=scene, unlock="1", sel=NOISE_SEL[scene])
    assert any(title in m.value for m in at.markdown), "deep-linked scene was not rendered"
    assert len(at.latex) >= 3


@pytest.mark.parametrize("scene,ctl,value", [("noise", "mode", "multiplicative"), ("psd", "kind", "pink"),
                                             ("psd", "asd", True), ("band", "kind", "pink"), ("band", "f2", 10.0),
                                             ("sides", "kind", "pink"), ("spectrum", "level", 0.0),
                                             ("stats", "n", 10000)])
def test_noise_variants(scene, ctl, value):
    at = AppTest.from_function(_page, args=("noise",), default_timeout=60)
    at.query_params["scene"] = scene
    at.query_params["unlock"] = "1"
    at.query_params["sel"] = "p2" if scene == "spectrum" else ""
    at.session_state[f"w_nz_{scene}_{ctl}"] = value
    at.run()
    assert not at.exception, [e.message for e in at.exception]
