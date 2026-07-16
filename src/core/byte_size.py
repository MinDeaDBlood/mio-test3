from __future__ import annotations

_UNITS = ('B', 'KB', 'MB', 'GB', 'TB', 'PB')


def format_bytes(value: int | float) -> str:
    """Return a stable binary size string without depending on presentation code."""

    if not isinstance(value, (int, float)):
        raise TypeError(f'Byte size must be numeric, got {type(value).__name__}')
    amount = float(value)
    for unit in _UNITS:
        if abs(amount) < 1024.0:
            return f'{amount:.2f}{unit}'
        amount /= 1024.0
    return f'{amount:.2f}EB'


__all__ = ['format_bytes']
