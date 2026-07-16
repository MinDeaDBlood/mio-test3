from __future__ import annotations

import os
import shutil
from pathlib import Path

from src.core.process_runner import call


def is_git_available() -> bool:
    return shutil.which('git') is not None


def is_git_repository(path: str | Path) -> bool:
    return (Path(path) / ".git").is_dir()


def pull_repository(repository_dir: str | Path) -> None:
    if not is_git_available():
        raise FileNotFoundError('git executable was not found')
    repository_path = Path(repository_dir).resolve()
    if not repository_path.is_dir():
        raise FileNotFoundError(repository_path)
    previous_dir = Path.cwd()
    try:
        os.chdir(repository_path)
        return_code = call(['git', 'pull'], extra_path=False)
    finally:
        os.chdir(previous_dir)
    if return_code not in (0, None):
        raise RuntimeError(f'git pull failed with exit code {return_code}')


__all__ = ['is_git_available', 'is_git_repository', 'pull_repository']
