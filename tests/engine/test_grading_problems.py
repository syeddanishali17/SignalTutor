import pytest

from tutor.engine.grading import ParseError, parse_quantity
from tutor.engine.problems import Instance, generate, grade, render
from tutor.models.loader import load_or_raise


@pytest.fixture(scope="module")
def bundle():
    return load_or_raise()


@pytest.mark.parametrize(
    "text, value, unit",
    [
        ("1.25 mV", 1.25e-3, "V"),
        ("1,25mV", 1.25e-3, "V"),
        ("−1.25 mV", -1.25e-3, "V"),
        ("-1.25e-3 V", -1.25e-3, "V"),
        ("1.25×10^-3 V", 1.25e-3, "V"),
        ("4.7kΩ", 4700, "ohm"),
        ("4.7 kohm", 4700, "ohm"),
        ("4.7 kOhms", 4700, "ohm"),
        ("350 Ω", 350, "ohm"),
        ("2 mΩ", 2e-3, "ohm"),
        ("3 MΩ", 3e6, "ohm"),
        ("500 µV", 500e-6, "V"),
        ("500 μV", 500e-6, "V"),
        ("500 uV", 500e-6, "V"),
        ("3 mA", 3e-3, "A"),
        ("0.5 %", 0.005, "1"),
        ("500 µε", 500e-6, "1"),
        ("1 kHz", 1e3, "Hz"),
        ("10 mv", 10e-3, "V"),
        ("2.5", 2.5, None),
    ],
)
def test_parse_quantity(text, value, unit):
    q = parse_quantity(text)
    assert q.value == pytest.approx(value)
    assert q.unit == unit


@pytest.mark.parametrize("bad", ["", "mV", "1.2.3 V", "5 furlongs", "1,5.2 V"])
def test_parse_quantity_errors(bad):
    with pytest.raises(ParseError):
        parse_quantity(bad)


def _inst(bundle, pid, params):
    from tutor.sim.registry import ANSWERS

    p = bundle.problems[pid]
    return p, Instance(pid, 0, params, render(p.template, params), ANSWERS[p.answer.fn](params))


def test_spec_worked_check_full_bridge(bundle):
    # spec 8.1: G = 2, ε = 500 µε, Vb = 5 V -> full bridge 5 mV; answering the quarter value flags the misconception
    p, inst = _inst(bundle, "full_bridge_output", {"G": 2.0, "eps_ue": 500.0, "Vb": 5.0})
    assert inst.answer == pytest.approx(5e-3)
    assert grade(p, inst, "5 mV", bundle).status == "correct"
    assert grade(p, inst, "-5 mV", bundle).status == "correct"  # sign convention accepted
    g = grade(p, inst, "1.25 mV", bundle)
    assert g.status == "wrong" and g.misconception_id == "quarter_vs_full"
    assert "4" in (g.correction or "")
    g = grade(p, inst, "5000 V", bundle)
    assert g.misconception_id == "microstrain_slip"


def test_missing_unit_is_not_counted(bundle):
    p, inst = _inst(bundle, "full_bridge_output", {"G": 2.0, "eps_ue": 500.0, "Vb": 5.0})
    g = grade(p, inst, "5", bundle)
    assert g.status == "invalid" and not g.counts


def test_unit_mismatch_is_wrong(bundle):
    p, inst = _inst(bundle, "full_bridge_output", {"G": 2.0, "eps_ue": 500.0, "Vb": 5.0})
    g = grade(p, inst, "5 mA", bundle)
    assert g.status == "wrong" and g.misconception_id == "unit_mismatch"


def test_prefix_slip_detected(bundle):
    p, inst = _inst(bundle, "ohm_current", {"V": 9.0, "R_k": 4.7})
    assert grade(p, inst, "1.91 mA", bundle).status == "correct"
    g = grade(p, inst, "1.91 A", bundle)
    assert g.misconception_id == "prefix_slip"


def test_divider_swapped_misconception(bundle):
    p, inst = _inst(bundle, "divider_vout", {"Vin": 10.0, "R1_k": 1.0, "R2_k": 22.0})
    assert grade(p, inst, f"{10 * 22 / 23:.3f} V", bundle).status == "correct"
    g = grade(p, inst, f"{10 * 1 / 23:.3f} V", bundle)
    assert g.misconception_id == "divider_swapped"


def test_percent_answers(bundle):
    p, inst = _inst(bundle, "approx_error", {"x_pct": 2.0})
    assert grade(p, inst, "1 %", bundle).status == "correct"
    assert grade(p, inst, "0.01", bundle).status == "correct"
    assert grade(p, inst, "1", bundle).status == "invalid"  # looks like a percentage without the sign


def test_choice_problems(bundle):
    p = bundle.problems["balance_condition"]
    inst = generate(p)
    assert grade(p, inst, "ratio", bundle).status == "correct"
    g = grade(p, inst, "equal", bundle)
    assert g.misconception_id == "balance_needs_equal" and g.correction


def test_generation_is_deterministic(bundle):
    p = bundle.problems["full_bridge_output"]
    assert generate(p, 7) == generate(p, 7)
    texts = {generate(p, s).text for s in range(15)}
    assert len(texts) > 3
    for s in range(30):
        inst = generate(p, s)
        assert 100 <= inst.params["eps_ue"] <= 1000 and inst.params["eps_ue"] % 50 == 0
