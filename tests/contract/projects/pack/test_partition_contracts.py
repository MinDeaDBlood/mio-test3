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
    _direct_relative = (
        _DirectPath(__file__)
        .resolve()
        .relative_to(_DIRECT_PROJECT_ROOT)
        .with_suffix("")
    )
    __package__ = ".".join(_direct_relative.parts[:-1])


import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace




def _pack_runtime(
    *,
    work_path: str = "/work/",
    input_path: str | None = None,
    output_path: str = "/out/",
    project_selected: bool = True,
    context_patch_enabled: bool = False,
    context_rule_file: str = "",
    tool_bin: str = "",
    magisk_not_decompress: str = "0",
    boot_skip_ramdisk: str = "0",
    output=None,
):
    from src.logic.projects.pack.runtime_context import PackPartitionRuntimeContext

    sink = output or SimpleNamespace(
        log=lambda *_args, **_kwargs: None,
        report=lambda *_args, **_kwargs: None,
        notify=lambda *_args, **_kwargs: None,
    )
    return PackPartitionRuntimeContext(
        input_path=input_path or work_path,
        work_path=work_path,
        output_path=output_path,
        project_selected=project_selected,
        context_patch_enabled=context_patch_enabled,
        context_rule_file=context_rule_file,
        tool_bin=tool_bin,
        magisk_not_decompress=magisk_not_decompress,
        boot_skip_ramdisk=boot_skip_ramdisk,
        output=sink,
    )


def test_pack_filesystem_size_helper() -> None:
    from src.logic.projects.pack.filesystem_service import GetFolderSize
    from src.logic.projects.pack import partition_size
    from src.logic.projects.pack.partition_size import (
        normalize_ext_image_size,
        resolve_configured_ext4_size,
        update_dynamic_partition_size,
    )

    class Output:
        def __init__(self):
            self.logs = []

        def log(self, message, **_kwargs):
            self.logs.append(message)

    assert normalize_ext_image_size(1) == 2 * 1024 * 1024
    assert normalize_ext_image_size(4097) == 2 * 1024 * 1024
    assert normalize_ext_image_size((3 * 1024 * 1024) + 1) % 4096 == 0
    assert partition_size._LARGE_IMAGE_PADDING == 16 * 1024 * 1024

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        system = root / "system"
        system.mkdir()
        (system / "build.prop").write_bytes(b"abc")
        op_list = root / "dynamic_partitions_op_list"
        op_list.write_text(
            "resize system 1\nresize system_a 2\n# Grow partition system from 0 to 3\n"
        )

        output = Output()
        update_dynamic_partition_size("system", 12345, str(op_list), output=output)
        content = op_list.read_text()
        assert "resize system 12345" in content
        assert "resize system_a 12345" in content
        assert "# Grow partition system from 0 to 12345" in content

        folder_size = GetFolderSize(
            str(system), num=1, get=3, list_f=str(op_list), output=output
        )
        assert folder_size.rsize_v >= 2 * 1024 * 1024
        assert "resize system " in op_list.read_text()
        assert output.logs

        op_list.write_text(
            "resize system 11\nresize system_a 22\nresize system_b broken\n"
        )
        assert (
            resolve_configured_ext4_size(
                str(root), "system", "", prefer_dynamic_resize=True
            )
            == 22
        )

        op_list.unlink()
        config_dir = root / "config"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "system_size.txt").write_text("33")
        assert (
            resolve_configured_ext4_size(
                str(root), "system", None, prefer_dynamic_resize=True
            )
            == 33
        )
        assert (
            resolve_configured_ext4_size(
                str(root), "system", "44", prefer_dynamic_resize=True
            )
            == 44
        )


def test_pack_partition_context_helper() -> None:
    from src.logic.projects.pack.partition_contexts import (
        prepare_partition_context_files,
    )

    class FakeJsonEdit:
        writes = []

        def __init__(self, path):
            self.path = path

        def read(self):
            return {"old_rule": "old"}

        def write(self, payload):
            self.writes.append((self.path, payload))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        work = str(root) + os.sep
        (root / "config").mkdir()
        (root / "system").mkdir()
        fs_config = root / "config" / "system_fs_config"
        contexts = root / "config" / "system_file_contexts"
        fs_config.write_text("/system/bin 0 0 0755\n")
        contexts.write_text("/system(/.*)? u:object_r:system_file:s0\n")
        calls = []

        deps = SimpleNamespace(
            fspatch_main=lambda path, cfg: calls.append(("fspatch", path, cfg)),
            contextpatch_main=lambda path, ctx, rule: calls.append(
                ("contextpatch", path, ctx, rule)
            ),
            contextpatch_scan_context=lambda ctx: {"new_rule": ctx},
            json_edit_cls=FakeJsonEdit,
            remove_duplicate_func=lambda path: calls.append(("dedupe", path)),
        )
        runtime = _pack_runtime(
            context_patch_enabled=True, context_rule_file=str(root / "rules.json")
        )
        request = SimpleNamespace(origin_fs="ext", modify_fs="erofs", fs_convert=True)
        parts = {"system": "ext"}

        result = prepare_partition_context_files(
            work=work,
            partition_name="system",
            request=request,
            parts_dict=parts,
            runtime=runtime,
            deps=deps,
        )

        assert result.endswith("system_file_contexts")
        assert parts["system"] == "erofs"
        assert any(call[0] == "fspatch" for call in calls)
        assert any(call[0] == "contextpatch" for call in calls)
        assert [call[0] for call in calls].count("dedupe") == 2
        assert FakeJsonEdit.writes and FakeJsonEdit.writes[0][1]["old_rule"] == "old"
        assert FakeJsonEdit.writes[0][1]["new_rule"].endswith("system_file_contexts")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        work = str(root) + os.sep
        (root / "config").mkdir()
        deps = SimpleNamespace()
        runtime = _pack_runtime(context_patch_enabled=False)
        request = SimpleNamespace(origin_fs="ext", modify_fs="erofs", fs_convert=True)
        parts = {"vendor": "ext"}
        result = prepare_partition_context_files(
            work=work,
            partition_name="vendor",
            request=request,
            parts_dict=parts,
            runtime=runtime,
            deps=deps,
        )
        assert result.endswith("vendor_file_contexts")
        assert parts["vendor"] == "erofs"


