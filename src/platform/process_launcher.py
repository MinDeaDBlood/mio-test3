from __future__ import annotations

import logging
import subprocess
import time
from collections.abc import Mapping, Sequence

from src.platform.operation_logging import operation_context

logger = logging.getLogger(__name__)


def launch_detached(
    command: str | Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
) -> subprocess.Popen:
    """Launch one external process without attaching application output streams."""
    argv = [command] if isinstance(command, str) else list(command)
    if not argv:
        raise ValueError("Launch command is empty")
    process_environment = dict(env) if env is not None else None
    started = time.perf_counter()
    with operation_context("process.launch_detached", command=argv):
        logger.info(
            "process.detached_start: command=%r custom_environment=%s",
            argv,
            process_environment is not None,
        )
        process = subprocess.Popen(
            argv,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=process_environment,
        )
        logger.info(
            "process.detached_started: pid=%s duration=%.3fs command=%r",
            process.pid,
            time.perf_counter() - started,
            argv,
        )
        return process


__all__ = ["launch_detached"]
