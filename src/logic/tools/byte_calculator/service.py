from __future__ import annotations

UNITS = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4, 'PB': 1024**5}


def _looks_like_partial_number(text: str) -> bool:
    if text in {'', '.', '-', '-.'}:
        return True
    if text.count('.') > 1:
        return False
    if text.startswith('-'):
        text = text[1:]
    return all(ch.isdigit() or ch == '.' for ch in text)


def parse_number(text: str) -> float | None:
    stripped = text.strip()
    if _looks_like_partial_number(stripped):
        try:
            return float(stripped)
        except ValueError:
            return None
    try:
        return float(stripped)
    except ValueError:
        return None


def format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f'{value:.6f}'.rstrip('0').rstrip('.')


def convert(value: float, from_unit: str, to_unit: str) -> float:
    return (float(value) * UNITS[from_unit]) / UNITS[to_unit]


def convert_text(text: str, from_unit: str, to_unit: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ''
    number = parse_number(stripped)
    if number is None:
        return '' if _looks_like_partial_number(stripped) else 'Invalid'
    if from_unit == to_unit:
        return format_number(number)
    return format_number(convert(number, from_unit, to_unit))
