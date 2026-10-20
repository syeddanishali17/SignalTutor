"""The tablet rules stay in the shared theme, not in a one-off page."""

from tutor.ui.svg.core import Canvas, as_img
from tutor.ui.theme import CSS


def test_tablet_breakpoint_stacks_columns_and_keeps_touch_targets():
    assert "@media (max-width: 900px)" in CSS
    assert "min-height: 44px" in CSS
    assert "st-key-lessonrow" in CSS
    assert "st-key-consequence" in CSS
    assert "touch-action: manipulation" in CSS


def test_svg_images_scale_to_their_container():
    svg = Canvas(400, 200, "bridge").render()
    img = as_img(svg)
    assert "width:100%" in img
    assert "height:auto" in img
    assert '@media (prefers-reduced-motion:reduce)' in img
    assert 'class="mst-motion-static"' in img
