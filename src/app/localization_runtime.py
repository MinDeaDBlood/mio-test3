from __future__ import annotations

import inspect
import logging
import os
from collections.abc import Mapping
from typing import Any

from src.core.paths import prog_path


class LangUtils:
    """Runtime localization resolver with an explicit optional and visible text resolution policy.

    Policy:
    * current-language value wins when present and non-empty;
    * optional text uses the supplied default, normally ``''``;
    * visible/required UI text uses the reference language next;
    * if no reference value exists, visible/required UI text returns
      ``[missing:<key>]`` so the UI is diagnosable instead of silently blank.
    """

    REFERENCE_LANGUAGE = "English"
    _VISIBLE_CONTEXTS = {"ui", "visible", "required"}

    def __init__(self):
        self._translations = {}
        self._reference_translations = {}
        self._current_language = None
        self._language_file = None
        self._reference_language = self.REFERENCE_LANGUAGE
        self._reference_language_file = None
        self._missing_log_cache = set()

    @staticmethod
    def _is_valid(value):
        return (
            isinstance(value, str) and value.strip() and value.strip().lower() != "none"
        )

    def set_source(
        self, *, language_name: str | None = None, language_file: str | None = None
    ) -> None:
        self._current_language = str(language_name) if language_name else None
        self._language_file = str(language_file) if language_file else None
        self._missing_log_cache.clear()

    def set_reference_source(
        self, *, language_name: str | None = None, language_file: str | None = None
    ) -> None:
        self._reference_language = str(language_name or self.REFERENCE_LANGUAGE)
        self._reference_language_file = str(language_file) if language_file else None
        self._missing_log_cache.clear()

    def current_language(self) -> str | None:
        return self._current_language

    def current_language_file(self) -> str | None:
        return self._language_file

    def reference_language(self) -> str | None:
        return self._reference_language

    def reference_language_file(self) -> str | None:
        return self._reference_language_file

    def has(self, key: str) -> bool:
        return self._resolve_from_mapping(self._translations, key) is not None

    def has_reference(self, key: str) -> bool:
        return self._resolve_from_mapping(self._reference_translations, key) is not None

    def is_loaded(self) -> bool:
        return bool(self._translations)

    def _resolve_from_mapping(
        self, translations: Mapping[str, Any], *keys: str
    ) -> str | None:
        for key in keys:
            if not key:
                continue
            value = translations.get(key)
            if self._is_valid(value):
                return value
        return None

    def _candidate_debug_details(self, *keys: str) -> str:
        parts = []
        for key in keys:
            if not key:
                continue
            raw_value = self._translations.get(key, "<missing>")
            reference_value = self._reference_translations.get(key, "<missing>")
            parts.append(f"{key}={raw_value!r}/ref={reference_value!r}")
        return "; ".join(parts)

    @staticmethod
    def _format_caller(frame_info) -> tuple[str, str, int]:
        filename = frame_info.filename
        try:
            filename = os.path.relpath(filename, prog_path)
        except ValueError:
            ...
        return filename, frame_info.function, frame_info.lineno

    def _caller_context(self) -> tuple[str, str, int]:
        current_file = os.path.abspath(__file__)
        skip_files = {
            current_file,
            os.path.abspath(
                os.path.join(
                    os.path.dirname(current_file), "..", "app", "localization.py"
                )
            ),
            os.path.abspath(os.path.join(os.path.dirname(current_file), "utils.py")),
        }
        for frame_info in inspect.stack()[2:]:
            filename = os.path.abspath(frame_info.filename)
            if filename in skip_files:
                continue
            return self._format_caller(frame_info)
        return ("<unknown>", "<unknown>", 0)

    @staticmethod
    def missing_marker(key: str | None) -> str:
        return f"[missing:{key or 'localization'}]"

    def _log_missing(
        self,
        *keys: str,
        default: str,
        context: str,
        resolution: str,
        level: int | None = None,
    ) -> None:
        candidate_keys = tuple(key for key in keys if key)
        if not candidate_keys:
            return
        file_name, function_name, line_no = self._caller_context()
        cache_key = (
            self._current_language,
            self._language_file,
            self._reference_language,
            self._reference_language_file,
            file_name,
            function_name,
            line_no,
            candidate_keys,
            context,
            resolution,
        )
        if cache_key in self._missing_log_cache:
            return
        self._missing_log_cache.add(cache_key)
        log_level = (
            level
            if level is not None
            else (
                logging.ERROR
                if resolution == "marker" and context == "required"
                else logging.WARNING
            )
        )
        logging.log(
            log_level,
            "Localization missing key; default=%r; context=%s; resolution=%s; language=%s; language_file=%s; "
            "reference_language=%s; reference_file=%s; caller=%s:%s:%s; keys=%s; values=%s",
            default,
            context,
            resolution,
            self._current_language or "<unknown>",
            self._language_file or "<unknown>",
            self._reference_language or "<unknown>",
            self._reference_language_file or "<unknown>",
            file_name,
            function_name,
            line_no,
            ",".join(candidate_keys),
            self._candidate_debug_details(*candidate_keys),
        )

    def resolve(
        self,
        *keys: str,
        default: str = "",
        context: str = "optional",
        use_reference_language: bool | None = None,
    ) -> str:
        current_value = self._resolve_from_mapping(self._translations, *keys)
        if current_value is not None:
            return current_value

        use_reference = (
            use_reference_language
            if use_reference_language is not None
            else context in self._VISIBLE_CONTEXTS
        )
        if use_reference:
            reference_value = self._resolve_from_mapping(
                self._reference_translations, *keys
            )
            if reference_value is not None:
                self._log_missing(
                    *keys,
                    default=reference_value,
                    context=context,
                    resolution="reference",
                )
                return reference_value

        if context in self._VISIBLE_CONTEXTS:
            marker = self.missing_marker(next((key for key in keys if key), None))
            self._log_missing(
                *keys, default=marker, context=context, resolution="marker"
            )
            return marker

        self._log_missing(*keys, default=default, context=context, resolution="default")
        return default

    def resolve_optional(self, *keys: str, default: str = "") -> str:
        return self.resolve(
            *keys, default=default, context="optional", use_reference_language=False
        )

    def resolve_ui_text(self, *keys: str) -> str:
        return self.resolve(*keys, context="ui", use_reference_language=True)

    def resolve_required_ui_text(self, *keys: str) -> str:
        return self.resolve(*keys, context="required", use_reference_language=True)

    def __setattr__(self, key, value):
        if key in {
            "_translations",
            "_reference_translations",
            "_current_language",
            "_language_file",
            "_reference_language",
            "_reference_language_file",
            "_missing_log_cache",
        }:
            object.__setattr__(self, key, value)
            return
        self._translations[key] = value

    def clear(self):
        self._translations.clear()
        self._missing_log_cache.clear()

    def clear_reference(self):
        self._reference_translations.clear()
        self._missing_log_cache.clear()

    def load_map(self, translations):
        self.clear()
        self._translations.update(dict(translations or {}))

    def load_reference_map(
        self,
        translations,
        *,
        language_name: str | None = None,
        language_file: str | None = None,
    ):
        self.clear_reference()
        self._reference_translations.update(dict(translations or {}))
        self.set_reference_source(
            language_name=language_name, language_file=language_file
        )


lang = LangUtils()

__all__ = ["LangUtils", "lang"]