def test_pack_partition_output_helper() -> None:
    from src.logic.common.service_output import build_service_output
    from src.logic.projects.pack.partition_output import (
        finalize_partition_output,
        is_sparse_output_requested,
    )

    calls = []
    events = []
    output = build_service_output(emit=events.append)
    assert is_sparse_output_requested("dat") is True
    assert is_sparse_output_requested("br") is True
    assert is_sparse_output_requested("sparse") is True
    assert is_sparse_output_requested("img") is False

    assert (
        finalize_partition_output(
            output_format="br",
            output_dir="/tmp/out",
            partition_name="system",
            brotli_level="6",
            dat_version="4",
            apply_output_format_func=lambda *args, **kwargs: (
                calls.append((args, kwargs)) or True
            ),
            output=output,
        )
        is True
    )
    assert calls == [
        (
            ("br", "/tmp/out", "system"),
            {"brotli_level": 6, "dat_version": 4, "output": output},
        )
    ]
    assert events[-1].message.code == "created"
    assert events[-1].message.params["item"] == "system"

    assert (
        finalize_partition_output(
            output_format="br",
            output_dir="/tmp/out",
            partition_name="system",
            brotli_level=6,
            dat_version=4,
            apply_output_format_func=lambda *args, **kwargs: False,
            output=output,
        )
        is False
    )

    assert (
        finalize_partition_output(
            output_format="raw",
            output_dir="/tmp/out",
            partition_name="vendor",
            brotli_level=1,
            dat_version=4,
            apply_output_format_func=lambda *args, **kwargs: calls.append(
                (args, kwargs)
            ),
            output=output,
        )
        is True
    )
    assert len(calls) == 1
    assert events[-1].message.params["item"] == "vendor"


def test_pack_partition_special_helper() -> None:
    from src.logic.common.service_output import build_service_output
    from src.logic.projects.pack.partition_special import (
        pack_special_partition,
        patch_vbmeta_images,
    )

    calls = []
    events = []
    output = build_service_output(emit=events.append)

    class FakeVbpatch:
        def __init__(self, path):
            self.path = path

        def disavb(self):
            calls.append(("disavb", self.path))

    class FakeGuokeLogo:
        def pack(self, src, dst):
            calls.append(("guoke_logo", src, dst))

    deps = SimpleNamespace(
        findfile_func=lambda name, work: str(Path(work) / name),
        gettype_func=lambda path: "vbmeta" if path.endswith("vbmeta.img") else "other",
        vbpatch_factory=FakeVbpatch,
        repack_boot_func=lambda name, runtime: calls.append(("boot", name)),
        pack_dtbo_func=lambda runtime: calls.append(("dtbo",)),
        logo_pack_func=lambda runtime: calls.append(("logo",)),
        guoke_logo_cls=FakeGuokeLogo,
        splash_repack_func=lambda src, dst: calls.append(("splash", src, dst)),
    )

    with tempfile.TemporaryDirectory() as td:
        patch_vbmeta_images(td, False, deps, output=output)
        assert not calls
        patch_vbmeta_images(td, True, deps, output=output)
        assert calls == [("disavb", str(Path(td) / "vbmeta.img"))]
        assert events[-1].message.code == "patching_image"
        runtime = _pack_runtime(
            input_path=td,
            work_path=td,
            output_path=td,
            tool_bin=td,
            output=output,
        )
        assert pack_special_partition("boot", td, runtime, deps) is True
        assert pack_special_partition("vendor_boot", td, runtime, deps) is True
        assert pack_special_partition("dtbo", td, runtime, deps) is True
        assert pack_special_partition("logo", td, runtime, deps) is True
        assert pack_special_partition("guoke_logo", td, runtime, deps) is True
        assert pack_special_partition("splash", td, runtime, deps) is True
        assert pack_special_partition("system", td, runtime, deps) is False
        assert ("boot", "boot") in calls
        assert ("boot", "vendor_boot") in calls
        assert ("dtbo",) in calls
        assert ("logo",) in calls
        assert any(call[0] == "guoke_logo" for call in calls)
        assert (
            "splash",
            str(Path(td) / "splash"),
            str(Path(td) / "splash.img"),
        ) in calls


