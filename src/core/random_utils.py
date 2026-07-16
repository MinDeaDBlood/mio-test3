from __future__ import annotations

from random import choice, randint


def v_code(num=6) -> str:
    """Return a short pseudo-random mixed letter/digit code."""
    ret = ""
    for i in range(num):
        number = randint(0, i)
        letter = chr(randint(97, 122))
        letter_upper = chr(randint(65, 90))
        ret += str(choice([number, letter, letter_upper]))
    return ret


__all__ = ['v_code']
