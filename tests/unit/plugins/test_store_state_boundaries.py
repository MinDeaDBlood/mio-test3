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


from types import SimpleNamespace

from tests.support.paths import PROJECT_ROOT


from src.app.localization_runtime import LangUtils
from src.ui.tabs.plugins.store.cards import StoreCatalogController
from src.ui.tabs.plugins.store.state import PluginStoreViewState
from tests.support.plugin_catalog import plugin_item


def _build_texts() -> LangUtils:
    texts = LangUtils()
    texts.load_map(
        {
            "plugins_store_button_state_install": "Install",
            "plugins_store_button_state_uninstall": "Uninstall",
            "plugins_store_button_state_ready": "Installing",
            "plugins_store_button_state_installation_complete": "Installed",
            "plugins_store_catalog_view_model_install": "Install",
            "plugins_store_catalog_view_model_uninstall": "Uninstall",
            "plugins_store_catalog_view_model_author_label": "Author",
            "plugins_store_catalog_view_model_version_label": "Version",
            "plugins_store_catalog_view_model_image_size_label": "Size",
        }
    )
    return texts


class _Widget:
    def __init__(self):
        self.alive = True
        self.mapped = False
        self.packs: list[dict] = []
        self.configs: list[dict] = []
        self.children: list[_Widget] = []
        self.updated = False
        self.scrolled = False

    def winfo_exists(self):
        return self.alive

    def winfo_ismapped(self):
        return self.mapped

    def pack(self, **kwargs):
        self.mapped = True
        self.packs.append(kwargs)

    def pack_forget(self):
        self.mapped = False

    def config(self, **kwargs):
        self.configs.append(kwargs)

    def winfo_children(self):
        return list(self.children)

    def destroy(self):
        self.alive = False

    def update_idletasks(self):
        self.updated = True

    def yview_moveto(self, value):
        self.scrolled = value


class _Builder:
    def build(self, card):
        return SimpleNamespace(
            frame=_Widget(),
            install_button=_Widget(),
            uninstall_button=_Widget(),
        )


class _ModuleManager:
    def __init__(self):
        self.installed = {"demo": False, "other": True}

    def is_installed(self, plugin_id):
        return self.installed.get(plugin_id, False)


class _Search:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value


class _Window:
    def __init__(self):
        self.store_state = PluginStoreViewState(
            catalog=[
                plugin_item("demo", name="Demo Plugin"),
                plugin_item("other", name="Other Plugin"),
            ]
        )
        self.alive = True
        self.module_manager = _ModuleManager()
        self.search = _Search("demo")
        self.label_frame = _Widget()
        self.canvas = _Widget()
        self.configure_calls = 0

    def winfo_exists(self):
        return self.alive

    def _on_label_frame_configure(self):
        self.configure_calls += 1


def test_view_state_owns_catalog_widget_and_control_state() -> None:
    state = PluginStoreViewState(catalog=[plugin_item("demo", name="Demo")])
    frame = _Widget()
    install = _Widget()
    uninstall = _Widget()
    state.set_app_frame("demo", frame)
    state.register_controls("demo", install, uninstall)

    assert state.catalog_items() == (plugin_item("demo", name="Demo"),)
    assert state.app_frame_for("demo") is frame
    assert state.app_info_ids() == ("demo",)
    assert state.app_info_items() == (("demo", frame),)
    assert state.controls_for("demo") == (install, uninstall)

    state.clear_catalog_widgets()
    assert state.app_frames == {}
    assert state.controls == {}


def _host_port(window):
    return SimpleNamespace(
        state=window.store_state,
        is_alive=window.winfo_exists,
        is_plugin_installed=window.module_manager.is_installed,
    )


def test_catalog_controller_uses_view_state_for_cards_controls_and_search() -> None:
    window = _Window()
    controller = StoreCatalogController(
        window,
        texts=_build_texts(),
        host_port=_host_port(window),
        button_width=12,
    )
    controller.card_widget_builder = _Builder()

    controller.add_app(window.store_state.catalog_items())

    state = window.store_state
    assert state.app_frame_for("demo") is not None
    assert state.controls_for("demo") is not None
    assert state.app_frame_for("other") is not None
    assert state.controls_for("other") is not None

    demo_frame = state.app_frame_for("demo")
    other_frame = state.app_frame_for("other")
    assert demo_frame.winfo_ismapped() is True
    assert other_frame.winfo_ismapped() is True

    controller.search_apps()
    assert demo_frame.winfo_ismapped() is True
    assert other_frame.winfo_ismapped() is False

    controller.clear()
    assert state.app_frames == {}
    assert state.controls == {}


def test_plugin_store_ui_has_no_runtime_or_type_dependency_on_logic() -> None:
    import ast

    store_dir = PROJECT_ROOT / "src/ui/tabs/plugins/store"
    forbidden_prefixes = ("src.app", "src.logic", "src.core")
    violations: list[str] = []
    for source_path in store_dir.glob("*.py"):
        tree = ast.parse(
            source_path.read_text(encoding="utf-8"), filename=str(source_path)
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith(forbidden_prefixes):
                    violations.append(f"{source_path.name}:{node.lineno}:{node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(forbidden_prefixes):
                        violations.append(
                            f"{source_path.name}:{node.lineno}:{alias.name}"
                        )

    assert violations == []
    assert not (store_dir / "state_access.py").exists()
    assert not (store_dir / "legacy_state.py").exists()
    assert not (store_dir / "catalog_refresh.py").exists()
    assert not (store_dir / "state_controller.py").exists()


if __name__ == "__main__":
    test_view_state_owns_catalog_widget_and_control_state()
    test_catalog_controller_uses_view_state_for_cards_controls_and_search()
    test_plugin_store_ui_has_no_runtime_or_type_dependency_on_logic()
    print("PLUGIN_STORE_STATE_BOUNDARY_TESTS_OK")
