# Signal Tutor

Signal Tutor is an interactive learning application for building intuition in sensor electronics, signal conditioning, circuit fundamentals, and oral technical explanation.

Every lesson follows the same loop: **predict → observe → name → derive → break it → check → explain it**, with a circuit picture, an inspector, controls, an equation strip and a plot that are all driven by the same simulation state.

Signal Tutor is an independent educational project created by Danish. It is not affiliated with, endorsed by, or an official product of any university or educational institution.

## Run it

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -e ".[dev]"
.venv/Scripts/streamlit run app.py
```

Learner data (attempts, review queue, settings) is stored locally in `data/tutor.db` (git-ignored). An optional `local/schedule.yaml` with `exam: YYYY-MM-DD` shows a personal countdown on Today. That file is git-ignored.

## Streamlit Community Cloud

Deploy manually from `syeddanishali17/SignalTutor`, branch `main`, entrypoint
`app.py`. In **Advanced settings**, choose **Python 3.12** and enter this in
**Secrets** (required for public multi-user use):

```toml
TUTOR_STORAGE_MODE = "session"
```

The root `requirements.txt` pins production dependencies; `pyproject.toml`
remains the local development configuration. No external service or database
credentials are required. Leave `TUTOR_DEV` unset for public use.

In session mode, each Streamlit session owns a separate in-memory SQLite
repository in `st.session_state`. Attempts, mastery, review queues, predictions,
settings and teaching mode are isolated. There is no globally cached learner
repository and no learner data is written to `data/tutor.db`. Only read-only
teaching content and its concept graph use the shared resource cache.

Session progress is temporary: a new session (including a reload that resets
the connection) or an instance restart can clear it. Cloud filesystem storage
is not treated as durable. The private local schedule is ignored in session
mode, and deployment needs no schedule file. Today and Progress explain the
temporary session lifetime to learners.

For local testing, set the environment variable `TUTOR_STORAGE_MODE=session`
before running Streamlit, or use the same setting in a git-ignored
`.streamlit/secrets.toml`. An explicit environment variable takes precedence.
Without either setting, `local` mode retains persistent `data/tutor.db`
(or `TUTOR_DATA_DIR/tutor.db`). Invalid mode values stop with an error. Storage
mode is fixed for each session; restart the app after changing configuration.

The optional `?for=lara` link shows “You can do this, Lara.” as a short,
non-blocking toast on Today. Other query values do not enable it.

Deployment controls: [Streamlit deployment settings](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
and [Secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Check it

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python scripts/validate_content.py
```

* `pytest` — reference values and property tests for every simulation, grading, scheduling and mastery rules, SymPy checks of every derivation step, and headless smoke tests of every page and scene.
* `validate_content.py` — concept graph (no cycles, no dangling prerequisites), dimension checks of every formula, symbol/term references, typography rules (balanced `$…$`, no dash sitting against inline math), and the rule that a *needs review* formula is never shown without its flag.

## What is in it

* Beginner electrical foundations: current, voltage, Ohm's law, dividers, ground, KCL, reading a circuit
* Wheatstone bridges: strain, quarter and full bridges, temperature drift, meter loading, checked derivations
* Op-amps and feedback, including the virtual short
* Difference and instrumentation amplifiers
* Capacitive sensors, nonlinear behaviour and pull-in
* Noise and power spectral density, including one-sided and two-sided conventions
* Practice problems with units and misconception notes
* Oral and whiteboard practice, including a 15-minute two-topic mock oral
* Spaced review (1/3/7/14/30 days) and rule-based mastery tracking

## What is not in it yet

* Later topics such as lock-in detection. The `course_l03` track is empty.
* The sensor-map stages ADC, processing and communication have no lessons.
* Known issues K1–K10 stay **open**. Dimension checks do not close them, and nothing here claims an official source has been compared.
* There is no printable one-pager export. The creator line (`Signal Tutor · Built by Danish`) is shared by the footer and the home page.

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
scripts/                   content validation
tests/                     sim / engine / content / ui
```

Formula status means:

* **verified** — the expression is consistent and passes the dimension or algebra checks in this app
* **needs review** — a written form still looks doubtful; it is shown with a flag
* **supplemental** — a standard relation added as explanation

## Visual rules

* Maths is typeset LaTeX. A full equation that introduces an explanation is drawn on its own line, so punctuation cannot be read as a minus.
* In circuit drawings a component's **name** and its **value** stay separate.
* A selection lights up the part, its control and its symbol together.
* The sensor-system map keeps every stage readable. The current stage is accented; later stages use a lighter border only.