def test_pack_partition_filesystem_handlers() -> None:
    from src.logic.common.service_output import build_service_output
    from src.logic.projects.pack.partition_flow.filesystem_handlers import (
        PACKABLE_FILESYSTEM_TYPES,
        PackFilesystemHandlerRegistry,
        pack_filesystem_partition,
    )
    from src.logic.projects.pack.partition_flow.models import (
        Ext4SizeMode,
        PackPartitionRequest,
    )

    assert {"ext", "erofs", "f2fs"} <= set(PACKABLE_FILESYSTEM_TYPES)
    assert PackFilesystemHandlerRegistry().is_supported("ext") is True
    assert PackFilesystemHandlerRegistry().is_supported("erofs") is True
    assert PackFilesystemHandlerRegistry().is_supported("f2fs") is True
    assert PackFilesystemHandlerRegistry().is_supported("yaffs") is False

    class FakeProjectManager:
        def __init__(self, output_path):
            self._output_path = output_path

        def current_work_output_path(self):
            return self._output_path

    def _request(**overrides):
        payload = dict(
            chosen_parts=["system"],
            patch_vbmeta=False,
            remove_source_files=False,
            ext4_packer="make_ext4fs",
            ext4_size_mode=Ext4SizeMode.FIXED,
            output_format="raw",
            erofs_compress_format="lz4hc",
            erofs_level=7,
            brotli_level=5,
            utc=123,
            origin_fs="ext",
            modify_fs="ext",
            fs_convert=False,
            erofs_old_kernel=False,
            custom_size={},
        )
        payload.update(overrides)
        return PackPartitionRequest(**payload)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        work = str(root) + os.sep
        output_dir = str(root / "out")
        (root / "out").mkdir()
        (root / "config").mkdir()
        (root / "system").mkdir()
        (root / "vendor").mkdir()
        (root / "product").mkdir()
        (root / "config" / "system_fs_config").write_text("/system 0 0 0755\n")
        (root / "config" / "system_file_contexts").write_text(
            "/system u:object_r:system_file:s0\n"
        )
        (root / "dynamic_partitions_op_list").write_text("resize system 999\n")

        calls = []
        events = []
        deps = SimpleNamespace(
            fspatch_main=lambda path, cfg: calls.append(("fspatch", path, cfg)),
            contextpatch_main=lambda path, ctx, rule: calls.append(
                ("contextpatch", path, ctx, rule)
            ),
            contextpatch_scan_context=lambda ctx: {},
            json_edit_cls=lambda _path: SimpleNamespace(
                read=lambda: {}, write=lambda _data: None
            ),
            remove_duplicate_func=lambda path: calls.append(("dedupe", path)),
            mkerofs_func=lambda *args, **kwargs: (
                calls.append(("erofs", args, kwargs)) or 0
            ),
            make_f2fs_func=lambda *args, **kwargs: (
                calls.append(("f2fs", args, kwargs)) or 0
            ),
            make_ext4fs_func=lambda *args, **kwargs: (
                calls.append(("ext4fs", args, kwargs)) or 0
            ),
            mke2fs_func=lambda *args, **kwargs: (
                calls.append(("mke2fs", args, kwargs)) or 0
            ),
            apply_output_format_func=lambda *args, **kwargs: (
                calls.append(("finalize", args, kwargs)) or True
            ),
            rdi_func=lambda work_arg, part, output=None: (
                calls.append(("rdi", work_arg, part)) or True
            ),
        )
        runtime = _pack_runtime(
            work_path=work,
            output_path=output_dir,
            context_rule_file=str(root / "rules.json"),
            output=build_service_output(emit=events.append),
        )

        parts = {"system": "ext", "dat_ver": "4"}
        assert (
            pack_filesystem_partition(
                work=work,
                partition_name="system",
                request=_request(custom_size={"system": 999}),
                parts_dict=parts,
                runtime=runtime,
                deps=deps,
            )
            is True
        )
        ext_call = next(call for call in calls if call[0] == "ext4fs")
        assert ext_call[2]["size"] == 999
        assert ext_call[2]["sparse"] is False
        assert ext_call[2]["output"] is runtime.output
        assert ext_call[2]["has_contexts"] is True

        parts = {"vendor": "erofs"}
        assert (
            pack_filesystem_partition(
                work=work,
                partition_name="vendor",
                request=_request(
                    erofs_compress_format="zstd", erofs_level=3, erofs_old_kernel=True
                ),
                parts_dict=parts,
                runtime=runtime,
                deps=deps,
            )
            is True
        )
        erofs_call = next(call for call in calls if call[0] == "erofs")
        assert erofs_call[1][:2] == ("vendor", "zstd")
        assert erofs_call[2]["level"] == 3
        assert erofs_call[2]["old_kernel"] is True
        assert erofs_call[2]["output"] is runtime.output

        parts = {"product": "f2fs"}
        assert (
            pack_filesystem_partition(
                work=work,
                partition_name="product",
                request=_request(
                    remove_source_files=True, output_format="br", brotli_level=6
                ),
                parts_dict=parts,
                runtime=runtime,
                deps=deps,
            )
            is True
        )
        assert any(call[0] == "f2fs" for call in calls)
        assert any(call[0] == "rdi" and call[2] == "product" for call in calls)
        finalize_call = [call for call in calls if call[0] == "finalize"][-1]
        assert finalize_call[1][:3] == ("br", output_dir, "product")
        assert finalize_call[2]["brotli_level"] == 6
        assert finalize_call[2]["output"] is runtime.output
        assert calls.index(finalize_call) < next(
            i
            for i, call in enumerate(calls)
            if call[0] == "rdi" and call[2] == "product"
        )

        failing_deps = SimpleNamespace(
            **{
                **deps.__dict__,
                "apply_output_format_func": lambda *args, **kwargs: False,
            }
        )
        assert (
            pack_filesystem_partition(
                work=work,
                partition_name="product",
                request=_request(output_format="br", remove_source_files=True),
                parts_dict={"product": "f2fs"},
                runtime=runtime,
                deps=failing_deps,
            )
            is False
        )
        assert any(event.message.code == "operation_failed" for event in events)


