from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_METRIC_FILE_ENV = "MIO_METRIC_OBSERVATIONS_FILE"


def metric_observations_path() -> Path | None:
    raw = os.environ.get(_METRIC_FILE_ENV, "").strip()
    if not raw:
        return None
    return Path(raw)


def reset_metric_observations_file() -> Path | None:
    path = metric_observations_path()
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return path


def record_metric_observation(
    label: str,
    elapsed: float,
    *,
    budget: float | None = None,
    within_budget: bool | None = None,
) -> None:
    path = metric_observations_path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "label": label,
        "elapsed": float(elapsed),
        "budget": None if budget is None else float(budget),
        "within_budget": within_budget,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_metric_observations(path: str | Path) -> list[dict[str, Any]]:
    resolved = Path(path)
    if not resolved.exists():
        return []
    observations: list[dict[str, Any]] = []
    with resolved.open("r", encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            observations.append(json.loads(raw))
    return observations


__all__ = [
    "load_metric_observations",
    "metric_observations_path",
    "record_metric_observation",
    "reset_metric_observations_file",
]
