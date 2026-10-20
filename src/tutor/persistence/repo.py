"""SQLite persistence (spec section 17), single local user.

A new connection per operation keeps this safe under Streamlit's threaded
script runs; SQLite handles the locking.

``attempts`` gains two columns over the spec schema, ``concept_id`` and
``skill``, so mastery can be derived without re-joining content files.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterator

from tutor.engine.mastery import Attempt
from tutor.engine.scheduler import ReviewItem

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    skill TEXT NOT NULL,
    correct INTEGER,
    checklist_json TEXT,
    duration_s REAL,
    mode TEXT NOT NULL DEFAULT 'practice'
);
CREATE INDEX IF NOT EXISTS attempts_concept ON attempts(concept_id);
CREATE TABLE IF NOT EXISTS review_queue (
    item_type TEXT NOT NULL,
    item_id TEXT NOT NULL,
    box INTEGER NOT NULL,
    due_date TEXT NOT NULL,
    PRIMARY KEY (item_type, item_id)
);
CREATE TABLE IF NOT EXISTS mastery (
    concept_id TEXT NOT NULL,
    skill TEXT NOT NULL,
    state TEXT NOT NULL,
    updated_ts TEXT NOT NULL,
    PRIMARY KEY (concept_id, skill)
);
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    lesson_id TEXT NOT NULL,
    prediction TEXT NOT NULL,
    actual TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


class Repo:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        if str(path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._memory_conn: sqlite3.Connection | None = None
        if str(path) == ":memory:":
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        if self._memory_conn is not None:
            yield self._memory_conn
            self._memory_conn.commit()
            return
        conn = sqlite3.connect(self.path, timeout=10)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # --- attempts --------------------------------------------------------------

    def record_attempt(self, a: Attempt) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO attempts (ts, item_type, item_id, concept_id, skill, correct, checklist_json, duration_s, mode)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    a.ts.isoformat(timespec="seconds"),
                    a.item_type,
                    a.item_id,
                    a.concept_id,
                    a.skill,
                    None if a.correct is None else int(a.correct),
                    json.dumps(a.checklist) if a.checklist else None,
                    a.duration_s,
                    a.mode,
                ),
            )
            return int(cur.lastrowid or 0)

    def attempts(self, concept_id: str | None = None) -> list[Attempt]:
        q = "SELECT ts, item_type, item_id, concept_id, skill, correct, checklist_json, duration_s, mode FROM attempts"
        args: tuple = ()
        if concept_id:
            q += " WHERE concept_id = ?"
            args = (concept_id,)
        q += " ORDER BY ts, id"
        with self._conn() as c:
            rows = c.execute(q, args).fetchall()
        return [
            Attempt(
                ts=datetime.fromisoformat(r[0]),
                item_type=r[1],
                item_id=r[2],
                concept_id=r[3],
                skill=r[4],
                correct=None if r[5] is None else bool(r[5]),
                checklist=json.loads(r[6]) if r[6] else {},
                duration_s=r[7],
                mode=r[8],
            )
            for r in rows
        ]

    def attempt_count(self) -> int:
        with self._conn() as c:
            return int(c.execute("SELECT COUNT(*) FROM attempts").fetchone()[0])

    # --- review queue -------------------------------------------------------------

    def review_items(self) -> list[ReviewItem]:
        with self._conn() as c:
            rows = c.execute("SELECT item_type, item_id, box, due_date FROM review_queue").fetchall()
        return [ReviewItem(r[0], r[1], int(r[2]), date.fromisoformat(r[3])) for r in rows]

    def review_item(self, item_type: str, item_id: str) -> ReviewItem | None:
        with self._conn() as c:
            r = c.execute(
                "SELECT item_type, item_id, box, due_date FROM review_queue WHERE item_type=? AND item_id=?",
                (item_type, item_id),
            ).fetchone()
        return ReviewItem(r[0], r[1], int(r[2]), date.fromisoformat(r[3])) if r else None

    def upsert_review(self, item: ReviewItem) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO review_queue (item_type, item_id, box, due_date) VALUES (?, ?, ?, ?)"
                " ON CONFLICT(item_type, item_id) DO UPDATE SET box=excluded.box, due_date=excluded.due_date",
                (item.item_type, item.item_id, item.box, item.due.isoformat()),
            )

    # --- mastery cache ---------------------------------------------------------------

    def cache_mastery(self, states: dict[str, dict[str, str]], now: datetime) -> None:
        with self._conn() as c:
            for cid, skills in states.items():
                for skill, state in skills.items():
                    c.execute(
                        "INSERT INTO mastery (concept_id, skill, state, updated_ts) VALUES (?, ?, ?, ?)"
                        " ON CONFLICT(concept_id, skill) DO UPDATE SET state=excluded.state, updated_ts=excluded.updated_ts",
                        (cid, skill, state, now.isoformat(timespec="seconds")),
                    )

    # --- predictions -------------------------------------------------------------------

    def record_prediction(self, lesson_id: str, prediction: str, actual: str, ts: datetime) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO predictions (ts, lesson_id, prediction, actual) VALUES (?, ?, ?, ?)",
                (ts.isoformat(timespec="seconds"), lesson_id, prediction, actual),
            )

    def predictions(self) -> list[tuple[str, str, str, str]]:
        with self._conn() as c:
            return [tuple(r) for r in c.execute("SELECT ts, lesson_id, prediction, actual FROM predictions ORDER BY id")]

    # --- settings -------------------------------------------------------------------------

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        with self._conn() as c:
            r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r[0] if r else default

    def set_setting(self, key: str, value: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
