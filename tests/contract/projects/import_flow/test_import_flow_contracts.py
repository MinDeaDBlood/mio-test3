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


import gzip
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.app.projects import import_controller as import_controller_module
from src.app.projects.import_controller import (
    ProjectImportController,
    ProjectImportViewActions,
)
from src.logic.common.service_output import ServiceOutputEvent, build_service_output
from src.logic.projects.common.project_manager import ProjectManager
from src.logic.projects.common.runtime_context import build_project_path_runtime_context
from src.logic.projects.common.runtime_context import ProjectImportRuntimeContext
from src.logic.projects.import_flow.models import ProjectImportResult


def _runtime(
    workspace: Path,
    *,
    auto_unpack: str = "0",
    ofp_mtk_decrypt: bool | None = None,
    events: list[ServiceOutputEvent] | None = None,
) -> ProjectImportRuntimeContext:
    from tkinter import StringVar, Tcl

    current_project_name = StringVar(master=Tcl(), value="")
    return ProjectImportRuntimeContext(
        project_manager=ProjectManager(
            build_project_path_runtime_context(
                workspace_path=str(workspace),
                current_project_name=current_project_name,
            )
        ),
        auto_unpack=str(auto_unpack) == "1",
        tool_bin="",
        magisk_not_decompress="0",
        boot_skip_ramdisk="0",
        output=build_service_output(
            emit=(events.append if events is not None else lambda _event: None)
        ),
        ofp_mtk_decrypt=ofp_mtk_decrypt,
    )


def _write_single_file_pac(path: Path, *, name: str, payload: bytes) -> None:
    from src.core.unpac import FileTypes, SprdFile, SprdHead

    head = SprdHead()
    entry = SprdFile()
    entry.struct_size = len(entry)
    entry.type = FileTypes.file.value
    entry.size = len(payload)
    entry.pac_offset = len(head) + len(entry)
    for index, character in enumerate(name):
        entry.name[index] = ord(character)
    head.pac_size = entry.pac_offset + len(payload)
    head.file_count = 1
    head.dir_offset = len(head)
    head.pac_magic = 0xFFFAFFFA
    path.write_bytes(head.pack() + entry.pack() + payload)


def test_archive_helpers_extract_safe_members_and_reject_unsafe_paths() -> None:
    from src.logic.projects.import_flow.archive_handlers import (
        decode_zip_member_name,
        extract_gzip_payload,
        extract_zip_members,
        strip_gzip_suffix,
    )

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        source = root / "system.img.gz"
        target = root / "system.img"
        with gzip.open(source, "wb") as handle:
            handle.write(b"payload-data")

        assert strip_gzip_suffix(str(source)) == "system.img"
        extract_gzip_payload(str(source), str(target), chunk_size=4)
        assert target.read_bytes() == b"payload-data"

        archive_path = root / "rom.zip"
        output_dir = root / "out"
        output_dir.mkdir()
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("../escape.txt", b"bad")
            archive.writestr("/absolute.txt", b"bad")
            archive.writestr("safe/system.img", b"ok")

        members: list[str] = []
        errors: list[tuple[str, Exception]] = []
        extract_zip_members(
            str(archive_path),
            str(output_dir),
            on_member=members.append,
            on_error=lambda name, exc: errors.append((name, exc)),
        )

        assert members == ["safe/system.img"]
        assert len(errors) == 2
        assert not (root / "escape.txt").exists()
        assert (output_dir / "safe" / "system.img").read_bytes() == b"ok"
        assert decode_zip_member_name("system.img") == "system.img"


def test_archive_helpers_reject_zip_symlinks() -> None:
    from src.logic.projects.import_flow.archive_handlers import extract_zip_members

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        archive_path = root / "symlink.zip"
        output_dir = root / "out"
        output_dir.mkdir()
        info = zipfile.ZipInfo("linked")
        info.external_attr = 0o120777 << 16
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr(info, "../target")

        errors: list[tuple[str, Exception]] = []
        extract_zip_members(
            str(archive_path),
            str(output_dir),
            on_member=lambda _name: None,
            on_error=lambda name, exc: errors.append((name, exc)),
        )

        assert len(errors) == 1
        assert not (output_dir / "linked").exists()


def test_script2fs_writes_partition_filesystem_metadata() -> None:
    from src.logic.projects.import_flow.fs_config_conversion import script2fs

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "system" / "app").mkdir(parents=True)
        (root / "META-INF").mkdir()
        calls: list[tuple[object, ...]] = []

        class JsonStore:
            def __init__(self, path: str):
                self.path = path

            def read(self):
                return {}

            def write(self, data):
                calls.append(("write", self.path, dict(data)))

        def fake_script2fs_context(script: str, config_dir: str, path: str) -> None:
            calls.append(("context", script, config_dir, path))
            Path(config_dir, "system_fs_config").write_text("fs")

        script2fs(
            str(root),
            findfile_func=lambda name, root_path: str(Path(root_path) / name),
            script2fs_context_func=fake_script2fs_context,
            json_edit_cls=JsonStore,
        )

        assert calls[0][0] == "context"
        assert calls[-1][0] == "write"
        assert calls[-1][2]["system"] == "ext"


