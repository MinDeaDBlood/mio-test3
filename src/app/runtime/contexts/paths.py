from __future__ import annotations


def resolve_temp_path(temp_path: str | None = None) -> str:
    if temp_path is not None:
        return str(temp_path)
    from src.app.runtime.defaults_access import require_temp_path
    return require_temp_path()


def resolve_log_dir(log_dir: str | None = None) -> str:
    if log_dir is not None:
        return str(log_dir)
    from src.app.runtime.defaults_access import require_log_dir
    return require_log_dir()


def resolve_prog_path(prog_path: str | None = None) -> str:
    if prog_path is not None:
        return str(prog_path)
    from src.app.runtime.defaults_access import require_prog_path
    return require_prog_path()


__all__ = ['resolve_log_dir', 'resolve_prog_path', 'resolve_temp_path']
