from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from src.app.runtime.contexts.contracts import SettingsProtocol
from src.logic.welcome.steps import WelcomeStepPolicy


@dataclass(frozen=True)
class WelcomeContentAccess:
    """Application accessors for welcome resources owned by platform adapters."""

    list_languages: Callable[[], tuple[str, ...]]
    list_licenses: Callable[[], tuple[str, ...]]
    read_license: Callable[[str], str]
    read_private_notice: Callable[[], str]


@dataclass(frozen=True)
class WelcomeMainData:
    languages: tuple[str, ...]
    selected_language: str


@dataclass(frozen=True)
class WelcomeWorkdirData:
    workdir: str


@dataclass(frozen=True)
class WelcomeLicenseData:
    licenses: tuple[str, ...]
    selected_license: str
    license_text: str


class WelcomeController:
    """Application orchestration for the initial setup workflow."""

    def __init__(
        self,
        *,
        settings: SettingsProtocol,
        content_service: WelcomeContentAccess,
        current_language: Callable[[], str],
        frame_count: int,
    ) -> None:
        self.settings = settings
        self.content_service = content_service
        self.current_language = current_language
        self.step_policy = WelcomeStepPolicy(frame_count)
        self.frame_count = frame_count

    def main_data(self) -> WelcomeMainData:
        selected = str(self.current_language()).strip()
        if not selected:
            raise ValueError("Current language is required.")
        return WelcomeMainData(
            languages=self.content_service.list_languages(),
            selected_language=selected,
        )

    def workdir_data(self) -> WelcomeWorkdirData:
        configured = str(self.settings.path or "").strip()
        if not configured:
            raise ValueError("Configured work directory is required.")
        return WelcomeWorkdirData(workdir=configured)

    def set_workdir(self, path: str) -> str:
        normalized = str(path or "").strip()
        if not normalized:
            raise ValueError("Work directory path is required.")
        self.settings.set_value("path", normalized)
        return normalized

    def license_data(self) -> WelcomeLicenseData:
        licenses = self.content_service.list_licenses()
        selected = licenses[0] if licenses else ""
        text = self.content_service.read_license(selected) if selected else ""
        return WelcomeLicenseData(
            licenses=licenses,
            selected_license=selected,
            license_text=text,
        )

    def read_license(self, license_name: str) -> str:
        return self.content_service.read_license(license_name)

    def read_private_notice(self) -> str:
        return self.content_service.read_private_notice()

    def initial_step(self) -> int:
        try:
            value = int(self.settings.oobe)
        except (TypeError, ValueError):
            value = 0
        return self.step_policy.clamp(value)

    def persist_step(self, step: int) -> int:
        normalized = self.step_policy.clamp(step)
        self.settings.set_value("oobe", str(normalized))
        return normalized

    def clamp_step(self, step: int) -> int:
        return self.step_policy.clamp(step)


__all__ = [
    "WelcomeContentAccess",
    "WelcomeController",
    "WelcomeLicenseData",
    "WelcomeMainData",
    "WelcomeWorkdirData",
]
