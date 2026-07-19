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


from src.logic.plugins.store_models import PluginCatalogItem


def plugin_item(
    plugin_id: str = 'demo',
    *,
    name: str | None = None,
    description: str = '',
    author: str = '',
    version: str = '',
    size_bytes: int = 0,
    dependencies: tuple[str, ...] = (),
    systems: str = 'all',
    architecture: str = 'all',
    files: tuple[str, ...] = (),
) -> PluginCatalogItem:
    return PluginCatalogItem(
        plugin_id=plugin_id,
        name=name or plugin_id,
        description=description,
        author=author,
        version=version,
        size_bytes=size_bytes,
        dependencies=dependencies,
        systems=systems,
        architecture=architecture,
        files=files,
    )

if __name__ == "__main__":
    from tests.support.direct_execution import support_module_main

    raise SystemExit(support_module_main(__file__))
