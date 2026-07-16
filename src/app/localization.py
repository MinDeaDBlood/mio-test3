from __future__ import annotations

import inspect
import logging
from pathlib import Path
from src.app.localization_runtime import lang
from src.core.paths import prog_path
from src.platform.language_repository import language_file_path, read_language_map


def _require_language_name(language_name: str | None = None) -> str:
    resolved = str(language_name or lang.current_language() or "").strip()
    if not resolved:
        raise RuntimeError("Localization language is not initialized")
    return resolved


def _caller_context() -> str:
    current_file = Path(__file__).resolve()
    for frame_info in inspect.stack()[2:]:
        filename = Path(frame_info.filename).resolve()
        if filename == current_file:
            continue
        try:
            display_name = filename.relative_to(Path(prog_path).resolve()).as_posix()
        except Exception:
            display_name = str(filename)
        return f"{display_name}:{frame_info.function}:{frame_info.lineno}"
    return "<unknown>"


def load_language_from_files(
    language_name: str | None = None, *, base_path: str | Path | None = None
) -> str:
    resolved_name = _require_language_name(language_name)
    lang_file = language_file_path(resolved_name, base_path=base_path)
    translations = read_language_map(resolved_name, base_path=base_path)
    lang.set_source(language_name=resolved_name, language_file=str(lang_file))
    lang.load_map(translations)
    try:
        reference_file = language_file_path(
            lang.REFERENCE_LANGUAGE, base_path=base_path
        )
        reference_translations = read_language_map(
            lang.REFERENCE_LANGUAGE, base_path=base_path
        )
        lang.load_reference_map(
            reference_translations,
            language_name=lang.REFERENCE_LANGUAGE,
            language_file=str(reference_file),
        )
    except Exception as exc:
        lang.clear_reference()
        lang.set_reference_source(
            language_name=lang.REFERENCE_LANGUAGE, language_file=None
        )
        logging.warning(
            "Reference language map could not be loaded: language=%s; base_path=%s; error=%s; caller=%s",
            lang.REFERENCE_LANGUAGE,
            base_path or prog_path,
            exc,
            _caller_context(),
        )
    logging.info(
        "Loaded language map: language=%s; file=%s; keys=%d; caller=%s",
        resolved_name,
        lang_file,
        len(translations),
        _caller_context(),
    )
    return resolved_name


def ensure_selected_language_loaded(
    *required_keys: str, base_path: str | Path | None = None
) -> str:
    current_language = _require_language_name()
    if required_keys and all(lang.has(key) for key in required_keys):
        return current_language
    if not required_keys and lang.is_loaded():
        return current_language
    resolved_name = load_language_from_files(current_language, base_path=base_path)
    if required_keys:
        missing_keys = [key for key in required_keys if not lang.has(key)]
        if missing_keys:
            logging.warning(
                "Language map loaded but required keys are still missing/invalid: language=%s; file=%s; caller=%s; keys=%s",
                resolved_name,
                language_file_path(resolved_name, base_path=base_path),
                _caller_context(),
                ",".join(missing_keys),
            )
    return resolved_name


__all__ = [
    "ensure_selected_language_loaded",
    "language_file_path",
    "load_language_from_files",
    "read_language_map",
]
