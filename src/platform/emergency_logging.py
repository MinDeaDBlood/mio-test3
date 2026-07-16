"""Last resort traceback writer used when normal logging cannot initialize."""

from __future__ import annotations

import os
from pathlib import Path
import time
import traceback


def write_emergency_fallback(
    project_root: str | os.PathLike[str],
    *,
    phase: str,
    exception: BaseException,
) -> Path | None:
    try:
        root = Path(project_root).expanduser().resolve()
        log_dir = root / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        fallback_path = log_dir / 'mio_emergency_startup.log'
        with fallback_path.open('a', encoding='utf-8') as stream:
            stream.write('\n')
            stream.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] phase={phase}\n')
            traceback.print_exception(
                type(exception),
                exception,
                exception.__traceback__,
                file=stream,
            )
            stream.flush()
        return fallback_path
    except Exception:
        return None


__all__ = ['write_emergency_fallback']
