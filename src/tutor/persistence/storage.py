"""Storage selection; callers own the repository, never a process-global cache."""

from __future__ import annotations

from pathlib import Path

from tutor.persistence.repo import Repo


def validate_mode(value: str) -> str:
    if value not in ("local", "session"):
        raise ValueError("TUTOR_STORAGE_MODE must be 'local' or 'session'.")
    return value


def create_repo(mode: str, local_path: Path) -> Repo:
    """Session repositories each get their own private SQLite connection in RAM.

    No shared file, connection name or URI is used. The connection and its data
    are released with the owning Streamlit session. Local mode keeps the usual
    persistent file, including TUTOR_DATA_DIR overrides supplied by paths.py.
    """
    validate_mode(mode)
    return Repo(":memory:" if mode == "session" else local_path)
