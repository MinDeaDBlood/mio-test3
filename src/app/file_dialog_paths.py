from __future__ import annotations

import os

from src.platform.filesystem import is_directory, is_file
from dataclasses import dataclass
from enum import Enum


class DialogTargetKind(str, Enum):
    NONE = "none"
    NAVIGATE = "navigate"
    SELECT = "select"


@dataclass(frozen=True, slots=True)
class DialogTarget:
    kind: DialogTargetKind
    path: str = ""


def initial_directory() -> str:
    return os.path.abspath(os.getcwd())


def resolve_file_activation(current_directory: str, selected_name: str) -> DialogTarget:
    name = str(selected_name or "").strip()
    if not name:
        return DialogTarget(DialogTargetKind.NONE)
    target = os.path.abspath(os.path.join(current_directory, name))
    if name == "..":
        target = os.path.dirname(os.path.abspath(current_directory))
    if is_directory(target):
        return DialogTarget(DialogTargetKind.NAVIGATE, target)
    if is_file(target):
        return DialogTarget(DialogTargetKind.SELECT, target)
    return DialogTarget(DialogTargetKind.NONE)


def resolve_directory_activation(
    current_directory: str, selected_name: str
) -> DialogTarget:
    result = resolve_file_activation(current_directory, selected_name)
    if result.kind is DialogTargetKind.SELECT:
        return DialogTarget(DialogTargetKind.NONE)
    return result


def accept_file_target(current_directory: str, selected_name: str) -> str:
    result = resolve_file_activation(current_directory, selected_name)
    return result.path if result.kind is DialogTargetKind.SELECT else ""


def accept_directory_target(current_directory: str, selected_name: str) -> str:
    name = str(selected_name or "").strip()
    if name and name != "..":
        target = os.path.abspath(os.path.join(current_directory, name))
    else:
        target = os.path.abspath(current_directory)
    return target if is_directory(target) else ""


__all__ = [
    "DialogTarget",
    "DialogTargetKind",
    "accept_directory_target",
    "accept_file_target",
    "initial_directory",
    "resolve_directory_activation",
    "resolve_file_activation",
]
