from __future__ import annotations


class CoreOperationError(RuntimeError):
    """A recoverable failure raised by a low level core operation."""

    def __init__(self, message: str, *, exit_code: int | str | None = None):
        super().__init__(message)
        self.exit_code = exit_code


__all__ = ['CoreOperationError']
