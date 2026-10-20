"""Load and schema-validate everything under ``content/``.

Errors are collected (not raised one at a time) so ``scripts/validate_content.py``
can report every problem in one run.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from tutor.models.content import (
    Concept,
    ContentBundle,
    Derivation,
    Formula,
    KnownIssue,
    Lesson,
    OralFile,
    ProblemFile,
    SymbolDef,
)
from tutor.paths import CONTENT_DIR

T = TypeVar("T", bound=BaseModel)


class ContentError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


class _YamlError(Exception):
    pass


def _read_yaml(path: Path) -> Any:
    # utf-8-sig tolerates a BOM (some Windows editors add one)
    with path.open(encoding="utf-8-sig") as fh:
        try:
            return yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise _YamlError(f"{path.name}: YAML syntax error: {exc}") from exc


def _validate(model: type[T], data: Any, where: str, errors: list[str]) -> T | None:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        for err in exc.errors():
            loc = ".".join(str(p) for p in err["loc"])
            errors.append(f"{where}: {loc}: {err['msg']}")
        return None


def _add(target: dict[str, Any], key: str, value: Any, where: str, errors: list[str]) -> None:
    if key in target:
        errors.append(f"{where}: duplicate id {key!r}")
        return
    target[key] = value


def load_content(root: Path = CONTENT_DIR) -> tuple[ContentBundle, list[str]]:
    """Load all content. Returns ``(bundle, errors)``; ``errors`` is empty when valid."""
    errors: list[str] = []
    bundle = ContentBundle()

    def read(path: Path) -> Any:
        try:
            return _read_yaml(path)
        except _YamlError as exc:
            errors.append(str(exc))
            return None

    # concepts: one YAML per concept, optional sibling .md prose
    for path in sorted((root / "concepts").glob("*.yaml")):
        rel = path.relative_to(root).as_posix()
        data = read(path)
        if data is None:
            continue
        concept = _validate(Concept, data, rel, errors)
        if concept is None:
            continue
        if concept.id != path.stem:
            errors.append(f"{rel}: id {concept.id!r} must match the file name {path.stem!r}")
        if concept.explanation_md:
            md_path = path.parent / concept.explanation_md
            if not md_path.exists():
                errors.append(f"{rel}: explanation_md {concept.explanation_md!r} not found")
            else:
                concept = concept.model_copy(update={"explanation": md_path.read_text(encoding="utf-8-sig")})
        _add(bundle.concepts, concept.id, concept, rel, errors)

    def load_list(rel_file: str, key: str, model: type[T], target: dict[str, T]) -> None:
        path = root / rel_file
        if not path.exists():
            errors.append(f"{rel_file}: missing")
            return
        data = read(path) or {}
        for i, item in enumerate(data.get(key, [])):
            obj = _validate(model, item, f"{rel_file}[{i}]", errors)
            if obj is not None:
                _add(target, obj.id, obj, rel_file, errors)  # type: ignore[attr-defined]

    load_list("formulas.yaml", "formulas", Formula, bundle.formulas)
    load_list("known_issues.yaml", "issues", KnownIssue, bundle.known_issues)
    load_list("symbols.yaml", "symbols", SymbolDef, bundle.symbols)

    def load_dir(sub: str, handle: Callable[[Any, str], None]) -> None:
        for path in sorted((root / sub).glob("*.yaml")):
            data = read(path)
            if data is not None:
                handle(data, path.relative_to(root).as_posix())

    def handle_problems(data: Any, rel: str) -> None:
        pf = _validate(ProblemFile, data, rel, errors)
        if pf:
            for p in pf.problems:
                _add(bundle.problems, p.id, p, rel, errors)

    def handle_oral(data: Any, rel: str) -> None:
        of = _validate(OralFile, data, rel, errors)
        if of:
            for q in of.questions:
                _add(bundle.oral, q.id, q, rel, errors)
            for w in of.whiteboard:
                _add(bundle.whiteboard, w.id, w, rel, errors)

    def handle_derivation(data: Any, rel: str) -> None:
        d = _validate(Derivation, data, rel, errors)
        if d:
            _add(bundle.derivations, d.id, d, rel, errors)

    def handle_lesson(data: Any, rel: str) -> None:
        # top-level keys starting with "x-" only hold YAML anchors (&shared blocks) for reuse
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if not str(k).startswith("x-")}
        lesson = _validate(Lesson, data, rel, errors)
        if lesson:
            _add(bundle.lessons, lesson.id, lesson, rel, errors)

    load_dir("problems", handle_problems)
    load_dir("oral", handle_oral)
    load_dir("derivations", handle_derivation)
    load_dir("lessons", handle_lesson)
    return bundle, errors


def load_or_raise(root: Path = CONTENT_DIR) -> ContentBundle:
    bundle, errors = load_content(root)
    if errors:
        raise ContentError(errors)
    return bundle