def test_pack_selected_partitions_stops_on_filesystem_failure_and_patches_vbmeta_once() -> (
    None
):
    from src.logic.projects.pack.partition_flow.models import (
        Ext4SizeMode,
        PackPartitionRequest,
    )
    from src.logic.projects.pack.partition_flow.service import pack_selected_partitions

    class FakeJsonEdit:
        def __init__(self, _path):
            pass

        def read(self):
            return {"system": "ext", "vendor": "ext"}

    class FakeProjectManager:
        def exist(self):
            return True

        def current_work_path(self):
            return "/work/"

        def current_work_output_path(self):
            return "/out/"

    calls = []
    deps = SimpleNamespace(
        json_edit_cls=FakeJsonEdit,
        findfile_func=lambda name, work: str(Path(work) / name),
        gettype_func=lambda path: "other",
        vbpatch_factory=lambda path: SimpleNamespace(
            disavb=lambda: calls.append(("vbmeta", path))
        ),
        fspatch_main=lambda path, cfg: None,
        contextpatch_main=lambda path, ctx, rule: None,
        contextpatch_scan_context=lambda ctx: {},
        remove_duplicate_func=lambda path: None,
        mkerofs_func=lambda *args, **kwargs: 0,
        make_f2fs_func=lambda *args, **kwargs: 0,
        make_ext4fs_func=lambda *args, **kwargs: (
            calls.append(("pack", kwargs["name"]))
            or (1 if kwargs["name"] == "system" else 0)
        ),
        mke2fs_func=lambda *args, **kwargs: 0,
        apply_output_format_func=lambda *args, **kwargs: True,
        rdi_func=lambda work, part, output=None: calls.append(("rdi", part)) or True,
        repack_boot_func=lambda name: None,
        pack_dtbo_func=lambda: None,
        logo_pack_func=lambda: None,
        guoke_logo_cls=lambda: None,
    )
    request = PackPartitionRequest(
        chosen_parts=["system", "vendor"],
        patch_vbmeta=True,
        remove_source_files=False,
        ext4_packer="make_ext4fs",
        ext4_size_mode=Ext4SizeMode.AUTO,
        output_format="raw",
        erofs_compress_format="lz4hc",
        erofs_level=0,
        brotli_level=0,
        utc=123,
        origin_fs="ext",
        modify_fs="ext",
        fs_convert=False,
        erofs_old_kernel=False,
        custom_size={},
    )

    assert (
        pack_selected_partitions(
            request, _pack_runtime(work_path="/work/", output_path="/out/"), deps
        )
        is False
    )
    assert calls == [("pack", "system")]


def test_pack_partition_window_form_captures_all_visible_options(monkeypatch) -> None:
    from types import SimpleNamespace

    from src.app.localization_runtime import LangUtils
    from src.app.projects.pack.partition_controller import PartitionPackController
    from src.logic.projects.pack.partition_flow import Ext4SizeMode
    from src.ui.common.technical_choices import LocalizedChoiceSet
    from src.ui.tabs.project.pack.partition import keys
    from src.ui.tabs.project.pack.partition.window import PackPartition

    class Var:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    class ChoiceWidget:
        def __init__(self, index):
            self.index = index

        def current(self):
            return self.index

    instance = object.__new__(PackPartition)
    instance.chosen_parts = ["vendor"]
    instance.custom_size = {"vendor": "123456"}
    instance.spatchvb = Var(1)
    instance.remove_source_files = Var(1)
    instance._ext4_packer_choices = LocalizedChoiceSet(
        values=("make_ext4fs", "mke2fs+e2fsdroid"),
        labels=("make_ext4fs", "mke2fs + e2fsdroid"),
    )
    instance._output_format_choices = LocalizedChoiceSet(
        values=("raw", "sparse", "dat", "br"),
        labels=("raw", "sparse", "new.dat", "new.dat.br"),
    )
    instance._erofs_compression_choices = LocalizedChoiceSet(
        values=("lz4", "lz4hc", "lzma", "deflate", "zstd"),
        labels=("LZ4", "LZ4HC", "LZMA", "Deflate", "Zstandard"),
    )
    instance._filesystem_choices = LocalizedChoiceSet(
        values=("ext", "f2fs", "erofs"),
        labels=("EXT4", "F2FS", "EROFS"),
    )
    instance.ext4_packer = Var("mke2fs + e2fsdroid")
    instance.ext4_packer_box = ChoiceWidget(1)
    instance._texts = LangUtils()
    instance._texts.load_map(
        {keys.PROJECT_PACK_PARTITION_WINDOW_SAME_AS_ORIGINAL: "fixed"}
    )
    instance.ext4_method = Var("fixed")
    instance.ext4_size_mode_box = ChoiceWidget(1)
    instance.format = Var("new.dat.br")
    instance.output_format_box = ChoiceWidget(3)
    instance.erofs_compress_format = Var("Zstandard")
    instance.erofs_compression_box = ChoiceWidget(4)
    instance.scale_erofs = Var(7)
    instance.scale = Var(9)
    instance.UTC = Var("1778608927")
    instance.origin_fs = Var("EXT4")
    instance.origin_fs_box = ChoiceWidget(0)
    instance.modify_fs = Var("EROFS")
    instance.modify_fs_box = ChoiceWidget(2)
    instance.fs_conver = Var(True)
    instance.erofs_old_kernel = Var(True)

    form = instance._collect_form_values()

    assert form == {
        "chosen_parts": ["vendor"],
        "patch_vbmeta": True,
        "remove_source_files": True,
        "ext4_packer": "mke2fs+e2fsdroid",
        "ext4_size_mode": "fixed",
        "output_format": "br",
        "erofs_compress_format": "zstd",
        "erofs_level": 7,
        "brotli_level": 9,
        "utc": "1778608927",
        "origin_fs": "ext",
        "modify_fs": "erofs",
        "fs_convert": True,
        "erofs_old_kernel": True,
        "custom_size": {"vendor": "123456"},
    }

    captured = {}
    controller = object.__new__(PartitionPackController)
    controller.runtime = SimpleNamespace(
        workflow=SimpleNamespace(
            marker="workflow",
            work_path="/work",
            output_path="/output",
        )
    )
    controller.dependencies = SimpleNamespace()
    controller.project_exists = lambda: True
    controller.notify_before_pack = lambda: None
    controller.notify_packing_start = lambda: None
    controller.prepare_request = lambda request: request

    def capture_pack(request, runtime, dependencies):
        captured["request"] = request
        captured["runtime"] = runtime
        captured["dependencies"] = dependencies
        return True

    monkeypatch.setattr(
        "src.app.projects.pack.partition_controller.pack_selected_partitions",
        capture_pack,
    )
    assert controller.execute_form(form) is True
    request = captured["request"]

    assert request.chosen_parts == ["vendor"]
    assert request.patch_vbmeta is True
    assert request.remove_source_files is True
    assert request.ext4_packer == "mke2fs+e2fsdroid"
    assert request.ext4_size_mode is Ext4SizeMode.FIXED
    assert request.output_format == "br"
    assert request.erofs_compress_format == "zstd"
    assert request.erofs_level == 7
    assert request.brotli_level == 9
    assert request.utc == 1778608927
    assert request.origin_fs == "ext"
    assert request.modify_fs == "erofs"
    assert request.fs_convert is True
    assert request.erofs_old_kernel is True
    assert request.custom_size == {"vendor": "123456"}

    invalid_form = dict(form, utc="bad")
    try:
        controller.validate_form(invalid_form)
    except ValueError as exc:
        assert str(exc) == "pack_partition_utc_invalid"
    else:
        raise AssertionError("Invalid UTC must be rejected instead of replaced.")


