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
from src.logic.projects.convert.models import ConvertSelection
from src.logic.projects.convert.runtime_context import ConvertRuntimeContext
from src.logic.projects.convert import service


class _Output:
    def __init__(self):
        self.logs = []
        self.reports = []

    def log(self, text, **_kwargs):
        self.logs.append(str(text))

    def report(self, text, **_kwargs):
        self.reports.append(str(text))


def _runtime(work: Path, output: Path):
    sink = _Output()
    return ConvertRuntimeContext(
        work_path=str(work), output_path=str(output), output=sink
    ), sink


def test_same_format_conversion_is_a_non_destructive_noop(
    tmp_path, monkeypatch
) -> None:
    work = tmp_path / "work"
    output = tmp_path / "output"
    work.mkdir()
    output.mkdir()
    source = work / "system.img"
    source.write_bytes(b"raw image")
    runtime, sink = _runtime(work, output)
    monkeypatch.setattr(
        service,
        "_normalize_input",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("must not normalize")
        ),
    )

    result = service.convert_selection(
        ConvertSelection("raw", "raw", ["system.img"]), runtime=runtime
    )

    assert result is True
    assert source.read_bytes() == b"raw image"
    assert (output / "system.img").read_bytes() == b"raw image"
    assert sink.reports


def test_conversion_reports_failure_when_an_item_did_not_convert(
    tmp_path, monkeypatch
) -> None:
    work = tmp_path / "work"
    output = tmp_path / "output"
    work.mkdir()
    output.mkdir()
    (work / "system.img").write_bytes(b"raw")
    runtime, sink = _runtime(work, output)
    monkeypatch.setattr(service, "raw_to_sparse", lambda *_args, **_kwargs: False)

    result = service.convert_selection(
        ConvertSelection("raw", "sparse", ["system.img"]), runtime=runtime
    )

    assert result is False
    assert sink.reports == []
    assert any("system.img" in line for line in sink.logs)


def test_raw_candidate_from_work_is_copied_to_output_before_conversion(
    tmp_path, monkeypatch
) -> None:
    work = tmp_path / "work"
    output = tmp_path / "output"
    work.mkdir()
    output.mkdir()
    source = work / "vendor.img"
    source.write_bytes(b"raw")
    runtime, _sink = _runtime(work, output)
    converted_paths = []

    def fake_sparse(directory, basename):
        converted_paths.append(Path(directory) / f"{basename}.img")
        return True

    monkeypatch.setattr(service, "raw_to_sparse", fake_sparse)

    result = service.convert_selection(
        ConvertSelection("raw", "sparse", ["vendor.img"]), runtime=runtime
    )

    assert result is True
    assert converted_paths == [output / "vendor.img"]
    assert source.read_bytes() == b"raw"


def test_dat_family_source_and_transfer_list_are_staged_in_output(
    tmp_path, monkeypatch
) -> None:
    source = tmp_path / "input"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    (source / "vendor.new.dat.br").write_bytes(b"br")
    (source / "vendor.transfer.list").write_text("4\n", encoding="utf-8")
    runtime, _sink = _runtime(source, output)

    def fake_convert(work, request, *, runtime):
        assert (Path(work) / "vendor.new.dat.br").read_bytes() == b"br"
        assert (Path(work) / "vendor.transfer.list").read_text(
            encoding="utf-8"
        ) == "4\n"
        return service.ConvertResult(
            item_name=request.item_name,
            source_format=request.source_format,
            target_format=request.target_format,
            succeeded=True,
        )

    monkeypatch.setattr(service, "_convert_request", fake_convert)

    result = service.convert_selection(
        ConvertSelection("br", "raw", ["vendor.new.dat.br"]),
        runtime=runtime,
    )

    assert result is True
    assert (source / "vendor.new.dat.br").exists()
    assert (source / "vendor.transfer.list").exists()

if __name__ == "__main__":
    from tests.support.direct_execution import run_test_file

    raise SystemExit(run_test_file(__file__))
