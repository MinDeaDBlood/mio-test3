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


import tempfile
from pathlib import Path

from tests.support.runtime_smoke import prepare_root, sync_runtime_globals
from src.app.composition.project_workspace import create_project_workspace
from src.app.runtime.phases import require_registered_bootstrap_window_runtime
from src.core.android_sparse import is_sparse_image, split_raw_image_to_sparse_parts
from src.logic.projects.common.project_manager import ProjectManager
from src.logic.projects.common.runtime_context import build_project_path_runtime_context
from src.platform.settings_repository import SettingsRepository


def main() -> None:
    root = prepare_root()
    try:
        window_runtime = require_registered_bootstrap_window_runtime()
        with tempfile.TemporaryDirectory(prefix='mio-scenario-') as td:
            settings = SettingsRepository(
                set_ini=str(Path(td) / 'settings.ini'),
                load=False,
            )
            settings.path = td
            manager = ProjectManager(
                runtime=build_project_path_runtime_context(
                    workspace_path=settings.path,
                    current_project_name=window_runtime.current_project_name,
                )
            )
            sync_runtime_globals(
                settings=settings,
                project_manager=manager,
                current_project_name=window_runtime.current_project_name,
            )

            manager.new('Demo')
            window_runtime.current_project_name.set('Demo')
            input_dir = Path(manager.current_input_path())
            raw_image = Path(td) / 'system.raw'
            raw_image.write_bytes(
                bytes((index * 17) % 256 for index in range(4096 * 2))
            )
            generated = split_raw_image_to_sparse_parts(
                raw_image,
                Path(td) / 'generated-sparse',
                part_count=2,
            ).output_paths[0]
            system_image = input_dir / 'system.img'
            system_image.write_bytes(generated.read_bytes())
            assert is_sparse_image(system_image)

            workspace = create_project_workspace(host_window=root)
            project_menu = workspace['project_menu']
            unpack_view = workspace['unpack_view']
            action_panel = workspace['action_panel']
            project_menu.gui()
            unpack_view.gui()
            action_panel.gui()
            root.update_idletasks()

            project_menu.listdir()
            assert 'Demo' in project_menu.combobox.cget('values')
            assert project_menu.current_project_name.get() == 'Demo'

            controller = unpack_view.view_controller.controller
            img_candidates = controller.list_unpack_items('img')
            assert any(item.name == 'system' for item in img_candidates)
            assert unpack_view.refs(auto=True) is True
            assert 'system' in unpack_view.lsg.loaded_value
            assert controller.workspace_exists()
            assert action_panel.winfo_children(), 'Project action panel was not rendered.'

            action_panel.destroy()
            unpack_view.destroy()
            project_menu.destroy()
    finally:
        root.destroy()

    print('SCENARIO_SMOKE_OK')


if __name__ == '__main__':
    main()