def test_partition_pack_hooks_run_only_when_execution_starts(monkeypatch) -> None:
    from types import SimpleNamespace

    from src.app.projects.pack.partition_controller import PartitionPackController

    events: list[str] = []
    controller = object.__new__(PartitionPackController)
    controller.runtime = SimpleNamespace(
        workflow=SimpleNamespace(
            project_selected=True,
            work_path="/work",
            output_path="/output",
        )
    )
    controller.dependencies = SimpleNamespace()
    controller.notify_before_pack = lambda: events.append("before_pack")
    controller.notify_packing_start = lambda: events.append("packing")
    controller.prepare_request = lambda request: request

    monkeypatch.setattr(
        "src.app.projects.pack.partition_controller.pack_selected_partitions",
        lambda request, runtime, dependencies: events.append("pack") or True,
    )

    form = {
        "chosen_parts": ["system"],
        "patch_vbmeta": False,
        "remove_source_files": False,
        "ext4_packer": "make_ext4fs",
        "ext4_size_mode": "auto",
        "output_format": "raw",
        "erofs_compress_format": "lz4hc",
        "erofs_level": 0,
        "brotli_level": 0,
        "utc": 0,
        "origin_fs": "ext",
        "modify_fs": "ext",
        "fs_convert": False,
        "erofs_old_kernel": False,
        "custom_size": {},
    }

    assert controller.execute_form(form) is True
    assert events == ["before_pack", "packing", "pack"]


def test_open_partition_pack_does_not_trigger_before_pack(monkeypatch) -> None:
    from types import SimpleNamespace

    import src.app.composition.partition_pack as composition

    events: list[str] = []
    fake_controller = SimpleNamespace(
        notify_before_pack=lambda: events.append("before_pack")
    )
    fake_window = object()

    monkeypatch.setattr(
        composition, "resolve_pack_partition_host_window", lambda: object()
    )
    monkeypatch.setattr(
        composition,
        "build_ui_notifier",
        lambda **kwargs: SimpleNamespace(show=lambda *args: None),
    )
    monkeypatch.setattr(
        composition, "build_ui_service_output", lambda **kwargs: object()
    )
    monkeypatch.setattr(
        composition, "build_pack_partition_runtime", lambda **kwargs: object()
    )
    monkeypatch.setattr(composition, "resolve_animation", lambda: object())
    monkeypatch.setattr(
        composition, "PartitionPackController", lambda **kwargs: fake_controller
    )
    monkeypatch.setattr(
        composition, "PackPartition", lambda *args, **kwargs: fake_window
    )

    assert composition.open_partition_pack(["system"]) is fake_window
    assert events == []


