from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from src.ui.localization import LocalizationCatalog
from src.ui.common.editor import keys


DEFAULT_ENCODINGS = ("utf-8", "gbk", "gb2312", "utf-16")


class EditorController(Protocol):
    def ensure_directory(self, path: str) -> object: ...
    def list_entries(self, path: str): ...
    def rename_selected(self, *, base_path: str, selected_name: str, new_name: str): ...
    def delete_selected(self, *, base_path: str, selected_name: str) -> bool: ...
    def create_new(self, *, base_path: str, name: str): ...
    def open_selection(
        self, *, current_path: str, selected_name: str, current_file_name: str
    ): ...
    def load_file(self, path: str, file_name: str, encoding: str): ...
    def save_file(self, path: str, file_name: str, text: str) -> object: ...


@dataclass(frozen=True)
class EditorUiState:
    path: str
    file_name: str
    encoding: str = "utf-8"


class EditorPresenter:
    """Translate editor view actions into application-controller calls."""

    def __init__(self, *, controller: EditorController, texts: LocalizationCatalog):
        self.controller = controller
        self._texts = texts

    def ensure_path(self, state: EditorUiState) -> EditorUiState:
        self.controller.ensure_directory(state.path)
        return state

    def list_entries(self, state: EditorUiState):
        return self.controller.list_entries(state.path)

    @staticmethod
    def change_encoding(state: EditorUiState, encoding: str) -> EditorUiState:
        return replace(state, encoding=encoding or state.encoding)

    def rename(
        self, state: EditorUiState, *, selected_name: str, new_name: str
    ) -> EditorUiState | None:
        result = self.controller.rename_selected(
            base_path=state.path,
            selected_name=selected_name,
            new_name=new_name,
        )
        if result is None:
            return None
        return replace(state, path=result.new_path, file_name=result.file_name)

    def delete(
        self, state: EditorUiState, *, selected_name: str
    ) -> tuple[EditorUiState, bool]:
        return state, self.controller.delete_selected(
            base_path=state.path, selected_name=selected_name
        )

    def create_new(self, state: EditorUiState, *, name: str) -> EditorUiState | None:
        result = self.controller.create_new(base_path=state.path, name=name)
        if result is None:
            return None
        return replace(state, path=result.new_path, file_name=result.file_name)

    def open_selection(
        self, state: EditorUiState, *, selected_name: str
    ) -> EditorUiState:
        result = self.controller.open_selection(
            current_path=state.path,
            selected_name=selected_name,
            current_file_name=state.file_name,
        )
        return replace(state, path=result.new_path, file_name=result.file_name)

    def load_content(self, state: EditorUiState) -> tuple[str, Exception | None]:
        result = self.controller.load_file(state.path, state.file_name, state.encoding)
        if result.succeeded:
            return result.content or "", None
        message = self._texts.resolve_required_ui_text(keys.LOAD_FAILED_FORMAT).format(
            path=result.path,
            file_type=result.file_type,
            error=result.error,
        )
        return message, result.error

    def save_content(self, state: EditorUiState, *, text: str) -> None:
        self.controller.save_file(state.path, state.file_name, text)

    def build_title(self, state: EditorUiState) -> str:
        return self._texts.resolve_required_ui_text(keys.TITLE_FORMAT).format(
            file_name=state.file_name,
            encoding=state.encoding,
        )


__all__ = ["DEFAULT_ENCODINGS", "EditorController", "EditorPresenter", "EditorUiState"]
