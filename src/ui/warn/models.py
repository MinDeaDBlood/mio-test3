from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class DialogRequest:
    text: str
    title: str = ''
    color: str = 'red'
    ok_text: Optional[str] = None
    cancel_text: Optional[str] = None

@dataclass(frozen=True)
class CrashContext:
    code: int
    description: str = 'unknown error'