def test_pack_partition_window_boundaries() -> None:
    from src.logic.projects.pack.partition_flow import (
        build_default_pack_partition_dependencies,
    )
    from src.logic.projects.pack.partition_flow.service import PackPartitionDependencies

    deps = build_default_pack_partition_dependencies()
    assert isinstance(deps, PackPartitionDependencies)
    assert callable(deps.make_ext4fs_func)
    assert callable(deps.mkerofs_func)
    assert callable(deps.make_f2fs_func)
    assert callable(deps.pack_dtbo_func)
    assert callable(deps.repack_boot_func)

    window_source = Path("src/ui/tabs/project/pack/partition/window.py").read_text(
        encoding="utf-8"
    )
    controller_source = Path("src/app/projects/pack/partition_controller.py").read_text(
        encoding="utf-8"
    )
    composition_source = Path("src/app/composition/partition_pack.py").read_text(
        encoding="utf-8"
    )

    assert "build_default_pack_partition_dependencies" not in window_source
    assert "build_pack_partition_runtime" not in window_source
    assert "resolve_pack_partition_host_window" not in window_source
    assert "subprocess" not in window_source
    assert "threading" not in window_source
    assert "edit_custom_ext4_sizes(" in window_source
    assert "build_default_pack_partition_dependencies()" in controller_source
    assert "build_pack_partition_runtime(" in composition_source
    assert "resolve_pack_partition_host_window()" in composition_source
    assert "PackPartitionRequest" not in window_source
    assert "Ext4SizeMode" not in window_source
    assert "PackPartitionRequest" in controller_source
    assert "Ext4SizeMode.FIXED" not in window_source
    assert "Ext4SizeMode.FIXED" in controller_source
    assert "lang.t33" not in controller_source


def test_pack_super_window_boundaries() -> None:
    from src.logic.projects.pack.super import planning as super_planning
    from src.logic.projects.pack.super.planning import (
        PackSuperInitialState,
        scan_packable_super_images,
        validate_super_size,
    )

    window_source = Path("src/ui/tabs/project/pack/super/window.py").read_text(
        encoding="utf-8"
    )
    controller_source = Path("src/app/projects/pack/super_controller.py").read_text(
        encoding="utf-8"
    )
    composition_source = Path("src/app/composition/super_pack.py").read_text(
        encoding="utf-8"
    )

    assert "build_pack_super_window_runtime" not in window_source
    assert "build_window_task_runner" not in window_source
    assert "build_host_task_runner" not in window_source
    assert "scan_packable_super_images" not in window_source
    assert "validate_super_size" not in window_source
    assert "generate_super_dynamic_list" not in window_source
    assert "os.listdir(" not in window_source
    assert "os.path.getsize(" not in window_source
    assert "scan_packable_super_images" in controller_source
    assert "validate_super_size" in controller_source
    assert "generate_super_dynamic_list" in controller_source
    assert "build_pack_super_window_runtime()" in composition_source
    assert "build_window_task_runner" in composition_source
    assert "build_host_task_runner" in composition_source

    service_source = Path("src/logic/projects/pack/super/service.py").read_text(
        encoding="utf-8"
    )
    assert "fallback_work" not in service_source
    assert "PackSuperResult" in service_source
    assert "super_pack_report.json" in service_source

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "system.img").write_bytes(b"1234")
        (root / "vendor.img").write_bytes(b"5678")
        original_gettype = super_planning.gettype
        original_is_empty_img = super_planning.is_empty_img
        try:
            super_planning.gettype = lambda path: (
                "ext" if path.endswith("system.img") else "erofs"
            )
            super_planning.is_empty_img = lambda path: path.endswith("vendor.img")
            entries = scan_packable_super_images(root, selected=["system"])
        finally:
            super_planning.gettype = original_gettype
            super_planning.is_empty_img = original_is_empty_img
        from src.ui.tabs.project.pack.super.presenter import format_packable_super_image

        language_values = json.loads(
            Path("languages/English.json").read_text(encoding="utf-8")
        )
        texts = SimpleNamespace(
            resolve_required_ui_text=lambda key: language_values[key]
        )
        labels = {
            entry.name: (
                format_packable_super_image(entry, texts=texts),
                entry.selected,
            )
            for entry in entries
        }
        assert labels["system"] == ("system [EXT4]", True)
        assert labels["vendor"] == ("vendor [Empty image]", False)

        result = validate_super_size(root, ["system"], requested_size=4)
        assert result.valid is True
        too_small = validate_super_size(root, ["system", "vendor"], requested_size=1)
        assert too_small.valid is False
        assert too_small.suggested_size >= 8

        sparse_header = __import__("struct").pack(
            "<I4H4I", 0xED26FF3A, 1, 0, 28, 12, 4096, 10, 0, 0
        )
        (root / "vendor_sparse.img").write_bytes(sparse_header)
        sparse_result = validate_super_size(
            root, ["vendor_sparse"], requested_size=4096 * 9
        )
        assert sparse_result.valid is False
        assert sparse_result.suggested_size >= 4096 * 10

        from src.logic.projects.pack.super.service import pack_super

        output_root = root / "Output"
        output_root.mkdir()
        command = pack_super(
            sparse=True,
            group_name="qti_dynamic_partitions",
            size=9126805504,
            super_type=1,
            part_list=["vendor"],
            return_cmd=1,
            work=str(root) + os.sep,
            output_dir=str(output_root) + os.sep,
        )
        assert f"vendor={root}{os.sep}vendor.img" in command
        assert command[-2:] == ["--out", f"{output_root}{os.sep}super.img"]
        assert "super:9126805504" in command
        assert "--sparse" in command

        rebuilt = output_root / "vendor.img"
        rebuilt.write_bytes(b"rebuilt")
        fallback_command = pack_super(
            sparse=True,
            group_name="qti_dynamic_partitions",
            size=9126805504,
            super_type=1,
            part_list=["vendor"],
            return_cmd=1,
            work=str(output_root),
            source_dirs=[str(root)],
            output_dir=str(output_root),
        )
        assert f"vendor={rebuilt}" in fallback_command

        result_missing = validate_super_size(
            root, ["missing_vendor"], requested_size=9126805504
        )
        assert result_missing.valid is False
        assert result_missing.missing and result_missing.missing[0].endswith(
            "missing_vendor.img"
        )

        state = PackSuperInitialState(
            block_device_name="super",
            super_size=123,
            group_name="main",
            super_type=2,
            selected=("system",),
        )
        assert state.selected == ("system",)

        config = root / "config"
        config.mkdir()
        (config / "parts_info").write_text(
            json.dumps(
                {
                    "super_info": {
                        "block_devices": [{"name": "super", "size": 9126805504}],
                        "group_table": [{"name": "default"}, {"name": "main_b"}],
                        "partition_table": [{"name": "vendor"}],
                    }
                }
            ),
            encoding="utf-8",
        )
        source_state = super_planning.load_pack_super_initial_state(root)
        assert source_state.super_size == 9126805504
        assert source_state.group_name is None
        assert source_state.selected == ("vendor",)

        (root / "dynamic_partitions_op_list").write_text(
            "remove_all_groups\nadd_group main_a 9126805504\nadd_group main_b 9126805504\nadd vendor_a main_a\nadd vendor_b main_b\n",
            encoding="utf-8",
        )
        generated_state = super_planning.load_pack_super_initial_state(root)
        assert generated_state.group_name == "main"
        assert generated_state.super_type == 2
        assert generated_state.selected == ("vendor",)


