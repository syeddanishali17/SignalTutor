"""The shared flow cue gets larger without changing direction, speed or physics."""

import math
import xml.etree.ElementTree as ET

import pytest

from tutor.ui.svg.core import CURRENT, flow


@pytest.mark.parametrize("strength", [.05, .5, 1.])
@pytest.mark.parametrize("reverse", [False, True])
def test_flow_visibility_preserves_path_direction_and_timing(strength, reverse):
    points = [(30., 50.), (170., 50.)]
    if reverse:
        points.reverse()
    root = ET.fromstring("<svg>" + flow(points, strength, eid="current") + "</svg>")
    moving = root.find("polyline")
    assert moving.attrib["points"] == " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    assert moving.attrib["id"] == "current"
    assert moving.attrib["style"] == f"animation-duration:{0.55 / max(strength, .08):.2f}s"
    # Bound the visible enlargement, rather than freezing an implementation constant.
    original_width = 2.2 + 3 * strength
    assert 1.3 <= float(moving.attrib["stroke-width"]) / original_width <= 1.6
    arrow = root.find("polygon")
    assert arrow.attrib["fill"] == CURRENT
    vertices = [tuple(map(float, p.split(","))) for p in arrow.attrib["points"].split()]
    direction = -1 if reverse else 1
    enlargement = direction * (vertices[0][0] - 100) / (7 + 5 * strength)
    assert 1.3 <= enlargement <= 1.6
    assert all(30 < x < 170 and abs(y - 50) < 12 for x, y in vertices)
    assert direction * (vertices[0][0] - vertices[1][0]) > 0
    assert all(math.isfinite(v) for pair in vertices for v in pair)


@pytest.mark.parametrize("strength", [0., -1., 1e-7])
def test_zero_or_invisible_current_has_no_moving_or_direction_marker(strength):
    assert flow([(0., 0.), (100., 0.)], strength) == ""


def test_optional_arrows_and_path_offset_still_work():
    root = ET.fromstring("<svg>" + flow([(0., 0.), (100., 0.)], .5, arrows=False, offset=8.) + "</svg>")
    assert root.find("polygon") is None
    assert root.find("polyline").attrib["points"] == "0.0,8.0 100.0,8.0"
