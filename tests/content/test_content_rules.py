"""Content validation as tests (spec 15), plus negative tests proving the checkers bite."""

import importlib.util
from pathlib import Path

import pytest

from tutor.engine.derivation import check_derivation
from tutor.engine.formula_view import MODES, view
from tutor.engine.oral import coverage, select_followups
from tutor.models.content import Derivation, Formula
from tutor.models.loader import load_content, load_or_raise
from tutor.ui.svg.figures import FIGURES

ROOT = Path(__file__).resolve().parents[2]


def _validate_module():
    spec = importlib.util.spec_from_file_location("validate_content", ROOT / "scripts" / "validate_content.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def test_content_loads_and_validates():
    bundle, errors = load_content()
    assert errors == []
    assert _validate_module().validate(bundle) == []


def test_exam_mode_never_hides_needs_review_flag():
    bundle = load_or_raise()
    flagged = [f for f in bundle.formulas.values() if f.status == "needs_review"]
    assert len(flagged) >= 6  # K1-K6 seeded
    for f in flagged:
        for mode in MODES:
            v = view(f, mode)
            assert v.flag and "needs review" in v.flag
            assert v.latex == f.canonical_form


def test_known_issue_k9_registered_and_linked():
    bundle = load_or_raise()
    k9 = bundle.known_issues["K9"]
    assert "bridge_quarter_approx" in k9.formulas
    assert bundle.formulas["bridge_quarter_approx"].known_issue == "K9"


def test_derivation_checker_catches_wrong_steps():
    bad = Derivation.model_validate(
        {
            "id": "bad",
            "title": "bad",
            "concept": "wheatstone_quarter",
            "figure": "bridge_quarter",
            "source": "test",
            "steps": [
                {"id": "a", "latex": "", "changed": "", "why": "", "check": {"kind": "define", "name": "V2", "expr": "V0/(2 + dR/R)"}},
                {"id": "b", "latex": "", "changed": "", "why": "",
                 "check": {"kind": "approx", "lhs": "V2 - V0/2", "expr": "-dR/R*V0/2", "small": "dR"},
                 "fade": {"prompt": "", "correct": 0, "options": [{"latex": "", "expr": "-dR/R*V0/4"},
                                                                   {"latex": "", "expr": "-dR*V0/(4*R)"}]}},
            ],
        }
    )
    errs = check_derivation(bad)
    assert any("first-order expansion" in e for e in errs)
    assert any("distractor" in e for e in errs) or any("marked-correct" in e for e in errs)


def test_needs_review_requires_issue_and_flagged_exam_mode():
    with pytest.raises(ValueError):
        Formula.model_validate({"id": "x", "title": "x", "status": "needs_review", "source": "s",
                                "lecture_form": "a", "dimension_check": "pass"})


def test_followups_probe_missing_points_first():
    bundle = load_or_raise()
    q = bundle.oral["why_bridge"]
    fups = select_followups(q, {"two_dividers", "tiny_change"})
    assert fups[0].when_missing == "balanced_zero"
    assert all(f.always for f in fups if f.when_missing is None)
    assert coverage(q, {"two_dividers", "tiny_change", "formula"}) == pytest.approx(0.5)


def test_all_figures_render_valid_svg():
    import xml.etree.ElementTree as ET

    for key, fn in FIGURES.items():
        svg = fn(["R1", "meter"])
        root = ET.fromstring(svg)
        assert root.tag.endswith("svg"), key
        assert "viewBox" in root.attrib
