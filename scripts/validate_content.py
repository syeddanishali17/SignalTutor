"""Content validation (spec 15). Exit code 1 on any error.

    python scripts/validate_content.py
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tutor.engine import dims  # noqa: E402
from tutor.engine.concept_graph import ConceptGraph  # noqa: E402
from tutor.engine.derivation import check_derivation  # noqa: E402
from tutor.engine.expr import ExprError, names, parse  # noqa: E402
from tutor.engine.formula_view import MODES, view  # noqa: E402
from tutor.engine.problems import generate, placeholders  # noqa: E402
from tutor.models.content import ContentBundle  # noqa: E402
from tutor.models.loader import load_content  # noqa: E402
from tutor.sim.registry import ANSWERS, MISCONCEPTION_VALUES  # noqa: E402
from tutor.ui.svg.figures import FIGURES  # noqa: E402

GENERIC_MISCONCEPTIONS = {"unit_mismatch"}  # produced by the grader itself
PLAIN_FIELDS = {"title", "short", "label", "plain_words"}  # rendered as plain text: no $maths$
CONTROL_CHARS = re.compile(r"[\x00-\x09\x0b\x0c\x0e-\x1f]")  # includes TAB: "\text" inside a YAML "..." string
TOKEN = re.compile(r"\[\[(\w+)\]\]")


def _walk(obj, path: str):
    """Yield (path, field_name, string) for every string inside a pydantic model tree."""
    if isinstance(obj, BaseModel):
        for name in type(obj).model_fields:
            yield from _walk(getattr(obj, name), f"{path}.{name}" if path else name)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}[{k}]")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, path.rsplit(".", 1)[-1].split("[")[0], obj


def _text_rules(bundle: ContentBundle) -> list[str]:
    """Typography rules: no control characters (YAML '\\t' traps), balanced $…$, plain fields stay plain."""
    errors: list[str] = []
    for group in ("concepts", "formulas", "known_issues", "problems", "derivations", "oral", "whiteboard",
                  "lessons", "symbols"):
        for key, model in getattr(bundle, group).items():
            for path, field, s in _walk(model, f"{group}[{key}]"):
                if CONTROL_CHARS.search(s):
                    errors.append(f"{path}: control character in text (a YAML escape like \\t or \\b?): {s[:60]!r}")
                if field in ("explanation",):
                    continue
                stripped = s.replace("\\$", "").replace("$$", "")
                if group != "formulas" and field not in ("latex", "lecture_form", "canonical_form", "proposed_form",
                                                        "expr", "symbol") and stripped.count("$") % 2:
                    errors.append(f"{path}: unbalanced $ maths delimiters")
                if field in PLAIN_FIELDS and "$" in s:
                    errors.append(f"{path}: '{field}' is shown as plain text — write it without $maths$")
    return errors


def validate(bundle: ContentBundle) -> list[str]:
    errors: list[str] = _text_rules(bundle)
    concepts = bundle.concepts
    graph = ConceptGraph(concepts)

    def need_concept(cid: str, where: str) -> None:
        if cid not in concepts:
            errors.append(f"{where}: unknown concept {cid!r}")

    # --- graph ---------------------------------------------------------------
    for cid, missing in graph.undefined_references():
        errors.append(f"concept {cid}: prerequisite {missing!r} is not defined")
    cycle = graph.find_cycle()
    if cycle:
        errors.append("concept graph has a cycle: " + " → ".join(cycle))

    # --- misconceptions --------------------------------------------------------
    seen: dict[str, str] = {}
    for c in concepts.values():
        for m in c.misconceptions:
            if m.id in seen:
                errors.append(f"misconception id {m.id!r} used by both {seen[m.id]} and {c.id}")
            seen[m.id] = c.id
    known_m = set(seen) | GENERIC_MISCONCEPTIONS

    # --- problems --------------------------------------------------------------
    for p in bundle.problems.values():
        where = f"problem {p.id}"
        need_concept(p.concept, where)
        ph = placeholders(p.template) | placeholders(p.solution)
        for name in ph - set(p.params):
            errors.append(f"{where}: placeholder [[{name}]] has no parameter")
        for name in set(p.params) - placeholders(p.template):
            errors.append(f"{where}: parameter {name!r} is never shown in the template")
        for o in p.options:
            if o.misconception and o.misconception not in known_m:
                errors.append(f"{where}: option {o.id}: unknown misconception {o.misconception!r}")
        for chk in p.misconception_checks:
            if chk.misconception not in known_m:
                errors.append(f"{where}: unknown misconception {chk.misconception!r}")
            if chk.fn and chk.fn not in MISCONCEPTION_VALUES:
                errors.append(f"{where}: misconception fn {chk.fn!r} is not registered")
        if p.kind == "numeric":
            assert p.answer is not None
            if p.answer.fn not in ANSWERS:
                errors.append(f"{where}: answer fn {p.answer.fn!r} is not registered")
                continue
            try:
                dims.unit_dim(p.answer.unit)
            except ExprError as exc:
                errors.append(f"{where}: bad unit: {exc}")
            for seed in range(25):
                try:
                    inst = generate(p, seed)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{where}: generation failed for seed {seed}: {exc}")
                    break
                if inst.answer is None or not math.isfinite(inst.answer):
                    errors.append(f"{where}: non-finite answer for seed {seed}")
                    break

    # --- formulas ----------------------------------------------------------------
    for f in bundle.formulas.values():
        where = f"formula {f.id}"
        if f.concept:
            need_concept(f.concept, where)
        if f.known_issue and f.known_issue not in bundle.known_issues:
            errors.append(f"{where}: unknown known_issue {f.known_issue!r}")
        shown = f.canonical_check if f.canonical_form else f.lecture_check
        if f.canonical_form and f.canonical_check is None and f.dimension_check != "not_applicable":
            errors.append(f"{where}: has a canonical form but no canonical_check")
        if shown is None:
            if f.dimension_check != "not_applicable":
                errors.append(f"{where}: no machine check, so dimension_check must be not_applicable")
        else:
            try:
                missing = names(parse(shown.expr)) - set(shown.symbols)
                if missing:
                    errors.append(f"{where}: no unit declared for {sorted(missing)}")
                    continue
                ok, msg = dims.check(shown.expr, shown.symbols, shown.result_unit)
            except ExprError as exc:
                errors.append(f"{where}: {exc}")
                continue
            got = "pass" if ok else "fail"
            if got != f.dimension_check:
                errors.append(f"{where}: dimension_check recorded {f.dimension_check!r} but the check gives {got!r} ({msg})")
        for mode in MODES:
            v = view(f, mode)
            if f.status == "needs_review" and not v.flag:
                errors.append(f"{where}: shown without its needs_review flag in {mode} mode")

    for sym in bundle.symbols.values():
        if sym.concept and sym.concept not in concepts:
            errors.append(f"symbol {sym.id}: unknown concept {sym.concept!r}")

    for k in bundle.known_issues.values():
        for fid in k.formulas:
            if fid not in bundle.formulas:
                errors.append(f"known issue {k.id}: unknown formula {fid!r}")

    # --- derivations ------------------------------------------------------------------
    for d in bundle.derivations.values():
        need_concept(d.concept, f"derivation {d.id}")
        if d.figure not in FIGURES:
            errors.append(f"derivation {d.id}: unknown figure {d.figure!r}")
        errors.extend(check_derivation(d))

    # --- oral / whiteboard -------------------------------------------------------------
    for q in bundle.oral.values():
        where = f"oral {q.id}"
        for cid in q.concepts:
            need_concept(cid, where)
        if not q.expected_points:
            errors.append(f"{where}: no expected points")
        ids = {p.id for p in q.expected_points}
        if len(ids) != len(q.expected_points):
            errors.append(f"{where}: duplicate expected point ids")
        for f in q.followups:
            if f.when_missing and f.when_missing not in ids:
                errors.append(f"{where}: follow-up refers to unknown point {f.when_missing!r}")
    for w in bundle.whiteboard.values():
        where = f"whiteboard {w.id}"
        for cid in w.concepts:
            need_concept(cid, where)
        if w.reference_figure and w.reference_figure not in FIGURES:
            errors.append(f"{where}: unknown figure {w.reference_figure!r}")
        if w.reference_derivation and w.reference_derivation not in bundle.derivations:
            errors.append(f"{where}: unknown derivation {w.reference_derivation!r}")
        if not w.checklist:
            errors.append(f"{where}: empty checklist")

    # --- lessons ------------------------------------------------------------------------
    for lesson in bundle.lessons.values():
        where = f"lesson {lesson.id}"
        for cid in lesson.concepts:
            need_concept(cid, where)
            if cid in concepts and not graph.grounded_in_foundations(cid):
                errors.append(f"{where}: concept {cid!r} is not reachable from foundation concepts")
        for pid in lesson.problems:
            if pid not in bundle.problems:
                errors.append(f"{where}: unknown problem {pid!r}")
        for qid in lesson.oral:
            if qid not in bundle.oral:
                errors.append(f"{where}: unknown oral question {qid!r}")
        for wid in lesson.whiteboard:
            if wid not in bundle.whiteboard:
                errors.append(f"{where}: unknown whiteboard prompt {wid!r}")
        for did in lesson.derivations:
            if did not in bundle.derivations:
                errors.append(f"{where}: unknown derivation {did!r}")
        for fid in lesson.formulas:
            if fid not in bundle.formulas:
                errors.append(f"{where}: unknown formula {fid!r}")
        scene_ids = [s.id for s in lesson.scenes]
        if len(set(scene_ids)) != len(scene_ids):
            errors.append(f"{where}: duplicate scene ids")
        break_ids = {b.id for b in lesson.break_it}
        for s in lesson.scenes:
            term_ids = {t.id for t in s.terms}
            for t in s.terms:
                if t.symbol not in bundle.symbols:
                    errors.append(f"{where}/{s.id}: term {t.id!r} uses unknown symbol {t.symbol!r}")
                for ref in TOKEN.findall(t.latex or ""):
                    if ref not in term_ids:
                        errors.append(f"{where}/{s.id}: term {t.id!r} refers to unknown term [[{ref}]]")
            if len(term_ids) != len(s.terms):
                errors.append(f"{where}/{s.id}: duplicate term ids")
            for cid in s.concepts:
                need_concept(cid, f"{where}/{s.id}")
            for bid in s.break_it:
                if bid not in break_ids:
                    errors.append(f"{where}/{s.id}: unknown break_it {bid!r}")
            for item in s.inspect:
                need_concept(item.concept, f"{where}/{s.id}/inspect {item.id}")
    return errors


def main() -> int:
    bundle, errors = load_content()
    if not errors:
        errors = validate(bundle)
    if errors:
        print(f"Content validation FAILED ({len(errors)} problem(s)):")
        for e in errors:
            print("  -", e)
        return 1
    print(
        "Content OK: "
        f"{len(bundle.concepts)} concepts, {len(bundle.formulas)} formulas, {len(bundle.known_issues)} known issues, "
        f"{len(bundle.problems)} problems, {len(bundle.derivations)} derivations, "
        f"{len(bundle.oral)} oral questions, {len(bundle.whiteboard)} whiteboard prompts, {len(bundle.lessons)} lessons."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