def test_handle_ofp_uses_explicit_decryption_mode_and_returns_result() -> None:
    from src.logic.projects.import_flow import format_handlers

    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        workspace.mkdir()
        runtime = _runtime(workspace, ofp_mtk_decrypt=False)
        calls: list[object] = []

        result = format_handlers.handle_ofp(
            str(Path(td) / "firmware.ofp"),
            runtime=runtime,
            ofp_mtk_decrypt=SimpleNamespace(
                main=lambda *_args, **_kwargs: calls.append("mtk")
            ),
            ofp_qc_decrypt=SimpleNamespace(
                main=lambda *_args, **_kwargs: calls.append("qc")
            ),
            script2fs_func=lambda path: calls.append(("script2fs", path)),
        )

        assert result == ProjectImportResult.success(project_name="firmware")
        assert calls[0] == "qc"
        assert Path(calls[1][1]) == workspace / "Projects" / "firmware" / "unpack"


def test_handle_ofp_requires_explicit_decryption_mode() -> None:
    from src.logic.projects.import_flow import format_handlers

    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        workspace.mkdir()
        runtime = _runtime(workspace)

        with pytest.raises(ValueError, match="explicit decryption mode"):
            format_handlers.handle_ofp(
                str(Path(td) / "firmware.ofp"),
                runtime=runtime,
                ofp_mtk_decrypt=SimpleNamespace(main=lambda *_args, **_kwargs: None),
                ofp_qc_decrypt=SimpleNamespace(main=lambda *_args, **_kwargs: None),
            )


def test_handle_pac_extracts_and_optionally_runs_unpack() -> None:
    from src.logic.projects.import_flow import format_handlers

    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        workspace.mkdir()
        runtime = _runtime(workspace, auto_unpack="1")
        source = Path(td) / "firmware.pac"
        _write_single_file_pac(source, name="system.img", payload=b"system-image")
        unpack_calls: list[tuple[list[str], object]] = []
        result = format_handlers.handle_pac(
            str(source),
            runtime=runtime,
            workflow_runtime="workflow-runtime",
            unpack_func=lambda selected, *, runtime=None: unpack_calls.append(
                (list(selected), runtime)
            ),
        )

        assert result == ProjectImportResult.success(project_name="firmware")
        assert unpack_calls == [(["system"], "workflow-runtime")]
        extracted = workspace / "Projects" / "firmware" / "unpack" / "system.img"
        assert extracted.read_bytes() == b"system-image"


def test_import_known_file_normalizes_image_and_returns_ui_neutral_result() -> None:
    from src.logic.projects.import_flow.generic_file_import import import_known_file

    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        workspace.mkdir()
        source_file = Path(td) / "imports" / "system.bin"
        source_file.parent.mkdir()
        source_file.write_bytes(b"raw-system")
        runtime = _runtime(workspace, auto_unpack="1")
        unpack_calls: list[tuple[list[str], object]] = []

        result = import_known_file(
            str(source_file),
            runtime=runtime,
            workflow_runtime="workflow-runtime",
            unpack_func=lambda selected, *, runtime=None: unpack_calls.append(
                (list(selected), runtime)
            ),
        )

        assert result == ProjectImportResult.success(project_name="system")
        project = workspace / "Projects" / "system"
        assert (project / "input" / "system.bin").read_bytes() == b"raw-system"
        assert (
            project / "unpack" / "system.img"
        ).read_bytes() == b"raw-system"
        assert (project / "output").is_dir()
        assert unpack_calls == [(["system"], "workflow-runtime")]


def test_import_project_folder_returns_result_without_touching_ui() -> None:
    from src.logic.projects.import_flow.project_folder_import import (
        import_project_folder,
    )

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        workspace = root / "workspace"
        workspace.mkdir()
        source = root / "imports" / "source-project"
        source.mkdir(parents=True)
        (source / "system.img").write_text("payload")
        runtime = _runtime(workspace)

        result = import_project_folder(str(source), runtime=runtime)

        assert result == ProjectImportResult.success(project_name="source-project")
        project = workspace / "Projects" / "source-project"
        assert (project / "system.img").read_text() == "payload"
        assert (project / "input").is_dir()
        assert (project / "unpack").is_dir()
        assert (project / "output").is_dir()


def test_import_project_folder_rejects_same_workspace_folder() -> None:
    from src.logic.projects.import_flow.project_folder_import import (
        import_project_folder,
    )

    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        source = workspace / "Projects" / "already-here"
        source.mkdir(parents=True)
        runtime = _runtime(workspace)

        result = import_project_folder(str(source), runtime=runtime)

        assert not result.imported
        assert result.error == "Source folder is already the selected project."


