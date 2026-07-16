# Copyright (C) 2022-2025 The MIO-KITCHEN-SOURCE Project
#
# Licensed under theGNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/agpl-3.0.en.html#license-text
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
from functools import lru_cache
import tkinter as tk
from tkinter import ttk, END, X, LEFT
from tkinter.ttk import Button

from src.ui.localization import LocalizationCatalog
from src.ui.common.editor.presenter import (
    DEFAULT_ENCODINGS,
    EditorUiState,
)
from src.ui.common.editor import keys
from src.ui.common.controls import input_


@lru_cache(maxsize=1)
def _resolve_editor_widgets():
    import pygments.lexers
    from chlorophyll import CodeView

    return CodeView, pygments.lexers


def _resolve_default_lexer(lexer=None):
    if lexer is not None:
        return lexer
    _code_view, lexers = _resolve_editor_widgets()
    return lexers.BashLexer


class PythonEditor(tk.Frame):
    def __init__(
        self,
        parent,
        path,
        file_name,
        *,
        texts: LocalizationCatalog,
        presenter,
        task_runner,
        lexer=None,
    ):
        super().__init__(parent)
        self.parent = parent
        self._texts = texts
        self.controller = presenter
        self.task_runner = task_runner
        self.state = self.controller.ensure_path(
            EditorUiState(path=path, file_name=file_name or "")
        )
        CodeView, _lexers = _resolve_editor_widgets()
        self.text = CodeView(
            self,
            wrap="word",
            undo=True,
            lexer=_resolve_default_lexer(lexer),
            color_scheme="dracula",
        )
        self.text.pack(side="left", fill="both", expand=True)
        self.encoding = tk.StringVar(value=self.state.encoding)
        self.encoding.trace("w", lambda *_: self.load())
        f1 = ttk.Frame(self.parent)
        ttk.Button(
            f1, text=self._texts.resolve_required_ui_text(keys.COMMON_EDITOR_WINDOW_CLOSE), command=self.parent.destroy
        ).pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=1)
        self.save_b = ttk.Button(
            f1,
            text=self._texts.resolve_required_ui_text(keys.COMMON_EDITOR_WINDOW_SAVE),
            command=self.save,
            style="Accent.TButton",
        )
        self.save_b.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=1)
        f1.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        self.show = tk.Listbox(self, activestyle="dotbox", highlightthickness=0)
        self.show.bind("<Double-Button-1>", lambda x: self.p_bind())
        self.show.pack(fill=tk.BOTH, padx=5, pady=5, expand=True)
        ff = ttk.Frame(self)
        Button(
            ff, text=self._texts.resolve_required_ui_text(keys.COMMON_EDITOR_WINDOW_REFRESH), command=self.refs
        ).pack(fill=X, side=LEFT, padx=5, pady=5, expand=True)
        Button(ff, text=self._texts.resolve_required_ui_text(keys.COMMON_EDITOR_WINDOW_NEW), command=self.new).pack(
            fill=X, side=LEFT, padx=5, pady=5, expand=True
        )
        Button(
            ff, text=self._texts.resolve_required_ui_text(keys.COMMON_EDITOR_WINDOW_DELETE), command=self.delete
        ).pack(fill=X, side=LEFT, padx=5, pady=5, expand=True)
        Button(
            ff, text=self._texts.resolve_required_ui_text(keys.COMMON_EDITOR_WINDOW_RENAME), command=self.rename
        ).pack(fill=X, side=LEFT, padx=5, pady=5, expand=True)
        ff.pack(padx=5, pady=5, fill=X, expand=True)
        format_frame = ttk.Frame(self)
        ttk.Label(
            format_frame,
            text=self._texts.resolve_required_ui_text(keys.ENCODING_LABEL),
        ).pack(padx=5, pady=5, expand=True, side=LEFT, fill=X)
        encoding_comboxx = ttk.Combobox(
            format_frame, values=list(DEFAULT_ENCODINGS), textvariable=self.encoding
        )
        encoding_comboxx.pack(fill=X, side=LEFT, padx=5, pady=5, expand=True)
        encoding_comboxx.bind("<<ComboboxSelected>>", lambda *x: self.load())
        format_frame.pack(padx=5, pady=5, fill=X, expand=True)
        self.refs()

    def _selected_name(self) -> str:
        try:
            return self.show.get(self.show.curselection())
        except Exception:
            return ""

    def rename(self):
        file = self._selected_name()
        if file in ["", ".", ".."]:
            return
        if file == self.state.file_name:
            self.save()
        new_name = input_(
            texts=self._texts,
            title=self._texts.resolve_required_ui_text(keys.RENAME_TITLE),
            text=file,
            master=self,
        )
        new_state = self.controller.rename(
            self.state, selected_name=file, new_name=new_name
        )
        if new_state is None:
            return
        self.state = new_state
        self.refs()
        self.load()

    def delete(self):
        file = self._selected_name()
        self.state, ok = self.controller.delete(self.state, selected_name=file)
        if not ok:
            return
        self.refs()

    def new(self):
        new_name = input_(
            texts=self._texts,
            title=self._texts.resolve_required_ui_text(keys.NEW_FILE_TITLE),
            text="new.txt",
            master=self,
        )
        new_state = self.controller.create_new(self.state, name=new_name)
        if new_state is None:
            return
        self.state = new_state
        self.refs()
        self.load()

    def p_bind(self):
        file = self._selected_name()
        self.state = self.controller.open_selection(self.state, selected_name=file)
        self.refs()
        self.load()

    def refs(self):
        self.show.delete(0, END)
        for entry in self.controller.list_entries(self.state):
            self.show.insert(END, entry)

    def _finalize_save(self):
        if self.winfo_exists():
            self.save_b.configure(
                text=self._texts.resolve_required_ui_text(keys.COMMON_EDITOR_WINDOW_SAVE), state="normal"
            )

    def _save_in_thread(self, state: EditorUiState, content: str):
        self.controller.save_content(state, text=content)

    def save(self):
        self.save_b.configure(
            text=self._texts.resolve_required_ui_text(keys.COMMON_EDITOR_WINDOW_SAVED), state="disabled"
        )
        content = self.text.get(1.0, tk.END)
        state = self.state
        self.task_runner.run(
            self._save_in_thread,
            state,
            content,
            on_finally=self._finalize_save,
        )

    def load(self):
        if not self.state.file_name:
            self.parent.title(self.controller.build_title(self.state))
            return
        try:
            self.state = self.controller.change_encoding(
                self.state, self.encoding.get()
            )
            self.text.delete(0.0, tk.END)
            data, exc = self.controller.load_content(self.state)
            if exc is not None:
                logging.debug(
                    "Editor could not load %s/%s: %s",
                    self.state.path,
                    self.state.file_name,
                    exc,
                )
            self.text.insert(tk.END, data)
        except Exception:
            logging.exception(
                "Editor load failed for %s/%s", self.state.path, self.state.file_name
            )
        self.parent.title(self.controller.build_title(self.state))


__all__ = ["PythonEditor"]
