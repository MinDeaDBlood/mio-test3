from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from src.ui.localization import LocalizationCatalog
from src.ui.common.formatting import enum_value


class LogicMessagePort(Protocol):
    code: str
    default: str
    params: Mapping[str, object]

    def render_default(self) -> str: ...


class ServiceOutputEventPort(Protocol):
    message: object
    channel: object
    severity: object


MESSAGE_KEYS: dict[str, str] = {
    "project_not_selected": "warn1",
    "operation_failed": "warn11",
    "file_not_found": "warn3",
    "operation_complete": "common_service_output_operation_success",
    "processing": "common_service_output_unpacking_label",
    "created": "common_service_output_packed_success_format",
    "removing": "common_service_output_removing_format",
    "remove_failed": "common_service_output_remove_failed_format",
    "size_detected": "common_service_output_resizing_format",
    "packing": "common_service_output_packing_started_format",
    "boot_image_origin_missing": "boot_image_origin_missing",
    "boot_image_source_missing": "boot_image_source_missing",
    "boot_image_repack_failed": "boot_image_repack_failed",
    "boot_image_output_missing": "boot_image_output_missing",
    "boot_image_repack_success": "boot_image_repack_success",
    "boot_image_unpack_done": "boot_image_unpack_done",
}

SEVERITY_COLORS: dict[str, str] = {
    "info": "blue",
    "success": "green",
    "warning": "orange",
    "error": "red",
}


def _enum_value(value: object) -> str:
    return str(enum_value(value)).strip().lower()


def _is_logic_message(value: object) -> bool:
    return all(
        hasattr(value, attribute)
        for attribute in ("code", "default", "params", "render_default")
    )


def render_logic_message(value: object, *, texts: LocalizationCatalog) -> str:
    if not _is_logic_message(value):
        return str(value)
    message = value
    code = str(getattr(message, "code"))
    default = str(getattr(message, "default"))
    params = getattr(message, "params")
    key = MESSAGE_KEYS.get(code)
    template = texts.resolve_optional(key, default=default) if key else default
    try:
        return template.format(**params)
    except (KeyError, ValueError, IndexError, TypeError):
        return str(message.render_default())


@dataclass(frozen=True)
class UiServiceOutputSink:
    log: Callable[[str], Any]
    texts: LocalizationCatalog
    notify: Callable[..., Any] | None = None

    def __call__(self, event: ServiceOutputEventPort) -> object:
        text = render_logic_message(event.message, texts=self.texts)
        if _enum_value(event.channel) == "log":
            return self.log(text)
        if self.notify is None:
            return self.log(text)
        color = SEVERITY_COLORS.get(_enum_value(event.severity), "blue")
        return self.notify(message=text, color=color)


__all__ = [
    "LogicMessagePort",
    "MESSAGE_KEYS",
    "SEVERITY_COLORS",
    "ServiceOutputEventPort",
    "UiServiceOutputSink",
    "render_logic_message",
]
