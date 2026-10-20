"""Pydantic v2 schemas for every content file under ``content/``.

``extra="forbid"`` everywhere: a typo in a YAML key is a validation error, not
a silently ignored field.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Status = Literal["verified", "needs_review", "supplemental", "future"]
Track = Literal["math", "physics", "electrical", "course_l01", "course_l02", "course_l03"]
Skill = Literal["compute", "derive", "explain", "draw"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# --- concepts ------------------------------------------------------------------


class Misconception(Strict):
    id: str
    text: str
    correction: str


class Analogy(Strict):
    text: str
    breaks_when: str


class Concept(Strict):
    id: str
    title: str
    short: str | None = None  # compact label for chips / popovers
    code: str | None = None  # spec curriculum code, e.g. "E2", "C3"
    track: Track
    prerequisites: list[str] = []
    status: Status
    source_refs: list[str] = []
    one_liner: str
    plain_words: str | None = None  # beginner-mode label
    explanation_md: str | None = None
    explanation: str = ""  # filled by the loader from explanation_md
    misconceptions: list[Misconception] = []
    analogy: Analogy | None = None
    units: str | None = None
    symbol: str | None = None  # LaTeX symbol, e.g. "V_{AB}"


# --- formulas and source integrity -------------------------------------------------


class DimCheck(Strict):
    expr: str  # machine-readable, parsed by tutor.engine.expr (never eval'd)
    symbols: dict[str, str]  # symbol -> unit expression
    result_unit: str


class SymbolMeaning(Strict):
    symbol: str  # LaTeX
    meaning: str
    unit: str
    when_it_goes_up: str | None = None


class Formula(Strict):
    id: str
    title: str
    concept: str | None = None
    module: str | None = None
    status: Status
    source: str
    evidence: list[Literal["slides", "notes", "dimension_check", "sympy", "textbook"]] = []
    lecture_form: str  # LaTeX as written in the source
    canonical_form: str | None = None  # LaTeX; required when it differs from lecture_form
    issue: str | None = None
    known_issue: str | None = None
    lecture_check: DimCheck | None = None
    canonical_check: DimCheck | None = None
    dimension_check: Literal["pass", "fail", "not_applicable"]  # recorded result for the *shown* form
    shown_in_exam_mode: Literal["lecture", "canonical", "canonical_with_flag"] = "lecture"
    assumptions: list[str] = []
    meaning: list[SymbolMeaning] = []
    comes_from: str | None = None

    @model_validator(mode="after")
    def _needs_review_has_issue(self) -> "Formula":
        if self.status == "needs_review" and not (self.issue and self.canonical_form):
            raise ValueError(f"Formula {self.id}: needs_review requires 'issue' and 'canonical_form'")
        if self.status == "needs_review" and self.shown_in_exam_mode != "canonical_with_flag":
            raise ValueError(f"Formula {self.id}: needs_review must be shown_in_exam_mode=canonical_with_flag")
        return self


class KnownIssue(Strict):
    id: str
    location: str
    lecture_form: str
    proposed_form: str
    reason: str
    severity: Literal["low", "medium", "high"]
    status: Literal["open", "confirmed", "resolved"] = "open"
    formulas: list[str] = []
    found_by: str = "analysis of the learner's L01/L02 notes"


# --- problems ----------------------------------------------------------------------


class ParamSpec(Strict):
    choices: list[float] | None = None
    range: tuple[float, float] | None = None
    step: float | None = None
    unit: str | None = None  # display only

    @model_validator(mode="after")
    def _one_kind(self) -> "ParamSpec":
        if (self.choices is None) == (self.range is None):
            raise ValueError("A parameter needs exactly one of 'choices' or 'range'")
        if self.range is not None and (self.step is None or self.step <= 0):
            raise ValueError("A 'range' parameter needs a positive 'step'")
        if self.range is not None and self.range[0] > self.range[1]:
            raise ValueError("range must be [low, high]")
        return self


class NumericAnswer(Strict):
    fn: str
    unit: str  # SI symbol: V, A, ohm, 1 ...
    tolerance_rel: float = 0.02
    accept_sign: Literal["exact", "either"] = "exact"
    display_prefix: str | None = None  # e.g. "m" to show expected value in mV


class MisconceptionCheck(Strict):
    misconception: str
    scale: float | None = None  # learner value ≈ answer * scale
    fn: str | None = None  # learner value ≈ registered misconception value

    @model_validator(mode="after")
    def _one_kind(self) -> "MisconceptionCheck":
        if (self.scale is None) == (self.fn is None):
            raise ValueError("A misconception check needs exactly one of 'scale' or 'fn'")
        return self


class Option(Strict):
    id: str
    text: str
    misconception: str | None = None


class Problem(Strict):
    id: str
    concept: str
    skill: Skill = "compute"
    kind: Literal["numeric", "mc", "direction"]
    level: Literal[1, 2, 3, 4, 5] = 4
    template: str
    params: dict[str, ParamSpec] = {}
    answer: NumericAnswer | None = None
    options: list[Option] = []
    correct: str | None = None
    misconception_checks: list[MisconceptionCheck] = []
    solution: str
    minutes: float = 2.0

    @model_validator(mode="after")
    def _kind_fields(self) -> "Problem":
        if self.kind == "numeric":
            if self.answer is None:
                raise ValueError(f"Problem {self.id}: numeric problems need 'answer'")
            if self.options:
                raise ValueError(f"Problem {self.id}: numeric problems take no options")
        else:
            if not self.options or self.correct is None:
                raise ValueError(f"Problem {self.id}: {self.kind} problems need 'options' and 'correct'")
            ids = [o.id for o in self.options]
            if self.correct not in ids:
                raise ValueError(f"Problem {self.id}: correct={self.correct!r} is not an option id")
            if len(set(ids)) != len(ids):
                raise ValueError(f"Problem {self.id}: duplicate option ids")
        return self


class ProblemFile(Strict):
    problems: list[Problem]


# --- derivations ---------------------------------------------------------------------


class FadeOption(Strict):
    latex: str
    expr: str  # machine form, checked with SymPy in tests


class Fade(Strict):
    prompt: str
    options: list[FadeOption]
    correct: int


class StepCheck(Strict):
    """Machine-checkable meaning of a step (SymPy, in tests and validation).

    ``define``  : introduces ``name = expr``
    ``equals``  : asserts ``lhs == expr`` given earlier definitions
    ``approx``  : asserts ``expr`` is the first-order expansion of ``lhs`` in ``small``
    """

    kind: Literal["define", "equals", "approx"]
    name: str | None = None
    lhs: str | None = None
    expr: str
    small: str | None = None


class DerivationStep(Strict):
    id: str
    latex: str
    changed: str
    why: str
    law: str | None = None
    assumption: str | None = None
    highlight: list[str] = []
    annotated: str | None = None  # beginner version with \underbrace labels for numerator/denominator
    check: StepCheck | None = None
    fade: Fade | None = None


class Derivation(Strict):
    id: str
    title: str
    concept: str
    figure: str  # key of an SVG builder in tutor.ui.svg
    source: str
    symbols: dict[str, str] = {}  # symbol -> unit (for dimension checks of step exprs)
    steps: list[DerivationStep]


# --- oral / whiteboard ------------------------------------------------------------------


class Point(Strict):
    id: str
    text: str


class StructurePart(Strict):
    label: Literal[
        "definition",
        "motivation",
        "mechanism",
        "key equation",
        "physical meaning",
        "assumptions",
        "limitations",
        "application",
    ]
    text: str


class Followup(Strict):
    ask: str
    when_missing: str | None = None  # expected-point id
    always: bool = False
    hint: str | None = None

    @model_validator(mode="after")
    def _trigger(self) -> "Followup":
        if self.always == (self.when_missing is not None):
            raise ValueError("A follow-up needs exactly one of 'always: true' or 'when_missing'")
        return self


class OralQuestion(Strict):
    id: str
    concepts: list[str]
    priority: Literal["medium", "high", "very_high"] = "high"
    question: str
    structure: list[StructurePart]
    expected_points: list[Point]
    followups: list[Followup] = []
    traps: list[str] = []
    minutes: float = 4.0


class WhiteboardPrompt(Strict):
    id: str
    concepts: list[str]
    skill: Literal["draw", "derive"]
    prompt: str
    time_limit_s: int = 300
    reference_figure: str | None = None
    reference_derivation: str | None = None
    checklist: list[Point]
    minutes: float = 6.0


class OralFile(Strict):
    questions: list[OralQuestion] = []
    whiteboard: list[WhiteboardPrompt] = []


# --- lessons --------------------------------------------------------------------------


class PredictOption(Strict):
    id: str
    label: str


class Predict(Strict):
    question: str
    options: list[PredictOption]
    correct: str
    reveal: str

    @model_validator(mode="after")
    def _correct_exists(self) -> "Predict":
        if self.correct not in {o.id for o in self.options}:
            raise ValueError(f"Predict: correct={self.correct!r} is not an option")
        return self


class InspectItem(Strict):
    """A physical part of the picture (resistor, node, meter, current path)."""

    id: str  # SVG element id, e.g. "R1"
    label: str  # how it appears in the selector, e.g. "R₁" (plain text / unicode)
    concept: str
    role: str  # what this element does in *this* picture (markdown + $LaTeX$)
    highlight: list[str] = []  # extra SVG ids to light up (default: [id])
    controls: list[str] = []  # control ids to outline when selected


class SymbolDef(Strict):
    """A mathematical symbol or expression with a plain-language meaning (content/symbols.yaml)."""

    id: str
    latex: str
    label: str  # plain unicode for buttons, e.g. "R + ΔR"
    meaning: str  # markdown + $LaTeX$
    unit: str | None = None
    concept: str | None = None


class Term(Strict):
    """A selectable symbol in one scene: which parts and controls it corresponds to.

    ``latex`` may contain ``[[other_term]]`` tokens so composite expressions
    (``R_1 + R_4``) can box their pieces individually.
    """

    id: str
    symbol: str  # SymbolDef id
    latex: str | None = None  # defaults to the symbol's LaTeX
    highlight: list[str] = []
    controls: list[str] = []


class ExplainAloud(Strict):
    prompt: str
    points: list[str]


class Scene(Strict):
    id: str
    title: str
    short: str
    concepts: list[str]
    problem: str
    predict: Predict | None = None
    inspect: list[InspectItem] = []
    explain: ExplainAloud
    notes_md: str = ""
    analogy_note: str | None = None
    break_it: list[str] = []  # ids of the lesson's break_it entries relevant here
    terms: list[Term] = []  # selectable symbols for the equation strip
    map_stage: str | None = None  # overrides the lesson's sensor-map stage


class BreakIt(Strict):
    id: str
    title: str
    cause: str
    condition: str
    consequence: str
    recovery: str


class Lesson(Strict):
    id: str
    title: str
    module: str
    map_stage: str | None = None
    map_note: str | None = None
    concepts: list[str]
    scenes: list[Scene] = []
    derivations: list[str] = []
    problems: list[str] = []
    oral: list[str] = []
    whiteboard: list[str] = []
    break_it: list[BreakIt] = []
    traps: list[str] = []
    formulas: list[str] = []


# --- bundle ------------------------------------------------------------------------------


class ContentBundle(BaseModel):
    """Everything loaded from ``content/``; lookups by id."""

    model_config = ConfigDict(frozen=False)

    concepts: dict[str, Concept] = Field(default_factory=dict)
    formulas: dict[str, Formula] = Field(default_factory=dict)
    known_issues: dict[str, KnownIssue] = Field(default_factory=dict)
    problems: dict[str, Problem] = Field(default_factory=dict)
    derivations: dict[str, Derivation] = Field(default_factory=dict)
    oral: dict[str, OralQuestion] = Field(default_factory=dict)
    whiteboard: dict[str, WhiteboardPrompt] = Field(default_factory=dict)
    lessons: dict[str, Lesson] = Field(default_factory=dict)
    symbols: dict[str, SymbolDef] = Field(default_factory=dict)

    @property
    def misconceptions(self) -> dict[str, tuple[str, Misconception]]:
        """misconception id -> (concept id, misconception)."""
        out: dict[str, tuple[str, Misconception]] = {}
        for c in self.concepts.values():
            for m in c.misconceptions:
                out[m.id] = (c.id, m)
        return out
