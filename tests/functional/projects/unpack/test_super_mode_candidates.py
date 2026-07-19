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

from src.logic.projects.unpack.img import service as img_service
from src.logic.projects.unpack.sparse import service as sparse_service
from src.logic.projects.unpack.super import service as super_service
from src.logic.projects.unpack.models import UnpackCandidate
from src.app.projects.unpack.controller import UnpackWorkspaceController
from src.logic.projects.unpack.workspace_service import UnpackWorkspaceService


class _ProjectManager:
    def __init__(self, input_dir, unpack_dir):
        self._input_dir = input_dir
        self._unpack_dir = unpack_dir

    def exist(self):
        return True

    def current_input_path(self):
        return str(self._input_dir)

    def current_work_path(self):
        return str(self._unpack_dir)


def test_img_candidates_exclude_super_image_by_name(tmp_path, monkeypatch):
    (tmp_path / "super.img").write_bytes(b"super")
    (tmp_path / "system.img").write_bytes(b"raw")
    monkeypatch.setattr(
        img_service,
        "gettype",
        lambda path: "super" if path.endswith("super.img") else "unknown",
    )

    assert img_service.scan_candidates(str(tmp_path)) == [
        UnpackCandidate(name="system", detected_type="img")
    ]


def test_img_candidates_exclude_super_typed_image_even_with_nonstandard_name(
    tmp_path, monkeypatch
):
    (tmp_path / "logical.img").write_bytes(b"super")
    monkeypatch.setattr(img_service, "gettype", lambda _path: "super")

    assert img_service.scan_candidates(str(tmp_path)) == []


def test_sparse_candidates_exclude_super_image(tmp_path, monkeypatch):
    (tmp_path / "super.img").write_bytes(b"sparse-super")
    (tmp_path / "vendor.img").write_bytes(b"sparse")
    monkeypatch.setattr(sparse_service, "gettype", lambda _path: "sparse")

    assert sparse_service.scan_candidates(str(tmp_path)) == [
        UnpackCandidate(name="vendor", detected_type="sparse")
    ]


def test_super_candidates_show_partitions_for_sparse_super(tmp_path, monkeypatch):
    (tmp_path / "super.img").write_bytes(b"sparse-super")
    monkeypatch.setattr(super_service, "gettype", lambda _path: "sparse")
    monkeypatch.setattr(
        super_service.lpunpack, "get_parts", lambda path: ["system", "vendor"]
    )

    assert super_service.scan_candidates(str(tmp_path)) == [
        UnpackCandidate(name="system"),
        UnpackCandidate(name="vendor"),
    ]


def test_controller_super_mode_lists_super_partitions_not_img_entry(
    tmp_path, monkeypatch
):
    (tmp_path / "super.img").write_bytes(b"sparse-super")
    monkeypatch.setattr(super_service, "gettype", lambda _path: "sparse")
    monkeypatch.setattr(
        super_service.lpunpack, "get_parts", lambda path: ["system", "vendor"]
    )
    monkeypatch.setattr(img_service, "gettype", lambda _path: "sparse")

    class ProjectManager:
        def exist(self):
            return True

        def current_input_path(self):
            return str(tmp_path)

        def current_work_path(self):
            return str(tmp_path)

    workspace_service = UnpackWorkspaceService(
        json_edit_cls=lambda _path: None,
        gettype_func=lambda _path: "sparse",
    )
    controller = UnpackWorkspaceController(
        project_manager=ProjectManager(),
        workspace_service=workspace_service,
        unpack_func=lambda *_args, **_kwargs: True,
    )

    assert controller.list_unpack_items("img") == []
    assert controller.list_unpack_items("super") == [
        UnpackCandidate(name="system"),
        UnpackCandidate(name="vendor"),
    ]


def test_controller_lists_dat_candidates_from_project_input_folder(
    tmp_path, monkeypatch
):
    input_dir = tmp_path / "input"
    unpack_dir = tmp_path / "unpack"
    input_dir.mkdir()
    unpack_dir.mkdir()
    (input_dir / "vendor.new.dat.br").write_bytes(b"br")
    (input_dir / "vendor.transfer.list").write_text("transfer")
    monkeypatch.setattr(
        "src.logic.projects.unpack.br.service.gettype", lambda _path: "unknown"
    )

    workspace_service = UnpackWorkspaceService(
        json_edit_cls=lambda _path: None,
        gettype_func=lambda _path: "new.dat.br",
    )
    controller = UnpackWorkspaceController(
        project_manager=_ProjectManager(input_dir, unpack_dir),
        workspace_service=workspace_service,
        unpack_func=lambda *_args, **_kwargs: True,
    )

    assert controller.list_unpack_items("new.dat.br") == [
        UnpackCandidate(name="vendor", detected_type="new.dat.br")
    ]


