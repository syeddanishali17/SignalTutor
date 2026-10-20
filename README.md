# Sensor Tutor

A visual, interactive tutor for a modern sensor technologies course, built for a learner with **no electrical-engineering background** who has to explain, draw, derive and defend the material in an oral whiteboard exam.

Every lesson follows the same loop: **predict → observe → name → derive → break it → check → explain it**, with a circuit picture, an inspector, controls, an equation strip and a plot that are all driven by the same simulation state.

## Run it

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -e ".[dev]"
.venv/Scripts/streamlit run app.py
```

Learner data (attempts, review queue, settings) is stored locally in `data/tutor.db` (git-ignored).

## Check it

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python scripts/validate_content.py
```

* `pytest` — reference values and property tests for every simulation, grading, scheduling and mastery rules, SymPy checks of every derivation step, and headless smoke tests of every page and scene.
* `validate_content.py` — concept graph (no cycles, no dangling prerequisites), dimension checks of every formula, symbol/term references, typography rules (no YAML escape traps such as `"\text"` → TAB, balanced `$…$`), and the rule that a *needs review* formula is never shown without its flag.
* `scripts/qa_screenshots.py` — full-page screenshots at laptop and tablet widths (needs the app running with `TUTOR_DEV=1`).

## What is in it

| Area | Content |
|---|---|
| Foundation Playground | closed loop & current, voltage as a difference, Ohm's law (with fractions), divider, ground, KCL, reading a circuit |
| Wheatstone Bridge Lab | pressure → strain → ΔR (membrane), two dividers → bridge, quarter bridge (exact vs approximate), full bridge, temperature drift, loading by a real meter, SymPy-checked derivations |
| Amplifier Lab | mains interference & common mode, the op-amp as a black box, negative feedback and the virtual short, non-inverting amplifier, difference amplifier, instrumentation amplifier |
| Practice | auto-graded problems with units and misconception diagnosis, spaced review (1/3/7/14/30 days), oral drills with examiner follow-ups, paper-first whiteboard drills |
| Reference | progress (rule-based mastery states), glossary with a concept map, sources & known issues (every deviation from the lecture notes, never silently corrected) |

## Layout

```
app.py                     st.navigation router
content/                   concepts (+ .md prose), symbols, formulas, known issues,
                           problems, derivations, oral/whiteboard, lessons  (YAML)
src/tutor/sim/             circuit and sensor models (pure Python)
src/tutor/engine/          concept graph, safe expression parser, dimension checks,
                           grading, problems, oral trees, Leitner scheduler, mastery
src/tutor/models/          pydantic schemas + loader
src/tutor/persistence/     SQLite repository
src/tutor/ui/              Streamlit pages, components, SVG figure builders
scripts/                   content validation, screenshot QA
tests/                     sim / engine / content / ui
```

## Visual rules (apply to every module)

* Maths is always typeset LaTeX; fractions are stacked; numerators and denominators are labelled in Beginner mode the first time they matter.
* In circuit drawings a component's **name** (bold, real subscripts) and its **value** (separate tag) are never merged.
* A selection — a part of the picture or a symbol in the equation — lights up the part, its control and its term together.
* Semantics never rely on colour alone (arrows, + / − badges, line styles, labels); a legend explains every icon.

Lecture-derived content is for personal study. Keep the repository private.
