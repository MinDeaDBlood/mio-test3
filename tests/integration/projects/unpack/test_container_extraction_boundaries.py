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

from src.logic.projects.unpack.runtime_context import UnpackWorkflowRuntimeContext
from src.logic.projects.unpack.workflow import service as workflow_service
from src.logic.projects.unpack.workflow.source_handlers import (
    extract_payload_images,
    extract_update_app_images,
)


class Output:
    def __init__(self) -> None:
        self.logs: list[str] = []
        self.reports: list[str] = []

    def log(self, text, *args, **kwargs) -> None:
        self.logs.append(str(text))

    def report(self, text, *args, **kwargs) -> None:
        self.reports.append(str(text))


def _runtime(
    input_dir: Path, unpack_dir: Path, output: Output | None = None
) -> UnpackWorkflowRuntimeContext:
    return UnpackWorkflowRuntimeContext(
        input_path=str(input_dir),
        work_path=str(unpack_dir),
        output_path=str(unpack_dir.parent / "output"),
        project_selected=True,
        tool_bin="",
        magisk_not_decompress="0",
        boot_skip_ramdisk="0",
        output=output or Output(),
    )


def test_payload_extracts_partition_images_into_input_not_unpack(
    tmp_path, monkeypatch
) -> None:
    input_dir = tmp_path / "input"
    unpack_dir = tmp_path / "unpack"
    input_dir.mkdir()
    unpack_dir.mkdir()
    (input_dir / "payload.bin").write_bytes(b"payload")
    calls = []

    def fake_extract(stream, selected, output_dir, workers):
        calls.append((stream.read(), tuple(selected), output_dir, workers))
        for partition in selected:
            (Path(output_dir) / f"{partition}.img").write_bytes(partition.encode())

    def run_payload(source, selected, *, output):
        return extract_payload_images(
            source, selected, output=output, extract_func=fake_extract
        )

    monkeypatch.setattr(workflow_service, "extract_payload_images", run_payload)
    runtime = _runtime(input_dir, unpack_dir)

    assert (
        workflow_service.unpack(["system", "vendor"], "payload", runtime=runtime)
        is True
    )
    assert calls == [(b"payload", ("system", "vendor"), str(input_dir), 1)]
    assert (input_dir / "system.img").read_bytes() == b"system"
    assert (input_dir / "vendor.img").read_bytes() == b"vendor"
    assert not (unpack_dir / "system.img").exists()
    assert not (unpack_dir / "vendor.img").exists()


def test_payload_reports_failure_when_selected_image_is_missing(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "payload.bin").write_bytes(b"payload")
    output = Output()

    def incomplete_extract(_stream, _selected, output_dir, _workers):
        (Path(output_dir) / "system.img").write_bytes(b"system")

    assert (
        extract_payload_images(
            str(input_dir),
            ["system", "vendor"],
            output=output,
            extract_func=incomplete_extract,
        )
        is False
    )
    assert output.reports
    assert not (input_dir / "vendor.img").exists()


def test_update_app_extracts_images_into_input_not_unpack(
    tmp_path, monkeypatch
) -> None:
    input_dir = tmp_path / "input"
    unpack_dir = tmp_path / "unpack"
    input_dir.mkdir()
    unpack_dir.mkdir()
    (input_dir / "UPDATE.APP").write_bytes(b"update")
    calls = []

    def fake_extract(source_path, output_dir, selected):
        calls.append((source_path, output_dir, tuple(selected)))
        for partition in selected:
            (Path(output_dir) / f"{partition}.img").write_bytes(partition.encode())

    def run_update(source, selected):
        return extract_update_app_images(source, selected, extract_func=fake_extract)

    monkeypatch.setattr(workflow_service, "extract_update_app_images", run_update)
    runtime = _runtime(input_dir, unpack_dir)

    assert (
        workflow_service.unpack(["boot", "vendor"], "update.app", runtime=runtime)
        is True
    )
    assert calls == [
        (str(input_dir / "UPDATE.APP"), str(input_dir), ("boot", "vendor"))
    ]
    assert (input_dir / "boot.img").exists()
    assert (input_dir / "vendor.img").exists()
    assert not (unpack_dir / "boot.img").exists()
    assert not (unpack_dir / "vendor.img").exists()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
