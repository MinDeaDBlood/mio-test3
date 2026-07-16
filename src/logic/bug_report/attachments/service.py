from __future__ import annotations
import os


def existing_attachments(paths: list[str]) -> list[str]:
    return [p for p in paths if os.path.exists(p)]
