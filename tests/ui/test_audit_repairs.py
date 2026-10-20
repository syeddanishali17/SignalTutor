"""Regression coverage for the concrete live-audit failures."""

import pytest
from streamlit.testing.v1 import AppTest

from tutor.sim import bridge
from tutor.ui.svg import figures


@pytest.mark.parametrize("mode", ["balanced", "quarter", "full"])
@pytest.mark.parametrize("layout", ["diamond", "dividers"])
@pytest.mark.parametrize("currents", [True, False])
def test_zero_supply_bridge_draws_without_flow(mode, layout, currents):
    result = bridge.simulate(mode, 0, 350, .001)
    svg = figures.bridge(result, mode, layout=layout, show_currents=currents)
    assert result.I1 == result.I2 == result.Vout == 0
    assert 'class="flow"' not in svg
    assert ">balanced</text>" in svg if mode == "balanced" else ">balanced</text>" not in svg


def _mock_noise():
    from tutor.ui import state
    from tutor.ui.components.oral import _mock_revealed
    b = state.bundle()
    _mock_revealed(b, b.oral["noise_psd_q"], "test_noise", last=True)


def test_mock_renders_all_explanation_bodies(monkeypatch):
    monkeypatch.setenv("TUTOR_STORAGE_MODE", "session")
    at = AppTest.from_function(_mock_noise, default_timeout=60).run()
    assert not at.exception
    copy = "\n".join(m.value for m in at.markdown)
    for phrase in ("Any random fluctuation", "Random means unpredictable", "The **power spectral density**",
                   "White:", "A measurement that only looks", "Watch the notation:", "Choosing the measurement bandwidth"):
        assert phrase in copy


def _conditional():
    import streamlit as st
    from tutor.ui.components import controls as C
    C.ensure_defaults("conditional", {"view": "first", "bias": 10., "amplitude": .1})
    C.segmented("conditional", "view", "View", ["first", "second"])
    if C.value("conditional", "view") == "second":
        C.slider("conditional", "bias", "Bias", 0., 20., 1., "%.0f V")
        C.slider("conditional", "amplitude", "Amplitude", 0., .4, .02, "%.2f")
    st.write(C.value("conditional", "bias"), C.value("conditional", "amplitude"))


def test_conditional_control_defaults_and_edits_survive_hidden_rerun():
    at = AppTest.from_function(_conditional).run()
    at.session_state["w_conditional_view"] = "second"
    at.run()
    assert at.slider[0].value == 10.
    assert at.slider[1].value == .1
    at.slider[0].set_value(7.).run()
    at.session_state["w_conditional_view"] = "first"
    at.run()
    at.session_state["w_conditional_view"] = "second"
    at.run()
    assert at.slider[0].value == 7.
    assert not at.exception


def _mode_page():
    import streamlit as st
    from tutor.ui.components.layout import mode_switch
    mode_switch()
    st.selectbox("Scene", ["Sensor", "Quarter"], key="test_scene")
    st.selectbox("Task", ["Why?", "Derive"], key="test_task")
    st.slider("Supply", 0., 10., value=5., key="test_supply")


def test_mode_callback_keeps_downstream_widgets(monkeypatch):
    monkeypatch.setenv("TUTOR_STORAGE_MODE", "session")
    at = AppTest.from_function(_mode_page).run()
    at.selectbox[0].set_value("Quarter")
    at.selectbox[1].set_value("Derive")
    at.slider[0].set_value(3.)
    at.run()
    for mode in ("course", "exam", "beginner"):
        at.get("button_group")[0].set_value(mode).run()
        assert at.selectbox[0].value == "Quarter"
        assert at.selectbox[1].value == "Derive"
        assert at.slider[0].value == 3.
        assert at.session_state["mode"] == mode
        assert not at.exception
