"""Parameterised problems: generate an instance, grade an answer, diagnose misconceptions."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Literal

from tutor.engine.grading import UNIT_NAMES, ParseError, close, parse_quantity
from tutor.models.content import ContentBundle, Problem
from tutor.sim.registry import ANSWERS, MISCONCEPTION_VALUES
from tutor.sim.units import format_si

# [[name]] placeholders, so templates can contain LaTeX braces ($\frac{V_0}{2R}$)
_PLACEHOLDER = re.compile(r"\[\[(\w+)\]\]")


@dataclass(frozen=True)
class Instance:
    problem_id: str
    seed: int
    params: dict[str, float]
    text: str
    answer: float | None  # SI value for numeric problems


@dataclass(frozen=True)
class Grade:
    status: Literal["correct", "wrong", "invalid"]
    message: str
    expected: str = ""
    misconception_id: str | None = None
    misconception_text: str | None = None
    correction: str | None = None
    extra: dict = field(default_factory=dict)

    @property
    def counts(self) -> bool:
        """Invalid input (unparseable, missing unit) is not recorded as an attempt."""
        return self.status != "invalid"


def fmt_param(v: float) -> str:
    if float(v).is_integer() and abs(v) < 1e6:
        return str(int(v))
    return f"{v:.4g}"


def sample_params(problem: Problem, seed: int) -> dict[str, float]:
    rng = random.Random(f"{problem.id}:{seed}")
    out: dict[str, float] = {}
    for name in sorted(problem.params):
        spec = problem.params[name]
        if spec.choices is not None:
            out[name] = float(rng.choice(spec.choices))
        else:
            lo, hi = spec.range  # type: ignore[misc]
            n = int(round((hi - lo) / spec.step)) + 1  # type: ignore[operator]
            out[name] = round(lo + spec.step * rng.randrange(n), 10)  # type: ignore[operator]
    return out


def render(template: str, params: dict[str, float]) -> str:
    def sub(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in params:
            raise KeyError(f"Template placeholder [[{key}]] has no parameter")
        return fmt_param(params[key])

    return _PLACEHOLDER.sub(sub, template)


def placeholders(template: str) -> set[str]:
    return set(_PLACEHOLDER.findall(template))


def generate(problem: Problem, seed: int = 0) -> Instance:
    params = sample_params(problem, seed)
    answer = None
    if problem.kind == "numeric":
        assert problem.answer is not None
        answer = ANSWERS[problem.answer.fn](params)
    return Instance(problem.id, seed, params, render(problem.template, params), answer)


def expected_text(problem: Problem, inst: Instance) -> str:
    if problem.kind != "numeric":
        opt = next(o for o in problem.options if o.id == problem.correct)
        return opt.text
    assert problem.answer is not None and inst.answer is not None
    a = problem.answer
    if a.unit == "1":
        return f"{fmt_param(round(inst.answer * 100, 6))} %" if abs(inst.answer) < 1 else fmt_param(inst.answer)
    return format_si(inst.answer, a.unit, sig=3, force_prefix=a.display_prefix)


def _misconception(bundle: ContentBundle | None, mid: str) -> tuple[str | None, str | None]:
    if bundle is None:
        return None, None
    found = bundle.misconceptions.get(mid)
    if not found:
        return None, None
    return found[1].text, found[1].correction


def grade_numeric(problem: Problem, inst: Instance, text: str, bundle: ContentBundle | None = None) -> Grade:
    assert problem.answer is not None and inst.answer is not None
    spec = problem.answer
    exp = expected_text(problem, inst)
    try:
        q = parse_quantity(text)
    except ParseError as exc:
        return Grade("invalid", str(exc))

    if spec.unit != "1" and q.unit is None:
        return Grade("invalid", f"Add a unit — this answer is {UNIT_NAMES.get(spec.unit, spec.unit)}.")
    value = q.value
    if spec.unit == "1" and q.unit is None and close(value, inst.answer * 100, spec.tolerance_rel):
        return Grade("invalid", "That looks like a percentage — add the % sign (or give it as a fraction).")
    if q.unit is not None and q.unit != spec.unit:
        return Grade(
            "wrong",
            f"Unit mismatch: you gave {UNIT_NAMES.get(q.unit, q.unit)}, "
            f"but the question asks for {UNIT_NAMES.get(spec.unit, spec.unit)}.",
            expected=exp,
            misconception_id="unit_mismatch",
        )

    target = inst.answer
    compare_value = abs(value) if spec.accept_sign == "either" else value
    compare_target = abs(target) if spec.accept_sign == "either" else target
    if close(compare_value, compare_target, spec.tolerance_rel):
        note = ""
        if spec.accept_sign == "either" and value != 0 and (value > 0) != (target > 0):
            note = " (Sign accepted: it depends on which node you call +.)"
        return Grade("correct", f"Correct: {exp}.{note}", expected=exp)

    # explicit misconception checks first
    for chk in problem.misconception_checks:
        if chk.scale is not None:
            cand = target * chk.scale
        else:
            cand = MISCONCEPTION_VALUES[chk.fn](inst.params)  # type: ignore[index]
        if close(cand, target, spec.tolerance_rel):
            continue  # indistinguishable from the right answer for these parameters
        cv = abs(cand) if spec.accept_sign == "either" else cand
        if close(compare_value, cv, spec.tolerance_rel):
            text_, corr = _misconception(bundle, chk.misconception)
            return Grade(
                "wrong",
                "Not quite — this is a classic slip.",
                expected=exp,
                misconception_id=chk.misconception,
                misconception_text=text_,
                correction=corr,
            )

    # generic checks: sign, SI prefix
    if spec.accept_sign == "exact" and target != 0 and close(value, -target, spec.tolerance_rel):
        t, c = _misconception(bundle, "sign_flip")
        return Grade("wrong", "Right size, wrong sign.", expected=exp, misconception_id="sign_flip",
                     misconception_text=t, correction=c)
    for factor in (1e3, 1e-3, 1e6, 1e-6):
        if target != 0 and close(compare_value, compare_target * factor, spec.tolerance_rel):
            t, c = _misconception(bundle, "prefix_slip")
            return Grade(
                "wrong",
                f"Off by a factor of {fmt_param(factor)} — check your SI prefixes.",
                expected=exp,
                misconception_id="prefix_slip",
                misconception_text=t,
                correction=c,
            )
    return Grade("wrong", "Not correct.", expected=exp)


def grade_choice(problem: Problem, choice_id: str, bundle: ContentBundle | None = None) -> Grade:
    exp = expected_text(problem, Instance(problem.id, 0, {}, problem.template, None))
    if choice_id == problem.correct:
        return Grade("correct", "Correct.", expected=exp)
    opt = next((o for o in problem.options if o.id == choice_id), None)
    if opt is None:
        return Grade("invalid", "Pick one of the options.")
    if opt.misconception:
        t, c = _misconception(bundle, opt.misconception)
        return Grade("wrong", "Not quite.", expected=exp, misconception_id=opt.misconception,
                     misconception_text=t, correction=c)
    return Grade("wrong", "Not correct.", expected=exp)


def grade(problem: Problem, inst: Instance, answer: str, bundle: ContentBundle | None = None) -> Grade:
    if problem.kind == "numeric":
        return grade_numeric(problem, inst, answer, bundle)
    return grade_choice(problem, answer, bundle)