def test_pack_window_request_boundaries() -> None:
    super_composition = Path("src/app/composition/super_pack.py").read_text(
        encoding="utf-8"
    )
    payload_composition = Path("src/app/composition/payload_pack.py").read_text(
        encoding="utf-8"
    )
    assert "PackSuper" in super_composition
    assert "SuperPackController" in super_composition
    assert "PayloadPackUnavailableWindow" in payload_composition
    assert not Path("src/logic/projects/pack/super/controller.py").exists()
    assert not Path("src/logic/projects/pack/payload/controller.py").exists()


def test_pack_payload_capability_contract() -> None:
    from src.logic.projects.pack.payload import service as payload_service

    project_root = Path(__file__).resolve().parent
    audit = payload_service.audit_implementation(project_root)
    assert audit.has_registered_pipeline is False
    assert audit.has_generator_backend is False, audit.evidence

    capability = payload_service.get_capability("Windows", project_root=project_root)
    assert capability.available is False
    assert capability.platform_name == "Windows"
    assert capability.audit is not None
    assert capability.audit.has_generator_backend is False
    assert "no verified payload generator pipeline" in capability.reason

    with tempfile.TemporaryDirectory() as d:
        candidate_root = Path(d)
        candidate_bin = candidate_root / "bin"
        candidate_bin.mkdir(parents=True)
        (candidate_bin / "brillo_update_payload").write_text(
            "#!/bin/sh\nexit 0\n", encoding="utf-8"
        )
        backend_audit = payload_service.audit_implementation(candidate_root)
        assert backend_audit.has_generator_backend is True
        assert backend_audit.evidence == ("bin/brillo_update_payload",)
        backend_capability = payload_service.get_capability(
            "Linux", project_root=candidate_root
        )
        assert backend_capability.available is False
        assert backend_capability.audit is not None
        assert backend_capability.audit.has_generator_backend is True


def run_all() -> None:
    test_pack_filesystem_size_helper()
    test_pack_partition_context_helper()
    test_pack_partition_output_helper()
    test_pack_partition_special_helper()
    test_pack_partition_filesystem_handlers()
    test_pack_partition_window_boundaries()
    test_pack_super_window_boundaries()
    test_pack_window_request_boundaries()
    test_pack_payload_capability_contract()


if __name__ == "__main__":
    run_all()
    print("PACK_PARTITION_CONTRACT_TESTS_OK")


def test_fixed_ext4_original_size_failure_gets_actionable_message() -> None:
    from src.logic.common.service_output import build_service_output
    from src.logic.projects.pack.partition_flow.filesystem_handlers import (
        pack_filesystem_partition,
    )
    from src.logic.projects.pack.partition_flow.models import (
        Ext4SizeMode,
        PackPartitionRequest,
    )

    class FakeProjectManager:
        def __init__(self, output_path):
            self._output_path = output_path

        def current_work_output_path(self):
            return self._output_path

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        work = str(root) + os.sep
        output_dir = str(root / "out")
        (root / "out").mkdir()
        (root / "vendor").mkdir()
        (root / "config").mkdir()
        (root / "dynamic_partitions_op_list").write_text("resize vendor 1024\n")
        (root / "vendor" / "large.bin").write_bytes(b"x" * (3 * 1024 * 1024))

        deps = SimpleNamespace(
            fspatch_main=lambda path, cfg: None,
            contextpatch_main=lambda path, ctx, rule: None,
            contextpatch_scan_context=lambda ctx: {},
            json_edit_cls=lambda _path: SimpleNamespace(
                read=lambda: {}, write=lambda _data: None
            ),
            remove_duplicate_func=lambda path: None,
            mkerofs_func=lambda *args, **kwargs: 0,
            make_f2fs_func=lambda *args, **kwargs: 0,
            make_ext4fs_func=lambda *args, **kwargs: 1,
            mke2fs_func=lambda *args, **kwargs: 0,
            apply_output_format_func=lambda *args, **kwargs: True,
            rdi_func=lambda work, part, output=None: True,
        )
        events = []
        runtime = _pack_runtime(
            work_path=work,
            output_path=output_dir,
            output=build_service_output(emit=events.append),
        )
        request = PackPartitionRequest(
            chosen_parts=["vendor"],
            patch_vbmeta=False,
            remove_source_files=False,
            ext4_packer="make_ext4fs",
            ext4_size_mode=Ext4SizeMode.FIXED,
            output_format="raw",
            erofs_compress_format="lz4hc",
            erofs_level=0,
            brotli_level=0,
            utc=123,
            origin_fs="ext",
            modify_fs="ext",
            fs_convert=False,
            erofs_old_kernel=False,
            custom_size={"vendor": 1024},
        )

        assert (
            pack_filesystem_partition(
                work=work,
                partition_name="vendor",
                request=request,
                parts_dict={"vendor": "ext"},
                runtime=runtime,
                deps=deps,
            )
            is False
        )

        rendered = [event.message.render_default() for event in events]
        assert any(
            "selected EXT4 size 1024 bytes may be too small" in line
            for line in rendered
        )
        assert any(
            "build failed with fixed EXT4 size 1024 bytes" in line for line in rendered
        )
        assert any(
            "Switch Size to Auto or increase the custom size" in line
            for line in rendered
        )


