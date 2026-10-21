"""Handbook smoke, math convention and independent diagram checks."""

import xml.etree.ElementTree as ET

import pytest
from streamlit.testing.v1 import AppTest

from tutor.ui.components.diagram import motion_svg
from tutor.ui.pages.circuit_reference import SECTIONS
from tutor.ui.svg.reference_figures import figure

FIGURES = sorted({e.figure for s in SECTIONS for e in s.entries if e.figure and e.figure != "chain"})


def test_reference_entries_have_equation_sequences_and_unique_anchors():
    assert len({s.anchor for s in SECTIONS}) == len(SECTIONS)
    for section in SECTIONS:
        for entry in section.entries:
            assert isinstance(entry.equations, tuple), entry.title
            assert all(isinstance(eq, str) and len(eq) > 2 for eq in entry.equations)


@pytest.mark.parametrize("name", FIGURES)
def test_handbook_figures_are_accessible_scalable_svg(name):
    svg = figure(name)
    root = ET.fromstring(svg)
    ns = {"s": "http://www.w3.org/2000/svg"}
    assert root.attrib["viewBox"].startswith("0 0 ")
    assert root.find("s:title", ns).text
    assert root.find("s:desc", ns).text
    assert "nan" not in svg.lower() and "infinity" not in svg.lower()
    assert "prefers-reduced-motion" in svg
    assert "animation: none !important" in motion_svg(svg, False)


def _handbook():
    from tutor.ui.pages.circuit_fundamentals import render
    render()


def test_handbook_loads_without_database_or_private_schedule(monkeypatch):
    from tutor.ui import state

    def forbidden(*args, **kwargs):
        raise AssertionError("The handbook must not access learner state")

    monkeypatch.setattr(state, "repo", forbidden)
    monkeypatch.setattr(state, "service", forbidden)
    monkeypatch.setattr(state, "mode", forbidden)
    at = AppTest.from_function(_handbook, default_timeout=60).run()
    assert not at.exception
    assert len(at.header) == len(SECTIONS) + 1
    copy = "\n".join(m.value for m in at.markdown)
    assert "#formula-summary" in copy and "#dividers" in copy
    assert "K9 remains open" in copy and "K4 and K5 remain open" in copy
    math = [m.value for m in at.latex]
    for representative in (r"V_{AB}=V_A-V_B", r"\tau=RC", r"\mathrm{ASD}(f)=\sqrt{S_x(f)}"):
        assert any(representative in rendered for rendered in math)
    assert not at.slider and not at.radio and not at.selectbox and not at.toggle
    # Formula Summary repeats section names; its headings must not create duplicate jump IDs.
    from tutor.ui.pages.circuit_reference import SUMMARY
    assert [heading.proto.anchor for heading in list(at.subheader)[-len(SUMMARY):]] == [
        f"summary-{i}" for i in range(len(SUMMARY))
    ]
    anchors = [heading.proto.anchor for heading in list(at.header) + list(at.subheader) if heading.proto.anchor]
    assert len(anchors) == len(set(anchors))


def test_bridge_and_ina_reference_follow_simulator_conventions():
    from tutor.sim import amplifiers, bridge

    r = bridge.solve(5., bridge.Arms(2000., 1000., 3000., 4000.))
    assert r.Vout == pytest.approx(5 * (4000 / 6000 - 3000 / 4000))
    assert bridge.quarter_exact(5., .001) == pytest.approx(5 * (1 / 2.001 - .5))
    assert bridge.full_output(5., .001) == pytest.approx(-.005)
    assert amplifiers.noninv_gain_ideal(10000, 1000) == pytest.approx(11)
