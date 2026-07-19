#!/usr/bin/env python3
from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import argparse
import os
from pathlib import Path


from src.app.metrics_baseline import METRIC_BASELINES
from src.platform.metrics_repository import load_metric_observations

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED = tuple(METRIC_BASELINES.keys())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Validate collected runtime metric observations.')
    arguments = (
        _direct_sys.argv[1:]
        if argv is None and __name__ == "__main__"
        else (argv or [])
    )
    parser.parse_args(arguments)
    metric_file = os.environ.get("MIO_METRIC_OBSERVATIONS_FILE", "").strip()
    if not metric_file:
        raise SystemExit("MIO_METRIC_OBSERVATIONS_FILE is not set")
    observations = load_metric_observations(metric_file)
    if not observations:
        raise SystemExit("No metric observations were recorded")
    maxima: dict[str, float] = {}
    for entry in observations:
        label = str(entry.get("label", ""))
        try:
            elapsed = float(entry.get("elapsed", 0.0))
        except Exception:
            continue
        maxima[label] = max(elapsed, maxima.get(label, 0.0))
    missing = [label for label in REQUIRED if label not in maxima]
    if missing:
        raise SystemExit("METRIC_OBSERVATIONS_MISSING: " + ", ".join(missing))
    over_budget = []
    for label, budget in METRIC_BASELINES.items():
        observed = maxima.get(label)
        if observed is None:
            continue
        if observed > budget:
            over_budget.append(f"{label}={observed:.3f}s>{budget:.3f}s")
    if over_budget:
        raise SystemExit("Metric budgets exceeded: " + ", ".join(over_budget))
    print("METRIC_OBSERVATIONS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
