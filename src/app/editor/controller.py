from __future__ import annotations

from dataclasses import dataclass
import os

from src.logic.editor.controller import EditorController


@dataclass(frozen=True)
class EditorSelectionResult:
    new_path: str
    file_name: str
    should_refresh: bool = True


class EditorWindowController:
    def __init__(self, *, logger=None):
        self.controller = EditorController(logger=logger)
        self.logger = logger

    def ensure_directory(self, path: str):
        return self.controller.ensure_directory(path)

    def list_entries(self, path: str):
        return self.controller.list_entries(path)

    def load_file(self, path: str, file_name: str, encoding: str):
        return self.controller.read_file(os.path.join(path, file_name), encoding)

    def save_file(self, path: str, file_name: str, text: str):
        return self.controller.write_file(os.path.join(path, file_name), text)

    def create_new(self, *, base_path: str, name: str) -> EditorSelectionResult | None:
        if not name:
            return None
        self.controller.ensure_directory(base_path)
        new_path = self.controller.build_new_path(base_path, name)
        if self.controller.exists(new_path):
            return None
        self.controller.create_empty_file(new_path)
        return EditorSelectionResult(new_path=base_path, file_name=name)

    def delete_selected(self, *, base_path: str, selected_name: str) -> bool:
        if selected_name in {'', '.', '..'}:
            return False
        self.controller.delete_entry(os.path.join(base_path, selected_name))
        return True

    def rename_selected(self, *, base_path: str, selected_name: str, new_name: str) -> EditorSelectionResult | None:
        if selected_name in {'', '.', '..'} or not new_name:
            return None
        source = os.path.join(base_path, selected_name)
        target = os.path.join(base_path, new_name)
        if self.controller.exists(target):
            return None
        self.controller.rename_entry(source, target)
        return EditorSelectionResult(new_path=base_path, file_name=new_name)

    def open_selection(self, *, current_path: str, selected_name: str, current_file_name: str) -> EditorSelectionResult:
        if selected_name == '..':
            return EditorSelectionResult(new_path=os.path.dirname(current_path), file_name='')
        target = os.path.abspath(os.path.join(current_path, selected_name))
        if self.controller.is_dir(target):
            return EditorSelectionResult(new_path=target, file_name='')
        if self.controller.is_file(target):
            return EditorSelectionResult(new_path=current_path, file_name=os.path.basename(target))
        return EditorSelectionResult(new_path=current_path, file_name=current_file_name)
