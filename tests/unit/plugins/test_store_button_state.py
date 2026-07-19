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



from tests.support.paths import PROJECT_ROOT


from src.app.localization_runtime import LangUtils
from src.ui.tabs.plugins.store.button_state import PluginStoreButtonState
from src.ui.tabs.plugins.store.state import PluginStoreViewState


def _build_texts() -> LangUtils:
    texts = LangUtils()
    texts.load_map(
        {
            "plugins_store_button_state_install": "Install",
            "plugins_store_button_state_uninstall": "Uninstall",
            "plugins_store_button_state_ready": "Installing",
            "plugins_store_button_state_installation_complete": "Installed",
        }
    )
    return texts


class _Button:
    def __init__(self):
        self.calls: list[dict] = []
        self.alive = True

    def winfo_exists(self):
        return self.alive

    def config(self, **kwargs):
        self.calls.append(kwargs)


def test_button_state_reads_controls_from_view_state_boundary() -> None:
    state = PluginStoreViewState()
    install = _Button()
    uninstall = _Button()
    state.register_controls("demo", install, uninstall)

    button_state = PluginStoreButtonState(
        texts=_build_texts(),
        state=state,
        is_alive=lambda: True,
    )
    assert button_state.controls_for("demo") == (install, uninstall)

    assert button_state.update_for_installed_state("demo", is_installed=False) is True
    assert install.calls[-1]["state"] == "normal"
    assert uninstall.calls[-1]["state"] == "disabled"

    assert button_state.update_for_installed_state("demo", is_installed=True) is True
    assert install.calls[-1]["state"] == "disabled"
    assert uninstall.calls[-1]["state"] == "normal"


def test_button_state_handles_missing_or_dead_controls_without_exceptions() -> None:
    state = PluginStoreViewState()
    button_state = PluginStoreButtonState(
        texts=_build_texts(),
        state=state,
        is_alive=lambda: True,
    )
    assert button_state.controls_for("missing") == (None, None)
    assert (
        button_state.update_for_installed_state("missing", is_installed=True) is False
    )

    install = _Button()
    uninstall = _Button()
    install.alive = False
    state.register_controls("dead", install, uninstall)
    assert button_state.update_for_installed_state("dead", is_installed=True) is False


def test_button_state_source_contract_requires_explicit_state() -> None:
    source = (PROJECT_ROOT / "src/ui/tabs/plugins/store/button_state.py").read_text(
        encoding="utf-8"
    )
    assert "state: StoreViewStateProtocol" in source
    assert "ensure_plugin_store_view_state" not in source
    assert "getattr(self.window, 'control', {})" not in source
    assert "src.app.runtime_state" not in source


if __name__ == "__main__":
    test_button_state_reads_controls_from_view_state_boundary()
    test_button_state_handles_missing_or_dead_controls_without_exceptions()
    test_button_state_source_contract_requires_explicit_state()
    print("PLUGIN_STORE_BUTTON_STATE_TESTS_OK")
