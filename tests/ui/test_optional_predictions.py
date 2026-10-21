"""Predictions never gate exploration or overwrite the live experiment."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tutor.models.loader import load_or_raise

LABS = [
    ('playground', 'foundation_playground', 'pg_scene', 'pgL', 'V', 8.0),
    ('wheatstone', 'wheatstone_lab', 'wb_scene', 'wb_sensor', 'p', 120),
    ('amplifiers', 'amplifier_lab', 'amp_scene', 'amp_problem', 'vd', 3.0),
    ('capacitive', 'capacitive_lab', 'cap_scene', 'cap_membrane', 'p', 2.0),
    ('noise', 'noise_lab', 'noise_scene', 'nz_noise', 'level', .1),
]
SCENES = [(page, scene.id) for page, lesson, *_ in LABS
          for scene in load_or_raise().lessons[lesson].scenes]


def _lab(name):
    import importlib
    from tutor.ui.components import layout
    layout.reset_box_counter()
    importlib.import_module(f'tutor.ui.pages.{name}').render()


@pytest.fixture(autouse=True)
def session_storage(monkeypatch):
    monkeypatch.setenv('TUTOR_STORAGE_MODE', 'session')
    monkeypatch.delenv('TUTOR_DEV', raising=False)


def run_lab(page, scene=None):
    at = AppTest.from_function(_lab, args=(page,), default_timeout=60)
    if scene:
        at.query_params['scene'] = scene
    at.run()
    assert not at.exception
    return at


def group(at, key):
    return next(g for g in at.get('button_group') if g.key == key)


def assert_interactive(at):
    widgets = [*at.slider, *at.toggle, *at.get('button_group')]
    controls = [w for w in widgets if w.key and w.key.startswith('w_')]
    assert all(not w.disabled for w in controls)
    copy = '\n'.join(m.value for m in at.markdown)
    for forbidden in ('locked until', 'controls unlock', 'Predict first', 'commit a prediction'):
        assert forbidden not in copy
    assert not any(b.label in ('Skip', 'Commit prediction') for b in at.button)
    assert not any(t.label == 'Animate diagrams' for t in at.toggle)
    assert not at.exception


@pytest.mark.parametrize('page,scene', SCENES)
def test_every_scene_is_interactive_without_prediction(page, scene):
    at = run_lab(page, scene)
    assert_interactive(at)
    assert at.session_state['_learner_repo'].predictions() == []
    for widget in at.slider:
        # Exercise actual control changes without ever choosing a prediction.
        new = widget.min if widget.value != widget.min else widget.max
        widget.set_value(new).run()
        assert not at.exception
        assert at.slider(key=widget.key).value == new
    assert at.session_state['_learner_repo'].predictions() == []


@pytest.mark.parametrize('page,lesson,scene_key,scope,cid,edited', LABS)
@pytest.mark.parametrize('answer_first', [True, False])
@pytest.mark.parametrize('correct', [True, False])
def test_prediction_order_recording_and_scene_mode_retention(
    page, lesson, scene_key, scope, cid, edited, answer_first, correct,
):
    at = run_lab(page)
    scene = load_or_raise().lessons[lesson].scenes[0]
    prediction = scene.predict
    choice = prediction.correct if correct else next(o.id for o in prediction.options if o.id != prediction.correct)
    key = f'w_{scope}_{cid}'
    assert_interactive(at)
    assert at.button(key=f'pred__{scope}__go').label == 'Check prediction'
    assert at.button(key=f'pred__{scope}__go').disabled  # choose an answer to check, never to explore
    if not answer_first:
        at.slider(key=key).set_value(edited).run()
    before = {s.key: s.value for s in [*at.slider, *at.toggle]}
    group(at, f'pred__{scope}__choice').set_value(choice).run()
    at.button(key=f'pred__{scope}__go').click().run()
    assert {s.key: s.value for s in [*at.slider, *at.toggle]} == before
    rows = at.session_state['_learner_repo'].predictions()
    assert len(rows) == 1
    assert rows[0][1:] == (f'{lesson}/{scope}', choice, prediction.correct)
    copy = '\n'.join(m.value for m in at.markdown)
    assert 'Expected in this scenario:' in copy
    assert 'observed' not in copy.lower()
    assert_interactive(at)
    at.slider(key=key).set_value(edited).run()
    for mode in ('course', 'exam', 'beginner'):
        group(at, 'mode_switch').set_value(mode).run()
        assert at.slider(key=key).value == edited
        assert at.session_state[f'pred__{scope}'] == choice
        assert_interactive(at)
    other = load_or_raise().lessons[lesson].scenes[1].id
    group(at, scene_key).set_value(other).run()
    assert_interactive(at)
    group(at, scene_key).set_value(scene.id).run()
    assert at.slider(key=key).value == edited
    assert at.session_state[f'pred__{scope}'] == choice
    assert len(at.session_state['_learner_repo'].predictions()) == 1
    # Reset is explicit and scene-local; returning again must keep the reset value.
    at.button(key=f'reset_{scope}').click().run()
    reset_value = at.slider(key=key).value
    assert reset_value != edited
    group(at, scene_key).set_value(other).run()
    group(at, scene_key).set_value(scene.id).run()
    assert at.slider(key=key).value == reset_value
    assert len(at.session_state['_learner_repo'].predictions()) == 1
    assert not at.exception


def test_no_unlock_api_or_prediction_dependency_remains():
    root = Path(__file__).resolve().parents[2] / 'src/tutor/ui'
    for relative in ['components/predict.py', 'pages/_lesson.py', *[f'pages/{p}.py' for p, *_ in LABS]]:
        source = (root / relative).read_text(encoding='utf-8')
        assert 'is_unlocked' not in source
        assert 'unlocked' not in source
        assert 'disabled=not' not in source


def test_old_skipped_state_is_an_unanswered_optional_prediction():
    at = AppTest.from_function(_lab, args=('playground',), default_timeout=60)
    at.session_state['pred__pgL'] = '__skipped'
    at.run()
    assert_interactive(at)
    assert at.button(key='pred__pgL__go').label == 'Check prediction'
    at.slider(key='w_pgL_V').set_value(9.).run()
    group(at, 'pred__pgL__choice').set_value('all').run()
    at.button(key='pred__pgL__go').click().run()
    assert at.slider(key='w_pgL_V').value == 9.
    assert len(at.session_state['_learner_repo'].predictions()) == 1
    assert not at.exception


@pytest.mark.parametrize('page,lesson,scene_key,scope,cid,edited', LABS)
def test_unanswered_experiment_survives_scene_and_mode_changes(page, lesson, scene_key, scope, cid, edited):
    at = run_lab(page)
    key = f'w_{scope}_{cid}'
    at.slider(key=key).set_value(edited).run()
    scenes = load_or_raise().lessons[lesson].scenes
    group(at, scene_key).set_value(scenes[1].id).run()
    group(at, scene_key).set_value(scenes[0].id).run()
    for mode in ('course', 'exam', 'beginner'):
        group(at, 'mode_switch').set_value(mode).run()
        assert at.slider(key=key).value == edited
        assert_interactive(at)
    assert at.session_state['_learner_repo'].predictions() == []
    assert at.button(key=f'pred__{scope}__go').label == 'Check prediction'
    # A new learner session starts with its own values and no predictions.
    fresh = run_lab(page)
    assert fresh.slider(key=key).value != edited
    assert fresh.session_state['_learner_repo'].predictions() == []
