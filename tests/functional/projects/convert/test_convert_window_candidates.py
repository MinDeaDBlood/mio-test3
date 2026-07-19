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
from types import SimpleNamespace

from src.logic.projects.convert import service as convert_service
from src.logic.projects.convert import operations as convert_operations
from src.logic.projects.convert.runtime_context import ConvertRuntimeContext
from src.ui.tabs.project.convert import presenter as convert_presenter


class _Output:
    def log(self, _text, **_kwargs):
        return None

    def report(self, _text, **_kwargs):
        return None


def _runtime(work: Path, output: Path | None = None):
    return ConvertRuntimeContext(
        work_path=str(work),
        output_path=str(output or work),
        output=_Output(),
    )


def test_choose_candidate_group_auto_selects_existing_input_br_when_raw_is_empty(
    tmp_path, monkeypatch
):
    work = tmp_path / "Source"
    output = tmp_path / "Output"
    work.mkdir()
    output.mkdir()
    (work / "vendor.new.dat.br").write_bytes(b"br-data")

    monkeypatch.setattr(convert_operations, "gettype", lambda _path: "unknown")

    source_format, items = convert_service.choose_candidate_group(
        "raw", runtime=_runtime(work, output)
    )

    assert source_format == "br"
    assert items == ["vendor.new.dat.br"]


def test_candidate_groups_do_not_treat_previous_output_as_new_input(
    tmp_path, monkeypatch
):
    source = tmp_path / "Input"
    output = tmp_path / "Output"
    source.mkdir()
    output.mkdir()
    (output / "old-system.img").write_bytes(b"old result")
    monkeypatch.setattr(convert_operations, "gettype", lambda _path: "ext")

    groups = convert_service.list_candidate_groups(
        runtime=_runtime(source, output)
    )

    assert all(not items for items in groups.values())


def test_list_candidate_groups_does_not_probe_dat_family_files(tmp_path, monkeypatch):
    work = tmp_path / "Project"
    work.mkdir()
    (work / "vendor.new.dat.br").write_bytes(b"large br payload")
    (work / "system.img").write_bytes(b"raw image")
    probed = []

    def fake_gettype(path):
        probed.append(Path(path).name)
        return "ext"

    monkeypatch.setattr(convert_operations, "gettype", fake_gettype)

    groups = convert_service.list_candidate_groups(runtime=_runtime(work))

    assert groups["br"] == ["vendor.new.dat.br"]
    assert groups["raw"] == ["system.img"]
    assert probed == ["system.img"]


def test_presenter_applies_candidate_group_to_source_selector_and_list():
    class _Selector:
        def __init__(self):
            self.value = "raw"

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    class _ListBox:
        def __init__(self):
            self.items = []

        def clear(self):
            self.items.clear()

        def insert(self, label, value):
            self.items.append((label, value))

    view = SimpleNamespace(h=_Selector(), list_b=_ListBox())

    convert_presenter.apply_candidate_group(view, ("br", ["vendor.new.dat.br"]))

    assert view.h.get() == "br"
    assert view.list_b.items == [("vendor.new.dat.br", "vendor.new.dat.br")]

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
