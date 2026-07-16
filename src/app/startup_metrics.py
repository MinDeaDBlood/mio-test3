from __future__ import annotations

import logging
from dataclasses import dataclass, field
from timeit import default_timer as dti

from src.app.metrics_baseline import metric_budget
from src.platform.metrics_repository import record_metric_observation


def _budget_status(label: str, elapsed: float) -> tuple[float | None, bool]:
    budget = metric_budget(label)
    return budget, (budget is None or elapsed <= budget)


@dataclass(frozen=True)
class StartupMark:
    label: str
    timestamp: float
    excluded_from_total: bool = False


@dataclass
class StartupTimeline:
    start_time: float = field(default_factory=dti)
    marks: list[StartupMark] = field(default_factory=list)

    def mark(self, label: str, *, excluded_from_total: bool = False) -> None:
        self.marks.append(StartupMark(label, dti(), excluded_from_total))

    def _stage_durations(self) -> list[tuple[StartupMark, float]]:
        durations: list[tuple[StartupMark, float]] = []
        previous = self.start_time
        for mark in self.marks:
            durations.append((mark, mark.timestamp - previous))
            previous = mark.timestamp
        return durations

    def elapsed_wall_total(self) -> float:
        if not self.marks:
            return 0.0
        return self.marks[-1].timestamp - self.start_time

    def elapsed_total(self) -> float:
        return sum(
            duration
            for mark, duration in self._stage_durations()
            if not mark.excluded_from_total
        )

    def _slowest_stages(self, *, limit: int = 3) -> list[tuple[str, float]]:
        durations = [
            (mark.label, duration)
            for mark, duration in self._stage_durations()
            if not mark.excluded_from_total
        ]
        durations.sort(key=lambda item: item[1], reverse=True)
        return durations[:limit]

    def summary(self) -> str:
        if not self.marks:
            return "startup: no marks"
        parts: list[str] = []
        for mark, duration in self._stage_durations():
            suffix = "[excluded]" if mark.excluded_from_total else ""
            parts.append(f"{mark.label}={duration:.3f}s{suffix}")
        total = self.elapsed_total()
        budget, within_budget = _budget_status("startup.total", total)
        if budget is None:
            parts.append(f"total={total:.3f}s")
        else:
            state = "within-budget" if within_budget else "OVER-BUDGET"
            parts.append(f"total={total:.3f}s/{budget:.3f}s[{state}]")
        parts.append(f"wall_total={self.elapsed_wall_total():.3f}s")
        return "startup: " + ", ".join(parts)

    def log(self, *, logger=logging) -> None:
        total = self.elapsed_total()
        budget, within_budget = _budget_status("startup.total", total)
        logger.info(self.summary())
        record_metric_observation(
            "startup.total", total, budget=budget, within_budget=within_budget
        )
        record_metric_observation("startup.wall_total", self.elapsed_wall_total())
        if budget is not None and not within_budget:
            slowest = ", ".join(
                f"{label}={duration:.3f}s"
                for label, duration in self._slowest_stages(limit=3)
            )
            logger.warning(
                "startup.total exceeded budget: %.3fs > %.3fs; slowest stages: %s",
                total,
                budget,
                slowest,
            )


@dataclass
class FeatureTimeline:
    label: str
    start_time: float = field(default_factory=dti)

    def elapsed(self) -> float:
        return dti() - self.start_time

    def summary(self) -> str:
        elapsed = self.elapsed()
        budget, within_budget = _budget_status(self.label, elapsed)
        if budget is None:
            return f"{self.label}: {elapsed:.3f}s"
        state = "within-budget" if within_budget else "OVER-BUDGET"
        return f"{self.label}: {elapsed:.3f}s/{budget:.3f}s[{state}]"

    def log(self, *, logger=logging) -> None:
        elapsed = self.elapsed()
        budget, within_budget = _budget_status(self.label, elapsed)
        logger.info(self.summary())
        record_metric_observation(
            self.label, elapsed, budget=budget, within_budget=within_budget
        )
        if budget is not None and not within_budget:
            logger.warning(
                "%s exceeded budget: %.3fs > %.3fs", self.label, elapsed, budget
            )


__all__ = ["FeatureTimeline", "StartupMark", "StartupTimeline"]
