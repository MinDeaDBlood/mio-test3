from __future__ import annotations

import os
import platform
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from src.core.archive_ops import write_zip_entries


@dataclass(frozen=True)
class BugReportRequest:
    output_dir: str
    tool_log: str
    version_code: str
    tool_version: str
    run_source: str
    settings: Mapping[str, str]


def normalize_output_dir(output: str | None) -> str | None:
    candidate = str(output or "").strip()
    if not candidate:
        return None
    if not os.path.isdir(candidate):
        return None
    return candidate


def build_bug_report_details(request: BugReportRequest) -> str:
    lines = [
        "----BasicInfo-----",
        f"Python: {sys.version}",
        f"Platform: {sys.platform}",
        f"Exec Command: {sys.argv}",
        f"Tool Version: {request.tool_version}",
        f"Source code running: {request.run_source}",
        f"python Implementation: {platform.python_implementation()}",
        f"Uname: {platform.uname()}",
        "----Settings-------",
    ]
    lines.extend(
        f"\t{name}={value}" for name, value in sorted(request.settings.items())
    )
    return "\n".join(lines) + "\n"


def generate_bug_report(request: BugReportRequest) -> str:
    filename = (
        f"Mio_Bug_Report{time.strftime('%Y%m%d_%H-%M-%S', time.localtime())}_"
        f"{request.version_code}.zip"
    )
    bugreport = Path(request.output_dir) / filename
    write_zip_entries(
        bugreport,
        text_entries={"detail.txt": build_bug_report_details(request)},
        file_entries={Path(request.tool_log).name: request.tool_log},
    )
    return str(bugreport)


__all__ = [
    "BugReportRequest",
    "build_bug_report_details",
    "generate_bug_report",
    "normalize_output_dir",
]
