from __future__ import annotations

import logging
from functools import lru_cache
from tkinter import Text

from src.app.localization import read_language_map
from src.app.localization_runtime import lang
from src.app.composition import log_stream_keys as keys
from src.app.runtime.contexts.settings import resolve_settings
from src.app.std_streams import attach_stream_sink
from src.app.ui_events import UiCoalescedDrain
from src.app.ui_feedback import build_ui_dispatcher
from src.app.log_interface.stdout_redirect_controller import StdoutRedirectController
from src.app.help.error_helper.localized_rules import (
    error_helper_detail_key,
    error_helper_solution_key,
    load_error_helper_rules_from_language_map,
)
from src.logic.help.error_helper.service import get_error_helper_match
from src.ui.common.dialogs.error_helper import show_error_helper
from src.ui.log_interface.stream_sink import StdoutRedirector


def _error_helper_threshold(settings) -> int:
    try:
        return int(round(float(settings.error_helper_confidence)))
    except (TypeError, ValueError):
        return 80


@lru_cache(maxsize=8)
def _load_error_helper_rules(language_name: str) -> tuple:
    try:
        translations = read_language_map(language_name)
    except Exception:
        logging.exception(
            "error_helper localization map could not be loaded: language=%s",
            language_name,
        )
        return ()
    return load_error_helper_rules_from_language_map(translations)


def _suggest_chunks(controller: StdoutRedirectController, chunks: list[str]) -> None:
    settings = resolve_settings()
    if settings.error_helper_enabled != "1":
        return
    threshold = _error_helper_threshold(settings)
    language_name = str(
        lang.current_language() or settings.language or ""
    ).strip()
    if not language_name:
        return
    rules = _load_error_helper_rules(language_name)
    if not rules:
        return
    for chunk in chunks:
        match = get_error_helper_match(chunk, threshold=threshold, rules=rules)
        if match is None:
            continue
        show_error_helper(
            texts=lang,
            source_text=match.source_text,
            detail=lang.resolve_required_ui_text(
                error_helper_detail_key(match.rule_id)
            ),
            solution=lang.resolve_required_ui_text(
                error_helper_solution_key(match.rule_id)
            ),
            confidence=match.confidence,
            ok_text=lang.resolve_required_ui_text(keys.ERROR_HELPER_OK_BUTTON),
        )


def create_stdout_redirector(
    text_widget: Text,
    *,
    error_mode: bool = False,
    error_popup=None,
    stdout: bool = False,
    stderr: bool = False,
) -> StdoutRedirector:
    controller = StdoutRedirectController(error_mode=error_mode, logger=logging)
    sink = StdoutRedirector(
        text_widget,
        controller=controller,
        suggest_chunks=lambda chunks: _suggest_chunks(controller, chunks),
        error_popup=error_popup,
    )
    dispatcher = build_ui_dispatcher(host_window=text_widget)
    drain = UiCoalescedDrain(
        dispatcher=dispatcher,
        drain=controller.drain_chunks,
        consume=sink.consume_ui_chunks,
        is_alive=sink.is_widget_alive,
        logger=logging,
    )
    sink.attach_ui_drain(drain)
    controller.on_chunk = drain.notify
    if stdout:
        sink.add_detach_callback(attach_stream_sink("stdout", sink))
    if stderr:
        sink.add_detach_callback(attach_stream_sink("stderr", sink))
    return sink


__all__ = ["create_stdout_redirector"]