def test_import_zip_returns_failure_when_member_extraction_fails() -> None:
    from src.logic.projects.import_flow.zip_import import import_zip_rom

    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        workspace.mkdir()
        source_zip = Path(td) / "rom.zip"
        with zipfile.ZipFile(source_zip, "w") as archive:
            archive.writestr("../bad.img", b"unsafe")
        events: list[ServiceOutputEvent] = []
        runtime = _runtime(workspace, auto_unpack="1", events=events)

        result = import_zip_rom(
            str(source_zip),
            runtime=runtime,
            workflow_runtime="workflow-runtime",
            unpack_func=lambda *_args, **_kwargs: pytest.fail(
                "unpack must not run after extraction failure"
            ),
            script2fs_func=lambda _path: pytest.fail(
                "script2fs must not run after extraction failure"
            ),
        )

        assert not result.imported
        assert "Unsafe traversal archive member" in (result.error or "")
        assert any(event.channel.value == "status" for event in events)


def test_import_zip_success_runs_postprocessing_and_returns_result() -> None:
    from src.logic.projects.import_flow.zip_import import import_zip_rom

    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        workspace.mkdir()
        source_zip = Path(td) / "rom.zip"
        from src.core.android_sparse import split_raw_image_to_sparse_parts

        raw_image = Path(td) / "system.raw"
        raw_image.write_bytes(bytes((index * 17) % 256 for index in range(8192)))
        sparse_image = split_raw_image_to_sparse_parts(
            raw_image, Path(td) / "sparse", part_count=2
        ).output_paths[0]
        with zipfile.ZipFile(source_zip, "w") as archive:
            archive.write(sparse_image, "system.img")
        runtime = _runtime(workspace, auto_unpack="1")
        script_calls: list[str] = []
        unpack_calls: list[tuple[list[str], object]] = []

        result = import_zip_rom(
            str(source_zip),
            runtime=runtime,
            workflow_runtime="workflow-runtime",
            unpack_func=lambda selected, *, runtime=None: unpack_calls.append(
                (list(selected), runtime)
            ),
            script2fs_func=script_calls.append,
        )

        assert result == ProjectImportResult.success(project_name="rom")
        project = workspace / "Projects" / "rom"
        assert [Path(path) for path in script_calls] == [project / "unpack"]
        assert (project / "input" / "rom.zip").read_bytes() == source_zip.read_bytes()
        assert (project / "unpack" / "system.img").read_bytes() == sparse_image.read_bytes()
        assert (project / "output").is_dir()
        assert unpack_calls == [(["system"], "workflow-runtime")]


def test_project_import_controller_owns_ui_updates_and_ofp_confirmation(
    monkeypatch,
) -> None:
    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        workspace.mkdir()
        source = Path(td) / "firmware.ofp"
        source.write_bytes(b"ofp")
        runtime = _runtime(workspace)
        calls: list[tuple[object, ...]] = []
        captured_modes: list[bool | None] = []

        def fake_unpackrom(
            path: str, *, runtime: ProjectImportRuntimeContext
        ) -> ProjectImportResult:
            captured_modes.append(runtime.ofp_mtk_decrypt)
            assert path == str(source)
            return ProjectImportResult.success(project_name="firmware")

        monkeypatch.setattr(import_controller_module, "unpackrom", fake_unpackrom)
        controller = ProjectImportController(
            runtime=runtime,
            view_actions=ProjectImportViewActions(
                refresh_project_list=lambda: calls.append(("refresh_project_list",)),
                select_project=lambda name: calls.append(("select_project", name)),
                refresh_unpack=lambda auto: calls.append(("refresh_unpack", auto)),
                confirm_ofp_mtk_decrypt=lambda: calls.append(("confirm_ofp", False))
                or False,
            ),
        )

        result = controller.import_file(str(source))

        assert result == ProjectImportResult.success(project_name="firmware")
        assert captured_modes == [False]
        assert calls == [
            ("confirm_ofp", False),
            ("refresh_project_list",),
            ("select_project", "firmware"),
            ("refresh_unpack", True),
        ]


def test_project_import_controller_does_not_update_ui_after_failure(
    monkeypatch,
) -> None:
    with tempfile.TemporaryDirectory() as td:
        workspace = Path(td) / "workspace"
        workspace.mkdir()
        source = Path(td) / "broken.img"
        source.write_bytes(b"broken")
        runtime = _runtime(workspace)
        calls: list[tuple[object, ...]] = []

        monkeypatch.setattr(
            import_controller_module,
            "unpackrom",
            lambda _path, *, runtime: ProjectImportResult.failure("broken"),
        )
        controller = ProjectImportController(
            runtime=runtime,
            view_actions=ProjectImportViewActions(
                refresh_project_list=lambda: calls.append(("refresh_project_list",)),
                select_project=lambda name: calls.append(("select_project", name)),
                refresh_unpack=lambda auto: calls.append(("refresh_unpack", auto)),
                confirm_ofp_mtk_decrypt=lambda: True,
            ),
        )

        result = controller.import_file(str(source))

        assert result == ProjectImportResult.failure("broken")
        assert calls == []

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
