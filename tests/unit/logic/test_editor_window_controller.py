from __future__ import annotations

# Direct file execution bootstrap
import sys as _direct_sys
from pathlib import Path as _DirectPath

_DIRECT_PROJECT_ROOT = _DirectPath(__file__).resolve().parent
while _DIRECT_PROJECT_ROOT != _DIRECT_PROJECT_ROOT.parent:
    if (
        (_DIRECT_PROJECT_ROOT / "src").is_dir()
        and (_DIRECT_PROJECT_ROOT / "tests").is_dir()
        and (_DIRECT_PROJECT_ROOT / "scripts").is_dir()
    ):
        break
    _DIRECT_PROJECT_ROOT = _DIRECT_PROJECT_ROOT.parent
else:
    raise RuntimeError(f"Project root was not found for {__file__}")

_direct_root_text = str(_DIRECT_PROJECT_ROOT)
if _direct_root_text not in _direct_sys.path:
    _direct_sys.path.insert(0, _direct_root_text)
if __package__ in {None, ""}:
    _direct_relative = _DirectPath(__file__).resolve().relative_to(
        _DIRECT_PROJECT_ROOT
    ).with_suffix("")
    __package__ = ".".join(_direct_relative.parts[:-1])


from pathlib import Path
import sys

sys.path.insert(0, '.')

from src.logic.editor.controller import EditorController
from src.app.editor.controller import EditorWindowController


def test_editor_opening_directory_clears_stale_file_name(tmp_path: Path) -> None:
    plugin_dir = tmp_path / 'MOOS'
    scripts_dir = plugin_dir / 'scripts'
    scripts_dir.mkdir(parents=True)
    (plugin_dir / 'main.sh').write_text("echo root\n", encoding='utf-8')

    controller = EditorWindowController()
    result = controller.open_selection(
        current_path=str(plugin_dir),
        selected_name='scripts',
        current_file_name='main.sh',
    )

    assert result.new_path == str(scripts_dir.resolve())
    assert result.file_name == ''


def test_editor_opening_parent_directory_clears_stale_file_name(tmp_path: Path) -> None:
    plugin_dir = tmp_path / 'MOOS'
    scripts_dir = plugin_dir / 'scripts'
    scripts_dir.mkdir(parents=True)

    controller = EditorWindowController()
    result = controller.open_selection(
        current_path=str(scripts_dir),
        selected_name='..',
        current_file_name='main.sh',
    )

    assert result.new_path == str(plugin_dir)
    assert result.file_name == ''


def test_editor_read_file_returns_error_payload_for_missing_file(tmp_path: Path) -> None:
    controller = EditorController()

    result = controller.read_file(str(tmp_path / 'missing.sh'), 'utf-8')

    assert result.succeeded is False
    assert result.content is None
    assert result.error is not None
    assert 'No such file or directory' in str(result.error)

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
