from __future__ import annotations

from dataclasses import dataclass
from platform import machine, system

from src.ui.localization import LocalizationCatalog
from src.ui.tabs.about import keys


@dataclass(frozen=True)
class AboutTabSpec:
    brand_heading: str
    runtime_text: str
    language_credit: str
    footer_text: str
    github_text: str
    description_text: str
    link_title: str


class AboutTabPresenter:
    def __init__(self, *, texts: LocalizationCatalog, settings_obj, py_version: str):
        self.texts = texts
        self.settings = settings_obj
        self.py_version = py_version

    def build_spec(self) -> AboutTabSpec:
        runtime_template = self.texts.resolve_required_ui_text(keys.RUNTIME_FORMAT)
        runtime_text = runtime_template.format(
            self.settings.version,
            self.py_version[:6],
            system(),
            machine(),
        )
        credit_template = self.texts.resolve_required_ui_text(
            keys.LANGUAGE_CREDIT_FORMAT
        )
        language_credit = credit_template.format(
            language=self.settings.language,
            author=self.texts.resolve_required_ui_text(keys.LANGUAGE_FILE_AUTHOR),
        )
        return AboutTabSpec(
            brand_heading=self.texts.resolve_required_ui_text(keys.BRAND_HEADING),
            runtime_text=runtime_text,
            language_credit=language_credit,
            footer_text=self.texts.resolve_required_ui_text(keys.FOOTER),
            github_text=self.texts.resolve_required_ui_text(keys.GITHUB_LABEL),
            description_text=self.texts.resolve_required_ui_text(keys.DESCRIPTION),
            link_title=self.texts.resolve_optional(keys.LINK_TITLE, default=""),
        )


__all__ = ["AboutTabPresenter", "AboutTabSpec"]
