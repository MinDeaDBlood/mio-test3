"""Optional pro-feature runtime flags.

This boundary keeps optional imports out of unrelated modules and exposes a
stable contract for code that needs to branch on pro availability.
"""

from __future__ import annotations

is_pro = False
try:
    from src.pro.sn import v as verify

    is_pro = True
except ImportError:
    verify = None
    is_pro = False

__all__ = ['is_pro', 'verify']
