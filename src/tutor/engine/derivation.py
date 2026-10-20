"""Symbolic consistency checks for derivation content (SymPy, no eval)."""

from __future__ import annotations

import sympy as sp

from tutor.engine import dims
from tutor.engine.expr import names, parse, to_sympy
from tutor.models.content import Derivation


def _sub(expr: sp.Expr, env: dict[sp.Symbol, sp.Expr]) -> sp.Expr:
    # repeated substitution so definitions may reference earlier definitions
    for _ in range(10):
        new = expr.subs(env)
        if new == expr:
            break
        expr = new
    return expr


def check_derivation(d: Derivation) -> list[str]:
    """Return a list of problems (empty if the derivation is consistent)."""
    errors: list[str] = []
    syms: dict[str, sp.Symbol] = {}
    env: dict[sp.Symbol, sp.Expr] = {}

    def S(text: str) -> sp.Expr:
        return _sub(to_sympy(text, syms), env)

    for step in d.steps:
        where = f"{d.id}/{step.id}"
        target: sp.Expr | None = None
        c = step.check
        if c is not None:
            try:
                if c.kind == "define":
                    if not c.name:
                        errors.append(f"{where}: define needs 'name'")
                        continue
                    target = S(c.expr)
                    env[sp.Symbol(c.name, positive=True)] = target
                    syms.setdefault(c.name, sp.Symbol(c.name, positive=True))
                    if d.symbols:
                        _dim_check(c.expr, c.name, d, where, errors)
                elif c.kind == "equals":
                    if not c.lhs:
                        errors.append(f"{where}: equals needs 'lhs'")
                        continue
                    lhs, target = S(c.lhs), S(c.expr)
                    if sp.simplify(lhs - target) != 0:
                        errors.append(f"{where}: {c.lhs} ≠ {c.expr} (difference {sp.simplify(lhs - target)})")
                elif c.kind == "approx":
                    if not (c.lhs and c.small):
                        errors.append(f"{where}: approx needs 'lhs' and 'small'")
                        continue
                    small = syms.setdefault(c.small, sp.Symbol(c.small, positive=True))
                    lhs, target = S(c.lhs), S(c.expr)
                    first = sp.series(lhs, small, 0, 2).removeO()
                    if sp.simplify(first - target) != 0:
                        errors.append(f"{where}: first-order expansion of {c.lhs} is {sp.simplify(first)}, not {c.expr}")
            except Exception as exc:  # noqa: BLE001 - report any content error
                errors.append(f"{where}: check failed: {exc}")
                continue
        if step.fade is not None:
            if target is None:
                errors.append(f"{where}: a faded step needs a 'check' to verify its options")
                continue
            if not (0 <= step.fade.correct < len(step.fade.options)):
                errors.append(f"{where}: fade.correct out of range")
                continue
            for i, opt in enumerate(step.fade.options):
                try:
                    same = sp.simplify(S(opt.expr) - target) == 0
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{where}: option {i} unparsable: {exc}")
                    continue
                if i == step.fade.correct and not same:
                    errors.append(f"{where}: the marked-correct option {opt.expr!r} is not equal to the step")
                if i != step.fade.correct and same:
                    errors.append(f"{where}: distractor {opt.expr!r} is actually equivalent to the answer")
    return errors


def _dim_check(expr: str, name: str, d: Derivation, where: str, errors: list[str]) -> None:
    if name not in d.symbols:
        return
    missing = names(parse(expr)) - set(d.symbols)
    if missing:
        errors.append(f"{where}: no unit declared for {sorted(missing)}")
        return
    ok, msg = dims.check(expr, d.symbols, d.symbols[name])
    if not ok:
        errors.append(f"{where}: dimension check failed for {name}: {msg}")
