"""Optional local exam date. The file is git-ignored and never required.

``local/schedule.yaml`` may contain ``exam: 2027-06-01``. Without that file the
app shows no countdown.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from tutor.paths import REPO_ROOT

SCHEDULE = REPO_ROOT / "local" / "schedule.yaml"


def exam_date(path: Path = SCHEDULE) -> date | None:
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = data.get("exam") if isinstance(data, dict) else None
    if raw is None:
        return None
    if isinstance(raw, date):
        return raw
    return date.fromisoformat(str(raw))
