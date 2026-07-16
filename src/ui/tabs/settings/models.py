from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToggleBinding:
    key: str
    value: str
    text: str
    on_value: str = "1"
    off_value: str = "0"
    style: str = "Toggle.TButton"


def _text(lang, *keys: str) -> str:
    return lang.resolve(*keys, default="")


def build_toggle_bindings(settings, lang) -> tuple[ToggleBinding, ...]:
    definitions = (
        ("magisk_not_decompress", ("settings_models_boot_skip_decompression_hint",)),
        ("boot_skip_ramdisk", ("skip_ramdisk",)),
        ("treff", ("settings_models_transparency_effect",)),
        ("auto_unpack", ("auto_unpack", "settings_models_automatic")),
    )
    return tuple(
        ToggleBinding(
            key=key,
            value=str(getattr(settings, key)),
            text=_text(lang, *text_keys),
        )
        for key, text_keys in definitions
    )


__all__ = ["ToggleBinding", "build_toggle_bindings"]