def test_controller_runs_unpack_without_copying_sources_into_unpack(
    tmp_path, monkeypatch
):
    input_dir = tmp_path / "input"
    unpack_dir = tmp_path / "unpack"
    input_dir.mkdir()
    unpack_dir.mkdir()
    (input_dir / "vendor.new.dat.br").write_bytes(b"br")
    (input_dir / "vendor.transfer.list").write_text("transfer")
    (input_dir / "vendor.patch.dat").write_text("patch")
    calls = []

    def fake_run_unpack(format_name, selected, unpack_func=None):
        calls.append((format_name, tuple(selected)))
        assert not (unpack_dir / "vendor.new.dat.br").exists()
        assert not (unpack_dir / "vendor.transfer.list").exists()
        assert not (unpack_dir / "vendor.patch.dat").exists()
        return True

    monkeypatch.setattr(
        "src.app.projects.unpack.controller.run_unpack", fake_run_unpack
    )

    workspace_service = UnpackWorkspaceService(
        json_edit_cls=lambda _path: None,
        gettype_func=lambda _path: "new.dat.br",
    )
    controller = UnpackWorkspaceController(
        project_manager=_ProjectManager(input_dir, unpack_dir),
        workspace_service=workspace_service,
        unpack_func=lambda *_args, **_kwargs: True,
    )

    assert controller.execute_unpack_selection(["vendor"], "new.dat.br") == (
        True,
        "auto",
    )
    assert calls == [("new.dat.br", ("vendor",))]


def test_controller_lists_super_candidates_from_project_input_folder(
    tmp_path, monkeypatch
):
    input_dir = tmp_path / "input"
    unpack_dir = tmp_path / "unpack"
    input_dir.mkdir()
    unpack_dir.mkdir()
    (input_dir / "super.img").write_bytes(b"sparse-super")
    monkeypatch.setattr(super_service, "gettype", lambda _path: "sparse")
    monkeypatch.setattr(
        super_service.lpunpack, "get_parts", lambda path: ["system", "vendor"]
    )

    workspace_service = UnpackWorkspaceService(
        json_edit_cls=lambda _path: None,
        gettype_func=lambda _path: "sparse",
    )
    controller = UnpackWorkspaceController(
        project_manager=_ProjectManager(input_dir, unpack_dir),
        workspace_service=workspace_service,
        unpack_func=lambda *_args, **_kwargs: True,
    )

    assert controller.list_unpack_items("super") == [
        UnpackCandidate(name="system"),
        UnpackCandidate(name="vendor"),
    ]


def test_unpack_super_extracts_partition_images_into_input_not_unpack(
    tmp_path, monkeypatch
):
    input_dir = tmp_path / "input"
    unpack_dir = tmp_path / "unpack"
    input_dir.mkdir()
    unpack_dir.mkdir()
    (input_dir / "super.img").write_bytes(b"super")
    calls = []

    from pathlib import Path

    from src.logic.projects.unpack.runtime_context import UnpackWorkflowRuntimeContext
    from src.logic.projects.unpack.workflow import service as workflow_service
    from src.logic.projects.unpack.workflow.source_handlers import extract_super_images

    def fake_unpack(image_path, output_dir, selected):
        calls.append((image_path, output_dir, tuple(selected)))
        (Path(output_dir) / "system_a.img").write_bytes(b"system")
        (Path(output_dir) / "vendor.img").write_bytes(b"vendor")

    def run_super(source, selected, parts, json_edit, *, output):
        return extract_super_images(
            source,
            selected,
            parts,
            json_edit,
            output=output,
            get_type=lambda _path: "super",
            get_info=lambda path: {"image": path},
            unpack_func=fake_unpack,
        )

    monkeypatch.setattr(workflow_service, "extract_super_images", run_super)

    class Output:
        def log(self, *_args, **_kwargs):
            pass

        def report(self, *_args, **_kwargs):
            pass

    runtime = UnpackWorkflowRuntimeContext(
        input_path=str(input_dir),
        work_path=str(unpack_dir),
        output_path=str(tmp_path / "output"),
        project_selected=True,
        tool_bin="",
        magisk_not_decompress="0",
        boot_skip_ramdisk="0",
        output=Output(),
    )

    assert (
        workflow_service.unpack(["system", "vendor"], "super", runtime=runtime) is True
    )
    assert calls == [
        (str(input_dir / "super.img"), str(input_dir), ("system", "vendor"))
    ]
    assert (input_dir / "system.img").exists()
    assert (input_dir / "vendor.img").exists()
    assert not (unpack_dir / "system.img").exists()
    assert not (unpack_dir / "vendor.img").exists()
    assert (unpack_dir / "config" / "parts_info").exists()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
