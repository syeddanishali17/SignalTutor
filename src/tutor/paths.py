"""Filesystem locations. Everything is resolved relative to the repository root."""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "content"
DATA_DIR = Path(os.environ.get("TUTOR_DATA_DIR", REPO_ROOT / "data"))
DB_PATH = DATA_DIR / "tutor.db"
