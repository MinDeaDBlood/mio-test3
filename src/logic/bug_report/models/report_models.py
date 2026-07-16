from dataclasses import dataclass


@dataclass(frozen=True)
class BugReportMeta:
    title: str
    include_log: bool = True
