from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


import sys
from pathlib import Path

sys.path.insert(0, '.')

from src.app.localization import read_language_map
from src.app.help.error_helper.localized_rules import (
    error_helper_detail_key,
    error_helper_solution_key,
    load_error_helper_rules_from_language_map,
)
from src.logic.help.error_helper.service import get_error_helper_match


def test_error_helper_without_localization_does_not_match() -> None:
    assert get_error_helper_match('error text', threshold=80, rules=None) is None
    assert get_error_helper_match('error text', threshold=80, rules=()) is None


def test_error_helper_matches_patterns_from_localization_keys() -> None:
    translations = read_language_map('Russian', base_path=Path.cwd())

    rules = load_error_helper_rules_from_language_map(translations)
    result = get_error_helper_match(
        'error: ext4_allocate_best_fit_partial: failed to allocate xxx blocks, out of space?',
        threshold=80,
        rules=rules,
    )

    assert result is not None
    assert result.rule_id == 'ext4_size_too_small'
    assert error_helper_detail_key(result.rule_id) == 'error_helper_ext4_size_too_small_detail'
    assert error_helper_solution_key(result.rule_id) == 'error_helper_ext4_size_too_small_solution'


def test_error_helper_threshold_blocks_weak_matches() -> None:
    translations = read_language_map('English', base_path=Path.cwd())

    rules = load_error_helper_rules_from_language_map(translations)
    result = get_error_helper_match(
        'ordinary progress message with no known failure',
        threshold=95,
        rules=rules,
    )

    assert result is None

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
