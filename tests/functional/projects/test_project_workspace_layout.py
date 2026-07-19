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


import sys

sys.path.insert(0, ".")
from pathlib import Path
from types import SimpleNamespace

from src.logic.projects.common.project_manager import ProjectManager
from src.logic.common.service_output import build_service_output
from src.logic.projects.import_flow.generic_file_import import import_known_file
from src.logic.projects.common import workspace_service
from src.core.merge_sparse import SparseMergeResult, SparseMergeStatus
from src.logic.tools.merge_super import (
    MergeSuperRequest,
    MergeSuperService,
    MergeSuperStatus,
)


class Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def _pm(tmp_path: Path, *, current="Alpha"):
    return ProjectManager(
        runtime=SimpleNamespace(
            workspace_path=str(tmp_path), current_project_name=Var(current)
        )
    )


def test_project_manager_keeps_projects_under_projects_root_and_output_isolated(
    tmp_path,
):
    pm = _pm(tmp_path, current="Alpha")
    project_root = Path(pm.new("Alpha"))

    assert project_root == tmp_path / "Projects" / "Alpha"
    assert (project_root / "input").is_dir()
    assert (project_root / "unpack").is_dir()
    assert (project_root / "output").is_dir()
    assert Path(pm.current_work_path()) == project_root / "unpack"
    assert Path(pm.current_input_path()) == project_root / "input"
    assert Path(pm.current_work_output_path()) == project_root / "output"
    assert sorted(pm.get_projects()) == ["Alpha"]


def test_project_manager_uses_one_canonical_workspace_layout(tmp_path):
    pm = _pm(tmp_path, current="Alpha")
    pm.new("Alpha")

    assert Path(pm.current_work_path()) == tmp_path / "Projects" / "Alpha" / "unpack"
    assert Path(pm.current_input_path()) == tmp_path / "Projects" / "Alpha" / "input"
    assert (
        Path(pm.current_work_output_path())
        == tmp_path / "Projects" / "Alpha" / "output"
    )


def test_drag_drop_known_file_import_uses_project_manager_layout(tmp_path):
    source = tmp_path / "vendor.img"
    source.write_bytes(b"abc")
    current = Var("")
    pm = ProjectManager(
        runtime=SimpleNamespace(
            workspace_path=str(tmp_path), current_project_name=current
        )
    )
    runtime = SimpleNamespace(
        project_manager=pm,
        auto_unpack=False,
        tool_bin="",
        magisk_not_decompress="0",
        boot_skip_ramdisk="0",
        output=build_service_output(emit=lambda _event: None),
    )

    result = import_known_file(
        str(source),
        runtime=runtime,
        workflow_runtime=object(),
        unpack_func=lambda *a, **k: None,
    )

    assert result.imported is True
    assert result.project_name == "vendor"
    assert (
        tmp_path / "Projects" / "vendor" / "input" / "vendor.img"
    ).read_bytes() == b"abc"
    assert (
        tmp_path / "Projects" / "vendor" / "unpack" / "vendor.img"
    ).read_bytes() == b"abc"
    assert (tmp_path / "Projects" / "vendor" / "output").is_dir()


def test_pack_zip_defaults_to_project_output_and_does_not_zip_itself(tmp_path):
    current = Var("Alpha")
    pm = ProjectManager(
        runtime=SimpleNamespace(
            workspace_path=str(tmp_path), current_project_name=current
        )
    )
    pm.new("Alpha")
    output_dir = Path(pm.current_work_output_path())
    (output_dir / "system.img").write_bytes(b"image")
    events = []
    workspace_service.pack_zip(
        input_dir=str(output_dir),
        output_zip=str(output_dir / "Alpha.zip"),
        project_name="Alpha",
        output=build_service_output(emit=events.append),
        silent=True,
    )
    assert events

    zip_path = output_dir / "Alpha.zip"
    assert zip_path.exists()
    import zipfile

    with zipfile.ZipFile(zip_path) as archive:
        assert "system.img" in archive.namelist()
        assert "Alpha.zip" not in archive.namelist()


def test_merge_super_service_reads_source_and_writes_output(tmp_path):
    pm = _pm(tmp_path, current="Alpha")
    pm.new("Alpha")
    calls = []

    def merge_function(**kwargs):
        calls.append(kwargs)
        output_path = Path(kwargs["output_path"])
        return SparseMergeResult(
            status=SparseMergeStatus.MERGED,
            output_path=output_path,
            segment_paths=(Path(kwargs["source_directory"]) / "super.img.0",),
        )

    service = MergeSuperService(
        project_manager=pm,
        tool_bin_path="/tools",
        merge_function=merge_function,
    )

    result = service.execute(
        MergeSuperRequest(output_name="super.img", delete_source=False),
        progress_callback=lambda _: None,
    )

    assert result.status is MergeSuperStatus.MERGED
    assert (
        Path(calls[0]["source_directory"]) == tmp_path / "Projects" / "Alpha" / "unpack"
    )
    assert (
        Path(calls[0]["output_path"])
        == tmp_path / "Projects" / "Alpha" / "output" / "super.img"
    )

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
