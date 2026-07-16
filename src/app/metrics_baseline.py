"""Metric baselines for startup and lazy feature-open paths.

These budgets are intentionally conservative. They are not hard real-time
assertions, but they provide a concrete regression reference for logs, manual
review and CI smoke environments.
"""

from __future__ import annotations

METRIC_BASELINES: dict[str, float] = {
    'startup.total': 8.0,
    'project_workspace_open': 3.0,
    'plugin_manager_open': 2.5,
    'plugin_store_open': 3.5,
}


def metric_budget(label: str) -> float | None:
    return METRIC_BASELINES.get(label)


__all__ = ['METRIC_BASELINES', 'metric_budget']
