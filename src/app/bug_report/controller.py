from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from src.logic.bug_report.service.service import (
    BugReportRequest,
    generate_bug_report,
    normalize_output_dir,
)

WorkerStarter = Callable[[Callable[[], str]], object]


@dataclass(frozen=True, slots=True)
class BugReportApplicationContext:
    tool_log: str
    version_code: str
    tool_version: str
    run_source: str
    settings: dict[str, str]


@dataclass(frozen=True)
class BugReportController:
    context: BugReportApplicationContext
    choose_output: Callable[[], str | None]
    start_worker: WorkerStarter
    logger: object = logging

    def request_generation(
        self, on_complete: Callable[[str], object] | None = None
    ) -> object | None:
        output_dir = normalize_output_dir(self.choose_output())
        if output_dir is None:
            return None

        request = BugReportRequest(
            output_dir=output_dir,
            tool_log=self.context.tool_log,
            version_code=self.context.version_code,
            tool_version=self.context.tool_version,
            run_source=self.context.run_source,
            settings=self.context.settings,
        )

        def worker() -> str:
            result = generate_bug_report(request)
            if on_complete is not None:
                on_complete(result)
            return result

        try:
            return self.start_worker(worker)
        except (OSError, RuntimeError, TypeError, ValueError):
            self.logger.exception("BugReportController.request_generation failed")
            raise


__all__ = ["BugReportApplicationContext", "BugReportController", "WorkerStarter"]