def test_ext4_size_fit_helper_reports_missing_bytes() -> None:
    from src.logic.projects.pack.partition_size import check_ext4_size_fit

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        partition = root / "vendor"
        partition.mkdir()
        (partition / "large.bin").write_bytes(b"x" * (3 * 1024 * 1024))

        result = check_ext4_size_fit(str(partition), 1024)
        assert result.requested_size == 1024
        assert result.recommended_size > result.requested_size
        assert result.missing_bytes == result.recommended_size - result.requested_size
        assert result.fits is False

        auto = check_ext4_size_fit(str(partition), 0)
        assert auto.fits is True


def test_contextpatch_zero_skips_context_rule_patch_even_when_contexts_exist_without_fs_config() -> (
    None
):
    from src.logic.projects.pack.partition_contexts import (
        prepare_partition_context_files,
    )

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        work = str(root) + os.sep
        (root / "config").mkdir()
        (root / "system").mkdir()
        contexts = root / "config" / "system_file_contexts"
        contexts.write_text("/system(/.*)? u:object_r:system_file:s0\n")
        calls = []

        deps = SimpleNamespace(
            fspatch_main=lambda path, cfg: calls.append(("fspatch", path, cfg)),
            contextpatch_main=lambda path, ctx, rule: calls.append(
                ("contextpatch", path, ctx, rule)
            ),
            contextpatch_scan_context=lambda ctx: {"new_rule": ctx},
            json_edit_cls=lambda _path: SimpleNamespace(
                read=lambda: {}, write=lambda _data: None
            ),
            remove_duplicate_func=lambda path: calls.append(("dedupe", path)),
        )
        runtime = _pack_runtime(
            context_patch_enabled=False, context_rule_file=str(root / "rules.json")
        )
        request = SimpleNamespace(origin_fs="ext", modify_fs="ext", fs_convert=False)
        parts = {"system": "ext"}

        result = prepare_partition_context_files(
            work=work,
            partition_name="system",
            request=request,
            parts_dict=parts,
            runtime=runtime,
            deps=deps,
        )

        assert result.endswith("system_file_contexts")
        assert ("dedupe", str(contexts)) in calls
        assert not any(call[0] == "contextpatch" for call in calls)
        assert not any(call[0] == "fspatch" for call in calls)


def test_contextpatch_one_patches_contexts_even_when_fs_config_is_missing() -> None:
    from src.logic.projects.pack.partition_contexts import (
        prepare_partition_context_files,
    )

    class FakeJsonEdit:
        writes = []

        def __init__(self, path):
            self.path = path

        def read(self):
            return {"old_rule": "old"}

        def write(self, payload):
            self.writes.append((self.path, payload))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        work = str(root) + os.sep
        (root / "config").mkdir()
        (root / "system").mkdir()
        contexts = root / "config" / "system_file_contexts"
        contexts.write_text("/system(/.*)? u:object_r:system_file:s0\n")
        calls = []

        deps = SimpleNamespace(
            fspatch_main=lambda path, cfg: calls.append(("fspatch", path, cfg)),
            contextpatch_main=lambda path, ctx, rule: calls.append(
                ("contextpatch", path, ctx, rule)
            ),
            contextpatch_scan_context=lambda ctx: {"new_rule": ctx},
            json_edit_cls=FakeJsonEdit,
            remove_duplicate_func=lambda path: calls.append(("dedupe", path)),
        )
        runtime = _pack_runtime(
            context_patch_enabled=True, context_rule_file=str(root / "rules.json")
        )
        request = SimpleNamespace(origin_fs="ext", modify_fs="ext", fs_convert=False)
        parts = {"system": "ext"}

        result = prepare_partition_context_files(
            work=work,
            partition_name="system",
            request=request,
            parts_dict=parts,
            runtime=runtime,
            deps=deps,
        )

        assert result.endswith("system_file_contexts")
        assert not any(call[0] == "fspatch" for call in calls)
        assert any(call[0] == "contextpatch" for call in calls)
        assert ("dedupe", str(contexts)) in calls
        assert FakeJsonEdit.writes and FakeJsonEdit.writes[0][1]["new_rule"].endswith(
            "system_file_contexts"
        )
