from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.ui.common.formatting import enum_value
from src.ui.contracts import MergeSuperContextPort
from src.ui.tabs.tools.merge_super import keys


class MergeSuperResultProtocol(Protocol):
    status: object
    output_path: Path | None


@dataclass(frozen=True)
class MergeSuperWindowSpec:
    can_run: bool
    project_path_text: str
    output_filename: str = "super.img"


class MergeSuperPresenter:
    """Format merge super state and results for the Tk view."""

    def __init__(self, *, language) -> None:
        self._language = language

    def _text(self, key: str) -> str:
        return self._language.resolve_required_ui_text(key)

    def build_spec(self, context: MergeSuperContextPort) -> MergeSuperWindowSpec:
        if not context.can_run:
            return MergeSuperWindowSpec(
                can_run=False,
                project_path_text=self._text(keys.NO_PROJECT_PATH_TEXT),
            )
        return MergeSuperWindowSpec(
            can_run=True,
            project_path_text=(
                f"{self._text(keys.PROJECT_PATH_LABEL)} {context.project_path}\n"
                f"{self._text(keys.OUTPUT_PATH_LABEL)} {context.output_path}"
            ),
        )

    def validate_output_name(
        self, output_name: str, *, can_run: bool
    ) -> tuple[bool, str]:
        if not can_run:
            return False, self._text(keys.PROJECT_NOT_SELECTED_MESSAGE)
        if not output_name.strip():
            return False, self._text(keys.OUTPUT_FILENAME_REQUIRED_MESSAGE)
        return True, ""

    def result_message(self, result: MergeSuperResultProtocol) -> tuple[str, str]:
        status = str(enum_value(result.status)).strip().lower()
        if status == "merged":
            return "info", self._text(keys.SUCCESS_MESSAGE).format(
                output_path=result.output_path
            )
        if status == "no_segments":
            return "info", self._text(keys.NO_SEGMENTS_MESSAGE)
        if status == "output_exists":
            output_path = result.output_path
            output_name = output_path.name if output_path is not None else ""
            return "info", self._text(keys.OUTPUT_EXISTS_MESSAGE).format(
                output_name=output_name
            )
        return "warn", self._text(keys.PROJECT_NOT_SELECTED_MESSAGE)

    def unexpected_error_message(self, exc: Exception) -> str:
        if isinstance(exc, FileNotFoundError) and "simg2img" in str(exc):
            return self._text(keys.SIMG2IMG_MISSING_MESSAGE)
        return self._text(keys.UNEXPECTED_ERROR_MESSAGE).format(error=exc)


__all__ = ["MergeSuperPresenter", "MergeSuperResultProtocol", "MergeSuperWindowSpec"]
